"""Deterministic domain-watch state transitions; no network calls or notifications."""
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from enum import Enum


class RegistrationStatus(str, Enum):
    REGISTERED = "registered"
    POSSIBLY_AVAILABLE = "possibly_available"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class DomainWatch:
    id: str
    account_id: str
    domain: str
    status: RegistrationStatus = RegistrationStatus.UNKNOWN
    consecutive_observations: int = 0
    last_checked_at: datetime | None = None
    next_check_at: datetime | None = None
    enabled: bool = True


@dataclass(frozen=True)
class Observation:
    status: RegistrationStatus
    checked_at: datetime
    source: str = "rdap"


@dataclass(frozen=True)
class WatchEvent:
    watch_id: str
    kind: str
    observed_at: datetime
    previous: RegistrationStatus
    current: RegistrationStatus


def apply_observation(watch: DomainWatch, observation: Observation, *, interval: timedelta = timedelta(hours=24), confirmations: int = 2) -> tuple[DomainWatch, WatchEvent | None]:
    """Require repeated positive evidence before notifying about possible availability.

    UNKNOWN never overrides the last confirmed state; it only reschedules a check.
    The caller must persist the new watch and event atomically before delivery.
    """
    if confirmations < 2 or interval.total_seconds() <= 0:
        raise ValueError("confirmations >= 2 and a positive interval are required")
    if observation.checked_at.tzinfo is None:
        raise ValueError("checked_at must be timezone-aware")
    if watch.last_checked_at and observation.checked_at <= watch.last_checked_at:
        raise ValueError("observations must be strictly chronological")
    if not watch.enabled:
        raise ValueError("cannot check a disabled watch")
    next_at = observation.checked_at + interval
    if observation.status == RegistrationStatus.UNKNOWN:
        return replace(watch, last_checked_at=observation.checked_at, next_check_at=next_at, consecutive_observations=0), None
    if observation.status == watch.status:
        return replace(watch, last_checked_at=observation.checked_at, next_check_at=next_at, consecutive_observations=0), None
    # Only notify on a repeated change, not a single potentially transient response.
    count = watch.consecutive_observations + 1 if watch.status != observation.status else 0
    if count < confirmations:
        return replace(watch, last_checked_at=observation.checked_at, next_check_at=next_at, consecutive_observations=count), None
    updated = replace(watch, status=observation.status, consecutive_observations=0, last_checked_at=observation.checked_at, next_check_at=next_at)
    event = WatchEvent(watch.id, "registration_status_changed", observation.checked_at, watch.status, observation.status)
    return updated, event
