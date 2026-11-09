#!/usr/bin/env python3
"""Check the shape of a research.md written by the research skill.

Purpose: prove every finding cites a source, every linked source carries an
evidence label, and the decision scorecard matches the questions, so a claim
no source backs cannot slip into a design.
Usage: python3 check_research.py <research.md>...
Output: one `file:line: RULE message` line per finding, then a count. Exit 0
when clean, 1 on findings, 2 when a file cannot be read.

Rules:
  SECTION   a `## Q<n>` section, each with an `Informs D<n>` line, then
            `## Decision Scorecard` with a Verdict table, and `## Gaps`
  FENCE     every code fence closes
  SOURCE    each top-level item under a question has a sub-item with a web
            link, or a "Same source." pointer to a link above it, unless it
            starts with "No source", which names a gap
  LABEL     each sub-item with a link names its evidence label
  VERDICT   each scorecard verdict is one of VERDICTS
  DECISION  the scorecard has rows; each decision a question informs has one
            row, and each row is informed by a question
"""
from __future__ import annotations

import argparse
import re
import sys

LABELS = ("Peer", "Survey", "Docs", "Preprint", "Practice", "Secondary")
VERDICTS = ("✅ Supported", "🟡 Weakened", "❌ Contradicted")

FENCE = re.compile(r"^\s*(`{3,}|~{3,})(.*)$")
QUESTION = re.compile(r"Q\d+\b")
H2 = re.compile(r"^## (.+)$")
RULE = re.compile(r"^ {0,3}([-*_])(?: *\1){2,} *$")
ITEM = r"(?:[-*+]|\d+[.)]) (.*)"
TOP_ITEM = re.compile(r"^" + ITEM)
SUB_ITEM = re.compile(r"^(?:\t| {2})\s*" + ITEM)
# Link text excludes `[`, so a run of brackets fails each start at the next one: linear, not quadratic.
WEB_LINK = re.compile(r"\[[^\[\]\n]{0,500}\]\(https?://[^)\s]{1,2000}\)")
ANY_LINK = re.compile(r"\[[^\[\]\n]{0,500}\]\([^)\n]{0,2000}\)")
CODE = re.compile(r"`[^`]*`")
SAME_SOURCE = re.compile(r"(?:[^,.]+,\s*)?same\b[^.,;]*\bsources?\b", re.I)
LABEL = re.compile(r"(?<![\w-])(?:" + "|".join(LABELS) + r")(?=[.,;]|$)")
DECISION = re.compile(r"\bD\d+\b")
GAP = re.compile(r"\**No source\b")
CELL_BORDER = re.compile(r"(?<!\\)\|")
SEPARATOR = frozenset("-: ")


def sections(lines: list[str]) -> tuple[list[tuple[str, int, list[tuple[int, str]]]], int | None]:
    """Split into H2 sections of (title, line, body lines), skipping fenced code.

    A fence closes only on the same character, at least as long, with nothing
    after it, so a fence quoted inside another stays quoted. Also returns the
    line of a fence left open, or None.
    """
    found, fence, opened = [("", 0, [])], None, None
    for number, line in enumerate(lines, 1):
        marker = FENCE.match(line)
        if marker and fence is None:
            fence, opened = marker.group(1), number
            continue
        if fence is not None:
            if (marker and marker.group(1)[0] == fence[0] and len(marker.group(1)) >= len(fence)
                    and not marker.group(2).strip()):
                fence = None
            continue
        heading = H2.match(line)
        if heading:
            found.append((heading.group(1).strip(), number, []))
        else:
            found[-1][2].append((number, line))
    return found, opened if fence is not None else None


def findings(body: list[tuple[int, str]]) -> list[tuple[int, str, list[tuple[int, str]]]]:
    """Each top-level item as (line, text, its sub-items as (line, text)).

    An indented line that is not an item, right after a sub-item or its last
    continuation, continues it, so a label or link wrapped onto the next line
    still counts. A blank line ends that.
    """
    items, open_sub = [], False
    for number, line in body:
        if RULE.match(line):
            open_sub = False
            continue
        top, sub = TOP_ITEM.match(line), SUB_ITEM.match(line)
        if top:
            items.append((number, top.group(1), []))
            open_sub = False
        elif sub and items:
            items[-1][2].append((number, sub.group(1)))
            open_sub = True
        elif open_sub and line[:1].isspace() and line.strip():
            at, text = items[-1][2][-1]
            items[-1][2][-1] = (at, f"{text} {line.strip()}")
        else:
            open_sub = False
    return items


