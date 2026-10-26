# Domain Watch M0.1 architecture

Status: initial code committed; tests not independently verified. No live scheduler, persistence, external RDAP polling or notifications yet.

## Data flow

1. Customer creates a watch for a validated domain.
2. Scheduler selects due enabled watches; per-registry rate limits apply.
3. Worker calls a restricted registry-aware RDAP adapter (Network API integration planned).
4. Observation maps to registered / possibly_available / unknown.
5. Pure state transition evaluates confirmation threshold.
6. Transaction persists observation, updated watch and outbox event together.
7. Notification worker delivers deduplicated emails or webhooks (later milestone).

## Important guarantees and caveats

- RDAP 404 is only **possibly available**, never proof of registrability.
- An RDAP timeout or unsupported TLD is **unknown**, not available.
- Require multiple confirmations for status changes; use separate timestamps and ideally independent evidence where available.
- Store expiry date, RDAP event timestamps and registry status codes separately in a later schema; expiration is not deletion.
- Polling frequency must respect registry terms and practical rate limits.
- Persist event IDs and an outbox to prevent duplicate notifications on retries.
- Customer account ownership and billing limits must be enforced at the API boundary.
- No registrar affiliate partner selected; registration referrals remain future optional functionality.

## Next milestone M0.2

SQLite-backed local prototype with schema migration, due-watch scheduler, deterministic fake RDAP adapter and outbox. Later migrate production storage to PostgreSQL and introduce real rate-limited RDAP adapter.
