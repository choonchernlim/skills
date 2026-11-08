#!/usr/bin/env python3
"""Self-test for doc_impact.py in a throwaway Git repository.

Purpose: prove that a committed source change flags the doc that links it, that
editing the doc or a Docs-checked trailer clears it, and that an uncommitted change
only warns.
Usage: python3 scripts/test_doc_impact.py
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "doc_impact.py")
# Git runs only inside the throwaway repository: no inherited GIT_DIR or index, and no user or system config.
ENV = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")} | {
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
}


def sh(cwd: str, *args: str) -> None:
    subprocess.run(args, cwd=cwd, check=True, capture_output=True, env=ENV)


def write(root: str, rel: str, text: str) -> None:
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def commit(root: str, message: str) -> None:
    sh(root, "git", "add", "-A")
    sh(root, "git", "commit", "-q", "-m", message)


def run(root: str) -> tuple[int, str]:
    proc = subprocess.run([sys.executable, SCRIPT, "--base", "base"], cwd=root, capture_output=True, text=True, env=ENV)
    return proc.returncode, proc.stdout + proc.stderr


def fresh(tmp: str) -> str:
    root = os.path.join(tmp, "repo")
    os.makedirs(root)
    sh(root, "git", "init", "-q", "-b", "main")
    sh(root, "git", "config", "user.email", "test@example.com")
    sh(root, "git", "config", "user.name", "Test")
    write(root, "src/cart.py", "TOTAL = 1\n")
    write(root, "docs/cart.md", "# Cart\n\nThe [cart total](../src/cart.py) adds every line.\n")
    write(root, "docs/other.md", "# Other\n\nNo links here.\n")
    commit(root, "base")
    sh(root, "git", "tag", "base")
    return root


def main() -> int:
    failures: list[str] = []

    with tempfile.TemporaryDirectory() as tmp:
        root = fresh(tmp)
        write(root, "src/cart.py", "TOTAL = 2\n")
        code, out = run(root)
        if code != 0 or "docs/cart.md" not in out or "not committed" not in out:
            failures.append(f"an uncommitted change should warn about docs/cart.md and pass, got {code}:\n{out}")

        commit(root, "change the total")
        code, out = run(root)
        if code != 1 or "docs/cart.md" not in out or "docs/other.md" in out:
            failures.append(f"a committed change should fail on docs/cart.md only, got {code}:\n{out}")

        commit_with = "re-read the cart guide\n\nDocs-checked: docs/cart.md"
        sh(root, "git", "commit", "-q", "--allow-empty", "-m", commit_with)
        code, out = run(root)
        if code != 0 or "docs/cart.md:" in out:
            failures.append(f"a Docs-checked trailer should clear docs/cart.md, got {code}:\n{out}")

    with tempfile.TemporaryDirectory() as tmp:
        root = fresh(tmp)
        write(root, "src/cart.py", "TOTAL = 3\n")
        write(root, "docs/cart.md", "# Cart\n\nThe [cart total](../src/cart.py) adds every line and the tax.\n")
        commit(root, "change the total and its guide")
        code, out = run(root)
        if code != 0 or "docs/cart.md:" in out:
            failures.append(f"a doc edited in the range should not be flagged, got {code}:\n{out}")

    with tempfile.TemporaryDirectory() as tmp:
        root = fresh(tmp)
        write(root, "docs/adrs/0001-cart.md", "# Cart\n\nThe [cart](../../src/cart.py) owns the total.\n")
        write(root, "docs/my guide.md", "# Guide\n\n```mermaid\ngraph TD\n  C[\"<a href='../src/cart.py'>Cart 🌐</a>\"]\n```\n")
        sh(root, "git", "add", "-A")
        sh(root, "git", "commit", "-q", "-m", "add the decision and the guide")
        sh(root, "git", "tag", "-f", "base")
        sh(root, "git", "mv", "src/cart.py", "src/basket.py")
        commit(root, "rename the cart")
        code, out = run(root)
        if code != 1 or "docs/cart.md:" not in out or "docs/my guide.md:" not in out or "docs/adrs/" in out:
            failures.append(f"a rename should flag the guide and the diagram that link the old path, never the ADR, got {code}:\n{out}")

        sh(root, "git", "commit", "-q", "--allow-empty", "-m",
           "re-read both guides\n\nDocs-checked: docs/cart.md\nDocs-checked: docs/my guide.md")
        code, out = run(root)
        if code != 0:
            failures.append(f"one trailer per guide, spaces included, should clear both, got {code}:\n{out}")

    if failures:
        print("\n\n".join(failures))
        print(f"\n{len(failures)} failure(s)")
        return 1
    print("ok: uncommitted changes warn, committed changes fail, and an edit or a Docs-checked trailer clears a doc")
    return 0


if __name__ == "__main__":
    sys.exit(main())
