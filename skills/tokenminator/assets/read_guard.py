#!/usr/bin/env python3
"""Claude Code PreToolUse hook that refuses to open a large text file whole.

Copy this file to scripts/read_guard.py and never edit it.
Purpose: make "read files in slices" a setting, not a habit. A Read with no offset or
limit on a file over the limit is denied with the cheaper way to get there.
Invariants: standard library only; fails open, so a broken hook never blocks work;
a Read that already names an offset, a limit, or pages always passes.
Usage: registered under hooks.PreToolUse with matcher "Read"; reads the hook JSON on stdin.
"""
from __future__ import annotations

import json
import os
import sys

LIMIT_BYTES = int(os.environ.get("READ_GUARD_BYTES", "40000"))
# The Read tool renders these instead of returning their bytes as text.
RENDERED = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".pdf", ".ipynb"}


def main() -> int:
    try:
        event = json.load(sys.stdin)
        call = event.get("tool_input") or {}
        path = call.get("file_path") or ""
        if event.get("tool_name") != "Read" or not path:
            return 0
        if any(call.get(key) not in (None, "") for key in ("offset", "limit", "pages")):
            return 0
        if os.path.splitext(path)[1].lower() in RENDERED:
            return 0
        size = os.path.getsize(path)
    except (OSError, ValueError, AttributeError, TypeError):
        return 0
    if size <= LIMIT_BYTES:
        return 0
    name = os.path.basename(path)
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": (
            f"{name} is {size // 1024} KB (~{size // 4} tokens). Find the range first: run "
            f"`scripts/outline` on it or search it, then Read again with offset and limit."
        ),
    }}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
