# Domain Watch M0.5 — local Debian worker operations

**Status:** prototype configuration only. Not deployed or enabled. No live notification delivery.

## Architecture

- Network API listens on localhost port 8000.
- Domain Watch is a one-shot Python process started by a systemd timer.
- SQLite state is stored in `/var/lib/voqryn/domain-watch.sqlite`.
- The timer wakes every 15 minutes, but **individual watches remain due every 24 hours** by default; timer cadence is not polling frequency.
- The service runs as a dedicated unprivileged `voqryn` account.

## Example manual installation (after reviewing security and tests)

1. Install Python >=3.12 and clone the monitoring repository into `/opt/voqryn/monitoring`.
2. Create a dedicated `voqryn` system user and group, and a virtual environment under the checkout; install the package with `python -m pip install .`.
3. Ensure `/var/lib/voqryn` is writable only by the dedicated service account.
4. Copy both unit files to `/etc/systemd/system/`, then run `systemctl daemon-reload`.
5. For an explicit single run, use `systemctl start voqryn-domain-watch.service`.
6. Inspect `journalctl -u voqryn-domain-watch.service` and `systemctl status voqryn-domain-watch.service`.
7. Only after approval and successful verification, enable the schedule using `systemctl enable --now voqryn-domain-watch.timer`.

## Production blockers

- Confirm passing tests and review external API behavior.
- Add multi-worker-safe leases or keep one strictly serialized worker.
- Enforce per-registry query budgets, retry/backoff and global rate limits.
- Implement account authorization, customer consent, retention and backups.
- Add outbox delivery with idempotency and retries; no emails are sent today.
- Introduce metrics and health reporting before production.
