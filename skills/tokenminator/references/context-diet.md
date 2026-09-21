<!--
Purpose: How to cut what loads into every session: skill scoping, one skill copy, read denies, and MCP placement.
Type: how-to
-->

# Context Diet

Audience: the agent fixing a skill, read-deny, or configuration finding.

Some context is paid for before the first prompt. Other context is paid for
by one careless read. This playbook removes both.

## Table of Contents

- [Codes This Fixes](#codes-this-fixes)
- [Keep One Copy of Each Skill](#keep-one-copy-of-each-skill)
- [Scope Skills to Folders](#scope-skills-to-folders)
- [Block Costly Reads](#block-costly-reads)
- [Cap Tool Output](#cap-tool-output)
- [Make Large Source Cheap](#make-large-source-cheap)
- [Place MCP Servers](#place-mcp-servers)
- [Verify](#verify)
- [Hand to the User](#hand-to-the-user)

## Codes This Fixes

| Code | Fix |
| --- | --- |
| `SKILL-DUP` | Replace the second copy with a relative link. |
| `SKILL-LINK` | Give both agents the skill, through per-skill relative links. |
| `SKILL-DEAD` | Repoint the link at the renamed skill, or delete the link. |
| `SKILL-BUDGET` | Move skills to the folder they serve, or delete unused ones. |
| `SKILL-DESC` | Shorten the description and lead with trigger words. |
| `DENY-MISSING` | Add a `Read(...)` deny for the file. |
| `DENY-DEAD` | Remove or correct the pattern. |
| `DENY-SEARCH` | List the file in the root `.ignore`. |
| `CFG-CAP` | Set the output cap in each agent's project config. |
| `CFG-PARSE` | Repair the JSON; a broken file disables its hooks and denies. |
| `SRC-LARGE` | Split the file, or ship the outline tool so agents read one range. |

Run `python3 scripts/audit_tokens.py <repo> --fix` first. It applies
`DENY-MISSING`, `DENY-SEARCH`, and `CFG-CAP` without judgement. Naming the
files under Do Not Read stays with you.

## Keep One Copy of Each Skill

Installers often write the same skill into `.claude/skills` and
`.agents/skills`. Two copies drift, and one agent ends up missing a skill.

1. Confirm the trees match before deleting anything:

   ```bash
   diff -rq .agents/skills .claude/skills
   ```

2. Keep the real folder under `.agents/skills/<name>`.
3. Replace each `.claude/skills/<name>` with a relative link:

   ```bash
   ln -s ../../.agents/skills/<name> .claude/skills/<name>
   ```

4. Link each skill, never the whole `skills` folder. Only per-skill links
   are documented for Claude Code.
5. Add a repository test that asserts every `.claude/skills` entry is a link
   to the sibling `.agents/skills` folder of the same name.

Links need macOS or Linux. On Windows keep two copies and add a parity check.

## Scope Skills to Folders

Every skill at the repository root adds its description to every session.
A skill used by one part of the codebase belongs in that part.

1. Move the skill to `<folder>/.agents/skills/<name>` and link it from
   `<folder>/.claude/skills/<name>`.
2. Delete skills the project does not use. Ask before deleting.
3. List each scope and its skills in `AGENTS.md`.

A skill that is only ever run by name can set
`disable-model-invocation: true`. Claude Code then drops its description
until a user invokes it. Codex still loads it, so the audit still counts it.

The agents load nested scopes differently. Claude Code loads one when it
first touches a file there. Codex loads one only when launched in that
folder, so tell Codex sessions which `SKILL.md` to read directly.

Moving a skill under a source folder can expose it to that folder's tools.
ESLint 9 lints dot-folders, so add `.agents/**` and `.claude/**` to its
ignores. Make autofixers and formatters skip both folders as well.

## Block Costly Reads

A lockfile read can cost more than the rest of the session.

1. Add deny rules to `.claude/settings.json`:

   ```json
   { "permissions": { "deny": ["Read(**/package-lock.json)", "Read(/data/big.json)"] } }
   ```

2. Use a bare or `**/` pattern for a name at any depth, and a leading `/`
   for one path from the project root.
3. Name the same files under Do Not Read in `AGENTS.md`.
4. List them in a root `.ignore` file, one gitignore pattern per line.
5. Add a test that every deny pattern still matches a file.

A Read deny does not keep a file out of search results. Both agents search
with ripgrep, which skips whatever `.ignore` lists. The file also hides
those paths from a developer's own `rg` and editor search; `rg -u` overrides
it.

A Read deny also blocks Edit and Write on that path. That suits files that
tools regenerate. Do not deny a file the agent is expected to edit by hand.

The audit flags lockfiles and generated files over 2,000 bytes, and data
files over 40,000 bytes. It never flags source code. Files with the same
name share one finding, which names the rule to add.

## Cap Tool Output

One noisy command can return more than the rest of the turn. A cap makes
the limit a setting and not a habit.

1. In `.claude/settings.json`, set the inline Bash limit in characters.
   Claude Code saves the overflow to a file and returns a preview and the
   path:

   ```json
   { "bashOutputMaxChars": 10000 }
   ```

2. In `.codex/config.toml`, set the same budget in tokens, above any table:

   ```toml
   tool_output_token_limit = 2500
   ```

Codex loads a project `config.toml` only after the project is trusted.

## Make Large Source Cheap

A source file cannot be denied, because agents must edit it. One full read
of an 80 KB file costs about 20,000 tokens, more than most other findings.

- Split the file by responsibility when the project can afford the refactor.
- Otherwise copy `assets/outline` to `scripts/outline` and name it in
  `AGENTS.md`. An agent outlines the file, then reads one range.
- For Claude Code, add the read guard from the hooks playbook.

`SRC-LARGE` is a note: it never fails the audit. It clears once
`scripts/outline` exists and `AGENTS.md` names it.

## Place MCP Servers

Claude Code defers MCP tool schemas, so an idle server costs little. The
cost is in the results: a browser snapshot can be thousands of tokens.

- Remove servers the project does not use.
- Declare a heavy server on an exploration subagent, so its results stay
  out of the main conversation.
- Prefer a script when the same steps will run again.
- For Codex, list only the tools in use under the server's `enabled_tools`.
  Codex does not document deferred schemas.
- Cap a server's results: `MAX_MCP_OUTPUT_TOKENS` under `env` in
  `.claude/settings.json`, and `output_token_limit` per tool for Codex.

## Verify

1. Re-run the audit and confirm the code cleared.
2. Run the project check entry point; moved skills must not break linters.
3. Search for a string found only in a file that `.ignore` lists, with the
   agent's own search tool. It returns nothing.

## Hand to the User

Put this under "Your next steps" in the report. Deny rules and skill lists
load at session start, so only a new session shows the change.

1. Start a fresh Claude Code session at the repository root.
2. Run `/context` and compare the skill and memory lines with the earlier
   values.
3. Ask it to read one denied file, by name, and confirm it is refused.
4. Ask it to run a command that prints more than the cap. It gets a preview
   and a file path.
