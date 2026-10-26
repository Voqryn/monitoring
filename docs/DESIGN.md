# Monitoring — M0 design

## Monitors
- Uptime: HTTP status, latency and optional content checks
- TLS: certificate chain, expiry and hostname validity
- DNS: selected record-set changes and resolution failures
- Domain: RDAP registration status and expiry when published

## Core entities
Monitor, Target, CheckSchedule, CheckResult, Incident, AlertRule, NotificationChannel, DeliveryAttempt.

## State transitions
Healthy -> suspected_failure -> confirmed_incident -> recovering -> resolved. Require configurable confirmation and recovery thresholds; deduplicate notifications and preserve event history.

## Scheduling and alerts
Use a durable job queue with jitter, concurrency caps, retries and per-tenant quotas. Record last successful check and next due time. Customer-facing notifications are opt-in and must respect suppression windows.

## M0 acceptance criteria
Deterministic incident state-machine tests, schedule validation, tenant isolation and mocked delivery adapter. No live outbound checks until safety controls are implemented.
