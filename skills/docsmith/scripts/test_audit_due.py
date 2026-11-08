#!/usr/bin/env python3
"""Self-test for audit_due.py in a throwaway Git repository.

Purpose: prove that a repository with no full audit fails, that guides changed
since the last audit count up to the limit, and that ADRs never count.
Usage: python3 scripts/test_audit_due.py
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile

from test_doc_impact import ENV, commit, sh, write

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audit_due.py")


def run(root: str) -> tuple[int, str]:
    proc = subprocess.run([sys.executable, SCRIPT, "--every", "2"], cwd=root, capture_output=True, text=True, env=ENV)
    return proc.returncode, proc.stdout + proc.stderr


def main() -> int:
    failures: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        root = os.path.join(tmp, "repo")
        os.makedirs(root)
        sh(root, "git", "init", "-q", "-b", "main")
        sh(root, "git", "config", "user.email", "test@example.com")
        sh(root, "git", "config", "user.name", "Test")
        write(root, "docs/a.md", "# A\n")
        commit(root, "add the first guide")
        code, out = run(root)
        if code != 1 or "no full audit yet" not in out:
            failures.append(f"a repository with no audit should fail, got {code}:\n{out}")

        sh(root, "git", "commit", "-q", "--allow-empty", "-m", "v9: docs audit cadence\n\ndocs audit")
        code, out = run(root)
        if code != 1 or "no full audit yet" not in out:
            failures.append(f"only a subject that starts with the phrase resets the count, got {code}:\n{out}")

        sh(root, "git", "commit", "-q", "--allow-empty", "-m", "docs audit: grade every guide")
        write(root, "docs/b.md", "# B\n")
        write(root, "docs/adrs/0001-cart.md", "# Cart\n")
        write(root, "docs/adrs/0002-basket.md", "# Basket\n")
        commit(root, "add a guide and two decisions")
        code, out = run(root)
        if code != 0 or not out.startswith("1 guide(s)"):
            failures.append(f"one guide and two ADRs since the audit should pass, got {code}:\n{out}")

        write(root, "docs/a.md", "# A\n\nMore.\n")
        commit(root, "extend the first guide")
        code, out = run(root)
        if code != 1 or "docs/a.md" not in out or "a full audit is due" not in out:
            failures.append(f"two guides since the audit should make one due, got {code}:\n{out}")

        sh(root, "git", "commit", "-q", "--allow-empty", "-m", "docs audit: grade every guide again")
        sh(root, "git", "rm", "-q", "docs/b.md")
        sh(root, "git", "mv", "docs/a.md", "docs/c.md")
        commit(root, "drop one guide and rename the other")
        code, out = run(root)
        if code != 0 or not out.startswith("1 guide(s)"):
            failures.append(f"a deleted guide counts for nothing and a renamed one once, got {code}:\n{out}")

        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, env=ENV).stdout.strip()
        proc = subprocess.run([sys.executable, SCRIPT, "--every", "2", "--head", head, "--", "docs/c.md"],
                              cwd=root, capture_output=True, text=True, env=ENV)
        if proc.returncode != 0 or not proc.stdout.startswith("1 guide(s)"):
            failures.append(f"a passed guide list counts only those guides, got {proc.returncode}:\n{proc.stdout}{proc.stderr}")

    if failures:
        print("\n\n".join(failures))
        print(f"\n{len(failures)} failure(s)")
        return 1
    print("ok: no audit fails, guides since the last audit count to the limit, and ADRs never count")
    return 0


if __name__ == "__main__":
    sys.exit(main())
