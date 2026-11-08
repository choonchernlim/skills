<!--
Purpose: The writing rules every document produced by docsmith must satisfy, with the lint code that enforces each.
Type: reference
-->

# Style Rules

> **Audience:** the writer, before drafting and again before handoff.

Every rule names the `lint_docs.py` code that checks it, or `[judgement]`
when it is reviewed by reading. A guide is any `how-to`, `reference`,
`explanation`, `index`, or `requirements` file.

## Table of Contents

- [Document Shape](#document-shape)
- [Density](#density)
- [Vocabulary](#vocabulary)
- [Meta-Commentary](#meta-commentary)
- [Bloat](#bloat)
- [One Home per Fact](#one-home-per-fact)
- [Links](#links)
- [Emoji Markers](#emoji-markers)
- [Line Caps](#line-caps)

## Document Shape

| Rule | Code |
| --- | --- |
| The file opens with a header comment: `Purpose:` line, `Type:` line, nothing else. | `HDR` |
| `Type` is one of `readme-project`, `readme-folder`, `how-to`, `reference`, `explanation`, `index`, `glossary`, `requirements`, `adr`. | `HDR` |
| One H1 follows the header. A README puts its one-line description directly under it. | `TTL` |
| A guide boxes its readers under the H1, as `> **Audience:** who and why`; each wrapped line keeps its `>`. | `TTL` |
| After a blank line, a plain paragraph says what a non-index guide covers and why, before any heading or table. | `INTRO` |
| A table of contents appears only past 100 lines or 5 H2 sections, and lists every H2. | `TOC` |
| Headings use Title Case. Code identifiers keep their own spelling. | `HCASE` |
| No heading is followed directly by another heading. | `EMPTY` |
| At most 10 H2 sections per file. | `H2N` |
| Every file stays under the line cap for its type (see [Line Caps](#line-caps)). | `CAP` |

Title Case (`HCASE`) capitalizes every word except articles, conjunctions, and short
prepositions: "Table of Contents", "Adding a Plugin", "How the Route
Finds the API". The first and last words are always capitalized.

## Density

| Rule | Code |
| --- | --- |
| A prose run is at most 6 consecutive lines. Break it with a list, table, or diagram. | `RUN` |
| A paragraph holds at most 4 sentences. | `PARA` |
| A sentence holds at most 30 words. Aim for 20. | `SENT` |
| A table cell holds at most 20 words. | `CELL` |
| A bullet holds at most 30 words. Explain with a sub-bullet, not a longer bullet. | `BUL` |
| A list holds at most 7 items; a table of contents is exempt. Past that, use a table or split. | `LIST` |
| Every code fence names its language. | `FENCE` |

Sentence craft `[judgement]`: one idea per sentence, one sentence per idea. Prefer a verb to a noun
phrase ("the route validates" over "validation is performed by the route").
Use second person for instructions and active voice everywhere.

## Vocabulary

Banned words are deleted, not replaced. If deleting one loses information,
the sentence needed a fact, not the word. Code: `WORD`.

```text
just simply easy easily trivial straightforward painless obviously of course
delve leverage utilize seamless seamlessly robust comprehensive cutting-edge
powerful innovative streamline empower crucially importantly notably
essentially basically actually
in order to  note that  it should be noted  please note  it's worth noting  in today's
```

A banned word used as a domain term stays: a library named `Seamless`, or
`robust against replay` as a property under test. The rule targets decoration.

Patterns to rewrite `[judgement]`:

- Throat-clearing openers ("Here is the thing", "Let me be clear").
- Reversal framing ("not X, but Y") when plain "Y" says it.
- Significance inflation ("transformative", "critical" as an adjective).
- Synonym cycling. One noun per concept; the glossary term is the noun.
- Vague `-ing` verbs ("fostering", "ensuring", "enabling") in place of a fact.
- Rhetorical questions and closing lines that restate the section.

## Meta-Commentary

A document never talks about its own history, length, or earlier versions.
Readers need the current state. Code: `META`.

```text
this section used to   this document previously   what was one 29-node map
replaces what was      kept for link stability   this corpus now calls
```

## Bloat

Bloat is anything a reader must skip to reach the point. Code owns its own facts; a guide explains them and links the code.

| Rule | Code |
| --- | --- |
| A table of 10 rows led by code identifiers, 20 in a reference, copies a schema. Keep what readers need. | `COPY` |
| No change-log phrases, such as `used to be`, `formerly` or `was renamed`. Git and the ADRs hold history. | `HIST` |

Patterns to cut `[judgement]`:

- UI copy, such as labels, tooltips, and toast text. Tests and the component own it.
- Pixel sizes, breakpoints, and animation timings.
- Edge cases before the main path. Lead with the common case; put exceptions last.
- One fact said three ways in one file. Keep the clearest one.
- A field-by-field list that repeats the schema beside a link to that schema.

### Frozen Facts

A frozen fact is a value copied from code into a doc. It goes stale silently, so it needs a reason to stay.

| Rule | Code |
| --- | --- |
| No patch-level version outside a code fence. The manifest or lockfile owns versions. | `PIN` |
| No source line reference in a guide. Link the file, or a symbol in it. | `LINE` |
| A value that must stay sits under `<!-- frozen: reason -->` on the line before, with a reason of 5 or more words. | `FROZEN` |

```text
2.4.1          a patch-level version, caught by PIN
server.py:42   a source line reference, caught by LINE
```

A marker exempts the next paragraph, list or table from `PIN` and `LINE`.
Write "every" or link the list instead of counting things the code lists, such as "five services" or "ten tests" `[judgement]`.
The [audit](audit.md#claim-checks) re-checks every marker.

Some types expect what `COPY`, `HIST`, `PIN`, `LINE`, and `FROZEN` catch, so the lint skips them there:

- An ADR is a dated record, so it skips all five.
- A glossary and the decision index may name old aliases (`HIST`).
- Requirements record retired rows (`HIST`, `COPY`), and a README maps its folder's files (`COPY`).

## One Home per Fact

Each category of fact has one owning document, listed in the
[fact-ownership table](guides.md#fact-ownership). Every other document may
spend one sentence on it and must link to the owner.

| Rule | Code |
| --- | --- |
| No 12-word run appears in two files. | `DUP` |
| No sentence shares half its content words with a sentence in another file. | `DUP` |
| No diagram relationship is drawn in two files; see [diagram ownership](mermaid.md#ownership). | `DUP` |
| One node title maps to one source across all files. | `NODE` |
| An owner file holds only its own diagram family. | `VIEW` |

The cross-file rules see only the files passed to the lint. Add untouched
files with `--dup-scope`; they join the comparison and report no findings of
their own.

## Links

| Rule | Code |
| --- | --- |
| Link text says what the target is. Never "here", "click here", or a bare URL. | `LINK` |
| Links inside the repo are relative paths that resolve from the file's folder. | `LINK` |
| Anchors match a real heading under GitHub slugging. | `LINK` |
| A linked heading holds only letters, digits, spaces and hyphens, since Azure DevOps slugs punctuation differently. | `LINK` |
| Absolute `github.com/.../blob/...` URLs into this repo are not allowed. | `LINK` |
| Sources for a table or paragraph take the boxed [Sources line](mermaid.md#source-links) a diagram uses. | `MMD` |

## Emoji Markers

An emoji marks what a reader scans for: a warning, a status, or a line's
topic. Each emoji has one meaning in every document, so the set is closed.
Code: `EMOJI`.

| Marker | Emojis | Where |
| --- | --- | --- |
| Callout | `⚠️ Warning`, `💡 Tip` | A blockquote line: `> ⚠️ **Warning:** text` |
| Status | ✅ pass or yes, ❌ fail or no, 🟡 partial or stale | Opening a table cell. A `> **Legend:**` line under the table keys them when the column name does not |
| Topic lead | One per topic, listed below | Opening a bullet, or a table row's first cell |

```text
🔐 Identity and access   📦 Data and storage   🧾 Audit and logs    🤖 Model call
🛡️ Safety                👤 People and roles   🧪 Tests and evals   💰 Cost
🚀 Deploy and release    ⏱️ Latency            ⚙️ Configuration     🔌 Integration
```

- Lead a list or table with topics only when its 3 or more items mix topics.
  One emoji per line, never on every line of a uniform list.
- A heading never holds an emoji: some viewers drop it from the anchor, so
  links break.
- A diagram holds none either. Its tag and shape name the type, and its title
  link icon and legend swatches are the only glyphs.
- An emoji quoted from a tool's output goes in inline code: `🧭 tools`.
- A new marker is added to this table and to the lint together.

## Line Caps

| Type | Cap |
| --- | ---: |
| `readme-project` | 200 |
| `readme-folder` | 80 |
| `how-to`, `explanation` | 200 |
| `explanation`, brief profile | 120 |
| `reference`, `requirements` | 300 |
| `index` | 120; none for the ADR directory's README |
| `adr` | 80 |
| `glossary` | none |

A cap counts every line outside Mermaid fences, so the color a diagram must
carry never pushes prose out. Past the cap, split by topic into a linked
file. Never trim meaning to fit.
