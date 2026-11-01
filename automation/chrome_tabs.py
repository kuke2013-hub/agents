#!/usr/bin/env python3
"""Safely bind and test Chrome tabs for AGENT CITY. Does not type or send messages.

Designed to sit alongside existing chrome_relay.py in ~/Downloads/agent_city_relay.
Uses macOS osascript / Google Chrome's AppleScript support, no third-party packages.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from pathlib import Path
from urllib.parse import urlparse

MAP_PATH = Path(__file__).resolve().with_name("tabs.local.json")

FRONT_SCRIPT = r'''
on run argv
  tell application "Google Chrome"
    if (count of windows) = 0 then error "There are no Chrome windows."
    return URL of active tab of front window
  end tell
end run
'''

LIST_SCRIPT = r'''
on run argv
  set outLines to {}
  tell application "Google Chrome"
    repeat with wi from 1 to (count of windows)
      repeat with ti from 1 to (count of tabs of window wi)
        set tabURL to URL of tab ti of window wi
        if tabURL contains "chatgpt.com" then
          set tabName to title of tab ti of window wi
          set end of outLines to ("Window " & wi & ", tab " & ti & " — " & tabName)
        end if
      end repeat
    end repeat
  end tell
  set AppleScript's text item delimiters to linefeed
  return outLines as text
end run
'''

SELECT_SCRIPT = r'''
on run argv
  set wantedURL to item 1 of argv
  tell application "Google Chrome"
    repeat with wi from 1 to (count of windows)
      repeat with ti from 1 to (count of tabs of window wi)
        if (URL of tab ti of window wi) is wantedURL then
          set active tab index of window wi to ti
          set index of window wi to 1
          activate
          return "Selected"
        end if
      end repeat
    end repeat
  end tell
  error "That ChatGPT tab is not open in Chrome."
end run
'''

def apple(script: str, *args: str) -> str:
    process = subprocess.run(
        ["osascript", "-e", script, *args],
        capture_output=True, text=True, timeout=20, check=False,
    )
    if process.returncode:
        raise RuntimeError(process.stderr.strip() or "osascript failed")
    return process.stdout.strip()

def check_chat_url(url: str) -> None:
    parts = urlparse(url)
    if parts.scheme != "https" or parts.netloc != "chatgpt.com" or "/c/" not in parts.path:
        raise ValueError("Select the actual Agent chat (not the project overview) in Chrome first.")

def load_tabs() -> dict[str, str]:
    if not MAP_PATH.exists():
        return {}
    data = json.loads(MAP_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Invalid tab mapping file.")
    return {str(k): str(v) for k, v in data.items()}

def save_tabs(data: dict[str, str]) -> None:
    # Local-only chat URLs must never be committed to the public GitHub repository.
    fd = os.open(str(MAP_PATH), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        json.dump(data, stream, indent=2)
        stream.write("\n")
    os.chmod(MAP_PATH, 0o600)

def bind(agent_id: str) -> None:
    url = apple(FRONT_SCRIPT)
    check_chat_url(url)
    data = load_tabs()
    for existing_id, existing_url in data.items():
        if existing_id != agent_id and existing_url == url:
            raise ValueError("This Chrome tab is already bound to Agent " + existing_id + ".")
    data[agent_id] = url
    save_tabs(data)
    print(f"PASS: Agent {agent_id} is bound to the currently selected Chrome chat tab.")
    print("Private chat URLs are kept locally in tabs.local.json (never posted to GitHub).")

def test_switching() -> None:
    data = load_tabs()
    for name in ("1", "2"):
        if name not in data:
            raise ValueError(f"Bind Agent {name} before running the test.")
        check_chat_url(data[name])
    original = apple(FRONT_SCRIPT)
    print("Testing tab switching only. No messages will be typed or sent.")
    try:
        for agent_id in ("1", "2", "1"):
            apple(SELECT_SCRIPT, data[agent_id])
            time.sleep(0.6)
            actual = apple(FRONT_SCRIPT)
            if actual != data[agent_id]:
                raise RuntimeError(f"Selected tab did not match Agent {agent_id}.")
            print(f"PASS: selected Agent {agent_id} and verified the active URL.")
    finally:
        # Do not leave Chrome on an unexpected tab if it is still open.
        try:
            apple(SELECT_SCRIPT, original)
        except RuntimeError:
            pass
    print("PASS: Agent 1 ↔ Agent 2 switching works. No chat messages sent.")

def main() -> int:
    parser = argparse.ArgumentParser(description="AGENT CITY safe Chrome tab-switch test")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true", help="List open ChatGPT Chrome tab titles")
    group.add_argument("--bind", choices=[str(n) for n in range(1, 6)],
                       help="Bind the currently selected Chrome tab to an agent number")
    group.add_argument("--test", action="store_true", help="Test Agent 1/2 tab switching without sending")
    args = parser.parse_args()
    try:
        if args.list:
            print(apple(LIST_SCRIPT) or "No ChatGPT tabs found in Chrome.")
        elif args.bind:
            bind(args.bind)
        else:
            test_switching()
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print("ERROR:", exc)
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
