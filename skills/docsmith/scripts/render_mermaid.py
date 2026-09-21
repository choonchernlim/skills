#!/usr/bin/env python3
"""Render every Mermaid block in Markdown files to PNG for visual inspection.

Purpose: replace hand extraction so no diagram reaches handoff unrendered.
Invariants: standard library only; one PNG per block at 2x so a line through a label shows; exit 1 when any block fails to render.
Usage: render_mermaid.py <file>... [--out DIR]
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor

PACKAGE = "@mermaid-js/mermaid-cli"
RUNNERS = ("bunx", "npx")
WORKERS = 4
SCALE = "2"


def extract(path: str) -> list[tuple[int, str]]:
    """Return (line number, source) for every mermaid fence, nested example fences included."""
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    blocks: list[tuple[int, str]] = []
    start: int | None = None
    for i, line in enumerate(lines):
        s = line.strip()
        if start is None and s == "```mermaid":
            start = i
        elif start is not None and s == "```":
            blocks.append((start + 1, "\n".join(lines[start + 1:i]) + "\n"))
            start = None
    return blocks


def render(runner: str, source: str, png: str) -> str | None:
    mmd = png[:-4] + ".mmd"
    with open(mmd, "w", encoding="utf-8") as fh:
        fh.write(source)
    proc = subprocess.run(
        [runner, "--yes", PACKAGE, "-i", mmd, "-o", png, "-s", SCALE, "-q"],
        capture_output=True, text=True,
    )
    if proc.returncode != 0 or not os.path.isfile(png):
        return (proc.stderr or proc.stdout).strip() or "renderer produced no image"
    return None


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Render the Mermaid blocks of Markdown files to PNG.")
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--out", help="directory for the images; defaults to a new temporary directory")
    args = ap.parse_args(argv)

    runner = next((r for r in RUNNERS if shutil.which(r)), None)
    if runner is None:
        print(f"neither {' nor '.join(RUNNERS)} is on PATH; install Bun or Node.js", file=sys.stderr)
        return 2

    jobs: list[tuple[str, int, str, str]] = []
    out = args.out or tempfile.mkdtemp(prefix="docsmith-mermaid-")
    os.makedirs(out, exist_ok=True)
    for p in args.paths:
        if not os.path.isfile(p):
            print(f"{p}:0: FILE not found", file=sys.stderr)
            return 2
        stem = re.sub(r"[^A-Za-z0-9]+", "-", os.path.splitext(os.path.relpath(p))[0]).strip("-")
        for line, source in extract(p):
            jobs.append((p, line, source, os.path.join(out, f"{stem}-L{line}.png")))

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        errors = list(pool.map(lambda j: render(runner, j[2], j[3]), jobs))

    failed = 0
    for (p, line, _, png), error in zip(jobs, errors):
        if error:
            failed += 1
            print(f"{p}:{line}: RENDER {error.splitlines()[-1]}")
        else:
            print(f"{p}:{line}: {png}")
    print(f"{len(jobs) - failed} of {len(jobs)} diagram(s) rendered; open every PNG and inspect it")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
