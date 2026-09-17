from __future__ import annotations

import argparse
import secrets
import time
from datetime import datetime, time as clock_time

from morning_digest.cli import main as digest_main


WINDOW_START = clock_time(8, 0)
WINDOW_END = clock_time(10, 50)


def choose_delay(now: datetime, randbelow=secrets.randbelow) -> int | None:
    """Choose a delay that keeps execution inside today's allowed window."""
    start = now.replace(hour=WINDOW_START.hour, minute=WINDOW_START.minute,
                        second=0, microsecond=0)
    end = now.replace(hour=WINDOW_END.hour, minute=WINDOW_END.minute,
                      second=0, microsecond=0)
    if now > end:
        return None
    earliest = max(now, start)
    wait_to_start = max(0, int((earliest - now).total_seconds()))
    available = max(0, int((end - earliest).total_seconds()))
    return wait_to_start + randbelow(available + 1)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run Morning Digest at a random time from 08:00 through 10:50")
    parser.add_argument("--config", default="config.yaml")
    args = parser.parse_args()

    now = datetime.now().astimezone()
    delay = choose_delay(now)
    if delay is None:
        print(f"Morning Digest skipped: random window already closed at {now.isoformat()}",
              flush=True)
        return 0
    target = datetime.fromtimestamp(now.timestamp() + delay, tz=now.tzinfo)
    print(f"Morning Digest scheduled randomly for {target.isoformat()}", flush=True)
    time.sleep(delay)

    current = datetime.now().astimezone()
    if current.time().replace(tzinfo=None) > WINDOW_END:
        print(f"Morning Digest skipped: Mac resumed after window at {current.isoformat()}",
              flush=True)
        return 0
    return digest_main(["--config", args.config])


if __name__ == "__main__":
    raise SystemExit(main())
