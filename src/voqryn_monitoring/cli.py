"""Explicit, one-shot local Domain Watch worker (no background daemon)."""
import argparse
import json
import fcntl
import os
from datetime import datetime, timezone
from voqryn_monitoring.network_checker import make_checker
from voqryn_monitoring.store import connect
from voqryn_monitoring.worker import run_due


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a single bounded Domain Watch batch")
    parser.add_argument("--db", required=True, help="Path to local SQLite database")
    parser.add_argument("--api-base", default="http://127.0.0.1:8000", help="Network API origin")
    parser.add_argument("--limit", type=int, default=25)
    args = parser.parse_args()
    checker = make_checker(args.api_base)
    lock_path = args.db + ".lock"
    with open(lock_path, "a+", encoding="utf-8") as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print(json.dumps({"skipped": "worker_already_running"}))
            return
        with connect(args.db) as db:
            result = run_due(db, datetime.now(timezone.utc), checker, limit=args.limit)
        print(json.dumps(result))


if __name__ == "__main__":
    main()
