"""Single-process domain watch worker; checker is injected for safe testing."""
from datetime import datetime
from typing import Callable
from sqlite3 import Connection
from voqryn_monitoring.domain_watch import Observation, RegistrationStatus
from voqryn_monitoring.store import due_watches, record_observation

Checker = Callable[[str], RegistrationStatus]


def run_due(db: Connection, now: datetime, checker: Checker, *, limit: int = 100) -> dict[str, int]:
    """Run a bounded batch; failed checks become UNKNOWN observations.

    A production scheduler must add leases, per-registry throttling and retry policies.
    """
    result = {"checked": 0, "failed": 0}
    for watch in due_watches(db, now, limit=limit):
        try:
            status = checker(watch.domain)
            if not isinstance(status, RegistrationStatus):
                raise ValueError("checker returned invalid status")
        except Exception:
            status = RegistrationStatus.UNKNOWN
            result["failed"] += 1
        record_observation(db, watch.id, Observation(status=status, checked_at=now))
        result["checked"] += 1
    return result
