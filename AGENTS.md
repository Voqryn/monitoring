# Voqryn Monitoring — Agent Instructions

Build reliable uptime, TLS certificate, DNS and domain monitoring with explainable alerts.

## Principles
- Reuse network-api diagnostics where appropriate; avoid duplicated network logic.
- Prevent SSRF and abuse in customer-configured targets.
- Model check schedules, retry policies, incident state, notification preferences and retention explicitly.
- Avoid false alerts with confirmation checks and clear incident transitions.
- Do not send production notifications or incur paid service charges without approval.

## M0 scope
Domain model, scheduler interface, alert state machine and deterministic tests.
