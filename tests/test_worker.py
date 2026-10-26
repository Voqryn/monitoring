from datetime import datetime, timezone, timedelta
from voqryn_monitoring.domain_watch import DomainWatch, RegistrationStatus as S
from voqryn_monitoring.store import connect, add_watch, pending_events
from voqryn_monitoring.worker import run_due

T0 = datetime(2026, 10, 26, tzinfo=timezone.utc)


def test_worker_confirms_and_queues(tmp_path):
    with connect(tmp_path / "db.sqlite") as db:
        add_watch(db, DomainWatch("w1", "acct", "example.com", status=S.REGISTERED))
        assert run_due(db, T0, lambda domain: S.POSSIBLY_AVAILABLE)["checked"] == 1
        assert run_due(db, T0 + timedelta(days=1), lambda domain: S.POSSIBLY_AVAILABLE)["checked"] == 1
        assert len(pending_events(db)) == 1


def test_worker_failure_is_unknown(tmp_path):
    with connect(tmp_path / "db.sqlite") as db:
        add_watch(db, DomainWatch("w1", "acct", "example.com"))
        def fail(domain):
            raise OSError("offline")
        assert run_due(db, T0, fail) == {"checked": 1, "failed": 1}
        assert pending_events(db) == []
