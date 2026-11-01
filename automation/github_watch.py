#!/usr/bin/env python3
"""AGENT CITY read-only GitHub Issue #1 watcher.

Polls authenticated GitHub CLI every 60 seconds, printing only NEW real
[AGENT:N] issue comments. Does not submit ChatGPT prompts or post comments.
Runs only while this Python process is alive; Ctrl+C stops it.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = "kuke2013-hub/agents"
ISSUE = 1
AUTHOR = "kuke2013-hub"
STATE_PATH = Path(__file__).resolve().with_name("github_watch.local.json")
LOCK_PATH = Path(__file__).resolve().with_name("github_watch.local.lock")
AGENT_HEADER = re.compile(r"^\[AGENT:([1-5])\][ \t]+[^\r\n]+\r?\n")

def fetch_comments() -> list[dict]:
    if not shutil.which("gh"):
        raise RuntimeError("GitHub CLI (gh) is not installed or is not in PATH.")
    command = [
        "gh", "api", "--paginate", "--slurp",
        f"repos/{REPO}/issues/{ISSUE}/comments?per_page=100",
    ]
    result = subprocess.run(command, capture_output=True, text=True, timeout=40)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "GitHub CLI returned an error.")
    payload = json.loads(result.stdout)
    if not isinstance(payload, list):
        raise ValueError("GitHub API response was not a list.")
    items = []
    for page in payload:
        if not isinstance(page, list):
            raise ValueError("Unexpected GitHub API pagination response.")
        items.extend(comment for comment in page if isinstance(comment, dict))
    return sorted(items, key=lambda c: int(c.get("id") or 0))

def load_last_id() -> int | None:
    if not STATE_PATH.exists():
        return None
    data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return max(0, int(data["last_id"]))

def save_last_id(last_id: int) -> None:
    # Store only comment IDs; do not put message bodies or private data in logs.
    temporary = STATE_PATH.with_suffix(".json.tmp")
    temporary.write_text(json.dumps({"last_id": last_id}) + "\n", encoding="utf-8")
    temporary.chmod(0o600)
    temporary.replace(STATE_PATH)

def format_new_agent_comments(comments: list[dict], since: int) -> list[str]:
    result = []
    for item in comments:
        comment_id = int(item.get("id") or 0)
        if comment_id <= since or item.get("user", {}).get("login") != AUTHOR:
            continue
        body = item.get("body")
        if not isinstance(body, str):
            continue
        match = AGENT_HEADER.match(body)
        if match:
            result.append(
                f"NEW: Agent {match.group(1)} posted comment #{comment_id} "
                f"(https://github.com/{REPO}/issues/{ISSUE}#issuecomment-{comment_id})"
            )
    return result

def poll(*, from_start: bool) -> bool:
    """Return True after a successful authenticated poll."""
    comments = fetch_comments()
    max_id = max((int(c.get("id") or 0) for c in comments), default=0)
    previous = load_last_id()
    if previous is None and not from_start:
        save_last_id(max_id)
        print(f"BASELINE: tracking {len(comments)} existing GitHub comments. "
              "Only later comments will be announced.", flush=True)
        return True
    previous = previous or 0
    events = format_new_agent_comments(comments, previous)
    for event in events:
        print(event, flush=True)
    if max_id > previous:
        save_last_id(max_id)
    if not events:
        print(f"CHECK OK: {len(comments)} total comments, no new agent messages.", flush=True)
    return True

def main() -> int:
    parser = argparse.ArgumentParser(description="Watch real AGENT CITY GitHub comments")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--once", action="store_true", help="One GitHub poll and exit")
    group.add_argument("--watch", action="store_true", help="Poll every 60 seconds until Ctrl+C")
    parser.add_argument("--interval", type=int, default=60,
                        help="Interval seconds in --watch mode; default 60 (min 30)")
    parser.add_argument("--from-start", action="store_true",
                        help="On first run, display existing labelled agent comments")
    args = parser.parse_args()
    if args.interval < 30:
        parser.error("--interval must be at least 30 seconds.")
    try:
        with LOCK_PATH.open("a+") as lock:
            try:
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                print("ERROR: another watcher is already running here.", file=sys.stderr)
                return 1
            print("AGENT CITY GitHub watcher started (read-only, no ChatGPT API).", flush=True)
            while True:
                begin = time.monotonic()
                try:
                    poll(from_start=args.from_start)
                except (RuntimeError, ValueError, json.JSONDecodeError, subprocess.TimeoutExpired) as exc:
                    print("CHECK FAILED:", exc, file=sys.stderr, flush=True)
                    if args.once:
                        return 1
                if args.once:
                    return 0
                # Approximate one-minute cadence, including the GitHub request time.
                time.sleep(max(0.0, args.interval - (time.monotonic() - begin)))
    except KeyboardInterrupt:
        print("\nStopped by BOSS (Ctrl+C).", flush=True)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
