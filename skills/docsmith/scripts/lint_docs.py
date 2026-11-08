#!/usr/bin/env python3
"""Static linter for documents written by the docsmith skill.

Purpose: enforce the rules in references/style.md, references/mermaid.md and
references/mermaid-visual.md mechanically so verification does not rely on reading alone.
Invariants: standard library only; one stable code per rule; exit 1 on any error.
Usage: lint_docs.py <file>... [--type TYPE] [--root DIR] [--dup-scope PATH...]
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import textwrap
import urllib.parse
from dataclasses import dataclass, field

TYPES = {
    "readme-project": 200,
    "readme-folder": 80,
    "how-to": 200,
    "explanation": 200,
    "reference": 300,
    "requirements": 300,
    "index": 120,
    "adr": 80,
    "glossary": None,
}
# Folder names that hold numbered ADRs.
ADR_DIRS = ("adrs", "adr", "decisions")
# The file name of a numbered ADR: four digits, a hyphen, a slug.
ADR_NAME_RX = re.compile(r"^(\d{4})-.*\.md$")
# Agent instruction files sit beside guides, often in docs/, but instruct agents, not readers.
AGENT_FILES = {"AGENTS.md", "CLAUDE.md"}
GUIDE_TYPES = {"how-to", "reference", "explanation", "index", "requirements"}
APPLICATION_MERMAID_TYPES = {
    "PERSON", "TEAM", "UI", "API", "AGENT", "TOOL", "SERVICE", "SYSTEM", "DATA", "DECISION",
}
INFRASTRUCTURE_MERMAID_TYPES = {
    "GCP PROJECT", "VPC", "PRIVATE SERVICE CONNECT", "EXTERNAL LOAD BALANCER",
    "CLOUD RUN JOB", "CLOUD SQL", "MEMORYSTORE", "SECRET MANAGER",
    "AZURE APP SERVICE", "AZURE FUNCTIONS", "AZURE SQL", "VIRTUAL NETWORK",
    "APPLICATION GATEWAY", "KEY VAULT", "KUBERNETES", "VM", "PHYSICAL SERVER",
    "FIREWALL", "LOAD BALANCER", "DNS", "OBJECT STORAGE",
    "MESSAGE BROKER", "CONTAINER REGISTRY",
}
# Named technologies both families accept: a store names its engine, and a
# vendor service or a runtime names its product. A new one is added here and in
# the application reference together.
TECHNOLOGY_STORE_TYPES = {
    "POSTGRES", "MYSQL", "SQL SERVER", "REDIS", "VALKEY", "MONGODB", "BIGQUERY",
    "CLOUD STORAGE", "S3", "SESSION STORAGE", "LOCAL STORAGE", "KAFKA",
}
TECHNOLOGY_SERVICE_TYPES = {
    "VERTEX AI", "SPEECH-TO-TEXT", "TEXT-TO-SPEECH", "APIGEE", "LANGFUSE", "ENTRA ID",
    "CLOUD RUN", "AZURE PIPELINES", "AZURE REPOS", "AZURE ARTIFACTS",
}
TECHNOLOGY_TYPES = TECHNOLOGY_STORE_TYPES | TECHNOLOGY_SERVICE_TYPES
MERMAID_TYPES = APPLICATION_MERMAID_TYPES | INFRASTRUCTURE_MERMAID_TYPES | TECHNOLOGY_TYPES
# Boundaries that only an infrastructure diagram draws.
INFRASTRUCTURE_BOUNDARY_TYPES = {"NETWORK", "DATACENTER", "SUBSCRIPTION", "GCP PROJECT"}
BOUNDARY_TYPES = {
    "REPO", "TEAM", "DEPLOYMENT", "TRUST BOUNDARY", "NETWORK", "ENVIRONMENT",
    "DATACENTER", "SUBSCRIPTION", "GCP PROJECT",
}
VIEW_OWNERS = {
    "application": "architecture.md",
    "runtime": "runtime-flows.md",
    "data": "data-model.md",
    "infrastructure": "infrastructure.md",
}
# Mermaid wraps a boundary title at 200 pixels and hides the extra line behind
# the first node. 24 characters stay on one line in every renderer font.
BOUNDARY_TITLE_MAX = 24
# Every flowchart node takes one owner color: a 20% tint of the base color
# with a solid stroke, so a node reads in a light or dark theme and the text
# keeps the viewer theme's color. Each stroke holds 3:1 contrast on a white
# and on a near-black page, and the four team owners stay apart under
# red-green color blindness; person and model also differ by shape. The swatch
# names the class in the legend line under the diagram. Each entry is
# (swatch, base color, extra style).
COLORS = {
    "own": ("\U0001F7E6", "2563eb", ""),
    "peer": ("\U0001F7E9", "0d9488", ""),
    "platform": ("\U0001F7E7", "d97706", ""),
    "external": ("\u2B1C", "64748b", ""),
    "person": ("\U0001F7E5", "e11d48", ""),
    "model": ("\U0001F7EA", "c026d3", ",stroke-width:3px"),
}
PALETTE = {name: (swatch, f"fill:#{base}33,stroke:#{base}{extra}") for name, (swatch, base, extra) in COLORS.items()}
# A boundary takes a dashed slate outline over a near-clear fill, so the tinted
# nodes inside it keep their color. It has no swatch: its title names its TYPE.
BOUNDARY_STYLE = "fill:#7d879914,stroke:#7d8799,stroke-dasharray:6"
# A part not built yet takes this class instead of an owner's: a neutral gray
# box with a dashed outline, so no reader mistakes it for something running.
FUTURE_CLASS = "future"
FUTURE_STYLE = "fill:#6b72801a,stroke:#6b7280,stroke-dasharray:5"
FUTURE_LEGEND = "dashed gray = future"
FUTURE_SUFFIX = " (Future)"
CLASS_STYLES = {**{name: style for name, (_, style) in PALETTE.items()}, "boundary": BOUNDARY_STYLE, FUTURE_CLASS: FUTURE_STYLE}
FUTURE_CLASS_RX = re.compile(rf"^class\s+(\w+(?:,\w+)*)\s+{FUTURE_CLASS}$")
# A sequence diagram puts its participants in owner bands. Mermaid reads '#' in
# a box line as a comment, so a band takes the rgba form of the owner's tint.
BAND_COLORS = {
    name: f"rgba({int(base[0:2], 16)},{int(base[2:4], 16)},{int(base[4:6], 16)},0.2)"
    for name, (_, base, _) in COLORS.items() if name != "model"
}
BAND_OWNERS = {rgba: name for name, rgba in BAND_COLORS.items()}
# A class bound to one TYPE marks every node of that TYPE and nothing else.
TYPE_CLASSES = {"model": "AGENT", "person": "PERSON"}

# A participant takes no class, so its box would wear the viewer theme's color.
# This one line, second in every sequence diagram, makes the box see-through,
# so it shows its band's owner tint, and draws borders and lifelines in slate.
# A viewer that reads the first line as the diagram type still accepts it.
SEQUENCE_INIT = (
    '%%{init: {"themeVariables": {"actorBkg": "transparent", "actorBorder": "#7d8799", '
    '"actorLineColor": "#7d8799", "labelBoxBorderColor": "#7d8799"}}}%%'
)
# The second line of every 'graph TD'. It draws straight edges with rounded
# corners, so an edge label sits on a straight run. A boundary title takes two
# lines, its name then its [TYPE]: the line centers both, which Mermaid leaves
# left-aligned in a frame title, and adds room under the title, so the second
# line clears the first node inside the frame.
FLOWCHART_INIT = (
    '%%{init: {"themeCSS": ".cluster-label, .cluster-label div, .cluster-label span, .cluster-label p '
    '{ text-align: center !important; }", "flowchart": {"curve": "rounded", '
    '"subGraphTitleMargin": {"top": 6, "bottom": 30}}}}%%'
)

BANNED_WORDS = [
    "just", "simply", "easy", "easily", "trivial", "straightforward", "painless",
    "obviously", "of course", "delve", "leverage", "utilize", "seamless",
    "seamlessly", "robust", "comprehensive", "cutting-edge", "powerful",
    "innovative", "streamline", "empower", "crucially", "importantly", "notably",
    "essentially", "basically", "actually", "in order to", "note that",
    "it should be noted", "please note", "it's worth noting", "in today's",
]
META_PHRASES = [
    r"this (section|document|guide|file|readme) (used to|previously|once)",
    r"what was (one|a) \d+-node",
    r"replaces? what was",
    r"kept for link stability",
    r"this corpus now calls",
    r"became (two|three|four|five) diagrams",
]
# Change-log phrases: a guide describes the current state, and Git and the ADRs hold history.
# "used to" is history only before "be" or "live": "the token used to live in a cookie", not "the bucket used to hold state".
# It matches across a line wrap, since prose wraps mid-phrase.
HIST_RX = re.compile(
    r"\bformerly\b|\b(was|were) renamed\b|\bin the past\b(?!\s+\d)|\bused to (be|live)\b",
    re.I,
)
PIN_RX = re.compile(r"(?<![\w.])\d+\.\d+\.\d+(?![\w.])")
LINE_RX = re.compile(r"[\w./-]+\.(?:py|pyi|ts|tsx|js|jsx|mjs|sql|tf|sh|go|rs|java|kt|rb|cs|ya?ml|json|toml|md):\d+")
FROZEN_RX = re.compile(r"^\s*<!--\s*frozen:\s*(.*?)\s*-->\s*$", re.I)
FROZEN_REASON_WORDS = 5
# A table is a copy of the code when this many rows, most of them led by an identifier, list it.
# A reference owns field tables, so it may run longer first.
COPY_ROWS = 10
COPY_ROWS_REFERENCE = 20
COPY_LED_SHARE = 0.8
# The codes a document type never reports, because its role makes them expected:
# an ADR is a dated record, a glossary names old aliases, a README maps its folder's
# files, and requirement rows are led by IDs and record retired behavior.
TYPE_SKIPS = {
    "adr": {"PIN", "LINE", "FROZEN", "HIST", "COPY"},
    "glossary": {"HIST"},
    "requirements": {"HIST", "COPY"},
    "readme-project": {"COPY"},
    "readme-folder": {"COPY"},
}

SMALL_WORDS = {
    "a", "an", "the", "and", "but", "or", "nor", "for", "so", "yet", "at", "by",
    "from", "in", "into", "of", "on", "onto", "to", "with", "via", "as", "per",
    "versus", "vs", "up", "down", "over", "under",
}

BRIEF_CAP = 120
SENTENCE_MAX = 30
PARAGRAPH_MAX = 4
RUN_MAX = 6
CELL_MAX = 20
BULLET_MAX = 30
LIST_MAX = 7
H2_MAX = 10
TOC_LINES = 100
TOC_H2 = 5
DUP_WINDOW = 12

# An ADR past Proposed is an immutable record: only a format-only pass may touch it,
# so only the codes such a pass can fix are reported on it.
SETTLED_STATUSES = {"accepted", "rejected", "deprecated", "superseded"}
SETTLED_ADR_CODES = {"HDR", "TTL", "HCASE", "EMPTY", "TOC", "FENCE", "LINK", "NUM"}
STATUS_WORD_RX = re.compile(r"\b(proposed|accepted|rejected|deprecated|superseded)\b", re.I)
STATUS_LINE_RX = re.compile(r"^\s*(?:[-*]\s*)?\**status\**\s*:", re.I)


@dataclass
class Finding:
    path: str
    line: int
    code: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.code} {self.message}"


@dataclass
class Diagram:
    line: int
    family: str
    titles: list[str]
    edges: list[tuple[str, str, str]]
    # (kind, title) to its normalized source, '' when it has none; kind is 'node' or 'boundary'.
    sources: dict[tuple[str, str], str] = field(default_factory=dict)


@dataclass
class Doc:
    path: str
    lines: list[str]
    doc_type: str | None = None
    findings: list[Finding] = field(default_factory=list)
    prose_shingles: dict[str, int] = field(default_factory=dict)
    # Start lines of a diagram's legend and Sources line: they repeat by design, so the duplicate checks skip them.
    captions: set[int] = field(default_factory=set)
    diagrams: list[Diagram] = field(default_factory=list)
    settled: bool = False
    # The absolute folder relative links resolve from.
    folder: str = ""

    def __post_init__(self) -> None:
        self.folder = os.path.dirname(os.path.abspath(self.path))

    def add(self, line: int, code: str, message: str) -> None:
        self.findings.append(Finding(self.path, line, code, message))


# ---------- helpers ----------

def slugify(heading: str) -> str:
    text = re.sub(r"`([^`]*)`", r"\1", heading).strip().lower()
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def strip_inline_code(text: str) -> str:
    return re.sub(r"`[^`]*`", "CODE", text)


def link_text_only(text: str) -> str:
    return re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)


def word_count(text: str) -> int:
    text = link_text_only(strip_inline_code(text))
    return len([w for w in re.split(r"\s+", text.strip()) if w])


def sentences(text: str) -> list[str]:
    text = link_text_only(strip_inline_code(text))
    text = re.sub(r"\b(e\.g|i\.e|vs|etc)\.", r"\1", text)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z\[`(])", text.strip())
    return [p for p in parts if p]


def heading_level(line: str) -> int:
    m = re.match(r"^(#{1,6})\s+\S", line)
    return len(m.group(1)) if m else 0


def is_title_case(title: str) -> bool:
    title = re.sub(r"`[^`]*`", "", title)
    title = re.sub(r"^ADR \d+:\s*", "", title)
    title = re.sub(r"^Flow \w+:\s*", "", title)
    words = [w for w in re.split(r"\s+", title.strip()) if w]
    for i, word in enumerate(words):
        bare = word.strip("()\"'“”:,.;!?")
        if not bare or not re.match(r"^[A-Za-z]", bare):
            continue
        if not re.match(r"^[A-Za-z][a-z]*(['’][a-z]+)?$|^[A-Z][A-Z0-9]+$|^[A-Za-z][a-zA-Z0-9]*[-/][A-Za-z0-9-]+$", bare):
            continue
        is_edge = i == 0 or i == len(words) - 1
        if bare.lower() in SMALL_WORDS and not is_edge:
            if bare[0].isupper():
                return False
            continue
        if bare[0].islower():
            return False
    return True


# ---------- segmentation ----------

@dataclass
class Block:
    kind: str  # fence, table, list, para, heading, blank, html
    start: int
    lines: list[str]
    lang: str = ""


def segment(lines: list[str]) -> list[Block]:
    blocks: list[Block] = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        m = re.match(r"^(\s*)(`{3,}|~{3,})\s*(\S*)", line)
        if m:
            fence = m.group(2)
            lang = m.group(3)
            start = i
            i += 1
            while i < n and not re.match(rf"^\s*{re.escape(fence[0])}{{{len(fence)},}}\s*$", lines[i]):
                i += 1
            blocks.append(Block("fence", start, lines[start:i + 1], lang))
            i += 1
            continue
        if line.strip().startswith("<!--"):
            start = i
            while i < n and "-->" not in lines[i]:
                i += 1
            blocks.append(Block("html", start, lines[start:i + 1]))
            i += 1
            continue
        if not line.strip():
            blocks.append(Block("blank", i, [line]))
            i += 1
            continue
        if heading_level(line):
            blocks.append(Block("heading", i, [line]))
            i += 1
            continue
        if line.lstrip().startswith("|"):
            start = i
            while i < n and lines[i].lstrip().startswith("|"):
                i += 1
            blocks.append(Block("table", start, lines[start:i]))
            continue
        if re.match(r"^\s*([-*+]|\d+\.)\s+", line):
            start = i
            while i < n and lines[i].strip() and not heading_level(lines[i]) and not lines[i].lstrip().startswith("|") and not re.match(r"^\s*(`{3,}|~{3,})", lines[i]):
                i += 1
            blocks.append(Block("list", start, lines[start:i]))
            continue
        start = i
        while i < n and lines[i].strip() and not heading_level(lines[i]) and not lines[i].lstrip().startswith("|") and not re.match(r"^\s*(`{3,}|~{3,}|[-*+]\s|\d+\.\s|<!--)", lines[i]):
            i += 1
        blocks.append(Block("para", start, lines[start:i]))
    return blocks


# ---------- checks ----------

def check_header(doc: Doc, blocks: list[Block], forced_type: str | None) -> None:
    first = blocks[0] if blocks else None
    if not first or first.kind != "html":
        doc.add(1, "HDR", "file must open with a <!-- Purpose: ... Type: ... --> header comment")
        doc.doc_type = forced_type
        return
    body = [l.strip() for l in first.lines[1:-1] if l.strip()]
    shape_ok = len(body) == 2 and body[0].startswith("Purpose:") and body[1].startswith("Type:")
    if not shape_ok:
        doc.add(1, "HDR", "header comment must hold exactly a Purpose: line and a Type: line")
    declared = None
    for l in body:
        if l.startswith("Type:"):
            declared = l.split(":", 1)[1].strip()
    if declared and declared not in TYPES:
        doc.add(1, "HDR", f"unknown Type '{declared}'; expected one of {', '.join(TYPES)}")
        declared = None
    doc.doc_type = forced_type or declared
    if not doc.doc_type and shape_ok:
        doc.add(1, "HDR", "Type missing; pass --type or add a Type: line")


def check_title(doc: Doc, blocks: list[Block]) -> None:
    h1s = [b for b in blocks if b.kind == "heading" and heading_level(b.lines[0]) == 1]
    if len(h1s) != 1:
        doc.add(1, "TTL", f"expected exactly one H1, found {len(h1s)}")
        return
    idx = blocks.index(h1s[0])
    following = [b for b in blocks[idx + 1:] if b.kind != "blank"]
    nxt = following[0] if following else None
    t = doc.doc_type
    if t in ("readme-project", "readme-folder"):
        if not nxt or nxt.kind != "para":
            doc.add(h1s[0].start + 1, "TTL", "a README puts its one-line description directly under the H1")
        elif t == "readme-project":
            text = " ".join(l.strip() for l in nxt.lines)
            if len(nxt.lines) > 2 or len(text) > 120:
                doc.add(nxt.start + 1, "TTL", "project one-liner must be one sentence under 120 characters")
    elif t in GUIDE_TYPES:
        if not nxt or not is_audience(nxt):
            doc.add(h1s[0].start + 1, "TTL", f"a guide boxes its readers directly under the H1, as '{AUDIENCE_PREFIX} who and why'")
        elif t != "index":
            # A guide says what it covers and why in a plain paragraph before its first heading or table.
            shown = [b for b in following if b.kind != "html"]
            # Every line of the box carries its marker; a bare line is the intro run into it.
            bare = [i for i, line in enumerate(nxt.lines) if not line.lstrip().startswith(">")]
            if bare:
                doc.add(nxt.start + bare[0] + 1, "INTRO", "leave a blank line between the Audience box and the intro paragraph")
            elif len(shown) < 2 or shown[1].kind != "para" or shown[1].lines[0].lstrip().startswith(">"):
                doc.add(nxt.start + 1, "INTRO", "follow the Audience box with a plain paragraph on what this guide covers and why")


def h2_headings(blocks: list[Block]) -> list[Block]:
    return [b for b in blocks if b.kind == "heading" and heading_level(b.lines[0]) == 2]


def check_headings(doc: Doc, blocks: list[Block]) -> None:
    headings = [b for b in blocks if b.kind == "heading"]
    for i, b in enumerate(headings):
        title = re.sub(r"^#+\s+", "", b.lines[0]).strip()
        if not is_title_case(title):
            doc.add(b.start + 1, "HCASE", f"heading is not Title Case: '{title}'")
    for i, b in enumerate(blocks):
        if b.kind != "heading":
            continue
        rest = [x for x in blocks[i + 1:] if x.kind != "blank"]
        if not rest or (rest[0].kind == "heading" and heading_level(rest[0].lines[0]) <= heading_level(b.lines[0])):
            doc.add(b.start + 1, "EMPTY", "heading has no content before the next heading")
    h2s = h2_headings(blocks)
    if len(h2s) > H2_MAX:
        doc.add(h2s[H2_MAX].start + 1, "H2N", f"more than {H2_MAX} H2 sections; split the file")


def check_toc(doc: Doc, blocks: list[Block]) -> None:
    h2s = h2_headings(blocks)
    titles = [re.sub(r"^#+\s+", "", b.lines[0]).strip() for b in h2s]
    toc_idx = next((i for i, t in enumerate(titles) if t.lower() == "table of contents"), None)
    needs = (len(doc.lines) > TOC_LINES or len(h2s) > TOC_H2) and len(h2s) >= 3 and doc.doc_type != "adr"
    if doc.doc_type == "adr" and toc_idx is not None:
        doc.add(h2s[toc_idx].start + 1, "TOC", "an ADR never has a table of contents")
        return
    if needs and toc_idx is None:
        doc.add(1, "TOC", f"file exceeds {TOC_LINES} lines or {TOC_H2} H2 sections and needs a Table of Contents")
        return
    if not needs and toc_idx is not None:
        doc.add(h2s[toc_idx].start + 1, "TOC", "file is under the threshold; remove the Table of Contents")
        return
    if toc_idx is None:
        return
    toc_block = blocks[blocks.index(h2s[toc_idx]) + 1:]
    toc_list = next((b for b in toc_block if b.kind == "list"), None)
    if not toc_list:
        doc.add(h2s[toc_idx].start + 1, "TOC", "Table of Contents has no list")
        return
    anchors = re.findall(r"\]\(#([^)]+)\)", "\n".join(toc_list.lines))
    expected = [slugify(t) for i, t in enumerate(titles) if i != toc_idx]
    if anchors != expected:
        doc.add(toc_list.start + 1, "TOC", f"Table of Contents entries must match the H2 headings in order: expected {expected}")


def check_cap(doc: Doc, blocks: list[Block]) -> None:
    # A cap bounds what a reader reads, so Mermaid source does not count: the
    # palette lines a diagram must carry never force prose out of a guide.
    diagram = {i for b in blocks if b.kind == "fence" and b.lang == "mermaid" for i in range(b.start, b.start + len(b.lines))}
    prose = [i for i in range(len(doc.lines)) if i not in diagram]
    cap = TYPES.get(doc.doc_type) if doc.doc_type else max(c for c in TYPES.values() if c)
    # The ADR index lists every decision, so it grows with the decision log, as the glossary does.
    if doc.doc_type == "index" and is_adr_index(doc.path):
        cap = None
    # The brief is read in ten minutes, so it holds less than any other explanation.
    elif doc.doc_type == "explanation" and os.path.basename(doc.path) == "brief.md":
        cap = BRIEF_CAP
    if not cap or len(prose) <= cap:
        return
    if doc.doc_type:
        message = f"exceeds the {cap}-line cap for type '{doc.doc_type}'; split by topic"
    else:
        message = f"exceeds even the widest cap ({cap}); declare a Type and split by topic"
    doc.add(prose[cap] + 1, "CAP", f"{len(prose)} lines outside diagrams {message}")


def check_fences(doc: Doc, blocks: list[Block]) -> None:
    for b in blocks:
        if b.kind == "fence" and not b.lang:
            doc.add(b.start + 1, "FENCE", "code fence has no language tag")


def check_density(doc: Doc, blocks: list[Block]) -> None:
    under_toc = False  # TOC must list every H2 (up to H2_MAX), so LIST_MAX cannot apply to it
    for b in blocks:
        if b.kind == "heading":
            under_toc = re.sub(r"^#+\s+", "", b.lines[0]).strip().lower() == "table of contents"
        elif b.kind == "para":
            if len(b.lines) > RUN_MAX:
                doc.add(b.start + 1, "RUN", f"prose run of {len(b.lines)} lines exceeds {RUN_MAX}; break it with a list, table, or diagram")
            # A blockquote marker is not a word.
            text = " ".join(QUOTE_RX.sub("", l).strip() for l in b.lines)
            # A Sources line is a list of links, not a sentence.
            if is_audience(b) or is_sources(b):
                continue
            sents = sentences(text)
            if len(sents) > PARAGRAPH_MAX:
                doc.add(b.start + 1, "PARA", f"paragraph has {len(sents)} sentences; cap is {PARAGRAPH_MAX}")
            for s in sents:
                wc = word_count(s)
                if wc > SENTENCE_MAX:
                    doc.add(b.start + 1, "SENT", f"sentence of {wc} words exceeds {SENTENCE_MAX}: '{s[:60]}...'")
        elif b.kind == "table":
            for j, row in enumerate(b.lines):
                if re.match(r"^\s*\|[\s:\-|]+\|\s*$", row):
                    continue
                cells = [c.strip() for c in row.strip().strip("|").split("|")]
                for c in cells:
                    wc = word_count(c)
                    if wc > CELL_MAX:
                        doc.add(b.start + j + 1, "CELL", f"table cell of {wc} words exceeds {CELL_MAX}: '{c[:50]}...'")
        elif b.kind == "list":
            items: list[tuple[int, str, int]] = []  # (line, text, indent)
            for j, l in enumerate(b.lines):
                m = re.match(r"^(\s*)([-*+]|\d+\.)\s+(.*)", l)
                if m:
                    items.append((b.start + j, m.group(3), len(m.group(1))))
                elif items:
                    ln, txt, ind = items[-1]
                    items[-1] = (ln, txt + " " + l.strip(), ind)
            top = [it for it in items if it[2] == 0]
            if len(top) > LIST_MAX and doc.doc_type != "index" and not under_toc:
                doc.add(top[LIST_MAX][0] + 1, "LIST", f"list has {len(top)} items; cap is {LIST_MAX}, use a table or split")
            for ln, txt, _ in items:
                wc = word_count(txt)
                if wc > BULLET_MAX:
                    doc.add(ln + 1, "BUL", f"bullet of {wc} words exceeds {BULLET_MAX}; use a sub-bullet")
                for s in sentences(txt):
                    wc = word_count(s)
                    if wc > SENTENCE_MAX:
                        doc.add(ln + 1, "SENT", f"sentence of {wc} words exceeds {SENTENCE_MAX}")


def check_words(doc: Doc, blocks: list[Block]) -> None:
    banned = [(w, re.compile(r"(?<![\w-])" + re.escape(w) + r"(?![\w-])", re.I)) for w in BANNED_WORDS]
    metas = [re.compile(p, re.I) for p in META_PHRASES]
    # The ADR index summarizes decisions, which may say what an older ADR did.
    history = not is_adr_index(doc.path)
    for b in blocks:
        if b.kind in ("fence", "html", "blank"):
            continue
        for j, raw in enumerate(b.lines):
            text = strip_inline_code(raw)
            for w, rx in banned:
                if rx.search(text):
                    doc.add(b.start + j + 1, "WORD", f"banned word '{w}'; delete it")
            for rx in metas:
                if rx.search(text):
                    doc.add(b.start + j + 1, "META", "meta-commentary about the document itself; describe the current state instead")
        if history and b.kind != "heading":
            joined = ""
            for j, raw in enumerate(b.lines):
                start = len(joined)
                joined += link_text_only(strip_inline_code(raw)).strip() + " "
                m = HIST_RX.search(joined, max(0, start - 40))
                if m and m.end() > start:
                    doc.add(b.start + j + 1, "HIST", "change-log phrase; describe the current state, and leave history to Git and the ADRs")
                    joined = ""


def check_bloat(doc: Doc, blocks: list[Block]) -> None:
    """Frozen values and schema-copy tables: facts the code already owns."""
    frozen_next = False
    for b in blocks:
        if b.kind == "blank":
            continue
        if b.kind == "html":
            m = FROZEN_RX.match(b.lines[0]) if len(b.lines) == 1 else None
            if m:
                if len(m.group(1).split()) < FROZEN_REASON_WORDS:
                    doc.add(b.start + 1, "FROZEN", f"a frozen marker needs a reason of {FROZEN_REASON_WORDS} or more words")
                frozen_next = True
            continue
        exempt, frozen_next = frozen_next, False
        if b.kind == "fence":
            continue
        for j, raw in enumerate(b.lines):
            if exempt:
                break
            if PIN_RX.search(raw):
                doc.add(b.start + j + 1, "PIN", "a patch-level version goes stale; link the manifest, or add a frozen marker with a reason")
            if LINE_RX.search(raw):
                doc.add(b.start + j + 1, "LINE", "a source line number goes stale; link the file or a symbol in it")
        if b.kind == "table":
            rows = [r for r in b.lines[2:] if r.strip()]
            led = [r for r in rows if r.strip().lstrip("|").strip().startswith("`")]
            limit = COPY_ROWS_REFERENCE if doc.doc_type == "reference" else COPY_ROWS
            if len(rows) >= limit and len(led) >= COPY_LED_SHARE * len(rows):
                doc.add(b.start + 1, "COPY", f"a {len(rows)}-row table led by code identifiers copies the code; keep what readers need and link the source")


def check_emoji(doc: Doc, blocks: list[Block]) -> None:
    """Emojis are fixed markers in the body: a callout, a status cell, or a topic lead."""
    glyphs = {swatch for swatch, _ in PALETTE.values()} | {LINK_ICON}
    for b in blocks:
        if b.kind in ("blank", "html") or (b.kind == "fence" and b.lang != "mermaid"):
            continue
        for j, raw in enumerate(b.lines):
            line_no = b.start + j + 1
            text = strip_inline_code(raw)
            found = [m.replace("\ufe0f", "") for m in EMOJI_RX.findall(text)]
            text = text.replace("\ufe0f", "")
            if not found:
                continue
            if b.kind == "fence":
                if any(ch != LINK_ICON for ch in found):
                    doc.add(line_no, "EMOJI", f"a diagram holds no emoji but {LINK_ICON}; the tag and shape carry the type")
                continue
            if b.kind == "heading":
                doc.add(line_no, "EMOJI", "a heading holds no emoji; it breaks the anchor in some viewers")
                continue
            lead = re.sub(r"^(\s*([-*+]|\d+[.)])\s+|\|\s*)", "", text)
            for ch in found:
                if ch in glyphs:
                    continue
                if ch in CALLOUT_MARKERS:
                    if not text.lstrip().startswith(f"> {ch} **{CALLOUT_MARKERS[ch]}:** "):
                        doc.add(line_no, "EMOJI", f"{ch} opens a callout only, as '> {CALLOUT_FORMS[ch]} **{CALLOUT_MARKERS[ch]}:** text'")
                elif ch in STATUS_MARKERS:
                    if b.kind != "table" and not is_legend(b):
                        doc.add(line_no, "EMOJI", f"{ch} marks a status in a table cell, or keys one on its legend line")
                elif ch in TOPIC_MARKERS:
                    if b.kind not in ("list", "table") or not lead.startswith(ch) or len(found) > 1 and found[0] != ch:
                        doc.add(line_no, "EMOJI", f"{ch} is a topic lead; open one bullet or a table row's first cell with it")
                else:
                    doc.add(line_no, "EMOJI", f"'{ch}' is not a docsmith marker; pick one from the style reference or drop it")


def check_unboxed_sources(doc: Doc, blocks: list[Block]) -> None:
    """A plain or bold 'Sources:' or 'References:' paragraph takes the boxed caption a diagram's Sources line uses."""
    for b in blocks:
        if b.kind == "para" and re.match(r"(\*\*)?(Sources?|References?):", b.lines[0]):
            doc.add(b.start + 1, "MMD", f"box the sources on one line, as '{SOURCES_PREFIX} *[a](a.md) · [b](b.md)*'")


