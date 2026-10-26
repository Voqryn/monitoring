from datetime import datetime, timedelta, timezone
import pytest
from voqryn_monitoring.domain_watch import DomainWatch, Observation, RegistrationStatus as S
from voqryn_monitoring.store import connect, add_watch, due_watches, record_observation, pending_events

T0 = datetime(2026, 10, 26, tzinfo=timezone.utc)


def test_due_schedule_and_outbox(tmp_path):
    with connect(tmp_path / "watch.db") as db:
        add_watch(db, DomainWatch("w1", "acct", "example.com", status=S.REGISTERED))
        assert len(due_watches(db, T0)) == 1
        first = record_observation(db, "w1", Observation(S.POSSIBLY_AVAILABLE, T0))
        assert first.status == S.REGISTERED
        assert due_watches(db, T0) == []
        assert pending_events(db) == []
        record_observation(db, "w1", Observation(S.POSSIBLY_AVAILABLE, T0 + timedelta(days=1)))
        events = pending_events(db)
        assert len(events) == 1
        assert events[0]["current"] == "possibly_available"


def test_failed_duplicate_is_atomic(tmp_path):
    with connect(tmp_path / "watch.db") as db:
        add_watch(db, DomainWatch("w1", "acct", "example.com"))
        record_observation(db, "w1", Observation(S.REGISTERED, T0))
        with pytest.raises(ValueError):
            record_observation(db, "w1", Observation(S.REGISTERED, T0))
        assert db.execute("SELECT COUNT(*) FROM observations").fetchone()[0] == 1


def test_disabled_not_due(tmp_path):
    with connect(tmp_path / "watch.db") as db:
        add_watch(db, DomainWatch("w1", "acct", "example.net", enabled=False))
        assert due_watches(db, T0) == []
