#!/usr/bin/env python3
"""Self-test for check_research.py.

Purpose: prove each rule fires on the research.md shape it guards, and that
the shape SKILL.md teaches passes, so the skill and its check cannot drift.
Usage: python3 scripts/test_check_research.py
"""
from __future__ import annotations

import concurrent.futures
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "check_research.py")
SKILL = os.path.join(HERE, "..", "SKILL.md")

GOOD = """\
# Order Export: Research

Which export format suits nightly order dumps.

## Q1 Format

Informs D1 and D2.

- **Columnar files compress well.** Detail.
  - [Parquet docs](https://example.com/parquet). Docs.
- **Row files stream.** A wrapped claim
  that continues here.
  - Same source.
- **No source compares both at this size.** The design rests on the docs.

## Decision Scorecard

| # | Decision | Verdict | Why | Change It Suggests |
| --- | --- | --- | --- | --- |
| D1 | Use Parquet | ✅ Supported | Compresses | None |
| D2 | Stream rows | 🟡 Weakened | Silent | Measure |

## Gaps

- Nothing measured at this size.
"""


def replace(old: str, new: str) -> str:
    assert GOOD.count(old) == 1, f"fixture text not found once: {old!r}"
    return GOOD.replace(old, new)


def run(files: str | None | list[str | None]) -> tuple[int, list[str]]:
    """Exit code and the `line:RULE message` findings for some files.

    A string is one file; a list is several, in order; None stands for a missing file.
    """
    files = files if isinstance(files, list) else [files]
    with tempfile.TemporaryDirectory() as base:
        paths = []
        for index, text in enumerate(files):
            paths.append(os.path.join(base, f"research{index}.md"))
            if text is not None:
                with open(paths[-1], "w", encoding="utf-8") as handle:
                    handle.write(text)
        done = subprocess.run([sys.executable, SCRIPT, *paths], capture_output=True, text=True, timeout=10)
    return done.returncode, re.findall(r"^.*?:(\d+: \w+ .*)$", done.stdout, re.M)


def shape() -> str:
    with open(SKILL, encoding="utf-8") as handle:
        block = re.search(r"^```markdown\n(.*?)^```$", handle.read(), re.M | re.S)
    assert block, "SKILL.md has no ```markdown shape block"
    return block.group(1)