def check_links(doc: Doc, blocks: list[Block], root: str, heading_cache: dict[str, dict[str, str]]) -> None:
    for b in blocks:
        if b.kind in ("fence", "html"):
            continue
        for j, raw in enumerate(b.lines):
            line_no = b.start + j + 1
            text = strip_inline_code(raw)
            for m in MD_LINK_RX.finditer(text):
                label, target = m.group(1), m.group(2)
                if label.strip().lower() in ("here", "click here", "link", "this"):
                    doc.add(line_no, "LINK", f"link text '{label}' says nothing; name the target")
                check_target(doc, line_no, target, root, heading_cache)
            for m in re.finditer(r"(?<![(<`\[])https?://\S+", text):
                doc.add(line_no, "LINK", f"bare URL '{m.group(0)[:40]}'; give it link text")


def check_target(doc: Doc, line_no: int, target: str, root: str, heading_cache: dict[str, dict[str, str]]) -> None:
    """Check one link target: a relative path must resolve, and its anchor must match a heading."""
    if re.match(r"https?://", target) and re.search(r"github\.com/[^/]+/[^/]+/(blob|tree)/", target):
        doc.add(line_no, "LINK", "absolute GitHub URL into a repo; use a relative path")
    full = local_path(doc, target)
    if full is None:
        return
    path_part, _, anchor = target.partition("#")
    if path_part and not os.path.exists(full):
        doc.add(line_no, "LINK", f"relative link does not resolve: {target}")
        return
    if not anchor:
        return
    if os.path.isdir(full):
        doc.add(line_no, "LINK", f"anchor on a directory link: {target}")
        return
    slugs = heading_cache.get(full)
    if slugs is None:
        try:
            with open(full, encoding="utf-8") as fh:
                slugs = collect_slugs(fh.read().splitlines())
        except OSError:
            slugs = {}
        heading_cache[full] = slugs
    heading = slugs.get(anchor.lower())
    if heading is None:
        doc.add(line_no, "LINK", f"anchor '#{anchor}' matches no heading in {os.path.relpath(full, root)}")
    elif not re.fullmatch(r"[A-Za-z0-9 -]+", heading):
        doc.add(line_no, "LINK", f"anchor '#{anchor}' targets '{heading}'; Azure DevOps slugs its punctuation differently, so keep only letters, digits, spaces and hyphens")


