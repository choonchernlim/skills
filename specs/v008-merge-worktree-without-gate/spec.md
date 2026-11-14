# v008: Merge Worktree Without Gate

Running `/merge-worktree` is the approval: it lands, pushes and removes the worktree with no picker,
unless a red flag shows.

## Shared Understanding

- **Why.** Gate ② asked "Approve and merge?" on every run, even when everything was green. v006 already
  removed the cleanup question and the permission prompts; only the gate remained.
- **Red flags still stop it.** The skill shows the packet and asks, as before, when any of these holds:
  a project check failed or did not run, a review finding is still open, `clashes` is not empty,
  `open_steps` is not zero, or a commit was dropped by a conflict resolution.
- **Replayed resolutions.** A `rerere` replay stops the run only through `clashes`; no extra red flag.
- **Who may start it.** Agents too; the skill description is unchanged. A run an agent starts counts the
  same as one the user starts, and the global rule says so.
- **Unchanged.** Skipping the pre-push hook still needs its own yes. `rejected` and `stale` loop back
  to step 1. `land --tip` still guards against a moved HEAD.
- **Global rule.** `~/.claude/CLAUDE.md` (a link to `dotfiles/home/ai/AGENTS.md`) says running
  `/merge-worktree` approves that run's merge, push and worktree removal, unless the skill stops on a
  red flag.
- **docs-lint folded in.** The 51 pre-existing `docs-lint` findings under
  `skills/tokenminator/references/` are fixed in this change, so `scripts/check --full` is green.

- **review-feature model.** `skills/review-feature/SKILL.md` pins `model: opus` in its frontmatter, so it never
  runs on Sonnet in Claude Code; Codex and agy may ignore the key.

## Assumptions

- Only the `--tip` help text in `merge_worktree.py` needed a script change; no logic changes.

## Definition of Done

- A green scratch run lands, pushes and removes the worktree with zero pickers.
- A red scratch run, with a failing check, stops at the picker and pushes nothing.
- A dropped commit is a listed red flag in `SKILL.md`.
- `scripts/check --full` is fully green.
- The review passes report no unresolved confirmed findings.
