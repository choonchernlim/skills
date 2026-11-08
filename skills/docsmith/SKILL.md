---
name: docsmith
description: >
  Writes and rewrites Markdown documentation to one linted house style:
  project and folder READMEs, docs/ guides (how-to, reference, explanation),
  a docs index, a glossary, requirements, MADR-style ADRs, and Mermaid
  diagrams. Use when asked to write or restructure a README or the docs,
  document a folder or module, record a decision or ADR, write or update
  requirements, or draw, edit, or fix any Mermaid diagram or flowchart in
  any Markdown file, or when documentation is bloated, inconsistent,
  duplicated across files, or drifted from the code. Also grades docs
  against their audiences and keeps them at A+ as the code and the docs grow.
---

# Docsmith

Produce Markdown documentation that a newly onboarded developer can read
and maintain. Follow the four steps in order. Script paths are relative to
this skill's folder; doc paths are relative to the project root.

## Step 1: Classify

Take the first row that matches.

| Signal | Type | Reference |
| --- | --- | --- |
| README at a repo, package, or runnable-project root | `readme-project` | [references/readme.md](references/readme.md) |
| README inside a source directory | `readme-folder` | [references/readme.md](references/readme.md) |
| `docs/README.md` | `index` | [references/guides.md](references/guides.md) |
| `docs/adrs/README.md` | `index`, decision index | [references/guides.md](references/guides.md#roles) |
| `docs/<domain>/README.md` | `index`, domain index profile | [references/guides.md](references/guides.md#domain-index-profile) |
| `docs/glossary.md` | `glossary` | [references/guides.md](references/guides.md) |
| `docs/brief.md`, the ten-minute summary for decision-makers | `explanation`, brief profile | [references/guides.md](references/guides.md#brief-profile) |
| A procedure: operations, a playbook, a runbook | `how-to` | [references/guides.md](references/guides.md) |
| Field-by-field facts: contracts, data model, config | `reference` | [references/guides.md](references/guides.md) |
| Why and how things fit: architecture, flows, infrastructure | `explanation` | [references/guides.md](references/guides.md) |
| One cross-cutting subject in depth, such as authentication | `explanation` topic guide | [references/guides.md](references/guides.md) |
| `docs/requirements.md`, or a domain file under `docs/requirements/` | `requirements`; a split `docs/requirements.md` is `index` | [references/requirements.md](references/requirements.md) |
| A decision to record, or another file in the ADR directory | `adr` | [references/adr.md](references/adr.md) |

Always load [references/style.md](references/style.md) and
[references/audit.md](references/audit.md). Before drawing or editing a diagram, also load:

- [references/mermaid.md](references/mermaid.md) and [references/mermaid-visual.md](references/mermaid-visual.md).
- The reference of each family you draw. A runtime diagram also loads
  [mermaid-application.md](references/mermaid-application.md#grammar) for its TYPE list.

If the target fits two document types, split it into two files; if it fits
none, ask before writing.

## Step 2: Audit

Lint the target files first, so the findings are mechanical, not
impressions. Run the script; do not read it.

```bash
python3 scripts/lint_docs.py <target files> --dup-scope .
```

Then take the audiences as the [audit method](references/audit.md#audiences)
says; never grade against guessed readers.

Read every file in scope in full and audit it with the
[audit method](references/audit.md). Before writing, show the findings, the
disposition map, and the owner map that the
[audit report](references/audit.md#report) lists.

## Step 3: Write

- Apply the profile. It is the minimum shape: extra sections need a reason
  stated in the handoff, and a profile section with no content is omitted.
- Write for a developer who joined this week. Open every guide with the
  plain-language point before any identifier appears.
- Keep [one home per fact](references/style.md#one-home-per-fact): check the
  [fact-ownership table](references/guides.md#fact-ownership) before restating
  anything, and link the owner instead.
- One relationship, one diagram. The README draws the context, each
  viewpoint file draws its own family, and a topic guide draws the zoom-in.
- Use the style reference's [emoji markers](references/style.md#emoji-markers)
  where readers scan. Never in a heading or a diagram.
- Use glossary terms as the only names for domain concepts. If a term is
  missing, add it to the glossary in the same change.
- Every diagram follows the mermaid references loaded in Step 1, including
  the [node title rules](references/mermaid-visual.md#node-titles).

A touched file is converted to house style in full. Untouched files are left
alone, even when they disagree with these rules.

## Step 4: Verify

Run every check on the final text of every touched file.

1. **Lint** every touched file, with the whole project in the cross-file
   checks. It must exit 0.

   ```bash
   python3 scripts/lint_docs.py <touched files> --dup-scope .
   ```

2. **Render every Mermaid block and inspect each image**, per the
   [mermaid reference](references/mermaid.md#render-and-inspect).

   ```bash
   python3 scripts/render_mermaid.py <touched files>
   ```

3. **Read it as the new developer:** name what each touched guide lets a
   reader do that they could not before. If you cannot, it is not done.

4. **Grade** each audience whose reading path passes through a touched
   file, with the [rubric](references/audit.md#grades). Fix and re-grade
   until a fresh audit gives each one A+, or name what blocks it.

5. **Handoff report.** Report as the [audit report](references/audit.md#report) says.

## Keep It A+

Docs decay in two ways: new text adds bloat, and code changes under text
that still describes the old code. Step 4 guards against the first on every
run. Against the second, wire the scripts in the
[audit triggers](references/audit.md#when-to-audit) into the project's
quality gate. One re-opens the docs that link changed code; the other says
when a full audit is due.

## Hard Limits

- [Line caps](references/style.md#line-caps) and
  [ADR immutability](references/adr.md#what-may-change-in-an-accepted-adr)
  are hard limits.
- The skill audits and documents; it never modifies source code to match
  the docs.
- `specs/` and `plans/` are out of scope; leave those files alone, except
  to fix a link path to a guide you moved.
- Diagram syntax stays within the
  [portable syntax](references/mermaid.md#portable-syntax) rules.
