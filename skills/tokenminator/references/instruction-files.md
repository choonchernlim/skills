<!--
Purpose: How to lay out AGENTS.md and CLAUDE.md so both agents read one source, including the managed rules block.
Type: how-to
-->

# Instruction Files

Audience: the agent fixing an instruction-file finding.

Both agents need the same short, accurate instructions at session start.
This playbook gives one source of truth and keeps it from drifting.

## Table of Contents

- [Codes This Fixes](#codes-this-fixes)
- [Bridge the Two Agents](#bridge-the-two-agents)
- [Scope Claude Rule Files](#scope-claude-rule-files)
- [Write the Orientation Section](#write-the-orientation-section)
- [Write the Do Not Read Section](#write-the-do-not-read-section)
- [Install the Rules Block](#install-the-rules-block)
- [Keep It Short](#keep-it-short)
- [Verify](#verify)
- [Hand to the User](#hand-to-the-user)

## Codes This Fixes

| Code | Fix |
| --- | --- |
| `AGT-MISSING` | Create a root `AGENTS.md`. |
| `CLD-IMPORT` | Add `CLAUDE.md` beside each `AGENTS.md` with one import line. |
| `CLD-FORK` | Move shared rules out of `CLAUDE.md` into `AGENTS.md`. |
| `CLD-RULE` | Add `paths:` frontmatter, or move a shared rule into `AGENTS.md`. |
| `CLD-COMPACT` | Add a Compact Instructions section to `CLAUDE.md`. |
| `ORIENT-MISSING` | Add the orientation section. |
| `DNR-MISSING`, `DNR-UNLISTED` | Add or extend the Do Not Read section. |
| `PATH-DEAD` | Correct or remove the path. |
| `INS-LONG` | Move detail into docs and link to them. |
| `RULES-MISSING`, `RULES-OUTDATED`, `RULES-EDITED` | Run `--fix-rules-block`. |

Run `python3 scripts/audit_tokens.py <repo> --fix` first. It writes a missing
`CLAUDE.md` bridge, the Compact Instructions section, and the rules block.
The sections that need knowledge of the project stay with you.

## Bridge the Two Agents

Codex reads `AGENTS.md`. Claude Code reads `CLAUDE.md` and ignores
`AGENTS.md`. Without a bridge, Claude sessions never see the project rules.

1. Put every shared instruction in `AGENTS.md`.
2. Create `CLAUDE.md` in the same folder containing one line:

   ```text
   @AGENTS.md
   ```

3. Repeat for a nested `AGENTS.md` only when a folder has facts of its own.
4. Keep `CLAUDE.md` for Claude-only notes, and keep those under 15 lines.

### Tell Compaction What to Keep

Claude Code reads a `## Compact Instructions` section when it summarizes a
long session. Without one, the summary can drop the plan or the failing
check, and the agent derives both again. Codex ignores the section, so it
goes in `CLAUDE.md`, under the import line:

```markdown
## Compact Instructions

Keep the plan, the files changed, the failing check ids, and the user's decisions.
```

## Scope Claude Rule Files

A file under `.claude/rules/` with no `paths:` frontmatter loads in every
Claude session, the same as `CLAUDE.md`. Codex never reads the folder.

1. Move a rule both agents need into `AGENTS.md`, or a nested `AGENTS.md`.
2. Give a Claude-only rule the globs it serves:

   ```yaml
   ---
   paths:
     - "**/*.test.ts"
   ---
   ```

The file then loads only when Claude reads a matching file.

## Write the Orientation Section

Name the heading `## Where Things Live`. It replaces the directory listing
and file reading that every new session otherwise repeats.

Include, as one table:

- each deployable unit, its path, and its local port
- the source of truth for contracts or schemas
- the command that starts everything locally
- the infrastructure folder and how environments are separated
- the CI and deploy pipeline files, in the order they trigger
- the check entry point and where its tests live
- a pointer to the docs index, if one routes tasks to guides

Put every path in backticks. The audit reports a path as dead when its
first folder exists in the repository but the rest does not resolve.

## Write the Do Not Read Section

Name the heading `## Do Not Read`. Claude Code can enforce read denies, but
for Codex this section is the dependable layer.

- List lockfiles by name and give the command to use in their place.
- List generated files and point to the source they derive from.
- List large data fixtures.
- Mark superseded plans or specs as history, and name the current docs.

## Install the Rules Block

The block holds working habits that must apply in every session. It is
managed text: never edit it by hand. Install it before trimming the file, so
the trim is measured against the final layout.

```bash
python3 scripts/audit_tokens.py <repo> --fix-rules-block
```

The command writes the block above the orientation heading. The text is
composed for the repository, so no session pays for a rule it cannot use:

- The check line names the real entry point, and is left out until one exists.
- The package-manager hints name only the lockfiles present.
- The Playwright line appears only when a Playwright config exists.
- The browser MCP line appears when a suite or a browser MCP config exists.

The managed-by note sits inside the begin marker. Claude Code strips block
comments, so the note costs a Claude session nothing.

When the repository gains an entry point, a lockfile, or a suite, the audit
reports `RULES-EDITED`; run the command again. The full text, with every
optional line, is:

```text
<!-- BEGIN:tokenminator-rules v3 | managed by the tokenminator skill; never edit by hand; refresh with its audit script and --fix-rules-block -->
## Token Discipline

- Run checks with `scripts/check`. Read its summary first, then only the failing check's log.
- Read files in slices with offset and limit. Search first, then open the matching range.
- Never open lockfiles, generated files, or anything under Do Not Read. Ask the package manager instead (`uv tree`, `poetry show --tree`, `bun pm ls`, `npm ls`, `pnpm ls`, `yarn list`, `go list -m all`, `cargo tree`, `nix flake metadata`, `terraform providers`).
- Prefer quiet and JSON flags over prose output. Send long output to a file and read only the part you need.
- Hand wide searches to a subagent and keep only its conclusion.
- Ask git for the short form first: `git status --short`, `git diff --stat`, `git log --oneline`.
- Test browsers with the scripted Playwright suite. Open one named screenshot only for a visual judgment.
- Use a browser MCP only to explore an unscripted page once, then turn what you learned into a test.
<!-- END:tokenminator-rules -->
```

If the markers are unpaired or duplicated the command exits 2 and changes
nothing. Repair the markers by hand, then run it again.

## Keep It Short

An instruction file is paid for in every session by both agents.

- The budget follows the repository: 1,200 bytes plus 40 per tracked file,
  between 2,000 and 8,000. A small repository is cheap to re-explore.
- The managed rules block is not counted, because it is not yours to trim.
- The audit prints what the root files cost today under `measured today`.
  When that passes the cost of re-exploring, it says so: trim them.
- To trim, print the bytes under each heading and cut the largest sections
  first: `python3 scripts/audit_tokens.py <repo> --sections`.
- Keep the root-to-leaf `AGENTS.md` chain under 32,768 bytes, or Codex stops
  reading part way through.
- State a rule once. A nested file adds facts; it does not repeat the root.
- Link to a guide for procedures. Do not paste the procedure.

## Verify

1. Re-run the audit and confirm the code cleared.
2. Copy `assets/test_agents_md.py` to `scripts/test_agents_md.py`, unedited,
   and add it to the project's checks. It fails when a backticked path in
   `AGENTS.md` does not exist.
   - It cuts the rules block out, and skips paths git ignores.
   - It fails when it checked no path, so an empty table cannot pass.

## Hand to the User

Put this under "Your next steps" in the report. A running session keeps the
instructions it started with, so only a new one proves the change.

1. Start a fresh Claude Code session at the repository root.
2. Ask it "what are this project's rules?" and confirm it answers from the
   new `AGENTS.md` without opening the file.