def informs(body: list[tuple[int, str]]) -> list[tuple[int, str]]:
    """Each decision an `Informs` paragraph names, as (line, decision); the paragraph may wrap."""
    found, reading = [], None
    for number, line in body:
        if line.lstrip(" *").startswith("Informs"):
            reading = number
        elif not line.strip() or TOP_ITEM.match(line):
            reading = None
        if reading is not None:
            found += [(reading, decision) for decision in DECISION.findall(line)]
    return found


def cells(line: str) -> list[str]:
    return [cell.strip() for cell in CELL_BORDER.split(line.strip().strip("|"))]


def check(path: str, text: str) -> list[str]:
    out = []

    def report(line: int, rule: str, message: str) -> None:
        out.append(f"{path}:{line}: {rule} {message}")

    parts, unclosed = sections(text.splitlines())
    if unclosed:
        report(unclosed, "FENCE", "this code fence never closes, so the rest of the file is skipped")
    questions = [part for part in parts if QUESTION.match(part[0])]
    titles = {title for title, _, _ in parts}
    if not questions:
        report(1, "SECTION", "no `## Q1 <sub-question>` section")
    for title in ("Decision Scorecard", "Gaps"):
        if title not in titles:
            report(1, "SECTION", f"no `## {title}` section")

    informed: dict[str, int] = {}
    linked_above = False
    for _, start, body in questions:
        named = informs(body)
        if not named:
            report(start, "SECTION", "question informs no decision: add an `Informs D1.` line under it")
        for number, decision in named:
            informed.setdefault(decision, number)
        for number, claim, subs in findings(body):
            sourced = False
            for at, sub in subs:
                if WEB_LINK.search(sub):
                    sourced = linked_above = True
                    if not LABEL.search(CODE.sub("", ANY_LINK.sub("", sub))):
                        report(at, "LABEL", f"linked source has no evidence label: name "
                                            f"one of {', '.join(LABELS)}")
                elif linked_above and SAME_SOURCE.match(sub):
                    sourced = True
            if not sourced and not GAP.match(claim):
                report(number, "SOURCE", "finding has no source: add a sub-item with its link, "
                                         "or start it with No source to name a gap")

    scorecard = next((part for part in parts if part[0] == "Decision Scorecard"), None)
    if scorecard:
        _, start, body = scorecard
        table = [(number, cells(line)) for number, line in body if line.lstrip().startswith("|")]
        header = table[0][1] if table else []
        if "Verdict" not in header:
            report(start, "SECTION", "the scorecard has no table with a Verdict column")
            return out
        column, rows = header.index("Verdict"), {}
        for number, row in table[1:]:
            if all(set(cell) <= SEPARATOR for cell in row):
                continue
            verdict = row[column] if column < len(row) else ""
            if verdict not in VERDICTS:
                report(number, "VERDICT", f"verdict {verdict!r} is not one of {', '.join(VERDICTS)}")
            decision = row[0]
            if not DECISION.fullmatch(decision):
                report(number, "DECISION", f"row id {decision!r} is not a decision like D1")
            elif decision in rows:
                report(number, "DECISION", f"{decision} already has a row at line {rows[decision]}")
            else:
                rows[decision] = number
                if questions and decision not in informed:
                    report(number, "DECISION", f"no question informs {decision}: add it to an Informs line")
        if not rows:
            report(start, "DECISION", "the scorecard has no decision rows")
        for decision, number in informed.items():
            if decision not in rows:
                report(number, "DECISION", f"{decision} has no scorecard row")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Check the shape of research.md files.")
    parser.add_argument("files", nargs="*", metavar="research.md", help="none checks nothing")
    args = parser.parse_args()
    problems, unread = [], 0
    for path in args.files:
        try:
            with open(path, encoding="utf-8-sig") as handle:
                problems += check(path, handle.read())
        except (OSError, UnicodeDecodeError) as error:
            print(f"{path}: cannot read: {error}", file=sys.stderr)
            unread += 1
    for problem in problems:
        print(problem)
    print(f"{len(problems)} finding(s)" if problems else f"ok: {len(args.files) - unread} file(s) hold")
    return 2 if unread else 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
