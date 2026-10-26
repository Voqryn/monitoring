"""SQLite prototype: transactional observations, watch state and notification outbox."""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from voqryn_monitoring.domain_watch import DomainWatch, Observation, RegistrationStatus, apply_observation

SCHEMA = """
CREATE TABLE IF NOT EXISTS watches (
 id TEXT PRIMARY KEY, account_id TEXT NOT NULL, domain TEXT NOT NULL,
 status TEXT NOT NULL, consecutive_observations INTEGER NOT NULL DEFAULT 0,
 last_checked_at TEXT, next_check_at TEXT, enabled INTEGER NOT NULL DEFAULT 1,
 pending_status TEXT,
 UNIQUE(account_id, domain)
);
CREATE TABLE IF NOT EXISTS observations (
 id INTEGER PRIMARY KEY AUTOINCREMENT, watch_id TEXT NOT NULL REFERENCES watches(id),
 status TEXT NOT NULL, checked_at TEXT NOT NULL, source TEXT NOT NULL,
 UNIQUE(watch_id, checked_at)
);
CREATE TABLE IF NOT EXISTS outbox (
 id INTEGER PRIMARY KEY AUTOINCREMENT, watch_id TEXT NOT NULL REFERENCES watches(id),
 kind TEXT NOT NULL, previous TEXT NOT NULL, current TEXT NOT NULL,
 observed_at TEXT NOT NULL, delivered_at TEXT,
 UNIQUE(watch_id, kind, observed_at)
);
CREATE INDEX IF NOT EXISTS watches_due ON watches(enabled, next_check_at);
"""


def connect(path: str | Path) -> sqlite3.Connection:
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.executescript(SCHEMA)
    columns = {row[1] for row in db.execute('PRAGMA table_info(watches)')}
    if 'pending_status' not in columns:
        db.execute('ALTER TABLE watches ADD COLUMN pending_status TEXT')
    return db


def stamp(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        raise ValueError("timestamps must be timezone-aware")
    return value.astimezone(timezone.utc).isoformat()


def parse(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def from_row(row: sqlite3.Row) -> DomainWatch:
    return DomainWatch(row["id"], row["account_id"], row["domain"], RegistrationStatus(row["status"]), row["consecutive_observations"], parse(row["last_checked_at"]), parse(row["next_check_at"]), bool(row["enabled"]), RegistrationStatus(row["pending_status"]) if row["pending_status"] else None)


def add_watch(db: sqlite3.Connection, watch: DomainWatch) -> None:
    with db:
        db.execute("INSERT INTO watches(id,account_id,domain,status,consecutive_observations,last_checked_at,next_check_at,enabled,pending_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                   (watch.id, watch.account_id, watch.domain, watch.status.value, watch.consecutive_observations, stamp(watch.last_checked_at), stamp(watch.next_check_at), int(watch.enabled), watch.pending_status.value if watch.pending_status else None))


def due_watches(db: sqlite3.Connection, now: datetime, limit: int = 100) -> list[DomainWatch]:
    if not 1 <= limit <= 1000:
        raise ValueError("limit out of range")
    rows = db.execute("SELECT * FROM watches WHERE enabled=1 AND (next_check_at IS NULL OR next_check_at<=?) ORDER BY next_check_at, id LIMIT ?", (stamp(now), limit)).fetchall()
    return [from_row(row) for row in rows]


def record_observation(db: sqlite3.Connection, watch_id: str, observation: Observation) -> DomainWatch:
    """Persist state, observation and outbox atomically. No delivery occurs here."""
    with db:
        row = db.execute("SELECT * FROM watches WHERE id=?", (watch_id,)).fetchone()
        if row is None:
            raise KeyError(watch_id)
        updated, event = apply_observation(from_row(row), observation)
        db.execute("INSERT INTO observations(watch_id,status,checked_at,source) VALUES(?,?,?,?)",
                   (watch_id, observation.status.value, stamp(observation.checked_at), observation.source))
        db.execute("UPDATE watches SET status=?, consecutive_observations=?, last_checked_at=?, next_check_at=?, pending_status=? WHERE id=?",
                   (updated.status.value, updated.consecutive_observations, stamp(updated.last_checked_at), stamp(updated.next_check_at), updated.pending_status.value if updated.pending_status else None, watch_id))
        if event:
            db.execute("INSERT INTO outbox(watch_id,kind,previous,current,observed_at) VALUES(?,?,?,?,?)",
                       (watch_id, event.kind, event.previous.value, event.current.value, stamp(event.observed_at)))
    return updated


def pending_events(db: sqlite3.Connection, limit: int = 100) -> list[sqlite3.Row]:
    if not 1 <= limit <= 1000:
        raise ValueError("limit out of range")
    return db.execute("SELECT * FROM outbox WHERE delivered_at IS NULL ORDER BY id LIMIT ?", (limit,)).fetchall()
