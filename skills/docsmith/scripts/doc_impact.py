#!/usr/bin/env python3
"""List the docs a code change may have made stale.

Purpose: a doc that links a source file can go stale when that file changes. This
script finds every doc that links a file changed since `--base` and was not edited
in the same range, so a writer re-reads it.

A committed change fails until each listed doc is edited in the range or named in a
`Docs-checked: <doc path>` trailer of a commit in the range. A change that is not
committed yet only warns, because it has no commit message to carry the trailer.

Usage: python3 doc_impact.py --base origin/main [--head <commit>] [-- docs/a.md ...]
Pass `--head` as a commit id when a cache keys on the command, so a new commit reruns it.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lint_docs import Doc, is_adr_file, linked_paths, segment  # noqa: E402


def git(root: str, *args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout


def paths(output: str) -> set[str]:
    return {p for p in output.split("\0") if p}


def linked_files(root: str, doc: str) -> set[str]:
    """Root-relative paths of the files `doc` links, resolved exactly as the lint resolves them.

    A folder link matches no changed file: link the file a guide describes."""
    path = os.path.join(root, doc)
    try:
        with open(path, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
    except (OSError, UnicodeDecodeError) as error:
        raise RuntimeError(f"{doc}: cannot read it: {error}") from error
    return linked_paths(Doc(path, lines), segment(lines), root)


def tracked_docs(root: str, given: list[str]) -> list[str]:
    """The given docs as root-relative paths, or every Markdown file Git tracks or would track."""
    if given:
        return [os.path.relpath(os.path.abspath(d), root).replace(os.sep, "/") for d in given]
    return sorted(paths(git(root, "ls-files", "-z", "--cached", "--others", "--exclude-standard", "*.md")))


def commit(root: str, ref: str) -> str:
    """The commit id a ref names, so no ref reaches git where it could read as an option."""
    return git(root, "rev-parse", "--verify", "--quiet", "--end-of-options", f"{ref}^{{commit}}").strip()


def acknowledged(root: str, base: str, head: str) -> set[str]:
    """Doc paths named in a `Docs-checked:` trailer of a commit in `base..head`."""
    log = git(root, "log", "--format=%(trailers:key=Docs-checked,valueonly)", f"{base}..{head}")
    return {line.strip() for line in log.splitlines() if line.strip()}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="List docs that link a changed source file but were not edited.")
    ap.add_argument("--base", required=True, help="the ref this branch is compared with, such as origin/main")
    ap.add_argument("--head", default="HEAD", help="the last commit of the range; changes after it count as not committed")
    ap.add_argument("docs", nargs="*", help="the docs to consider, after '--'; defaults to every Markdown file Git tracks or would track")
    args = ap.parse_args(argv)
    if not args.base:
        print("doc_impact: the base is unknown here; fetch the branch it is compared with", file=sys.stderr)
        return 2
    try:
        root = git(os.getcwd(), "rev-parse", "--show-toplevel").strip()
        base, head = commit(root, args.base), commit(root, args.head)
        committed = paths(git(root, "diff", "-z", "--name-only", "--no-renames", f"{base}...{head}", "--"))
        pending = paths(git(root, "diff", "-z", "--name-only", "--no-renames", head, "--"))
        pending |= paths(git(root, "ls-files", "-z", "--others", "--exclude-standard"))
        docs = tracked_docs(root, args.docs)
        checked = acknowledged(root, base, head)
        failures = warnings = 0
        edited = {p for p in committed | pending if p.endswith(".md")}
        committed -= edited
        pending -= edited
        for doc in docs if committed or pending else []:
            # An ADR records a decision on its date, so code changing under it is expected.
            if doc in edited or doc in checked or is_adr_file(doc):
                continue
            links = linked_files(root, doc)
            stale = sorted(links & committed)
            if stale:
                failures += 1
                print(f"{doc}: links {', '.join(stale)}, changed on this branch; edit the doc, or end a commit message with the trailer 'Docs-checked: {doc}'")
                continue
            unsaved = sorted(links & pending)
            if unsaved:
                warnings += 1
                print(f"{doc}: links {', '.join(unsaved)}, changed but not committed; re-read the doc before you commit")
    except RuntimeError as error:
        print(error, file=sys.stderr)
        return 2
    print(f"{failures} stale doc(s), {warnings} to re-read")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
