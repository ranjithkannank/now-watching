#!/usr/bin/env python3
"""Now-watching state machine.

Commands:
  movie.py set "<title>"   start watching a movie (ends any current one)
  movie.py tick            promote the current movie to "last watched" once 3h have passed
  movie.py stop            end the current movie immediately (manual override)

State lives in ../data.json. The script only rewrites the file when something
actually changed, so callers can `git diff --quiet` to decide whether to commit.
"""
import json
import os
import sys
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data.json")
WATCH_HOURS = 3

FMT = "%Y-%m-%dT%H:%M:%SZ"


def now():
    return datetime.now(timezone.utc)


def iso(dt):
    return dt.strftime(FMT)


def parse(s):
    return datetime.strptime(s, FMT).replace(tzinfo=timezone.utc)


def load():
    with open(DATA) as f:
        return json.load(f)


def save(d):
    with open(DATA, "w") as f:
        json.dump(d, f, indent=2)
        f.write("\n")


def promote(d, finished_at):
    """Move the current movie into last_watched and the watched log."""
    cur = d.get("now_watching")
    if not cur:
        return
    finished = iso(finished_at)
    d["last_watched"] = {"title": cur["title"], "finished_at": finished}
    d.setdefault("watched", []).append(
        {
            "title": cur["title"],
            "started_at": cur["started_at"],
            "finished_at": finished,
        }
    )
    d["now_watching"] = None


def cmd_set(title):
    title = title.strip()
    if not title:
        print("empty title; ignoring")
        return
    d = load()
    cur = d.get("now_watching")
    if cur and cur.get("title", "").strip().lower() == title.lower():
        print("same title already playing; no change")
        return
    # Starting a new movie ends the previous one.
    promote(d, now())
    d["now_watching"] = {"title": title, "started_at": iso(now())}
    save(d)
    print(f"now watching: {title}")


def cmd_tick():
    d = load()
    cur = d.get("now_watching")
    if not cur:
        print("nothing playing")
        return
    started = parse(cur["started_at"])
    deadline = started + timedelta(hours=WATCH_HOURS)
    if now() >= deadline:
        # Record the flip at the 3h mark, not whenever the cron happened to run.
        promote(d, deadline)
        save(d)
        print(f"flipped: {cur['title']} -> last watched")
    else:
        print(f"still playing: {cur['title']} ({deadline - now()} left)")


def cmd_stop():
    d = load()
    cur = d.get("now_watching")
    if not cur:
        print("nothing playing")
        return
    promote(d, now())
    save(d)
    print(f"stopped: {cur['title']}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "set":
        cmd_set(" ".join(sys.argv[2:]))
    elif cmd == "tick":
        cmd_tick()
    elif cmd == "stop":
        cmd_stop()
    else:
        print(f"unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