CASES = {
    "skill_shape_passes": (shape(), 0, []),
    "good_file_passes": (GOOD, 0, []),
    "missing_sections_are_named": ("# Empty\n\nNothing here.\n", 1, ["1: SECTION ", "1: SECTION ", "1: SECTION "]),
    "scorecard_needs_a_verdict_table": (
        replace("| # | Decision | Verdict |", "| # | Decision | Result |"), 1, ["16: SECTION "]),
    "finding_without_source_fails": (replace("  - Same source.\n", ""), 1, ["11: SOURCE "]),
    "local_link_is_not_a_source": (
        replace("(https://example.com/parquet)", "(#format)"), 1, ["9: SOURCE ", "11: SOURCE "]),
    "negative_claim_needs_source": (replace("**No source compares", "**No locking compares"), 1, ["14: SOURCE "]),
    "linked_source_needs_label": (replace("(https://example.com/parquet). Docs.", "(https://example.com/parquet)."), 1, ["10: LABEL "]),
    "label_inside_link_text_does_not_count": (
        replace("[Parquet docs](https://example.com/parquet). Docs.", "[Vendor Docs, 2024](https://example.com/parquet)."),
        1, ["10: LABEL "]),
    "label_inside_code_does_not_count": (
        replace("(https://example.com/parquet). Docs.", "(https://example.com/parquet), see `Docs.`"),
        1, ["10: LABEL "]),
    "label_before_comma_passes": (replace("(https://example.com/parquet). Docs.", "(https://example.com/parquet). Peer, secondary."), 0, []),
    "unknown_verdict_fails": (replace("🟡 Weakened", "Weak"), 1, ["21: VERDICT "]),
    "uninformed_row_fails": (replace("Informs D1 and D2.", "Informs D1."), 1, ["21: DECISION "]),
    "informed_decision_needs_row": (replace("| D2 | Stream rows | 🟡 Weakened | Silent | Measure |\n", ""), 1, ["7: DECISION "]),
    "duplicate_row_fails": (replace("| D2 | Stream", "| D1 | Stream"), 1, ["21: DECISION D1 already", "7: DECISION D2 has no"]),
    "row_needs_decision_id": (replace("| D2 | Stream", "| Two | Stream"), 1, ["21: DECISION row id", "7: DECISION D2 has no"]),
    "wrapped_label_counts": (
        replace("(https://example.com/parquet). Docs.", "(https://example.com/parquet), the format\n    reference. Docs."),
        0, []),
    "fenced_example_is_skipped": (
        replace("## Gaps", "```markdown\n## Q9 Example\n\n- **Unsourced.** Inside a fence.\n```\n\n## Gaps"), 0, []),
    "quoted_fence_stays_quoted": (
        replace("## Gaps", "~~~markdown\n```\n## Q9 Example\n\n- **Unsourced.** Inside a fence.\n```\n~~~\n\n## Gaps"),
        0, []),
    "unreadable_file_exits_two": (None, 2, []),
    "unreadable_file_keeps_other_findings": ([replace("  - Same source.\n", ""), None], 2, ["11: SOURCE"]),
    "no_files_check_nothing": ([], 0, []),
    "bracket_run_stays_fast": (replace("  - Same source.", "  - " + "[" * 400_000), 1, ["11: SOURCE"]),
    "numbered_finding_needs_source": (
        replace("  - Same source.\n- **No source", "1. **Numbered.** Unsourced.\n- **No source"), 1,
        ["11: SOURCE", "13: SOURCE"]),
    "tab_sub_item_counts": (replace("  - [Parquet docs]", "\t- [Parquet docs]"), 0, []),
    "loose_same_source_fails": (replace("  - Same source.", "  - Not the same source."), 1, ["11: SOURCE"]),
    "loose_gap_fails": (replace("**No source compares", "**No sources were compared"), 1, ["14: SOURCE"]),
    "question_needs_informs": (
        replace("Informs D1 and D2.\n", ""), 1,
        ["5: SECTION question informs no", "19: DECISION no question", "20: DECISION no question"]),
    "wrapped_informs_counts": (replace("Informs D1 and D2.", "Informs D1\nand D2."), 0, []),
    "empty_scorecard_fails": (
        replace("Informs D1 and D2.\n", "").replace(
            "| D1 | Use Parquet | ✅ Supported | Compresses | None |\n| D2 | Stream rows | 🟡 Weakened | Silent | Measure |\n", ""),
        1, ["5: SECTION", "15: DECISION the scorecard has no"]),
    "escaped_pipe_stays_in_cell": (replace("| D1 | Use Parquet |", "| D1 | Use a \\| b |"), 0, []),
    "byte_order_mark_is_ignored": ("\ufeff" + GOOD[GOOD.index("## Q1"):], 0, []),
    "unclosed_fence_is_reported": (replace("## Gaps", "```\n## Gaps"), 1, ["23: FENCE", "1: SECTION no `## Gaps`"]),
    "rule_line_is_not_a_finding": (replace("## Decision Scorecard", "- - -\n\n## Decision Scorecard"), 0, []),
    "blank_line_ends_continuation": (
        replace("(https://example.com/parquet). Docs.", "(https://example.com/parquet).\n\n    Docs."), 1, ["10: LABEL"]),
}


def check(case: tuple[str, tuple]) -> str | None:
    name, (text, code, want) = case
    try:
        got = run(text)
    except subprocess.TimeoutExpired:
        return f"{name}: timed out"
    # Each wanted finding is a prefix of the one reported: its line and rule, and the message start when given.
    held = got[0] == code and len(got[1]) == len(want) and all(g.startswith(w) for g, w in zip(got[1], want))
    return None if held else f"{name}: got {got!r}, want {(code, want)!r}"


def main() -> int:
    # Each case runs its own interpreter, so they run side by side.
    with concurrent.futures.ThreadPoolExecutor() as pool:
        failures = [f for f in pool.map(check, CASES.items()) if f]
    if failures:
        print("\n\n".join(failures))
        print(f"\n{len(failures)} failure(s)")
        return 1
    print(f"ok: {len(CASES)} research rules hold")
    return 0


if __name__ == "__main__":
    sys.exit(main())
