---
name: tokenminator
description: >
  Cuts AI coding-agent token usage in any repository, the same way for
  Claude Code and Codex. Use when asked to reduce tokens, context, or agent
  cost; when sessions hit context limits or compact often; when an agent
  reads lockfiles, generated files, or giant logs; when setting up or
  reviewing AGENTS.md, CLAUDE.md, skill layout, agent hooks, a quiet check
  runner, read-deny rules, or Playwright e2e for agents; or when preparing a
  repository for agent work.
---

# Tokenminator

Make a repository cheap for coding agents to work in. Most token waste is
configuration, so a script finds it and a playbook fixes it.

One run fixes what the `next:` line names: audit, apply that playbook, verify,
report. That is one area, or every area at once when only low findings remain.
The user runs the skill again until the audit says `next: none`.

Paths below are relative to this skill's folder.

## Step 1: Decide Whether to Change Anything

Audit and report only, changing nothing, when any of these hold:

- The repository is not the user's: the remote belongs to someone else, or
  the user has no commits in it. Ask when unsure.
- The user asked for a review or a report.

Within a run, never change a finding's file when:

- It sits in a vendored folder, a submodule, or generated files.
- It resolves outside the audited repository. Resolve links first: a path in
  the repository can point elsewhere, and a path under the home folder can
  point back in. The audit marks these `proposal only`.

## Step 2: Audit

```bash
python3 scripts/audit_tokens.py <repo>
```

Exit 0 is clean, 1 means findings, 2 means the audit could not run. Do not
re-derive findings by reading the repository; the script already did that
without spending tokens. Read the output in this order:

| Line | Meaning |
| --- | --- |
| `next:` | What to fix in this run, and its playbook or playbooks. `next: none` means this repository is done. |
| `CODE severity path ...` | One finding, with `~before->~after tok/session` and its basis: `measured` from real file sizes, or `estimated` from the impact class. |
| `measured today` | What the root instruction files cost in every session, and the log size of the last check run. |
| `user scope` | Read only. What the config under the home folder costs in every session, in every repository. Each finding names its real owner and is `fixable here` or `proposal only`. |
| `tokens per session` | Before and after per area, with a TOTAL row. |
| `summary:` | Counts, detected stacks, the oldest tool fact. |

| Flag | Use |
| --- | --- |
| `--fix` | Apply every fix that needs no judgement, then re-audit in brief. |
| `--expect-cleared CODE...` | Re-audit in three lines: what cleared, what is open, what is next. |
| `--brief` | The same three lines, with no codes to confirm. |
| `--format json`, `--user`, `--no-user`, `--list-codes` | Machine output, user scope alone, no user scope, every code with its area. |

The numbers rank areas against each other. They do not predict a bill.
[references/principles.md](references/principles.md) gives the model.

## Step 3: Take the Area the Audit Names

Load the playbook or playbooks on the `next:` line, and nothing else. Do not
pick a different area: the script has already ranked by severity, put
instruction files first, and put the check runner before the hooks that call
it. `--list-codes` maps any code to its area.

When the saving on the `next:` line is `estimated`, tell the user before
applying. An estimated area can be worth less than its number, and whether
to spend a run on it is the user's call.

## Step 4: Apply

- Run `--fix` first. It applies what needs no judgement, so you write only
  what needs knowledge of the project.
- Copy the templates under `assets/` where a playbook names one. Never
  rewrite one by hand, and never edit a copy.
- Reuse what the project has. Wrap its existing tools and entry point
  before adding new ones.
- Everything must behave the same in Claude Code and Codex. Shared rules go
  in `AGENTS.md`, shared logic under `scripts/`. A Claude-only setting is an
  extra layer on top, never the only layer.
- When a finding does not apply, record it with a reason in
  `.agents/tokenminator.json`. The key is `CODE`, or `CODE:glob`
  matched against the finding's path:

  ```json
  { "ignore": { "CI-DUP:deploy/*.yml": "deploy pipeline, runs no checks" } }
  ```

## Step 5: Verify

1. Run the playbook's verify steps. A step only the user can do, such as
   starting a fresh session, goes into the report, not into this run.
2. Run the project's own check entry point, if it has one.
3. Audit again with `--expect-cleared` and the codes you fixed. They cleared,
   and the `open:` line shows no code that the first audit did not.
4. Run `git status --short`. Every changed file is inside the repository
   and is one you meant to change.

## Step 6: Report

The report is what the user acts on. Use these headings, in this order, and
leave one out only when it would be empty.

1. **Result.** One sentence: the area fixed and the tokens saved per
   session, marked measured or estimated.
2. **What changed.** A table of `Action | Before | After | Basis`, one row
   per action taken in this run, then a TOTAL row. Numbers come from the two
   audit runs. Open findings do not go in this table.
3. **Your next steps.** A numbered list of what only the user can do, each
   one a command or a click:
   - the playbook's user-only checks, such as a fresh session
   - `git add` for each new file, then review and commit
   - each `proposal only` finding: its cost, its real owner, and the exact
     change to make there
4. **Not done, and why.** Findings ignored with their reason, playbook steps
   skipped, and any estimate the repository contradicts.
5. **Next run.** The `next:` line in plain words, with its basis. When it
   says `none`, write "This repository is done."
6. `Touched outside the repository: none`. If that is not true, say what
   was touched and why.

## Tool Facts

Playbooks depend on how each agent behaves, and that changes. Dated facts
live in [references/claude-code.md](references/claude-code.md),
[references/codex.md](references/codex.md), and the table that ends the
browser playbook. Trust a row until it fails in practice or the audit
reports `FACT-STALE`. Then re-verify that single row with `ctx7` and update
its date. Never re-read all the documentation up front.

## Hard Limits

- Never write outside the audited repository, by any tool, shell included.
  A `proposal only` finding is shown to the user and applied by the user.
- The script writes only under `--fix` and `--fix-rules-block`, and refuses
  a target that resolves outside the repository. Run the script; do not read
  it. Its self-tests are
  [scripts/test_audit_tokens.py](scripts/test_audit_tokens.py) and
  [scripts/test_assets.py](scripts/test_assets.py).
- Never edit the rules block by hand, and never weaken an existing check,
  hook, or permission rule to save tokens.
- Never rewrite vendored or third-party skill content. Move it, or delete it
  after asking.
- Never copy this skill into a project. Porting it is the user's decision.
- Never commit unless asked, and add no co-author line.
