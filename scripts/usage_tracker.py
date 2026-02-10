#!/usr/bin/env python3
"""Context7 API usage tracker for smart-search skill.

Tracks monthly Context7 API calls and provides quota management.
Data stored in ~/.claude/skills/smart-search/data/usage.json

Usage:
    python3 usage_tracker.py status          # Show current month usage
    python3 usage_tracker.py increment       # Record one API call
    python3 usage_tracker.py check           # Check if quota available (exit 0=yes, 1=no)
    python3 usage_tracker.py reset           # Reset current month counter
    python3 usage_tracker.py set-limit N     # Change monthly limit (default 1000)
    python3 usage_tracker.py set-threshold N # Change warning threshold (default 900)
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

DATA_DIR = Path.home() / ".claude" / "skills" / "smart-search" / "data"
USAGE_FILE = DATA_DIR / "usage.json"
DEFAULT_LIMIT = 1000
DEFAULT_THRESHOLD = 900


def load_data():
    if USAGE_FILE.exists():
        with open(USAGE_FILE) as f:
            data = json.load(f)
    else:
        data = {}

    current_month = datetime.now().strftime("%Y-%m")
    if data.get("month") != current_month:
        data = {
            "month": current_month,
            "count": 0,
            "limit": data.get("limit", DEFAULT_LIMIT),
            "threshold": data.get("threshold", DEFAULT_THRESHOLD),
            "history": data.get("history", {}),
        }
        # Save previous month to history
        if "month" in data:
            pass  # Already reset

    if "limit" not in data:
        data["limit"] = DEFAULT_LIMIT
    if "threshold" not in data:
        data["threshold"] = DEFAULT_THRESHOLD
    if "history" not in data:
        data["history"] = {}

    return data


def save_data(data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(USAGE_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def cmd_status():
    data = load_data()
    remaining = data["limit"] - data["count"]
    pct = (data["count"] / data["limit"]) * 100 if data["limit"] > 0 else 0

    status = "OK"
    if data["count"] >= data["limit"]:
        status = "EXHAUSTED"
    elif data["count"] >= data["threshold"]:
        status = "WARNING"

    print(json.dumps({
        "month": data["month"],
        "count": data["count"],
        "limit": data["limit"],
        "remaining": remaining,
        "percentage": round(pct, 1),
        "threshold": data["threshold"],
        "status": status,
    }, indent=2, ensure_ascii=False))


def cmd_increment():
    data = load_data()
    data["count"] += 1
    save_data(data)

    remaining = data["limit"] - data["count"]
    status = "OK"
    if data["count"] >= data["limit"]:
        status = "EXHAUSTED"
    elif data["count"] >= data["threshold"]:
        status = "WARNING"

    print(json.dumps({
        "count": data["count"],
        "remaining": remaining,
        "status": status,
    }, indent=2, ensure_ascii=False))


def cmd_check():
    data = load_data()
    if data["count"] >= data["limit"]:
        print(json.dumps({"available": False, "reason": "Monthly limit reached", "count": data["count"], "limit": data["limit"]}))
        sys.exit(1)
    elif data["count"] >= data["threshold"]:
        print(json.dumps({"available": True, "warning": True, "remaining": data["limit"] - data["count"]}))
        sys.exit(0)
    else:
        print(json.dumps({"available": True, "warning": False, "remaining": data["limit"] - data["count"]}))
        sys.exit(0)


def cmd_reset():
    data = load_data()
    old_count = data["count"]
    data["history"][data["month"]] = old_count
    data["count"] = 0
    save_data(data)
    print(json.dumps({"reset": True, "previous_count": old_count}))


def cmd_set_limit(n):
    data = load_data()
    data["limit"] = int(n)
    save_data(data)
    print(json.dumps({"limit": data["limit"]}))


def cmd_set_threshold(n):
    data = load_data()
    data["threshold"] = int(n)
    save_data(data)
    print(json.dumps({"threshold": data["threshold"]}))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "status":
        cmd_status()
    elif cmd == "increment":
        cmd_increment()
    elif cmd == "check":
        cmd_check()
    elif cmd == "reset":
        cmd_reset()
    elif cmd == "set-limit" and len(sys.argv) > 2:
        cmd_set_limit(sys.argv[2])
    elif cmd == "set-threshold" and len(sys.argv) > 2:
        cmd_set_threshold(sys.argv[2])
    else:
        print(__doc__)
        sys.exit(1)
