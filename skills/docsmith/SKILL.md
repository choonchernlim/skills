---
name: docsmith
description: >
  Writes and rewrites Markdown documentation to one linted house style:
  project and folder READMEs, docs/ guides (how-to, reference, explanation),
  a docs index, a glossary, requirements, and MADR-style ADRs. Use when asked
  to write or restructure a README or the docs, document a folder or module,
  record a decision or ADR, write or update requirements, or when
  documentation is bloated, inconsistent, duplicated across files, or
  drifted from the code.
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
| `docs/glossary.md` | `glossary` | [references/guides.md](references/guides.md) |
| A procedure: operations, a playbook, a runbook | `how-to` | [references/guides.md](references/guides.md) |
| Field-by-field facts: contracts, data model, config | `reference` | [references/guides.md](references/guides.md) |
| Why and how things fit: architecture, flows | `explanation` | [references/guides.md](references/guides.md) |
| `docs/requirements.md` | `requirements` | [references/requirements.md](references/requirements.md) |
| A decision to record, or a file in the ADR directory | `adr` | [references/adr.md](references/adr.md) |

Always load [references/style.md](references/style.md). Load
[references/mermaid.md](references/mermaid.md) before drawing or editing a
diagram. If the target fits two types, split it into two files; if it fits
none, ask before writing.

## Step 2: Audit

Run the lint first on the existing file and its siblings so the findings are
mechanical, not impressions. Run the script; do not read it.

```bash
python3 scripts/lint_docs.py docs/*.md README.md
```

Then produce two artifacts and show both in the handoff:

- **Findings list.** Every lint error plus every `[judgement]` violation
  from the style reference, each with a location.
- **Disposition map.** Every existing section mapped to keep, condense,
  move to a named file, or delete with a reason. Content that fails the
  profile is relocated to its owner, never dropped.

## Step 3: Write

- Apply the profile. It is the minimum shape: extra sections need a stated
  reason, and a profile section with no content is omitted.
- Write for a developer who joined this week. Open every guide with the
  plain-language point before any identifier appears.
- One fact, one home. Check the fact-ownership table in the guides
  reference before restating anything; link to the owner instead.
- Use glossary terms as the only names for domain concepts. If a term is
  missing, add it to the glossary in the same change.
- Every diagram uses the one block from the mermaid reference.
- A touched file is converted to house style in full. Untouched files are
  left alone, even when they disagree with these rules.

## Step 4: Verify

Run every check on the final text of every touched file.

1. **Lint.** Pass the touched files and their sibling guides together so
   the cross-file duplicate check runs. The command must exit 0.

   ```bash
   python3 scripts/lint_docs.py docs/*.md docs/adrs/*.md README.md
   ```

2. **Render every Mermaid block and look at the image**, following Render
   and Inspect in the mermaid reference.

3. **Read it as the new developer.** For each touched guide, answer: what
   can I do after reading this that I could not do before? If the answer
   is unclear, the guide is not done.

4. **Handoff report.** Files touched, the disposition map, the lint output,
   the diagrams rendered, and any finding left unresolved.

## Hard Limits

- Line caps per type, from the style reference, are hard. Over the cap,
  split by topic; never trim meaning.
- An accepted ADR's decision text is immutable. Supersede it with a new
  ADR. A format-only pass may normalize its headings and status table.
- The skill audits and documents; it never modifies source code to match
  the docs.
- `specs/` and `plans/` are out of scope; leave those files alone.