def collect_slugs(lines: list[str]) -> dict[str, str]:
    """Map each heading's GitHub slug to its heading text, in document order."""
    seen: dict[str, int] = {}
    out: dict[str, str] = {}
    in_fence = False
    for l in lines:
        if re.match(r"^\s*(`{3,}|~{3,})", l):
            in_fence = not in_fence
            continue
        if in_fence or not heading_level(l):
            continue
        heading = re.sub(r"^#+\s+", "", l).strip()
        s = slugify(heading)
        if s in seen:
            seen[s] += 1
            s = f"{s}-{seen[s]}"
        else:
            seen[s] = 0
        out[s] = heading
    return out


def split_frontmatter(body: list[str]) -> tuple[list[str] | None, list[str]]:
    if not body or body[0].strip() != "---":
        return None, body
    for k in range(1, len(body)):
        if body[k].strip() == "---":
            config = textwrap.dedent("\n".join(body[1:k])).splitlines()
            return [l.rstrip() for l in config], body[k + 1:]
    return [], body[1:]


def required_init(lines: list[str]) -> tuple[str, str] | None:
    """Return what needs a fixed second line, and that line, for a diagram's directive-free lines."""
    if lines[:1] == ["sequenceDiagram"]:
        return "a sequence diagram", SEQUENCE_INIT
    if lines[:1] == ["graph TD"]:
        return "a flowchart", FLOWCHART_INIT
    return None


