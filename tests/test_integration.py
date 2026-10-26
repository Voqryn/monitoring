"""Offline integration of scheduler, HTTP adapter, state machine and outbox."""
from datetime import datetime, timedelta, timezone
import httpx
from voqryn_monitoring.domain_watch import DomainWatch, RegistrationStatus as S
from voqryn_monitoring.network_checker import make_checker
from voqryn_monitoring.store import connect, add_watch, pending_events
from voqryn_monitoring.worker import run_due


def test_http_to_outbox(tmp_path):
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json={"status": "possibly_available"}))
    checker = make_checker("http://127.0.0.1:8000", transport=transport)
    t0 = datetime(2026, 10, 26, tzinfo=timezone.utc)
    with connect(tmp_path / "test.db") as db:
        add_watch(db, DomainWatch("watch-1", "account-1", "example.com", status=S.REGISTERED))
        assert run_due(db, t0, checker)["checked"] == 1
        assert not pending_events(db)
        assert run_due(db, t0 + timedelta(days=1), checker)["checked"] == 1
        assert len(pending_events(db)) == 1
