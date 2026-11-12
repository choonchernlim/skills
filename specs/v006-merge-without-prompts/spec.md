# v006: Merge Without Prompts

After the user approves gate ②, `/merge-worktree` lands the worktree and removes it without another
permission prompt or question.

## Shared Understanding

- **Why it prompted.** Sessions run in Claude Code auto mode, and nothing pre-approved the script, so the
  classifier judged every call. Auto mode drops wildcard interpreter rules such as `Bash(python3 *)`.
  Agents also wrapped `land` in `cd`, `PATH=` or `core.hooksPath=/dev/null` prefixes; the last is a hook
  bypass the classifier flags.
- **Pre-approval in the skill.** `SKILL.md` frontmatter `allowed-tools` approves the script for the turn
  that invoked the skill. The script runs directly, through its shebang, so the rule is not an
  interpreter wildcard. The skill forbids wrappers around the command, so the rule matches.
- **Approved hook skip.** When the pre-push hook refuses a `land`, the result carries `hook` and the
  skill asks whether to fix the cause or land skipping the hook. `land --no-verify` passes `--no-verify`
  to the push, and is refused unless that hook refused this packet first. Predicting the hook at gate ②
  would need commands outside the pre-approval.
- **Cleanup asks nothing.** `cleanup` deletes ignored files with the worktree and lists them in `dropped`.
  It still refuses on non-ignored uncommitted files and on commits that never landed. `dropped` holds
  the first 20 entries and `dropped_count` the total. A repository or worktree inside an ignored folder
  is unreviewed work, so cleanup refuses and lists it.
- **Hardened for the pre-approval.** The rule approves every subcommand, so none may reach beyond its
  worktree: `abort` acts only on a conflict its own `prepare` stopped on, and the Herdr `finish` step reads
  its job from the repository instead of taking paths and branches as arguments. `finish` now passes
  `--workspace ID`, the form Herdr accepts.

## Assumptions

- Confirmed end to end: `${CLAUDE_SKILL_DIR}` expands inside `allowed-tools` to the absolute skill path,
  and in auto mode `prepare`, `land` and `cleanup` ran with no permission denial.
- The grant lasts one turn. Picker answers stay inside it; a typed follow-up message ends it.

## Definition of Done

- In auto mode, after **Approve and merge**, `/merge-worktree` lands and removes the worktree with no
  permission prompt and no ignored-files question.
- An approved hook skip goes through `land --no-verify`.
- `scripts/check --full` passes; the new and changed tests fail before the change and pass after.