def check_mermaid(doc: Doc, blocks: list[Block], root: str, heading_cache: dict[str, dict[str, str]]) -> None:
    for i, b in enumerate(blocks):
        if b.kind != "fence" or b.lang != "mermaid":
            continue
        line_no = b.start + 1
        raw = [l for l in b.lines[1:-1] if l.strip()]
        # Plain '%%' comments drop out, so a comment above the head cannot hide a sequence diagram.
        lines = [l.strip() for l in raw if not l.strip().startswith("%%") or l.strip().startswith("%%{")]
        required = required_init(lines)
        if required and lines[1:2] != [required[1]]:
            doc.add(line_no, "MMD", f"{required[0]} has the second line exactly '{required[1]}'")
        # A required second line is judged above, whatever it holds.
        if any(l.startswith("%%{") for l in (lines[2:] if required else lines)):
            doc.add(line_no, "MMD", "init directives are not portable; a viewer that reads the first line as the diagram type rejects the block")
        body = [l for l in raw if not l.strip().startswith("%%")]
        config, body = split_frontmatter(body)
        if config is not None:
            doc.add(line_no, "MMD", "frontmatter is not portable; Azure DevOps reads the first line as the diagram type and reports 'Unsupported diagram type'")
        if not body:
            doc.add(line_no, "MMD", "empty diagram")
            continue
        head = body[0].strip()
        stacked: dict[str, str] = {}
        if head == "graph TD":
            body, stacked = unstack(body)
        check_portable(doc, line_no, body, head == "graph TD")
        colors = check_colors(doc, line_no, body[1:], head == "graph TD") if head in ("graph TD", "sequenceDiagram", "erDiagram") else set()
        boundaries: list[str] = []
        links: list[tuple[tuple[str, str], str]] = []
        if head == "graph TD":
            family = flowchart_family(body[1:])
            titles, edges, boundaries, links = check_flowchart(doc, line_no, body[1:], family, stacked)
        elif head.startswith("flowchart"):
            doc.add(line_no, "MMD", f"use 'graph TD', not '{head}'; Azure DevOps documents the 'flowchart' keyword as unsupported")
            continue
        elif head == "sequenceDiagram":
            family = "runtime"
            titles, edges = check_sequence(doc, line_no, body[1:])
        elif head == "erDiagram":
            family = "data"
            titles, edges = check_er_diagram(doc, line_no, body[1:])
        else:
            doc.add(line_no, "MMD", f"diagram must start with 'graph TD', 'sequenceDiagram', or 'erDiagram', found '{head}'")
            continue
        if any("click " in l for l in body):
            doc.add(line_no, "MMD", f"click directives are not allowed; link a node from its title, as \"<a href='path'>Title {LINK_ICON}</a>\"")
        before = [x for x in blocks[:i] if x.kind != "blank"]
        if not before or before[-1].kind != "para" or is_legend(before[-1]) or is_sources(before[-1]):
            doc.add(line_no, "MMD", "a diagram is preceded by one lead sentence")
        # The blocks a diagram owns run to the next heading, fence, or data
        # table: its legend, then its numbered list, then its Sources line.
        # A Sources line after a data table cites that table.
        tail: list[Block] = []
        for x in blocks[i + 1:]:
            if x.kind in ("heading", "fence") or (x.kind == "table" and not NODE_TABLE_RX.match(x.lines[0])):
                break
            if x.kind != "blank":
                tail.append(x)
        k = 0
        legend = tail[k] if k < len(tail) and is_legend(tail[k]) else None
        k += legend is not None
        if k < len(tail) and tail[k].kind == "list" and re.match(r"^\s*\d+\.", tail[k].lines[0]):
            k += 1
        listed = tail[k] if k < len(tail) and is_sources(tail[k]) else None
        k += listed is not None
        # A legend anywhere else is misplaced. Each one is reported, and the
        # first stands in for the missing legend.
        misplaced: list[Block] = []
        for x in tail[k:]:
            if is_legend(x):
                misplaced.append(x)
            elif is_sources(x) and listed is None:
                listed = x
                doc.add(x.start + 1, "MMD", "move the Sources line under the diagram, after its legend and numbered list")
            elif is_sources(x):
                doc.captions.add(x.start)
                doc.add(x.start + 1, "MMD", "a diagram takes one Sources line; remove this one")
            elif x.kind == "table" and NODE_TABLE_RX.match(x.lines[0]):
                doc.add(x.start + 1, "MMD", f"drop the Node table; a flowchart links each node from its title, and a sequence or ER diagram lists its sources on one '{SOURCES_PREFIX}' line")
            elif x.kind == "para" and x.lines[0].startswith(UNBOXED_CAPTIONS):
                doc.add(x.start + 1, "MMD", f"box the caption and italicize its text, as '{LEGEND_PREFIX} *...*' or '{SOURCES_PREFIX} *...*'")
        for extra in misplaced:
            if legend is None:
                legend = extra
                doc.add(extra.start + 1, "MMD", "move the legend directly under the diagram, above the numbered list and Sources line")
            else:
                doc.add(extra.start + 1, "MMD", "a diagram takes one legend, directly under it; remove this one")
                # Reported here, so the stray copy is not also a duplicate fact.
                doc.captions.add(extra.start)
        if legend and len(legend.lines) > 1:
            doc.add(legend.start + 1, "MMD", "a legend is one line; move any explanation into the paragraph after it, and keep a blank line above the Sources line")
        elif legend:
            boxed_text(doc, legend, LEGEND_PREFIX)
            # A legend repeats by design, so it is not a fact to deduplicate.
            doc.captions.add(legend.start)
        if colors and legend is None:
            doc.add(line_no, "MMD", f"a colored diagram is followed directly by a '{LEGEND_PREFIX}' line")
        elif colors and len(legend.lines) == 1:
            for name, (swatch, _) in PALETTE.items():
                if (name in colors) != (swatch in legend.lines[0]):
                    doc.add(legend.start + 1, "MMD", f"legend names the '{name}' swatch {swatch} exactly when the diagram uses that class")
            if (FUTURE_CLASS in colors) != (FUTURE_LEGEND in legend.lines[0]):
                doc.add(legend.start + 1, "MMD", f"legend says '{FUTURE_LEGEND}' exactly when a node takes the {FUTURE_CLASS} class")
        if legend and not colors and any(swatch in legend.lines[0] for swatch, _ in PALETTE.values()):
            doc.add(legend.start + 1, "MMD", "legend names a palette swatch, but no node above it takes a palette class; a sequence diagram's band titles name its owners")
        # Every title maps to its source, or to '' when it has none, so the
        # cross-file NODE check also catches a title linked in one place only.
        # Nodes and boundaries keep apart: a frame often shares its name with
        # the node it deploys.
        sources = {**{("node", t): "" for t in titles}, **{("boundary", t): "" for t in boundaries}}
        for key, target in links:
            check_target(doc, line_no, target, root, heading_cache)
            full = local_path(doc, target)
            if full is not None and "#" not in target and os.path.isdir(full):
                doc.add(line_no, "MMD", f"{key[0]} '{key[1]}' links a folder; link a file, since an IDE preview cannot open a folder: {target}")
            source = resolve_source(doc, target, root)
            if sources.get(key, "") not in ("", source):
                doc.add(line_no, "NODE", f"{key[0]} '{key[1]}' links both '{sources[key]}' and '{source}' in one diagram; one title, one source")
            sources[key] = source
        if listed and head == "graph TD":
            doc.captions.add(listed.start)
            doc.add(listed.start + 1, "MMD", "a flowchart links each node from its title; drop the Sources line")
        elif listed:
            check_sources_line(doc, listed, sources, root)
        doc.diagrams.append(Diagram(line_no, family, titles, edges, sources))


def boxed_text(doc: Doc, b: Block, prefix: str) -> str:
    """Return the italic text after a boxed line's bold label, reporting it when it is not in italics."""
    first, *rest = b.lines
    text = " ".join([first.strip()[len(prefix):], *(QUOTE_RX.sub("", l) for l in rest)]).strip()
    if not (len(text) > 2 and text.startswith("*") and text.endswith("*")):
        doc.add(b.start + 1, "MMD", f"the text after '{prefix}' is in italics, as '{prefix} *...*'")
    return text.strip("*")


def check_sources_line(doc: Doc, listed: Block, sources: dict[tuple[str, str], str], root: str) -> None:
    """Read a sequence or ER diagram's Sources line into sources; check_links checks its targets."""
    # The line repeats each participant's file by design, so it is not a fact to deduplicate.
    doc.captions.add(listed.start)
    line_no = listed.start + 1
    if len(listed.lines) > 1:
        doc.add(line_no, "MMD", "the Sources line is one line")
    listed_titles: set[str] = set()
    for item in boxed_text(doc, listed, SOURCES_PREFIX).split(" · "):
        m = SOURCE_ITEM_RX.match(item)
        if not m:
            doc.add(line_no, "MMD", f"a Sources item is 'Title [file](path)', with any further links after ', ': '{item[:50]}'")
            continue
        title = m.group(1)
        if ("node", title) not in sources:
            # A bare title names the one participant that carries it; two need the tag.
            named_as = [t for kind, t in sources if kind == "node" and bare(t) == title]
            if len(named_as) != 1:
                doc.add(line_no, "MMD", f"Sources item '{title}' names {'several participants; add its tag' if named_as else 'no participant or entity in the diagram above'}")
                continue
            title = named_as[0]
        if title in listed_titles:
            doc.add(line_no, "MMD", f"Sources item '{title}' is listed twice")
        listed_titles.add(title)
        # The first link is the title's source; any after it are further references.
        sources[("node", title)] = resolve_source(doc, MD_LINK_RX.search(m.group(2)).group(2), root)


# The only targets outside the repository: a web page or a mail address.
EXTERNAL_RX = re.compile(r"https?://|mailto:")


def local_path(doc: Doc, target: str) -> str | None:
    """Return the file a relative link target names, the doc itself for a bare anchor, or None for a web or mail URL."""
    if EXTERNAL_RX.match(target):
        return None
    path_part = urllib.parse.unquote(target.partition("#")[0])
    if not path_part:
        return os.path.abspath(doc.path)
    return os.path.normpath(os.path.join(doc.folder, path_part))


def resolve_source(doc: Doc, target: str, root: str) -> str:
    """Normalize a link target so the same file compares equal from any folder."""
    full = local_path(doc, target)
    if full is None:
        return target.split("#")[0]
    return os.path.relpath(full, root).replace(os.sep, "/")


# Every quoted node shape, longest opening first, so a disallowed shape is
# still read as a node and reported once, with no follow-on findings.
NODE_OPEN = r'\(\(\(|\(\[|\[\[|\[\(|\[/|\[\\|\{\{|\(\(|>|\[|\(|\{'
NODE_RX = re.compile(r'(\w+)\s*(' + NODE_OPEN + r')\s*"([^"]*)"')
NODE_DEF_RX = re.compile(r'(\w+)\s*(?:' + NODE_OPEN + r')\s*"[^"]*"\s*[\])}/\\]{1,3}')
ARROW = r'(?:(?:-{2,3}>|={2,3}>|-\.{1,2}->)\s*(?:\|\s*"([^"]*)"\s*\|)?|-\.\s*"([^"]*)"\s*\.->|--\s*"([^"]*)"\s*-->|==\s*"([^"]*)"\s*==>)'
EDGE_RX = re.compile(r'(\w+)\s*' + ARROW + r'\s*(?=(\w+))')
BOUNDARY_TITLE_RX = re.compile(r"^[^<>\[\]]+$")
SUBGRAPH_RX = re.compile(r"^subgraph\s+(\w+)")
# A node or boundary links its source from its title: the whole title wrapped
# in one link, then a globe that marks it as one. Every viewer opens a label
# link, while Mermaid 'click' links fail and their tooltips are unreadable.
LINK_ICON = "\U0001F310"
LINKED_TITLE_RX = re.compile(rf"^<a href='([^'\s<>]+)'>([^<>]+) {LINK_ICON}</a>$")
# The target of every linked title inside a diagram block.
TITLE_HREF_RX = re.compile(r"<a href='([^'\s<>]+)'>")


