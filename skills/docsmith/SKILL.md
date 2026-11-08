---
name: docsmith
description: >
  Writes and rewrites Markdown documentation to one linted house style:
  project and folder READMEs, docs/ guides (how-to, reference, explanation),
  a docs index, a glossary, requirements, and MADR-style ADRs. Use when asked
  to write or restructure a README or the docs, document a folder or module,
  record a decision or ADR, write or update requirements, or when
  documentation is bloated, inconsistent, duplicated across files, or
  drifted from the code. Also grades docs against their audiences and keeps
  them at A+ as the code and the docs grow.
---

# Docsmith

Produce Markdown documentation that a newly onboarded developer can read
and maintain. Follow the four steps in order. Paths are relative to this
skill's folder.

## Step 1: Classify

| Signal | Type | Reference |
| --- | --- | --- |
| README at a repo, package, or runnable-project root | `readme-project` | [references/readme.md](references/readme.md) |
| README inside a source directory | `readme-folder` | [references/readme.md](references/readme.md) |
| `docs/README.md` | `index` | [references/guides.md](references/guides.md) |
| `docs/<domain>/README.md` | `index`, domain index profile | [references/guides.md](references/guides.md#domain-index-profile) |
| `docs/glossary.md` | `glossary` | [references/guides.md](references/guides.md) |
| `docs/brief.md`, the ten-minute summary for decision-makers | `explanation`, brief profile | [references/guides.md](references/guides.md#brief-profile) |
| A procedure: operations, a playbook, a runbook | `how-to` | [references/guides.md](references/guides.md) |
| Field-by-field facts: contracts, data model, config | `reference` | [references/guides.md](references/guides.md) |
| Why and how things fit: architecture, flows, infrastructure | `explanation` | [references/guides.md](references/guides.md) |
| One cross-cutting subject in depth, such as authentication | `explanation` topic guide | [references/guides.md](references/guides.md) |
| `docs/requirements.md` | `requirements` | [references/requirements.md](references/requirements.md) |
| A decision to record, or a file in the ADR directory | `adr` | [references/adr.md](references/adr.md) |

Always load [references/style.md](references/style.md) and
[references/audit.md](references/audit.md). Before drawing or
editing a diagram, load [references/mermaid.md](references/mermaid.md) and
[references/mermaid-visual.md](references/mermaid-visual.md), then load exactly
one diagram-family reference selected there. If the target fits
two document types, split it into two files; if it fits none, ask before
writing.

## Step 2: Audit

Run the lint first on the existing file and its siblings so the findings are
mechanical, not impressions. Run the script; do not read it.

```bash
python3 scripts/lint_docs.py docs/*.md docs/*/*.md README.md --dup-scope .
```

`--dup-scope .` lets untouched files join the cross-file checks without reporting on them.

Then find the audiences in the project README's Reading Paths table. If it
is missing, or a row does not name its reader's role, stop and ask the user
who reads the docs and what each reader does. Offer default readers, and
write the answer into the README, as the
[audit method](references/audit.md#audiences) says. Never grade against
guessed readers.

Read every file in scope in full and audit it with the
[audit method](references/audit.md): audiences, a verdict per file, claim
checks against the source, and an owner for each repeated fact. Produce
these artifacts and show them in the handoff:

- **Findings list.** Every lint error plus every `[judgement]` violation
  from the style reference, each with a location.
- **Disposition map.** Every existing section mapped to keep, condense,
  move to a named file, or delete with a reason. Content that fails the
  profile is relocated to its owner, never dropped.
- **Owner map.** For each fact that appears in more than one file, the one
  file that owns it.

## Step 3: Write

- Apply the profile. It is the minimum shape: extra sections need a stated
  reason, and a profile section with no content is omitted.
- Write for a developer who joined this week. Open every guide with the
  plain-language point before any identifier appears.
- One home per fact. Check the fact-ownership table in the guides
  reference before restating anything; link to the owner instead.
- One relationship, one diagram. The README draws the context, each
  viewpoint file draws its own family, and a topic guide draws the zoom-in.
- Break up walls of text with the emoji markers in the style reference:
  warnings and tips as callouts, statuses in table cells, and topic leads
  on mixed lists. Never in a heading or a diagram.
- Use glossary terms as the only names for domain concepts. If a term is
  missing, add it to the glossary in the same change.
- Every diagram uses the one block and only the portable syntax from the
  mermaid reference, so it renders in an IDE, GitHub, and Azure DevOps.
- Every node follows the mermaid reference's node title rules: plain Title
  Case words that never repeat the tag, a stacked shape for several things,
  and a TYPE that states what the code is.
- A touched file is converted to house style in full. Untouched files are
  left alone, even when they disagree with these rules.

## Step 4: Verify

Run every check on the final text of every touched file.

1. **Lint.** Pass the touched files and their sibling guides together so
   the cross-file duplicate check runs. The command must exit 0.

   ```bash
   python3 scripts/lint_docs.py docs/*.md docs/*/*.md README.md --dup-scope .
   ```

2. **Render every Mermaid block and inspect each image**, per the mermaid reference.
   The render proves layout only. The lint proves the syntax is portable.

   ```bash
   python3 scripts/render_mermaid.py docs/*.md docs/*/*.md README.md
   ```

3. **Read it as the new developer.** For each touched guide, answer: what
   can I do after reading this that I could not do before? If the answer
   is unclear, the guide is not done.

4. **Grade it.** Grade each audience whose reading path passes through a
   touched file, with the [rubric](references/audit.md#grades). Fix and
   re-grade until every one is A+, or name exactly what blocks it.

5. **Handoff report.** Files touched, the disposition map, the lint output,
   the diagrams rendered, the grades, and any finding left unresolved.

## Keep It A+

Docs decay in two ways: new text adds bloat, and code changes under text
that still describes the old code. Guard against both.

- **Every run grades.** Step 4 grades the touched docs and their reading
  paths, so each addition is checked against the whole journey.
- **A code change re-opens the docs that link it.** Run the script below
  against the branch base. It lists every doc that links a changed source
  file but was not edited. Edit each one, or, when it is still true, end a
  commit message with one `Docs-checked: <doc path>` trailer line per doc,
  after a blank line. Wire it into the
  project's quality gate when there is one.

  ```bash
  python3 scripts/doc_impact.py --base origin/main
  ```

- **A full audit on a cadence.** Before a release, or once 10 or more
  guides changed since the last one, audit every file for every audience,
  as the [audit method](references/audit.md#when-to-audit) says. The script
  below fails when one is due; the audit's commit subject starts with
  `docs audit`, which resets the count. Wire it in beside `doc_impact.py`.

  ```bash
  python3 scripts/audit_due.py
  ```

- **Frozen values need a reason.** A version, a line number, or a count
  goes stale silently. Link the source instead, or keep the value under a
  reasoned [frozen marker](references/style.md#frozen-facts).

## Hard Limits

- Line caps per type, from the style reference, are hard. Over the cap,
  split by topic; never trim meaning.
- An accepted ADR's decision text is immutable. Supersede it with a new
  ADR. A format-only pass may normalize its headings and status table.
- The skill audits and documents; it never modifies source code to match
  the docs.
- `specs/` and `plans/` are out of scope; leave those files alone, except
  to fix a link path to a guide you moved.
- When editing this skill itself, keep it project agnostic: its templates,
  examples, and fixtures use invented names, never names from a real repository.
- A new diagram construct or setting is proven in the viewers before it is
  applied everywhere, as the [mermaid reference](references/mermaid.md#portable-syntax) describes.
