from datetime import datetime, timedelta, timezone
import pytest
from voqryn_monitoring.domain_watch import DomainWatch, Observation, RegistrationStatus as S, apply_observation

T0 = datetime(2026, 10, 26, tzinfo=timezone.utc)


def test_two_checks_before_alert():
    watch = DomainWatch("w1", "a1", "example.com", status=S.REGISTERED)
    first, event = apply_observation(watch, Observation(S.POSSIBLY_AVAILABLE, T0))
    assert event is None
    assert first.status == S.REGISTERED
    second, event = apply_observation(first, Observation(S.POSSIBLY_AVAILABLE, T0 + timedelta(days=1)))
    assert second.status == S.POSSIBLY_AVAILABLE
    assert event is not None and event.previous == S.REGISTERED


def test_unknown_does_not_trigger_alert():
    watch = DomainWatch("w1", "a1", "example.com", status=S.REGISTERED)
    updated, event = apply_observation(watch, Observation(S.UNKNOWN, T0))
    assert updated.status == S.REGISTERED and event is None


def test_stale_observation_rejected():
    watch = DomainWatch("w1", "a1", "example.com", last_checked_at=T0)
    with pytest.raises(ValueError):
        apply_observation(watch, Observation(S.REGISTERED, T0))


def test_disabled_watch_rejected():
    watch = DomainWatch("w1", "a1", "example.com", enabled=False)
    with pytest.raises(ValueError):
        apply_observation(watch, Observation(S.REGISTERED, T0))


def test_alternating_candidate_resets_confirmation():
    watch = DomainWatch("w1", "a1", "example.com", status=S.UNKNOWN)
    first, _ = apply_observation(watch, Observation(S.REGISTERED, T0))
    second, event = apply_observation(first, Observation(S.POSSIBLY_AVAILABLE, T0 + timedelta(days=1)))
    assert event is None
    assert second.status == S.UNKNOWN
    assert second.pending_status == S.POSSIBLY_AVAILABLE
    assert second.consecutive_observations == 1
    third, event = apply_observation(second, Observation(S.REGISTERED, T0 + timedelta(days=2)))
    assert event is None
    assert third.pending_status == S.REGISTERED


def test_unknown_resets_candidate():
    watch = DomainWatch("w1", "a1", "example.com", status=S.REGISTERED)
    first, _ = apply_observation(watch, Observation(S.POSSIBLY_AVAILABLE, T0))
    second, _ = apply_observation(first, Observation(S.UNKNOWN, T0 + timedelta(days=1)))
    assert second.pending_status is None
    third, event = apply_observation(second, Observation(S.POSSIBLY_AVAILABLE, T0 + timedelta(days=2)))
    assert event is None
    assert third.consecutive_observations == 1