def linked_paths(doc: Doc, blocks: list[Block], root: str) -> set[str]:
    """Root-relative paths of the local files a doc links, from prose links and diagram titles."""
    targets: list[str] = []
    for b in blocks:
        if b.kind == "fence" and b.lang == "mermaid":
            targets += [m.group(1) for raw in b.lines for m in TITLE_HREF_RX.finditer(raw)]
        elif b.kind not in ("fence", "html"):
            targets += [m.group(2) for raw in b.lines for m in MD_LINK_RX.finditer(strip_inline_code(raw))]
    return {resolve_source(doc, t, root) for t in targets if local_path(doc, t) is not None}
# A link that opens a node or boundary label, so the portability check can set
# it aside; linked_title judges its exact form. An edge label's '|"' never matches.
TITLE_LINK_RX = re.compile(r"""(?:(?<=[\[({/]")|(?<=label: "))<a [^>]*>([^<]*)</a>""")
HTML_TAG_RX = re.compile(r"<(?!br/>)/?[a-zA-Z][^>]*>")
# A sequence or ER diagram, whose participants and entities cannot hold a
# link, lists its sources on one boxed line under it, '> **Sources:** *...*',
# the list in italics: 'Title [file](path)' items joined by ' · ', each with
# one link or several joined by ', '. The legend sits in the same kind of box,
# '> **Legend:** *...*'.
# The emoji markers a guide may use, each with one meaning; style.md lists them.
# Variation selectors are dropped before matching, so a marker with or without
# U+FE0F counts as the same one.
CALLOUT_MARKERS = {"\u26a0": "Warning", "\U0001F4A1": "Tip"}
STATUS_MARKERS = {"\u2705", "\u274c", "\U0001F7E1"}
TOPIC_MARKERS = {
    "\U0001F510", "\U0001F9FE", "\U0001F6E1", "\U0001F9EA", "\U0001F680", "\u2699",
    "\U0001F4E6", "\U0001F916", "\U0001F464", "\U0001F4B0", "\u23f1", "\U0001F50C",
}
EMOJI_RX = re.compile(
    "[\U0001F000-\U0001FAFF]\ufe0f?"
    "|[\u2000-\u2BFF]\ufe0f"
    "|[0-9#*]?\ufe0f?\u20e3"
    "|[\u231a\u231b\u23e9-\u23ec\u23f0\u23f3\u25fd\u25fe\u2614\u2615\u2648-\u2653\u267f\u2693"
    "\u26a1\u26aa\u26ab\u26bd\u26be\u26c4\u26c5\u26ce\u26d4\u26ea\u26f2\u26f3\u26f5\u26fa\u26fd"
    "\u2705\u270a\u270b\u2728\u274c\u274e\u2753-\u2755\u2757\u2795-\u2797\u27b0\u27bf"
    "\u2b1b\u2b1c\u2b50\u2b55]"
)
# How a callout marker is written, with its emoji presentation selector where it needs one.
CALLOUT_FORMS = {"\u26a0": "\u26a0\ufe0f", "\U0001F4A1": "\U0001F4A1"}
SOURCES_PREFIX = "> **Sources:**"
# A guide names its readers in a box under the H1, as a diagram boxes its legend and sources.
AUDIENCE_PREFIX = "> **Audience:**"
LEGEND_PREFIX = "> **Legend:**"
UNBOXED_CAPTIONS = ("**Legend:**",)
# The marker that opens each line of a Markdown blockquote.
QUOTE_RX = re.compile(r"^\s*>\s?")
# A Markdown link, never an image: its text and its target.
MD_LINK_RX = re.compile(r"(?<!!)\[([^\]]*)\]\(([^)\s]+)\)")
MD_LINK = r"\[[^\]]+\]\([^)\s]+\)"
SOURCE_ITEM_RX = re.compile(rf"^(.+?) ({MD_LINK}(?:, {MD_LINK})*)$")
NODE_TABLE_RX = re.compile(r"^\|\s*Node\s*\|\s*Source\s*\|")
# A label that opens like a Markdown block. Mermaid 11 parses labels as
# Markdown, and several releases draw 'Unsupported markdown: list' instead.
MARKDOWN_LABEL_RX = re.compile(r"^\s*(?:\d+[.)]|[-*+>]|#{1,6})\s")
STEP_RX = re.compile(r"^\d+[a-z]?:\s")
TYPED_LABEL_RX = re.compile(r"^(.+)<br/>\[([A-Z0-9, -]+)\]$")
# These run on a line whose quoted strings are blanked, so label text cannot
# trigger them. An unquoted edge label, piped or inline, hides the edge from
# every other edge check, and so does any link other than the three portable
# ones, or a second link on the same line.
QUOTED_RX = re.compile(r'"[^"]*"')
UNQUOTED_EDGE_RX = re.compile(
    r'(?:-{2,3}>|={2,3}>|-\.{1,2}->)\s*\|(?!\s*")'
    r'|(?:--|==|-\.)\s*(?!"")[^\s\-=.>|"][^>|]*?(?:-->|==>|\.->)'
    r'|\|\s*""\s*[^\s|]'
)
# A lengthened arrow is left to ARROW_HEAD_RX.
OTHER_LINK_RX = re.compile(r'<[-=.]|---(?!-*>)|===(?!=*>)|\.-(?!>)|[-=]{2}[xo]|~~~')
# Every arrow head on a line. A piped-label link may be one character longer,
# which moves its label off a bend onto the straight run below it, so a long
# head must open a '|' label.
ARROW_HEAD_RX = re.compile(r'[-=.]{2,}>')
SHORT_HEADS = {"-->", "==>", "-.->", ".->"}
LONG_HEADS = {"--->", "===>", "-..->"}
LINK_HEAD_RX = re.compile(r'-->|==>|\.->')
# The node and edge id and property syntax of newer Mermaid releases, such as
# 'A@{ shape: circle }' or 'A e1@--> B'.
PROPERTY_SYNTAX_RX = re.compile(r'\w+@')


def masked(s: str) -> str:
    """Blank every quoted string to spaces in place, so a match cannot start inside a label and positions still map to s."""
    return QUOTED_RX.sub(lambda m: '"' + " " * (len(m.group(0)) - 2) + '"', s)


def quoted_nodes(s: str) -> list[tuple[str, str, str, int]]:
    """Return (id, opening, label, end) for each quoted node definition on a line."""
    return [(m.group(1), m.group(2), s[m.start(3):m.end(3)], m.end()) for m in NODE_RX.finditer(masked(s))]


def strip_node_defs(s: str) -> str:
    """Replace each quoted node definition with its id, so EDGE_RX reads the edge around it."""
    out, last = [], 0
    for m in NODE_DEF_RX.finditer(masked(s)):
        out += [s[last:m.start()], m.group(1)]
        last = m.end()
    return "".join(out) + s[last:]
# The opening and closing brackets of the allowed node shapes, and the shape
# each TYPE takes; every other TYPE is a rectangle. Each is a classic shape that
# every viewer's Mermaid release draws. Circles stay out: they balloon around a
# two-line label. The rhombus balloons too, so only a short DECISION takes it.
SHAPES = {"[": "]", "(": ")", "([": "])", "[[": "]]", "[(": ")]", "{{": "}}", "[/": "/]", "{": "}"}
CYLINDER = ("[(", ")]")
TYPE_SHAPES = {
    "PERSON": ("([", "])"),
    "UI": ("(", ")"),
    "API": ("[/", "/]"),
    "AGENT": ("{{", "}}"),
    "TOOL": ("[[", "]]"),
    "DECISION": ("{", "}"),
    "DATA": CYLINDER,
    "CLOUD SQL": CYLINDER,
    "AZURE SQL": CYLINDER,
    "MEMORYSTORE": CYLINDER,
    "OBJECT STORAGE": CYLINDER,
    **{typ: CYLINDER for typ in TECHNOLOGY_STORE_TYPES},
}
RECTANGLE = ("[", "]")

SHAPE_MESSAGE = "node '{}' must be a rectangle, rounded box, stadium, subroutine, cylinder, hexagon, parallelogram, or rhombus"


# The two stacked shapes, the only '@{ }' form allowed, for a node that stands
# for several things. Mermaid stacks no other shape, so stacked documents carry
# a cylinder TYPE and a stacked rectangle any other TYPE, its tag naming the
# type. Each viewer's Mermaid release draws them.
STACKED_RX = re.compile(r'^(\s*)(\w+)@\{ shape: (st-rect|docs), label: "([^"]*)" \}$')
STACKED_SHAPES = {"st-rect": RECTANGLE, "docs": CYLINDER}


def unstack(body: list[str]) -> tuple[list[str], dict[str, str]]:
    """Rewrite each stacked node as the classic shape it stacks, so the node checks read it, and return each stacked id's shape."""
    out, stacked = [], {}
    for l in body:
        m = STACKED_RX.match(l.rstrip())
        if m:
            indent, ident, shape, label = m.groups()
            opening, closing = STACKED_SHAPES[shape]
            l = f'{indent}{ident}{opening}"{label}"{closing}'
            stacked[ident] = shape
        out.append(l)
    return out, stacked


# English words that end in "s" yet name one thing, so the plural check passes them.
SINGULAR_S = {"analytics", "atlas", "bias", "canvas", "kubernetes", "lens", "news", "postgres", "series", "status"}
PLURAL_ACRONYM_RX = re.compile(r"[A-Z0-9]+s")
# A hyphenated acronym such as X12-EDI is a product name, not a code name.
HYPHENATED_ACRONYM_RX = re.compile(r"[A-Z0-9]+(?:-[A-Z0-9]+)+")
# A repository or cloud project keeps its real name, so a reader can search for it.
REAL_NAME_TYPES = {"REPO", "GCP PROJECT"}


def is_plural(title: str) -> bool:
    """A title names several things when it lists them, with 'and' or commas, or ends in a plural noun such as 'Tools' or 'APIs'."""
    words = title.split()
    last = words[-1] if words else ""
    if "and" in words or "," in title or PLURAL_ACRONYM_RX.fullmatch(last):
        return True
    # An acronym such as AWS, a product name such as DevOps or Node.js, and a possessive each name one thing;
    # an underscored title is already reported as a code name.
    if last.isupper() or any(c.isupper() for c in last[1:]) or any(c in last for c in "._'"):
        return False
    last = last.lower()
    return last.endswith("s") and not last.endswith(("ss", "us", "is")) and last not in SINGULAR_S


def named(title: str, typ: str) -> str:
    """A node's name is its title with its tag, since a title never repeats the tag: 'Order [API]' and 'Order [DATA]' are two things."""
    return f"{title} [{typ}]"


def bare(name: str) -> str:
    """The title inside a name, the inverse of named()."""
    return name.rsplit(" [", 1)[0]


def wording_problem(title: str, typ: str) -> str | None:
    """Why a title breaks the wording rule: words, not code names, in Title Case, and a DECISION in sentence case."""
    # A title holding markup is reported as markup, so its words are not judged.
    if typ in REAL_NAME_TYPES or "<" in title:
        return None
    words = title.split()
    if "_" in title or any("-" in w and not HYPHENATED_ACRONYM_RX.fullmatch(w) for w in words):
        return "write words, not a code name: drop its hyphens and underscores"
    if typ == "DECISION":
        return "start the question with a capital" if words and words[0][:1].islower() else None
    if any(w[:1].islower() and (i == 0 or w not in SMALL_WORDS) for i, w in enumerate(words)):
        return "write it in Title Case"
    return None


def check_title_words(doc: Doc, line_no: int, kind: str, title: str, typ: str) -> None:
    """Report a title that breaks the wording rule or repeats the noun its TYPE ends in, such as 'Tools' for TOOL."""
    problem = wording_problem(title, typ)
    if problem:
        doc.add(line_no, "MMD", f"{kind} '{title}': {problem}")
    if kind == "boundary" and typ not in REAL_NAME_TYPES and is_plural(title):
        doc.add(line_no, "MMD", f"boundary '{title}' is plural, but Mermaid cannot stack a frame; name the one thing it frames, or the project or repo that holds several")
    noun = typ.split()[-1].lower()
    for word in title.split():
        if word.lower() in (noun, noun + "s", noun + "es"):
            doc.add(line_no, "MMD", f"{kind} '{title}' repeats '{word}' from its [{typ}] tag; drop it")


