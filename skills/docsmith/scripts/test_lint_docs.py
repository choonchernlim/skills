#!/usr/bin/env python3
"""Fixture self-test for lint_docs.py.

Purpose: prove the linter accepts the good fixture set and raises the expected
code for every bad fixture, so a rule change cannot silently disable a check.
The Mermaid examples in the references are linted too, so they cannot drift.
Usage: python3 scripts/test_lint_docs.py
"""
from __future__ import annotations

import glob
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
LINT = os.path.join(HERE, "lint_docs.py")
GOOD = os.path.join(HERE, "fixtures", "good")
BAD = os.path.join(HERE, "fixtures", "bad")
REFERENCES = os.path.join(HERE, "..", "references")

EXPECTED = {
    "hdr.md": "HDR",
    "hdr-type.md": "HDR",
    "ttl.md": "TTL",
    "ttl-readme.md": "TTL",
    "hcase.md": "HCASE",
    "empty.md": "EMPTY",
    "toc-missing.md": "TOC",
    "toc-order.md": "TOC",
    "toc-adr.md": "TOC",
    "cap.md": "CAP",
    "fence.md": "FENCE",
    "run.md": "RUN",
    "sent.md": "SENT",
    "para.md": "PARA",
    "cell.md": "CELL",
    "bul.md": "BUL",
    "list.md": "LIST",
    "h2n.md": "H2N",
    "word.md": "WORD",
    "meta.md": "META",
    "link.md": "LINK",
    "mmd-direction.md": "MMD",
    "mmd-click.md": "MMD",
    "mmd-table.md": "MMD",
    "mmd-small.md": "MMD",
    "mmd-label.md": "MMD",
    "mmd-lead.md": "MMD",
    "mmd-disconnected.md": "MMD",
    "mmd-sequence.md": "MMD",
    "mmd-boundary.md": "MMD",
    "mmd-boundary-width.md": "MMD",
    "mmd-boundary-direction.md": "MMD",
    "mmd-boundary-sideways.md": "MMD",
    "mmd-frontmatter.md": "MMD",
    "mmd-frontmatter-changed.md": "MMD",
    "mmd-frontmatter-stray.md": "MMD",
    "view/docs/architecture.md": "VIEW",
    "mmd-infrastructure-generic.md": "MMD",
}
EXPECTED_COUNTS = {
    "link.md": ("LINK", 5),
    "word.md": ("WORD", 3),
    "mmd-label.md": ("MMD", 5),
    "mmd-sequence.md": ("MMD", 3),
    "mmd-boundary.md": ("MMD", 1),
    "mmd-boundary-width.md": ("MMD", 1),
    "mmd-boundary-direction.md": ("MMD", 1),
    "mmd-boundary-sideways.md": ("MMD", 1),
    "mmd-frontmatter.md": ("MMD", 1),
    "mmd-frontmatter-changed.md": ("MMD", 1),
    "mmd-frontmatter-stray.md": ("MMD", 1),
}


def run(paths: list[str], root: str, *flags: str) -> tuple[int, str]:
    proc = subprocess.run([sys.executable, LINT, *paths, "--root", root, *flags], capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr


def reference_examples() -> list[tuple[str, str]]:
    """Return (name, document) for every Markdown example fenced inside a Mermaid reference."""
    out: list[tuple[str, str]] = []
    for path in sorted(glob.glob(os.path.join(REFERENCES, "mermaid*.md"))):
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        for n, m in enumerate(re.finditer(r"^````markdown\n(.*?)^````$", text, re.S | re.M)):
            name = f"{os.path.basename(path)[:-3]}-{n}.md"
            head = "<!--\nPurpose: Example.\nType: explanation\n-->\n\n# Example\n\nAudience: the self-test.\n\n"
            body = m.group(1)
            if body.lstrip().startswith("```mermaid"):
                body = "Lead.\n\n" + body
            out.append((name, head + body))
    return out


def main() -> int:
    failures: list[str] = []

    good = sorted(glob.glob(os.path.join(GOOD, "**", "*.md"), recursive=True))
    code, out = run(good, GOOD)
    if code != 0:
        failures.append(f"good fixtures should pass but returned {code}:\n{out}")

    for name, expected in sorted(EXPECTED.items()):
        path = os.path.join(BAD, name)
        code, out = run([path], BAD)
        if code == 0 or f" {expected} " not in out:
            failures.append(f"{name}: expected code {expected}, got:\n{out}")
        if name in EXPECTED_COUNTS:
            want_code, want_n = EXPECTED_COUNTS[name]
            got = out.count(f" {want_code} ")
            if got != want_n:
                failures.append(f"{name}: expected {want_n} x {want_code}, got {got}:\n{out}")

    code, out = run([os.path.join(BAD, "dup-a.md"), os.path.join(BAD, "dup-b.md")], BAD)
    if " DUP " not in out:
        failures.append(f"dup-a/dup-b: expected DUP, got:\n{out}")

    code, out = run([os.path.join(BAD, "dup-c.md"), os.path.join(BAD, "dup-d.md")], BAD)
    if " DUP " not in out:
        failures.append(f"dup-c/dup-d: expected DUP for a paraphrase, got:\n{out}")

    code, out = run([os.path.join(BAD, "edge-a.md"), os.path.join(BAD, "edge-b.md")], BAD)
    if out.count(" DUP ") != 1 or "'Alpha' to 'Beta' is already drawn" not in out:
        failures.append(f"edge-a/edge-b: expected one DUP for the redrawn relationship, got:\n{out}")

    code, out = run([os.path.join(BAD, "node-a.md"), os.path.join(BAD, "node-b.md")], BAD)
    if out.count(" NODE ") != 1 or "node 'Omega'" not in out:
        failures.append(f"node-a/node-b: expected one NODE for the title with two sources, got:\n{out}")

    # A scope file joins the comparison, owns the shared fact, and reports nothing itself.
    for linted, scope in (("dup-a.md", "dup-b.md"), ("dup-b.md", "dup-a.md")):
        code, out = run([os.path.join(BAD, linted)], BAD, "--dup-scope", os.path.join(BAD, scope))
        owners = {line.split(":")[0] for line in out.splitlines() if " DUP " in line}
        if owners != {os.path.join(BAD, linted)} or "in 1 file(s)" not in out:
            failures.append(f"--dup-scope {scope}: expected DUP reported on {linted} only, got:\n{out}")

    examples = reference_examples()
    if len(examples) < 2:
        failures.append(f"expected a Markdown example in the application and infrastructure references, found {len(examples)}")
    with tempfile.TemporaryDirectory() as tmp:
        for name, text in examples:
            path = os.path.join(tmp, name)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(text)
            code, out = run([path], tmp, "--no-dup")
            if " MMD " in out:
                failures.append(f"reference example {name} breaks the Mermaid rules it teaches:\n{out}")

    if failures:
        print("\n\n".join(failures))
        print(f"\n{len(failures)} failure(s)")
        return 1
    print(f"ok: good set passes, {len(EXPECTED)} bad fixtures raise their codes, cross-file DUP and NODE detected, "
          f"{len(examples)} reference examples obey the Mermaid rules")
    return 0


if __name__ == "__main__":
    sys.exit(main())
