# v008 Plan

- [x] Record the spec and plan → verify: both files exist
- [x] Edit `skills/merge-worktree/SKILL.md` lines 11 and 28-45, and the `--tip` help in `merge_worktree.py` → verify: no "approved tip" wording remains
- [x] Edit the global `/merge-worktree` rule → verify: no other bullet contradicts it
- [x] Add "a commit was dropped" to step 4's red flags → verify: `grep -n "dropped" skills/merge-worktree/SKILL.md` shows it in the red-flag line
- [x] Global rule: an agent-started run counts like a user-started one → verify: lines 9-12 of `dotfiles/home/ai/AGENTS.md` do not contradict
- [x] Fix the 51 `docs-lint` findings in `skills/tokenminator/references/` → verify: `scripts/check --full` shows 0 docs-lint findings and the tokenminator checks pass
- [x] Pin `model: opus` in `skills/review-feature/SKILL.md` → verify: frontmatter has it, `scripts/check --impacted` passes
- [x] E2E in a scratch repo, green and red runs, through headless `claude -p` → verify: green lands with no picker; red stops and pushes nothing
- [x] `scripts/check --full` → verify: all pass
- [x] Pre-commit review: cohesion pass ran on SKILL.md (findings fixed); `/simplify` and bug passes skipped, docs-only diff → verify: no open confirmed findings
- [ ] Show both diffs for approval

## Files touched

- `skills/review-feature/SKILL.md` (frontmatter)
- `skills/merge-worktree/SKILL.md`, `skills/merge-worktree/scripts/merge_worktree.py:508`
- `dotfiles/home/ai/AGENTS.md:11`
- `skills/tokenminator/references/*.md`
- `specs/v008-merge-worktree-without-gate/`