def linked_title(doc: Doc, line_no: int, text: str) -> tuple[str, str | None]:
    """Split a node or boundary title into its plain text and its link target, if it has one."""
    if "<a" not in text and "</a>" not in text and LINK_ICON not in text:
        return text, None
    m = LINKED_TITLE_RX.match(text)
    if not m:
        doc.add(line_no, "MMD", f"a linked title is exactly \"<a href='path'>Title {LINK_ICON}</a>\": '{text[:60]}'")
        return re.sub(r"<[^>]*>|" + LINK_ICON, "", text).strip(), None
    return m.group(2).strip(), m.group(1)


def link_problems(blanked: str, s: str) -> list[str]:
    """Describe each link on a line that the edge checks cannot read. Its pieces would read as phantom edges, so callers skip its edges."""
    problems = []
    if UNQUOTED_EDGE_RX.search(blanked):
        problems.append(f"edge label must be quoted, as '-->|\"verb\"|': '{s[:50]}'")
    if OTHER_LINK_RX.search(blanked):
        problems.append(f"link with '-->', '-.->', or '==>', or one character longer, only: '{s[:50]}'")
    if any(
        m.group(0) not in SHORT_HEADS and not (m.group(0) in LONG_HEADS and blanked[m.end():].lstrip().startswith("|"))
        for m in ARROW_HEAD_RX.finditer(blanked)
    ):
        problems.append(f"lengthen only a piped-label link, and by one character: '--->', '===>' or '-..->': '{s[:50]}'")
    if len(LINK_HEAD_RX.findall(blanked)) > 1 or "&" in blanked:
        problems.append(f"draw one edge per line: '{s[:50]}'")
    return problems


def check_portable(doc: Doc, line_no: int, body: list[str], flowchart: bool) -> None:
    """Syntax that one common viewer rejects, whatever the newest Mermaid accepts."""
    for l in body:
        s = l.strip()
        tag = HTML_TAG_RX.search(TITLE_LINK_RX.sub(r"\1", s) if flowchart else s)
        if tag:
            doc.add(line_no, "MMD", f"'{tag.group(0)[:30]}' is not portable; a label holds only '<br/>', and a flowchart title its source link")
        if "`" in s:
            doc.add(line_no, "MMD", f"Markdown string labels are not portable: '{s[:40]}'")
        labels = re.findall(r'"([^"]*)"', s)
        message = re.match(r"^\w+\s*-{1,2}(?:>>?|x|\))\s*\w+\s*:\s*(.*)$", s)
        if message:
            labels.append(message.group(1))
        for label in labels:
            if MARKDOWN_LABEL_RX.match(label):
                doc.add(line_no, "MMD", f"label opens like a Markdown list or heading: '{label[:40]}'; write step numbers as '1: text'")


def unknown_type(typ: str, kind: str, title: str) -> str:
    if typ == "DATABASE":
        return f"{kind} '{title}': DATABASE is gone; name the engine, such as [POSTGRES]"
    return f"unknown TYPE '{typ}' in {kind} '{title}'"


def flowchart_family(body: list[str]) -> str:
    """A flowchart is infrastructure when a node or boundary holds an
    infrastructure-only TYPE. Named technologies such as CLOUD RUN appear in
    both families, so they decide nothing."""
    for line in body:
        for _, _, label, _ in quoted_nodes(line):
            label_match = TYPED_LABEL_RX.match(label)
            if label_match and label_match.group(2).strip() in INFRASTRUCTURE_MERMAID_TYPES | INFRASTRUCTURE_BOUNDARY_TYPES:
                return "infrastructure"
    return "application"


def check_colors(doc: Doc, line_no: int, body: list[str], flowchart: bool) -> set[str]:
    """Check one diagram's palette classes and return the ones it colors nodes with."""
    types: dict[str, str] = {}
    boundaries: set[str] = set()
    declared: set[str] = set()
    defined: set[str] = set()
    assigned: dict[str, list[str]] = {}
    invalid = False
    # A line the edge checks cannot read leaves its bare endpoints untyped.
    skipped = False
    for l in body:
        s = l.strip()
        keyword = re.match(r"^(style|linkStyle|classDef|class)\b", s)
        if flowchart and ":::" in re.sub(r'"[^"]*"', '""', s):
            doc.add(line_no, "MMD", "':::' is not allowed; assign a palette class with a 'class' line")
            invalid = True
        if keyword and keyword.group(1) in ("style", "linkStyle"):
            doc.add(line_no, "MMD", f"'{keyword.group(1)}' is not allowed; only palette classes add color, and edges keep the viewer theme")
            invalid = True
            continue
        if keyword and not flowchart:
            doc.add(line_no, "MMD", "only a 'graph TD' diagram takes classes; a sequence diagram uses owner bands")
            invalid = True
            continue
        if keyword and keyword.group(1) == "classDef":
            m = re.match(r"^classDef\s+(\w+)\s+(\S+)$", s)
            name = m.group(1) if m else ""
            declared.add(name)
            if name not in CLASS_STYLES:
                doc.add(line_no, "MMD", f"classDef must be one of the palette classes {', '.join(CLASS_STYLES)}: '{s[:50]}'")
                invalid = True
            elif m.group(2) != CLASS_STYLES[name]:
                doc.add(line_no, "MMD", f"classDef {name} must be exactly '{CLASS_STYLES[name]}', with nothing after it")
                invalid = True
            else:
                defined.add(name)
            continue
        if keyword:
            m = re.match(r"^class\s+(\w+(?:,\w+)*)\s+(\w+)$", s)
            if not m:
                doc.add(line_no, "MMD", f"class line must be 'class id,id name', with no space after a comma and no ';': '{s[:50]}'")
                invalid = True
                continue
            for ident in m.group(1).split(","):
                assigned.setdefault(ident, []).append(m.group(2))
            continue
        if not flowchart:
            continue
        sub = SUBGRAPH_RX.match(s)
        if sub:
            boundaries.add(sub.group(1))
            continue
        for ident, _, label, _ in quoted_nodes(s):
            tm = TYPED_LABEL_RX.match(label)
            types[ident] = tm.group(2).strip() if tm else ""
        blanked = QUOTED_RX.sub('""', s)
        if link_problems(blanked, s) or PROPERTY_SYNTAX_RX.search(blanked):
            skipped = True
            continue
        for em in EDGE_RX.finditer(strip_node_defs(s)):
            types.setdefault(em.group(1), "")
            types.setdefault(em.group(6), "")
    for ident in boundaries:
        types.pop(ident, None)
    used = {name for names in assigned.values() for name in names}
    for name in sorted(defined - used):
        doc.add(line_no, "MMD", f"classDef {name} is never assigned; drop it or add a 'class' line")
    for name in sorted(used - declared):
        doc.add(line_no, "MMD", f"class '{name}' has no palette classDef in this diagram")
    for ident, names in assigned.items():
        if len(names) > 1:
            doc.add(line_no, "MMD", f"'{ident}' takes one class, found {', '.join(names)}")
        elif ident in boundaries:
            if names[0] != "boundary":
                doc.add(line_no, "MMD", f"boundary '{ident}' takes the boundary class; a tinted frame blends into the tinted nodes inside it")
        elif ident not in types and not skipped:
            doc.add(line_no, "MMD", f"class line names '{ident}', which is not a node")
        elif names[0] == "boundary":
            doc.add(line_no, "MMD", f"'{ident}': the boundary class marks subgraphs only; give the node its owner's class")
        elif names[0] != FUTURE_CLASS:
            for cls, typ in TYPE_CLASSES.items():
                if (names[0] == cls) != (types.get(ident) == typ):
                    doc.add(line_no, "MMD", f"'{ident}': the {cls} class marks every [{typ}] node and nothing else")
                    break
    missing = [ident for ident in [*types, *sorted(boundaries)] if ident not in assigned]
    if missing and not invalid:
        doc.add(line_no, "MMD", f"color every node with its owner's class and every boundary with 'boundary'; uncolored: {', '.join(missing)}")
    return used & declared


