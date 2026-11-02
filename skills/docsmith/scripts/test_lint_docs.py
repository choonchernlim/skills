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
PALETTE_OWN = "fill:#1a73e833,stroke:#1a73e8"
BAND_OWN = "rgba(26,115,232,0.2)"

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
    "mmd-boundary-table.md": "MMD",
    "mmd-boundary-link.md": "MMD",
    "mmd-frontmatter.md": "MMD",
    "mmd-directive.md": "MMD",
    "mmd-html.md": "MMD",
    "mmd-keyword.md": "MMD",
    "mmd-markdown-label.md": "MMD",
    "mmd-long-arrow.md": "MMD",
    "mmd-shape.md": "MMD",
    "mmd-edge-quote.md": "MMD",
    "mmd-link.md": "MMD",
    "mmd-color-palette.md": "MMD",
    "mmd-color-style.md": "MMD",
    "mmd-color-partial.md": "MMD",
    "mmd-color-model.md": "MMD",
    "mmd-color-legend.md": "MMD",
    "mmd-color-rules.md": "MMD",
    "mmd-color-boundary.md": "MMD",
    "mmd-band.md": "MMD",
    "view/docs/architecture.md": "VIEW",
    "view/docs/orders/architecture.md": "VIEW",
    "mmd-infrastructure-generic.md": "MMD",
    "adr-settled.md": "TOC",
    "adr-proposed.md": "SENT",
}
EXPECTED_COUNTS = {
    "link.md": ("LINK", 5),
    "word.md": ("WORD", 3),
    "mmd-label.md": ("MMD", 6),
    "mmd-sequence.md": ("MMD", 3),
    "mmd-boundary.md": ("MMD", 1),
    "mmd-boundary-width.md": ("MMD", 1),
    "mmd-boundary-direction.md": ("MMD", 1),
    "mmd-boundary-sideways.md": ("MMD", 1),
    "mmd-boundary-table.md": ("MMD", 1),
    "mmd-boundary-link.md": ("MMD", 1),
    "mmd-frontmatter.md": ("MMD", 1),
    "mmd-directive.md": ("MMD", 1),
    "mmd-html.md": ("MMD", 1),
    "mmd-keyword.md": ("MMD", 1),
    "mmd-markdown-label.md": ("MMD", 1),
    "mmd-color-palette.md": ("MMD", 1),
    "mmd-color-style.md": ("MMD", 1),
    "mmd-color-partial.md": ("MMD", 1),
    "mmd-color-model.md": ("MMD", 1),
    "mmd-color-legend.md": ("MMD", 1),
    "mmd-color-rules.md": ("MMD", 20),
    "mmd-color-boundary.md": ("MMD", 2),
    "mmd-band.md": ("MMD", 8),
    "mmd-shape.md": ("MMD", 9),
    "mmd-edge-quote.md": ("MMD", 5),
    "mmd-link.md": ("MMD", 12),
    "mmd-long-arrow.md": ("MMD", 3),
}


