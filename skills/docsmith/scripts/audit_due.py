#!/usr/bin/env python3
"""Fail when a full documentation audit is due.

Purpose: docs drift as guides are added and edited one at a time. A full audit
grades every guide for every audience, and this script says when one is due:
once a given number of guides changed since the last commit whose subject
starts with "docs audit", or when no such commit exists yet. ADRs do not count,
because a dated record is never re-graded.

Usage: python3 audit_due.py [--every 10] [--head <commit>] [-- docs/a.md ...]
Pass `--head` as a commit id when a cache keys on the command, so a new commit reruns it.
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from doc_impact import commit, git, paths, tracked_docs  # noqa: E402
from lint_docs import is_adr_file  # noqa: E402

AUDIT_SUBJECT = "docs audit"


def last_audit(root: str, head: str) -> str:
    """The newest commit at or before `head` whose subject starts with the audit phrase, or ''."""
    log = git(root, "log", "-i", f"--grep={AUDIT_SUBJECT}", "--format=%H%x00%s", head, "--")
    for line in log.splitlines():
        sha, _, subject = line.partition("\0")
        if subject.lower().startswith(AUDIT_SUBJECT):
            return sha
    return ""


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Fail when a full documentation audit is due.")
    ap.add_argument("--every", type=int, default=10, help="the number of changed guides that makes an audit due")
    ap.add_argument("--head", default="HEAD", help="the last commit to count")
    ap.add_argument("docs", nargs="*", help="the guides that count, after '--'; defaults to every Markdown file Git tracks or would track")
    args = ap.parse_args(argv)
    try:
        root = git(os.getcwd(), "rev-parse", "--show-toplevel").strip()
        head = commit(root, args.head)
        since = last_audit(root, head)
        if not since:
            print(f"no full audit yet; run one and start its commit subject with '{AUDIT_SUBJECT}'")
            return 1
        changed = paths(git(root, "diff", "-z", "--name-only", "--no-renames", f"{since}..{head}", "--"))
        guides = set(tracked_docs(root, args.docs))
    except RuntimeError as error:
        print(error, file=sys.stderr)
        return 2
    counted = sorted(p for p in changed & guides if not is_adr_file(p))
    print(f"{len(counted)} guide(s) changed since the last full audit {since[:8]}; one is due at {args.every}")
    if len(counted) < args.every:
        return 0
    print("\n".join(counted))
    print(f"a full audit is due; grade every guide for every audience, and start its commit subject with '{AUDIT_SUBJECT}'")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