def check_flowchart(doc: Doc, line_no: int, body: list[str], family: str, stacked: dict[str, str]) -> tuple[list[str], list[tuple[str, str, str]], list[str], list[tuple[tuple[str, str], str]]]:
    """Check a 'graph TD' body; return its node titles, edges, boundary titles, and each linked (kind, title)'s target."""
    nodes: dict[str, str] = {}
    edges: list[tuple[str, str]] = []
    boundaries: dict[str, str] = {}
    links: list[tuple[tuple[str, str], str]] = []
    node_types: dict[str, str] = {}
    frames = {m.group(1) for l in body if (m := SUBGRAPH_RX.match(l.strip()))}
    future = {ident for l in body if (m := FUTURE_CLASS_RX.match(l.strip())) for ident in m.group(1).split(",")} - frames
    opened: str | None = None
    any_malformed = False
    for l in body:
        s = l.strip()
        if opened is not None and not s.startswith("direction"):
            doc.add(line_no, "MMD", f"boundary '{opened}' must declare 'direction TB' on its first line")
        was_opened, opened = opened, None
        if s.startswith("subgraph"):
            subgraph_match = re.match(r'^subgraph\s+(\w+)\["([^"]+)"\]$', s)
            if not subgraph_match:
                doc.add(line_no, "MMD", f"subgraph needs an id and a quoted label: '{s}'")
                continue
            ident, opened = subgraph_match.groups()
            label = opened
            bm = TYPED_LABEL_RX.match(label)
            if not bm:
                doc.add(line_no, "MMD", f"boundary title is 'Title<br/>[TYPE]', its type on the second line: '{label[:50]}'")
                continue
            title, href = linked_title(doc, line_no, bm.group(1))
            opened = title
            typ = bm.group(2).strip()
            if not BOUNDARY_TITLE_RX.match(title):
                doc.add(line_no, "MMD", f"boundary title is a plain name above its [TYPE]: '{label[:50]}'")
                continue
            if typ not in BOUNDARY_TYPES:
                doc.add(line_no, "MMD", f"unknown boundary TYPE '{typ}' in '{title}'")
            if title.lower().endswith(FUTURE_SUFFIX.lower()):
                doc.add(line_no, "MMD", f"boundary '{title}': a frame is never a future part; mark the nodes inside it")
            check_title_words(doc, line_no, "boundary", title, typ)
            visible = f"{title} {LINK_ICON}" if href else title
            if len(visible) > BOUNDARY_TITLE_MAX:
                doc.add(line_no, "MMD", f"boundary title '{visible}' exceeds {BOUNDARY_TITLE_MAX} characters; a longer title wraps behind the first node")
            boundaries[ident] = named(title, typ)
            if href:
                links.append((("boundary", boundaries[ident]), href))
            continue
        if s in ("end",) or s.startswith("direction"):
            if s.startswith("direction") and (s != "direction TB" or was_opened is None):
                doc.add(line_no, "MMD", "the only direction line allowed is 'direction TB' on the first line of a boundary")
            continue
        blanked = QUOTED_RX.sub('""', s)
        problems = link_problems(blanked, s)
        for problem in problems:
            doc.add(line_no, "MMD", problem)
        property_syntax = PROPERTY_SYNTAX_RX.search(blanked)
        if property_syntax:
            doc.add(line_no, "MMD", f"'@' ids and properties are not portable; the one exception is a stacked node, 'id@{{ shape: st-rect, label: \"...\" }}' or 'docs': '{s[:50]}'")
        malformed = bool(problems or property_syntax)
        any_malformed = any_malformed or malformed
        for ident, opening, label, end in quoted_nodes(s):
            shape_ok = opening in SHAPES and s[end:].lstrip().startswith(SHAPES[opening])
            lm = TYPED_LABEL_RX.match(label)
            if not shape_ok:
                doc.add(line_no, "MMD", SHAPE_MESSAGE.format(lm.group(1).strip() if lm else label))
            if not lm:
                doc.add(line_no, "MMD", f"node label must be 'Title<br/>[TYPE]': '{label}'")
                nodes[ident] = label
                continue
            title, href = linked_title(doc, line_no, lm.group(1).strip())
            typ = lm.group(2).strip()
            marked = title.lower().endswith(FUTURE_SUFFIX.lower())
            if marked and not title.endswith(FUTURE_SUFFIX):
                doc.add(line_no, "MMD", f"node '{title}': write the suffix as '{FUTURE_SUFFIX.strip()}'")
            if marked != (ident in future):
                doc.add(line_no, "MMD", f"node '{title}': a title ends in '{FUTURE_SUFFIX.strip()}' exactly when the node takes the {FUTURE_CLASS} class")
            # The suffix marks the state, not the thing, so the title rules and the
            # cross-file identity judge the words before it.
            title = title[: -len(FUTURE_SUFFIX)] if marked else title
            name = named(title, typ)
            if href:
                links.append((("node", name), href))
            if typ not in MERMAID_TYPES:
                doc.add(line_no, "MMD", unknown_type(typ, "node", title))
            if shape_ok and typ in MERMAID_TYPES:
                want = TYPE_SHAPES.get(typ, RECTANGLE)
                stack = "docs" if want == CYLINDER else "st-rect"
                if ident in stacked and stacked[ident] != stack:
                    doc.add(line_no, "MMD", f"stacked node '{title}' is {typ}; stack it as '{stack}'")
                elif ident not in stacked and opening != want[0]:
                    doc.add(line_no, "MMD", f"node '{title}' is {typ}; draw it as '{want[0]}\"...\"{want[1]}'")
            if family == "infrastructure" and typ in {"SYSTEM", "SERVICE", "DATA"}:
                doc.add(line_no, "MMD", f"infrastructure node '{title}' uses generic TYPE '{typ}'; name the platform service")
            if re.match(r"^\d+[a-z]?[.:]\s", title):
                doc.add(line_no, "MMD", f"node title carries a number: '{title}'; numbers belong on edges")
            if typ == "DECISION":
                if not title.endswith("?") or len(title.split()) > 3:
                    doc.add(line_no, "MMD", f"DECISION '{title}' must be a question of three words or fewer, ending in '?'")
            elif len(title.split()) > 4:
                doc.add(line_no, "MMD", f"node title longer than three or four words: '{title}'")
            check_title_words(doc, line_no, "node", title, typ)
            if ident not in stacked and is_plural(title):
                doc.add(line_no, "MMD", f"node '{title}' names several things; stack it as 'id@{{ shape: st-rect, label: \"...\" }}', or 'docs' for a cylinder TYPE")
            nodes[ident] = name
            node_types[ident] = typ
        stripped = "" if malformed else strip_node_defs(s)
        for em in EDGE_RX.finditer(stripped):
            src, dst = em.group(1), em.group(6)
            label = next((g for g in em.groups()[1:5] if g is not None), None)
            edges.append((src, dst))
            dotted = em.group(0)[len(src):].lstrip().startswith("-.")
            if (src in future or dst in future) != (dotted and bool(future)):
                doc.add(line_no, "MMD", f"edge {src} -> {dst}: in a diagram with a future node, an edge is dotted exactly when it touches one")
            for end in (src, dst):
                if end in boundaries:
                    doc.add(line_no, "MMD", f"edge {src} -> {dst} links boundary '{boundaries[end]}'; link the nodes inside it, since Azure DevOps rejects subgraph links")
            if label is None:
                doc.add(line_no, "MMD", f"edge {src} -> {dst} has no label")
            else:
                words = STEP_RX.sub("", label).split()
                if len(words) > 4:
                    doc.add(line_no, "MMD", f"edge label longer than four words: '{label}'")
    count = len(nodes)
    # A malformed line drops its edges, and an '@' node other than a stacked one is never counted, so a small or split graph here would be a follow-on finding.
    if count < 4 and not any_malformed:
        doc.add(line_no, "MMD", f"only {count} nodes; write a sentence instead of a diagram")
    if count > 12:
        doc.add(line_no, "MMD", f"{count} nodes exceeds the cap of 12; split the diagram")
    if not any_malformed:
        sources = {a for a, _ in edges}
        for ident, typ in node_types.items():
            if typ == "TOOL" and ident not in sources:
                doc.add(line_no, "MMD", f"node '{nodes[ident]}' ends the flow; point it to the node or person that gets its result")
    if nodes and edges and not any_malformed:
        adj: dict[str, set[str]] = {n: set() for n in nodes}
        for a, c in edges:
            adj.setdefault(a, set()).add(c)
            adj.setdefault(c, set()).add(a)
        seen: set[str] = set()
        stack = [next(iter(nodes))]
        while stack:
            n = stack.pop()
            if n in seen:
                continue
            seen.add(n)
            stack.extend(adj.get(n, ()))
        if not set(nodes) <= seen:
            doc.add(line_no, "MMD", "diagram holds more than one disconnected graph; split it")
    return list(nodes.values()), [(nodes.get(a, a), nodes.get(c, c), "") for a, c in edges], list(boundaries.values()), links


def check_er_diagram(doc: Doc, line_no: int, body: list[str]) -> tuple[list[str], list[tuple[str, str, str]]]:
    entities: list[str] = []
    edges: list[tuple[str, str, str]] = []
    for line in body:
        stripped = line.strip()
        entity_match = re.match(r"^(\w+)\s*\{$", stripped)
        if entity_match:
            entities.append(entity_match.group(1))
            continue
        relationship = re.match(r'^(\w+)\s+[|o}{.]+--[|o}{.]+\s+(\w+)\s*:\s*"[^"]+"$', stripped)
        if relationship:
            # An entity named only in a relationship still draws as a box.
            entities.extend(relationship.groups())
            a, c = sorted(relationship.groups())
            edges.append((a, c, ""))
        if stripped.startswith("subgraph"):
            doc.add(line_no, "MMD", "ER diagrams do not use boundaries; state ownership in prose")
    unique_entities = list(dict.fromkeys(entities))
    if len(unique_entities) < 2:
        doc.add(line_no, "MMD", "an ER diagram needs at least two entities")
    if len(unique_entities) > 8:
        doc.add(line_no, "MMD", f"{len(unique_entities)} entities exceeds the cap of 8; split by aggregate")
    if not edges:
        doc.add(line_no, "MMD", "an ER diagram needs at least one labelled relationship")
    return unique_entities, edges


def check_sequence(doc: Doc, line_no: int, body: list[str]) -> tuple[list[str], list[tuple[str, str, str]]]:
    titles: list[str] = []
    idents: dict[str, str] = {}
    edges: list[tuple[str, str, str]] = []
    messages = 0
    in_band = False
    band: str | None = None
    for l in body:
        s = l.strip()
        if re.match(r"box\b", s):
            if in_band:
                doc.add(line_no, "MMD", "close a band with 'end' before opening the next; bands do not nest")
            bm = re.match(r"^box\s+(rgba\([^)]*\))\s+(\S.*)$", s)
            band = BAND_OWNERS.get(bm.group(1)) if bm else None
            if not bm:
                doc.add(line_no, "MMD", f"band must be 'box <palette rgba> <owner name>': '{s[:50]}'")
            elif band is None:
                doc.add(line_no, "MMD", f"band color must be an owner palette color, one of {', '.join(BAND_OWNERS)}: '{bm.group(1)}'")
            in_band = True
            continue
        if in_band and s == "end":
            in_band, band = False, None
            continue
        cm = re.match(r"create\s+(?:participant|actor)\s+(\w+)", s)
        if cm:
            doc.add(line_no, "MMD", f"'create' places '{cm.group(1)}' outside every owner band; declare it up front in its band")
            idents[cm.group(1)] = cm.group(1)
            continue
        pm = re.match(r"^(actor|participant)\s+(\w+)(?:\s+as\s+(.+))?$", s)
        if in_band and not pm:
            doc.add(line_no, "MMD", f"a band holds participant lines only; close it with 'end' first: '{s[:40]}'")
            continue
        if pm:
            kw, ident, label = pm.groups()
            label = label or ident
            if not in_band:
                doc.add(line_no, "MMD", f"participant '{ident}' sits outside an owner band; wrap it in 'box <palette rgba> <owner name>' ... 'end'")
            lm = TYPED_LABEL_RX.match(label)
            if not lm:
                doc.add(line_no, "MMD", f"participant label must be 'Title<br/>[TYPE]': '{label}'")
                titles.append(label)
                idents[ident] = label
                continue
            title, typ = lm.group(1).strip(), lm.group(2).strip()
            if typ not in MERMAID_TYPES:
                doc.add(line_no, "MMD", unknown_type(typ, "participant", title))
            if re.match(r"^\d+[.:]\s", title):
                doc.add(line_no, "MMD", f"participant carries an ordinal prefix: '{title}'; number messages, not participants")
            check_title_words(doc, line_no, "participant", title, typ)
            if kw == "actor":
                doc.add(line_no, "MMD", f"'{title}': use 'participant' for every TYPE; an actor figure collides with its two-line label")
            if in_band and band and (band == "person") != (typ == TYPE_CLASSES["person"]):
                doc.add(line_no, "MMD", f"'{title}': the person band holds every [PERSON] participant and nothing else")
            idents[ident] = named(title, typ)
            titles.append(idents[ident])
            continue
        if re.match(r"^links?\s+\w+\s*:", s):
            doc.add(line_no, "MMD", "the 'link' directive is not allowed; list the participant's source on the Sources line")
            continue
        mm = re.match(r"^(\w+)\s*(?:-{1,2}>>?|-{1,2}x|-{1,2}\))\s*(\w+)\s*:\s*(.*)$", s)
        if mm:
            messages += 1
            src, dst, text = mm.groups()
            for ident in dict.fromkeys((src, dst)):
                if ident not in idents:
                    doc.add(line_no, "MMD", f"'{ident}' is not a declared participant; declare it inside its owner's band")
                    idents[ident] = ident
            if not STEP_RX.match(text):
                doc.add(line_no, "MMD", f"sequence message is not numbered '1: text': '{text[:40]}'")
            action = re.sub(r"^\d+[a-z]?[.:]\s*", "", text).strip().lower()
            edges.append((idents[src], idents[dst], action))
        elif re.match(r"^\w+\s*-{3,}", s):
            doc.add(line_no, "MMD", f"long arrows are not portable; use '->>': '{s[:40]}'")
    if in_band:
        doc.add(line_no, "MMD", "a band is never closed; end it with 'end' after its last participant")
    if len(titles) > 7:
        doc.add(line_no, "MMD", f"{len(titles)} participants exceeds the cap of 7; split the flow")
    if messages > 12:
        doc.add(line_no, "MMD", f"{messages} messages exceeds the cap of 12; split the flow by phase")
    return titles, edges


def docs_parts(path: str) -> list[str] | None:
    """Return the path parts below the nearest enclosing docs/ folder, or None outside one.

    The nearest folder wins, so the answer holds whatever --root or working
    directory the lint runs from, and a repo checked out under a folder named
    docs still resolves its own docs/ tree.
    """
    folders = os.path.abspath(path).split(os.sep)[:-1]
    if "docs" not in folders:
        return None
    cut = len(folders) - folders[::-1].index("docs")
    return os.path.abspath(path).split(os.sep)[cut:]


def is_adr_file(path: str) -> bool:
    """Whether `path` is a numbered ADR inside an ADR directory."""
    folder, name = os.path.split(path)
    return os.path.basename(folder) in ADR_DIRS and bool(ADR_NAME_RX.match(name))