def flowchart(prefix: str, padding: int = 0) -> tuple[str, str]:
    """Return a lead sentence and a colored four-node diagram, and its Node table.

    Padding adds comment lines inside the fence, so the diagram grows without prose.
    """
    names = [f"{prefix}{n}" for n in range(4)]
    nodes = "".join(f'  {n}["{n}<br/>[SERVICE]"]\n' for n in names)
    edges = "".join(f'  {a} -->|"calls"| {b}\n' for a, b in zip(names, names[1:]))
    pad = "".join(f"  %% padding {n}\n" for n in range(padding))
    diagram = (f"Lead.\n\n```mermaid\ngraph TD\n{nodes}{edges}  class {','.join(names)} own\n"
               f"  classDef own {PALETTE_OWN}\n{pad}```\n\n")
    table = "| Node | Source |\n| --- | --- |\n" + "".join(f"| {n} | - |\n" for n in names) + "\n"
    return diagram, table


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

    # A settled ADR is immutable, so it reports only what a format-only pass can fix.
    code, out = run([os.path.join(BAD, "adr-settled.md")], BAD)
    if " SENT " in out or "1 finding(s)" not in out:
        failures.append(f"adr-settled.md: expected TOC alone on an accepted ADR, got:\n{out}")

    # A settled ADR owns a shared fact, so DUP lands on the editable guide in either order.
    pair = [os.path.join(BAD, "adr-settled-dup.md"), os.path.join(BAD, "adr-settled-guide.md")]
    for paths in (pair, pair[::-1]):
        code, out = run(paths, BAD)
        owners = {line.split(":")[0] for line in out.splitlines() if " DUP " in line}
        if owners != {pair[1]}:
            failures.append(f"settled ADR with a guide: expected DUP on the guide only, got:\n{out}")

    # A diagram's legend repeats by design, so two identical legends are not a duplicate fact,
    # whether the key names colors or, under a sequence diagram, only line styles. The same
    # paragraph without a diagram above it is still checked.
    legend = "**Legend:** \U0001F7E6 Platform team \u00b7 thick line = a call that crosses the boundary between the two cloud projects\n"
    line_key = "**Legend:** thick line = a call that crosses the boundary between the two cloud projects\n"
    with tempfile.TemporaryDirectory() as tmp:
        colored, keyed, plain = [], [], []
        for prefix in ("A", "B"):
            diagram, nodes_table = flowchart(prefix)
            participants = "".join(f"    participant {prefix}{n} as {prefix}{n}<br/>[SERVICE]\n" for n in range(4))
            messages = "".join(f"  {prefix}{n}->>{prefix}{n + 1}: {n + 1}: calls\n" for n in range(3))
            banded = (f"Lead.\n\n```mermaid\nsequenceDiagram\n  box {BAND_OWN} Platform team\n"
                      f"{participants}  end\n{messages}```\n\n")
            head = "<!--\nPurpose: Example.\nType: explanation\n-->\n\n# Example\n\nAudience: the self-test.\n\n"
            for group, body in ((colored, diagram + legend + "\n" + nodes_table),
                                (keyed, f"{banded}{line_key}\n{nodes_table}"), (plain, legend)):
                path = os.path.join(tmp, f"{prefix}-{len(colored) + len(keyed) + len(plain)}.md")
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(head + body)
                group.append(path)
        code, out = run(colored, tmp)
        if " DUP " in out or " MMD " in out:
            failures.append(f"identical legends under colored diagrams should pass, got:\n{out}")
        code, out = run(keyed, tmp)
        if " DUP " in out or " MMD " in out:
            failures.append(f"identical line-style legends under sequence diagrams should pass, got:\n{out}")
        code, out = run(plain, tmp)
        if "12-word run" not in out or "sentence restates" not in out:
            failures.append(f"a legend paragraph with no diagram above it should still raise both DUP checks, got:\n{out}")

    # A line cap counts lines outside Mermaid fences: a 60-line diagram keeps a short ADR under
    # its cap, and 30 more prose lines push the same ADR over it.
    with tempfile.TemporaryDirectory() as tmp:
        head = "<!--\nPurpose: Example.\nType: adr\n-->\n\n# ADR 0001: Example\n\n## Context and Problem Statement\n\n"
        diagram, table = flowchart("N", padding=60)
        body = head + diagram + "**Legend:** \U0001F7E6 Platform team\n\n" + table
        for name, extra, want in (("short.md", "", False), ("long.md", "x\n\n" * 30, True)):
            path = os.path.join(tmp, name)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(body + extra)
            code, out = run([path], tmp, "--no-dup")
            if (" CAP " in out) != want:
                failures.append(f"line cap on {name}: expected CAP {want}, got:\n{out}")

    # The docs/ folder is found from the file's own path, so the view rule holds from any --root.
    view = os.path.join(BAD, "view", "docs", "architecture.md")
    code, out = run([view], os.path.dirname(view))
    if " VIEW " not in out:
        failures.append(f"view rule with --root at docs/: expected VIEW, got:\n{out}")

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
    print(f"ok: good set passes, {len(EXPECTED)} bad fixtures raise their codes, cross-file DUP and NODE detected, settled ADRs hold format rules only, "
          f"{len(examples)} reference examples obey the Mermaid rules")
    return 0


if __name__ == "__main__":
    sys.exit(main())
