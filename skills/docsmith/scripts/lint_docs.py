#!/usr/bin/env python3
"""Static linter for documents written by the docsmith skill.

Purpose: enforce the rules in references/style.md and references/mermaid.md
mechanically so verification does not rely on reading alone.
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
    "readme-project": 150,
    "readme-folder": 80,
    "how-to": 200,
    "explanation": 200,
    "reference": 300,
    "requirements": 300,
    "index": 120,
    "adr": 80,
    "glossary": None,
}
GUIDE_TYPES = {"how-to", "reference", "explanation", "index", "requirements"}
APPLICATION_MERMAID_TYPES = {
    "PERSON", "TEAM", "UI", "API", "AGENT", "TOOL", "SERVICE", "SYSTEM", "DATA", "DATABASE",
}
INFRASTRUCTURE_MERMAID_TYPES = {
    "GCP PROJECT", "VPC", "PRIVATE SERVICE CONNECT", "EXTERNAL LOAD BALANCER",
    "CLOUD RUN", "CLOUD RUN JOB", "CLOUD SQL", "SECRET MANAGER",
    "AZURE APP SERVICE", "AZURE FUNCTIONS", "AZURE SQL", "VIRTUAL NETWORK",
    "APPLICATION GATEWAY", "KEY VAULT", "KUBERNETES", "VM", "PHYSICAL SERVER",
    "POSTGRES", "FIREWALL", "LOAD BALANCER", "DNS", "OBJECT STORAGE",
    "MESSAGE BROKER", "CONTAINER REGISTRY",
}
MERMAID_TYPES = APPLICATION_MERMAID_TYPES | INFRASTRUCTURE_MERMAID_TYPES
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
# Mermaid wraps a boundary title at 200 pixels and hides the second line behind
# the first node. 24 characters stay on one line in every renderer font.
BOUNDARY_TITLE_MAX = 24

BANNED_WORDS = [
    "just", "simply", "easy", "easily", "trivial", "straightforward", "painless",
    "obviously", "of course", "delve", "leverage", "utilize", "seamless",
    "seamlessly", "robust", "comprehensive", "cutting-edge", "powerful",
    "innovative", "streamline", "empower", "crucially", "importantly", "notably",
    "essentially", "basically", "actually", "in order to", "note that",
    "it should be noted", "please note", "it's worth noting", "in today's",
]
META_PHRASES = [
    r"this (section|document|guide|file|readme) (used to|previously|formerly|once)",
    r"what was (one|a) \d+-node",
    r"replaces? what was",
    r"kept for link stability",
    r"this corpus now calls",
    r"became (two|three|four|five) diagrams",
    r"used to carry",
]
SMALL_WORDS = {
    "a", "an", "the", "and", "but", "or", "nor", "for", "so", "yet", "at", "by",
    "from", "in", "into", "of", "on", "onto", "to", "with", "via", "as", "per",
    "versus", "vs", "up", "down", "over", "under",
}

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
SETTLED_ADR_CODES = {"HDR", "TTL", "HCASE", "EMPTY", "TOC", "FENCE", "LINK"}
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
    sources: dict[str, str] = field(default_factory=dict)


@dataclass
class Doc:
    path: str
    lines: list[str]
    doc_type: str | None = None
    findings: list[Finding] = field(default_factory=list)
    prose_shingles: dict[str, int] = field(default_factory=dict)
    diagrams: list[Diagram] = field(default_factory=list)
    settled: bool = False

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
        if not nxt or nxt.kind != "para" or not nxt.lines[0].startswith("Audience:"):
            doc.add(h1s[0].start + 1, "TTL", "a guide puts one 'Audience:' line directly under the H1")


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


def check_cap(doc: Doc) -> None:
    if doc.doc_type is None:
        widest = max(c for c in TYPES.values() if c)
        if len(doc.lines) > widest:
            doc.add(widest + 1, "CAP", f"{len(doc.lines)} lines exceeds even the widest cap ({widest}); declare a Type and split by topic")
        return
    cap = TYPES.get(doc.doc_type)
    if cap and len(doc.lines) > cap:
        doc.add(cap + 1, "CAP", f"{len(doc.lines)} lines exceeds the {cap}-line cap for type '{doc.doc_type}'; split by topic")


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
            text = " ".join(l.strip() for l in b.lines)
            if b.lines[0].startswith("Audience:"):
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


def check_links(doc: Doc, blocks: list[Block], root: str, heading_cache: dict[str, list[str]]) -> None:
    base = os.path.dirname(os.path.abspath(doc.path))
    for b in blocks:
        if b.kind in ("fence", "html"):
            continue
        for j, raw in enumerate(b.lines):
            line_no = b.start + j + 1
            text = strip_inline_code(raw)
            for m in re.finditer(r"(?<!!)\[([^\]]*)\]\(([^)\s]+)\)", text):
                label, target = m.group(1), m.group(2)
                if label.strip().lower() in ("here", "click here", "link", "this"):
                    doc.add(line_no, "LINK", f"link text '{label}' says nothing; name the target")
                if re.match(r"https?://", target):
                    if re.search(r"github\.com/[^/]+/[^/]+/(blob|tree)/", target):
                        doc.add(line_no, "LINK", "absolute GitHub URL into a repo; use a relative path")
                    continue
                if target.startswith("mailto:"):
                    continue
                path_part, _, anchor = target.partition("#")
                path_part = urllib.parse.unquote(path_part)
                if path_part:
                    full = os.path.normpath(os.path.join(base, path_part))
                    if not os.path.exists(full):
                        doc.add(line_no, "LINK", f"relative link does not resolve: {target}")
                        continue
                else:
                    full = os.path.abspath(doc.path)
                if anchor:
                    if os.path.isdir(full):
                        doc.add(line_no, "LINK", f"anchor on a directory link: {target}")
                        continue
                    slugs = heading_cache.get(full)
                    if slugs is None:
                        try:
                            with open(full, encoding="utf-8") as fh:
                                slugs = collect_slugs(fh.read().splitlines())
                        except OSError:
                            slugs = []
                        heading_cache[full] = slugs
                    if anchor.lower() not in slugs:
                        doc.add(line_no, "LINK", f"anchor '#{anchor}' matches no heading in {os.path.relpath(full, root)}")
            for m in re.finditer(r"(?<![(<`\[])https?://\S+", text):
                doc.add(line_no, "LINK", f"bare URL '{m.group(0)[:40]}'; give it link text")


def collect_slugs(lines: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    out: list[str] = []
    in_fence = False
    for l in lines:
        if re.match(r"^\s*(`{3,}|~{3,})", l):
            in_fence = not in_fence
            continue
        if in_fence or not heading_level(l):
            continue
        s = slugify(re.sub(r"^#+\s+", "", l))
        if s in seen:
            seen[s] += 1
            s = f"{s}-{seen[s]}"
        else:
            seen[s] = 0
        out.append(s)
    return out


def split_frontmatter(body: list[str]) -> tuple[list[str] | None, list[str]]:
    if not body or body[0].strip() != "---":
        return None, body
    for k in range(1, len(body)):
        if body[k].strip() == "---":
            config = textwrap.dedent("\n".join(body[1:k])).splitlines()
            return [l.rstrip() for l in config], body[k + 1:]
    return [], body[1:]


def check_mermaid(doc: Doc, blocks: list[Block], root: str) -> None:
    for i, b in enumerate(blocks):
        if b.kind != "fence" or b.lang != "mermaid":
            continue
        line_no = b.start + 1
        raw = [l for l in b.lines[1:-1] if l.strip()]
        if any(l.strip().startswith("%%{") for l in raw):
            doc.add(line_no, "MMD", "init directives are not portable; a viewer that reads the first line as the diagram type rejects the block")
        body = [l for l in raw if not l.strip().startswith("%%")]
        config, body = split_frontmatter(body)
        if config is not None:
            doc.add(line_no, "MMD", "frontmatter is not portable; Azure DevOps reads the first line as the diagram type and reports 'Unsupported diagram type'")
        if not body:
            doc.add(line_no, "MMD", "empty diagram")
            continue
        head = body[0].strip()
        check_portable(doc, line_no, body)
        boundaries: list[str] = []
        if head == "graph TD":
            family = flowchart_family(body[1:])
            titles, edges, boundaries = check_flowchart(doc, line_no, body[1:], family)
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
            doc.add(line_no, "MMD", "click directives are not allowed; the Node table carries the links")
        before = [x for x in blocks[:i] if x.kind != "blank"]
        if not before or before[-1].kind != "para":
            doc.add(line_no, "MMD", "a diagram is preceded by one lead sentence")
        after = [x for x in blocks[i + 1:] if x.kind != "blank"]
        if after and after[0].kind == "list" and re.match(r"^\s*\d+\.", after[0].lines[0]):
            after = after[1:]
        if not after or after[0].kind != "table" or not re.match(r"^\|\s*Node\s*\|\s*Source\s*\|", after[0].lines[0]):
            doc.add(line_no, "MMD", "a diagram is followed by an optional numbered list and then a '| Node | Source |' table")
            doc.diagrams.append(Diagram(line_no, family, titles, edges))
            continue
        sources: dict[str, str] = {}
        boundary_rows: dict[str, str] = {}
        for r in after[0].lines[2:]:
            cells = [c.strip() for c in r.strip().strip("|").split("|")]
            if not cells or not cells[0]:
                continue
            name = re.sub(r"`", "", cells[0])
            row = BOUNDARY_ROW_RX.match(name)
            if row and row.group(1) in boundaries:
                boundary_rows[row.group(1)] = row.group(2)
                continue
            sources[name] = resolve_source(doc, cells[1] if len(cells) > 1 else "", root)
        for name in boundaries:
            if name not in boundary_rows:
                doc.add(after[0].start + 1, "MMD", f"boundary '{name}' needs a '{name} [TYPE]' row in the Node table")
            elif boundary_rows[name] not in BOUNDARY_TYPES:
                doc.add(after[0].start + 1, "MMD", f"unknown boundary TYPE '{boundary_rows[name]}' in '{name}'")
        for t in titles:
            if t not in sources:
                doc.add(after[0].start + 1, "MMD", f"node '{t}' is missing from the Node table")
        doc.diagrams.append(Diagram(line_no, family, titles, edges, sources))


def resolve_source(doc: Doc, cell: str, root: str) -> str:
    """Normalize a Source cell so the same target compares equal from any folder."""
    m = re.search(r"\]\(([^)\s]+)\)", cell)
    if not m:
        return cell
    target = m.group(1).split("#")[0]
    if re.match(r"^[a-z][a-z0-9+.-]*:", target):
        return target
    full = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(doc.path)), urllib.parse.unquote(target)))
    return os.path.relpath(full, root).replace(os.sep, "/")


NODE_RX = re.compile(r'(\w+)\s*(\[\(|\[/|\[|\(\(|\(|\{)\s*"([^"]*)"')
NODE_DEF_RX = re.compile(r'(\w+)\s*(?:\[\(|\[/|\[|\(\(|\(|\{)\s*"[^"]*"\s*(?:\)\]|/\]|\]|\)\)|\)|\})')
ARROW = r'(?:(?:-->|==>|-\.->|---)\s*(?:\|\s*"([^"]*)"\s*\|)?|-\.\s*"([^"]*)"\s*\.->|--\s*"([^"]*)"\s*-->|==\s*"([^"]*)"\s*==>)'
EDGE_RX = re.compile(r'(\w+)\s*' + ARROW + r'\s*(?=(\w+))')
BOUNDARY_TITLE_RX = re.compile(r"^[^<>\[\]]+$")
BOUNDARY_ROW_RX = re.compile(r"^(.+?) \[([A-Z ]+)\]$")
HTML_TAG_RX = re.compile(r"<(?!br/>)/?[a-zA-Z][^>]*>")
# A label that opens like a Markdown block. Mermaid 11 parses labels as
# Markdown, and several releases draw 'Unsupported markdown: list' instead.
MARKDOWN_LABEL_RX = re.compile(r"^\s*(?:\d+[.)]|[-*+>]|#{1,6})\s")
STEP_RX = re.compile(r"^\d+[a-z]?:\s")


def check_portable(doc: Doc, line_no: int, body: list[str]) -> None:
    """Syntax that one common viewer rejects, whatever the newest Mermaid accepts."""
    for l in body:
        s = l.strip()
        tag = HTML_TAG_RX.search(s)
        if tag:
            doc.add(line_no, "MMD", f"'{tag.group(0)[:30]}' is not portable; '<br/>' is the only HTML a label may hold")
        if "`" in s:
            doc.add(line_no, "MMD", f"Markdown string labels are not portable: '{s[:40]}'")
        if re.search(r"-{4,}>|={4,}>|-\.{2,}->", s):
            doc.add(line_no, "MMD", f"long arrows are not portable; use '-->': '{s[:40]}'")
        labels = re.findall(r'"([^"]*)"', s)
        message = re.match(r"^\w+\s*-{1,2}(?:>>?|x|\))\s*\w+\s*:\s*(.*)$", s)
        if message:
            labels.append(message.group(1))
        for label in labels:
            if MARKDOWN_LABEL_RX.match(label):
                doc.add(line_no, "MMD", f"label opens like a Markdown list or heading: '{label[:40]}'; write step numbers as '1: text'")


def flowchart_family(body: list[str]) -> str:
    for line in body:
        for match in NODE_RX.finditer(line):
            label = match.group(3)
            label_match = re.match(r"^.+<br/>\[([A-Z, ]+)\]$", label)
            if label_match and label_match.group(1).strip() in INFRASTRUCTURE_MERMAID_TYPES:
                return "infrastructure"
    return "application"


def check_flowchart(doc: Doc, line_no: int, body: list[str], family: str) -> tuple[list[str], list[tuple[str, str, str]], list[str]]:
    nodes: dict[str, str] = {}
    edges: list[tuple[str, str]] = []
    boundaries: dict[str, str] = {}
    opened: str | None = None
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
            if not BOUNDARY_TITLE_RX.match(opened):
                doc.add(line_no, "MMD", f"boundary title is the plain name on one line; its [TYPE] goes in the Node table: '{opened[:50]}'")
                continue
            if len(opened) > BOUNDARY_TITLE_MAX:
                doc.add(line_no, "MMD", f"boundary title '{opened}' exceeds {BOUNDARY_TITLE_MAX} characters; a longer title wraps behind the first node")
            boundaries[ident] = opened
            continue
        if s in ("end",) or s.startswith("direction"):
            if s.startswith("direction") and (s != "direction TB" or was_opened is None):
                doc.add(line_no, "MMD", "the only direction line allowed is 'direction TB' on the first line of a boundary")
            continue
        for m in NODE_RX.finditer(s):
            ident, label = m.group(1), m.group(3)
            lm = re.match(r"^(.+)<br/>\[([A-Z, ]+)\]$", label)
            if not lm:
                doc.add(line_no, "MMD", f"node label must be 'Title<br/>[TYPE]': '{label}'")
                nodes[ident] = label
                continue
            title, typ = lm.group(1).strip(), lm.group(2).strip()
            if typ not in MERMAID_TYPES:
                doc.add(line_no, "MMD", f"unknown TYPE '{typ}' in node '{title}'")
            if family == "infrastructure" and typ in {"SYSTEM", "SERVICE", "DATABASE"}:
                doc.add(line_no, "MMD", f"infrastructure node '{title}' uses generic TYPE '{typ}'; name the platform service")
            if re.match(r"^\d+[a-z]?[.:]\s", title):
                doc.add(line_no, "MMD", f"node title carries a number: '{title}'; numbers belong on edges")
            if len(title.split()) > 4:
                doc.add(line_no, "MMD", f"node title longer than three or four words: '{title}'")
            nodes[ident] = title
        stripped = NODE_DEF_RX.sub(r"\1", s)
        for em in EDGE_RX.finditer(stripped):
            src, dst = em.group(1), em.group(6)
            label = next((g for g in em.groups()[1:5] if g is not None), None)
            edges.append((src, dst))
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
    if count < 4:
        doc.add(line_no, "MMD", f"only {count} nodes; write a sentence instead of a diagram")
    if count > 12:
        doc.add(line_no, "MMD", f"{count} nodes exceeds the cap of 12; split the diagram")
    if nodes and edges:
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
    return list(nodes.values()), [(nodes.get(a, a), nodes.get(c, c), "") for a, c in edges], list(boundaries.values())


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
            a, c = sorted(relationship.groups())
            edges.append((a, c, ""))
        if stripped.startswith("subgraph"):
            doc.add(line_no, "MMD", "ER diagrams do not use boundaries; state ownership in prose and the source table")
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
    for l in body:
        s = l.strip()
        pm = re.match(r"^(actor|participant)\s+(\w+)(?:\s+as\s+(.+))?$", s)
        if pm:
            kw, ident, label = pm.groups()
            label = label or ident
            lm = re.match(r"^(.+)<br/>\[([A-Z, ]+)\]$", label)
            if not lm:
                doc.add(line_no, "MMD", f"participant label must be 'Title<br/>[TYPE]': '{label}'")
                titles.append(label)
                idents[ident] = label
                continue
            title, typ = lm.group(1).strip(), lm.group(2).strip()
            if typ not in MERMAID_TYPES:
                doc.add(line_no, "MMD", f"unknown TYPE '{typ}' in participant '{title}'")
            if re.match(r"^\d+[.:]\s", title):
                doc.add(line_no, "MMD", f"participant carries an ordinal prefix: '{title}'; number messages, not participants")
            if kw == "actor":
                doc.add(line_no, "MMD", f"'{title}': use 'participant' for every TYPE; an actor figure collides with its two-line label")
            titles.append(title)
            idents[ident] = title
            continue
        mm = re.match(r"^(\w+)\s*(?:-{1,2}>>?|-{1,2}x|-{1,2}\))\s*(\w+)\s*:\s*(.*)$", s)
        if mm:
            messages += 1
            src, dst, text = mm.groups()
            if not STEP_RX.match(text):
                doc.add(line_no, "MMD", f"sequence message is not numbered '1: text': '{text[:40]}'")
            action = re.sub(r"^\d+[a-z]?[.:]\s*", "", text).strip().lower()
            edges.append((idents.get(src, src), idents.get(dst, dst), action))
    if len(titles) > 7:
        doc.add(line_no, "MMD", f"{len(titles)} participants exceeds the cap of 7; split the flow")
    if messages > 12:
        doc.add(line_no, "MMD", f"{messages} messages exceeds the cap of 12; split the flow by phase")
    return titles, edges


def check_view(doc: Doc) -> None:
    p = os.path.abspath(doc.path)
    if os.path.basename(os.path.dirname(p)) != "docs":
        return
    name = os.path.basename(p)
    owned = next((family for family, owner in VIEW_OWNERS.items() if owner == name), None)
    if owned is None:
        return
    for d in doc.diagrams:
        if d.family != owned:
            doc.add(d.line, "VIEW", f"{name} owns {owned} diagrams only; move this {d.family} diagram to {VIEW_OWNERS[d.family]} or a topic guide")


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
    owner: dict[str, tuple[Doc, int, str]] = {}
    for doc in docs:
        for d in doc.diagrams:
            for title, source in d.sources.items():
                first = owner.setdefault(title, (doc, d.line, source))
                if first[2] != source:
                    doc.add(d.line, "NODE", f"node '{title}' maps to '{source}' here but to '{first[2]}' in {first[0].path}:{first[1]}; one title, one source")


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


def collect_sentences(doc: Doc, blocks: list[Block]) -> list[tuple[int, str, frozenset[str]]]:
    out: list[tuple[int, str, frozenset[str]]] = []
    for b in blocks:
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
            if text.startswith("Audience:"):
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
                        b.add(lb, "DUP", f"sentence restates {a.path}:{la} ('{sa[:50]}...'); one fact, one home")


def collect_shingles(doc: Doc, blocks: list[Block]) -> None:
    for b in blocks:
        if b.kind not in ("para", "list"):
            continue
        for j, raw in enumerate(b.lines):
            text = raw.strip()
            if b.kind == "list":
                text = re.sub(r"^\s*([-*+]|\d+\.)\s+", "", text)
            if text.startswith("Audience:"):
                continue
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
                d.add(ln, "DUP", f"12-word run also appears in {owner[sh][0].path}:{owner[sh][1]}; one fact, one home")
            else:
                owner.setdefault(sh, (d, ln))


def guess_type(path: str, root: str) -> str | None:
    p = os.path.abspath(path)
    rel = os.path.relpath(p, root).replace(os.sep, "/")
    name = os.path.basename(p)
    parent = os.path.basename(os.path.dirname(p))
    if re.match(r"^\d{4}-.*\.md$", name) and parent in ("adrs", "adr", "decisions"):
        return "adr"
    if name.lower() == "readme.md":
        if parent == "docs":
            return "index"
        d = os.path.dirname(p)
        markers = ("package.json", "pyproject.toml", "run.sh", ".git", "Cargo.toml", "go.mod")
        if any(os.path.exists(os.path.join(d, m)) for m in markers) or rel == "README.md":
            return "readme-project"
        return "readme-folder"
    if parent == "docs":
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


def lint_file(path: str, root: str, forced: str | None, heading_cache: dict[str, list[str]]) -> Doc:
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
    check_cap(doc)
    check_fences(doc, blocks)
    check_density(doc, blocks)
    check_words(doc, blocks)
    check_links(doc, blocks, root, heading_cache)
    check_mermaid(doc, blocks, root)
    check_view(doc)
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
    cache: dict[str, list[str]] = {}
    for p in args.paths:
        if not os.path.isfile(p):
            print(f"{p}:0: FILE not found", file=sys.stderr)
            return 2
        docs.append(lint_file(p, root, args.type, cache))
    primary = {os.path.abspath(d.path) for d in docs}
    scope = [lint_file(p, root, None, cache) for p in expand_scope(args.dup_scope) if os.path.abspath(p) not in primary]
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
            if d.settled and f.code not in SETTLED_ADR_CODES:
                continue
            print(f)
            total += 1
    print(f"{total} finding(s) in {len(docs)} file(s)")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
