from datetime import datetime, timezone
from voqryn_monitoring.domain_watch import DomainWatch, Observation, RegistrationStatus as S
from voqryn_monitoring.store import connect, add_watch, record_observation
from voqryn_monitoring.notifications import deliver_pending

T0 = datetime(2026, 10, 26, tzinfo=timezone.utc)


def test_retry_after_failure(tmp_path):
    with connect(tmp_path / "test.db") as db:
        add_watch(db, DomainWatch("w1", "a1", "example.com", status=S.REGISTERED))
        from datetime import timedelta
        record_observation(db, "w1", Observation(S.POSSIBLY_AVAILABLE, T0))
        record_observation(db, "w1", Observation(S.POSSIBLY_AVAILABLE, T0 + timedelta(days=1)))
        def broken(notification):
            raise RuntimeError("temporary failure")
        assert deliver_pending(db, broken, now=T0)["failed"] == 1
        received = []
        assert deliver_pending(db, received.append, now=T0)["delivered"] == 1
        assert len(received) == 1
        assert deliver_pending(db, received.append, now=T0)["delivered"] == 0