def is_adr_index(path: str) -> bool:
    """Whether `path` is the README that indexes an ADR directory."""
    parent = os.path.basename(os.path.dirname(os.path.abspath(path)))
    return os.path.basename(path).lower() == "readme.md" and parent in ADR_DIRS


def check_view(doc: Doc) -> None:
    # A viewpoint owner keeps its canonical name in any domain folder under docs/.
    if docs_parts(doc.path) is None:
        return
    name = os.path.basename(doc.path)
    owned = next((family for family, owner in VIEW_OWNERS.items() if owner == name), None)
    if owned is None:
        return
    for d in doc.diagrams:
        if d.family != owned:
            doc.add(d.line, "VIEW", f"{name} owns {owned} diagrams only; move this {d.family} diagram to {VIEW_OWNERS[d.family]} or a topic guide")


def check_adr_number(doc: Doc) -> None:
    # A shared number makes a bare "ADR NNNN" citation ambiguous, so every sibling ADR needs its own.
    # The folder is listed from disk, so a new ADR linted alone still meets an older twin.
    name = os.path.basename(doc.path)
    own = ADR_NAME_RX.match(name)
    if doc.doc_type != "adr" or own is None:
        return
    number = own.group(1)
    clashes = sorted(other for other in os.listdir(doc.folder)
                     if other != name and (m := ADR_NAME_RX.match(other)) and m.group(1) == number)
    if clashes:
        doc.add(1, "NUM", f"ADR number {number} is also used by {', '.join(clashes)}; give one of them the next free number")


def check_redrawn_edges(docs: list[Doc]) -> None:
    owner: dict[tuple[str, str, str, str], tuple[Doc, int]] = {}
    for doc in docs:
        for d in doc.diagrams:
            for src, dst, action in d.edges:
                key = (d.family, src, dst, action)
                first = owner.setdefault(key, (doc, d.line))
                if first[0] is not doc:
                    what = f"'{src}' to '{dst}'" + (f" ('{action}')" if action else "")
                    doc.add(d.line, "DUP", f"{d.family} relationship {what} is already drawn in {first[0].path}:{first[1]}; link to that diagram")


def check_node_identity(docs: list[Doc]) -> None:
    owner: dict[tuple[str, str], tuple[Doc, int, str]] = {}
    for doc in docs:
        for d in doc.diagrams:
            for (kind, title), source in d.sources.items():
                first = owner.setdefault((kind, title), (doc, d.line, source))
                if first[2] != source:
                    doc.add(d.line, "NODE", f"{kind} '{title}' maps to '{source or 'no link'}' here but to '{first[2] or 'no link'}' in {first[0].path}:{first[1]}; one title, one source")


STOPWORDS = set("""a an the and or but of to in on at by for with from as is are be was were
it its this that these those there here not any all each every than then so
into over under without within between must may can will should also only when where
which who whose what how""".split())
NEAR_MIN_WORDS = 8
NEAR_THRESHOLD = 0.4


def stem(word: str) -> str:
    for suffix in ("ing", "ed", "es", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            return word[: -len(suffix)]
    return word


def content_words(sentence: str) -> frozenset[str]:
    words = re.findall(r"[a-z0-9']+", link_text_only(strip_inline_code(sentence)).lower())
    return frozenset(stem(w) for w in words if w not in STOPWORDS and len(w) > 2)


def is_legend(b: Block) -> bool:
    return b.kind == "para" and b.lines[0].startswith(LEGEND_PREFIX)


def is_audience(b: Block) -> bool:
    return b.kind == "para" and b.lines[0].startswith(AUDIENCE_PREFIX)


def is_sources(b: Block) -> bool:
    return b.kind == "para" and b.lines[0].startswith(SOURCES_PREFIX)


def collect_sentences(doc: Doc, blocks: list[Block]) -> list[tuple[int, str, frozenset[str]]]:
    out: list[tuple[int, str, frozenset[str]]] = []
    for b in blocks:
        # A diagram's legend repeats the shared palette and line styles by design, so it is not a fact to deduplicate.
        if b.start in doc.captions:
            continue
        if b.kind == "para":
            units = [" ".join(l.strip() for l in b.lines)]
        elif b.kind == "list":
            units = []
            for l in b.lines:
                m = re.match(r"^\s*([-*+]|\d+\.)\s+(.*)", l)
                if m:
                    units.append(m.group(2))
                elif units:
                    units[-1] += " " + l.strip()
        else:
            continue
        for text in units:
            if text.startswith(AUDIENCE_PREFIX):
                continue
            for sent in sentences(text):
                words = content_words(sent)
                if len(words) >= NEAR_MIN_WORDS:
                    out.append((b.start + 1, sent, words))
    return out


def check_near_duplicates(docs: list[Doc], sentence_sets: dict[str, list[tuple[int, str, frozenset[str]]]]) -> None:
    reported: set[tuple[str, int, str]] = set()
    for i, a in enumerate(docs):
        for b in docs[i + 1:]:
            for la, sa, wa in sentence_sets[a.path]:
                for lb, sb, wb in sentence_sets[b.path]:
                    inter = len(wa & wb)
                    union = len(wa | wb)
                    if union and inter / union >= NEAR_THRESHOLD:
                        key = (b.path, lb, a.path)
                        if key in reported:
                            continue
                        reported.add(key)
                        b.add(lb, "DUP", f"sentence restates {a.path}:{la} ('{sa[:50]}...'); one home per fact")


def collect_shingles(doc: Doc, blocks: list[Block]) -> None:
    for b in blocks:
        if b.kind not in ("para", "list") or b.start in doc.captions:
            continue
        if is_audience(b):
            continue
        for j, raw in enumerate(b.lines):
            text = raw.strip()
            if b.kind == "list":
                text = re.sub(r"^\s*([-*+]|\d+\.)\s+", "", text)
            text = link_text_only(strip_inline_code(text))
            words = re.findall(r"[a-z0-9']+", text.lower())
            for k in range(0, len(words) - DUP_WINDOW + 1):
                doc.prose_shingles.setdefault(" ".join(words[k:k + DUP_WINDOW]), b.start + j + 1)


def check_duplicates(docs: list[Doc]) -> None:
    owner: dict[str, tuple[Doc, int]] = {}
    reported: set[tuple[str, str]] = set()
    for d in docs:
        for sh, ln in d.prose_shingles.items():
            if sh in owner and owner[sh][0] is not d:
                pair = (owner[sh][0].path, d.path)
                if pair in reported:
                    continue
                reported.add(pair)
                d.add(ln, "DUP", f"12-word run also appears in {owner[sh][0].path}:{owner[sh][1]}; one home per fact")
            else:
                owner.setdefault(sh, (d, ln))


def guess_type(path: str, root: str) -> str | None:
    p = os.path.abspath(path)
    rel = os.path.relpath(p, root).replace(os.sep, "/")
    name = os.path.basename(p)
    parent = os.path.basename(os.path.dirname(p))
    if ADR_NAME_RX.match(name) and parent in ADR_DIRS:
        return "adr"
    under_docs = docs_parts(p)
    if name.lower() == "readme.md":
        # docs/README.md routes to the domains, and each docs/<domain>/README.md to its guides.
        if under_docs is not None and len(under_docs) <= 2:
            return "index"
        d = os.path.dirname(p)
        markers = ("package.json", "pyproject.toml", "run.sh", ".git", "Cargo.toml", "go.mod")
        if any(os.path.exists(os.path.join(d, m)) for m in markers) or rel == "README.md":
            return "readme-project"
        return "readme-folder"
    if under_docs == [name]:
        if name == "glossary.md":
            return "glossary"
        if name.startswith("requirements"):
            return "requirements"
    return None


def expand_scope(paths: list[str]) -> list[str]:
    out: list[str] = []
    for p in paths:
        if os.path.isfile(p):
            out.append(p)
            continue
        for folder, dirs, files in os.walk(p):
            dirs[:] = sorted(d for d in dirs if not d.startswith(".") and d != "node_modules")
            out.extend(os.path.join(folder, f) for f in sorted(files) if f.endswith(".md"))
    return out


SENTENCE_SETS: dict[str, list[tuple[int, str, frozenset[str]]]] = {}


def adr_status(lines: list[str]) -> str | None:
    """Return the ADR's status word from a status table, a 'Status:' line, or a Status section."""
    for i, line in enumerate(lines):
        if re.match(r"^\|\s*status\s*\|", line, re.I):
            candidates = lines[i + 2:i + 3]
        elif STATUS_LINE_RX.match(line):
            candidates = [line.split(":", 1)[1]]
        elif re.match(r"^#{2,6}\s+status\s*$", line, re.I):
            rest = lines[i + 1:]
            stop = next((n for n, text in enumerate(rest) if heading_level(text)), len(rest))
            candidates = rest[:stop]
        else:
            continue
        for text in candidates:
            found = STATUS_WORD_RX.search(text)
            if found:
                return found.group(1).lower()
        return None
    return None


def lint_file(path: str, root: str, forced: str | None, heading_cache: dict[str, dict[str, str]]) -> Doc:
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    doc = Doc(path, lines)
    blocks = segment(lines)
    check_header(doc, blocks, forced)
    if doc.doc_type is None:
        doc.doc_type = guess_type(path, root)
    doc.settled = doc.doc_type == "adr" and adr_status(lines) in SETTLED_STATUSES
    check_title(doc, blocks)
    check_headings(doc, blocks)
    check_toc(doc, blocks)
    check_cap(doc, blocks)
    check_fences(doc, blocks)
    check_density(doc, blocks)
    check_words(doc, blocks)
    check_bloat(doc, blocks)
    check_unboxed_sources(doc, blocks)
    check_emoji(doc, blocks)
    check_links(doc, blocks, root, heading_cache)
    check_mermaid(doc, blocks, root, heading_cache)
    check_view(doc)
    check_adr_number(doc)
    collect_shingles(doc, blocks)
    SENTENCE_SETS[path] = collect_sentences(doc, blocks)
    return doc


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Lint Markdown docs against the docsmith house style.")
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--type", choices=sorted(TYPES), help="force the document type instead of reading the header")
    ap.add_argument("--root", default=os.getcwd(), help="repo root used to guess types and report paths")
    ap.add_argument("--no-dup", action="store_true", help="skip the cross-file duplicate check")
    ap.add_argument("--dup-scope", nargs="+", action="extend", default=[], metavar="PATH",
                    help="files or directories that join the cross-file checks but report no findings of their own")
    args = ap.parse_args(argv)
    root = os.path.abspath(args.root)
    docs: list[Doc] = []
    cache: dict[str, dict[str, str]] = {}
    for p in args.paths:
        if not os.path.isfile(p):
            print(f"{p}:0: FILE not found", file=sys.stderr)
            return 2
        if os.path.basename(p) not in AGENT_FILES:
            docs.append(lint_file(p, root, args.type, cache))
    primary = {os.path.abspath(d.path) for d in docs}
    scope = [lint_file(p, root, None, cache) for p in expand_scope(args.dup_scope)
             if os.path.abspath(p) not in primary and os.path.basename(p) not in AGENT_FILES]
    # Scope files go first so they own a shared fact and the finding lands on the file being linted.
    # A settled ADR cannot be reworded, so it owns a shared fact ahead of every editable file.
    everyone = scope + sorted(docs, key=lambda d: not d.settled)
    if len(everyone) > 1 and not args.no_dup:
        check_duplicates(everyone)
        check_near_duplicates(everyone, SENTENCE_SETS)
        check_redrawn_edges(everyone)
        check_node_identity(everyone)
    total = 0
    for d in docs:
        for f in sorted(d.findings, key=lambda x: (x.line, x.code)):
            if (d.settled and f.code not in SETTLED_ADR_CODES) or f.code in TYPE_SKIPS.get(d.doc_type or "", ()):
                continue
            print(f)
            total += 1
    print(f"{total} finding(s) in {len(docs)} file(s)")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
