"""Notification outbox delivery primitives. No external delivery configured by default."""
from dataclasses import dataclass
from datetime import datetime, timezone
from sqlite3 import Connection, Row
from typing import Callable
from voqryn_monitoring.store import stamp


@dataclass(frozen=True)
class Notification:
    event_id: int
    watch_id: str
    kind: str
    previous: str
    current: str
    observed_at: str


def deliver_pending(db: Connection, sender: Callable[[Notification], None], *, limit: int = 25, now: datetime | None = None) -> dict[str, int]:
    """Deliver with retry-on-next-run semantics; at-least-once, not exactly-once.

    Callers must provide a sender that supports idempotency by event_id.
    No network calls are made by this module itself.
    """
    if not 1 <= limit <= 1000:
        raise ValueError("limit must be between 1 and 1000")
    if now is None:
        now = datetime.now(timezone.utc)
    results = {"delivered": 0, "failed": 0}
    rows = db.execute("SELECT * FROM outbox WHERE delivered_at IS NULL ORDER BY id LIMIT ?", (limit,)).fetchall()
    for row in rows:
        notice = Notification(row["id"], row["watch_id"], row["kind"], row["previous"], row["current"], row["observed_at"])
        try:
            sender(notice)
        except Exception:
            results["failed"] += 1
            continue
        with db:
            db.execute("UPDATE outbox SET delivered_at=? WHERE id=? AND delivered_at IS NULL", (stamp(now), notice.event_id))
        results["delivered"] += 1
    return results
