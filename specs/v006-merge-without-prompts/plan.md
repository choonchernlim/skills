# v006: Plan

- [x] Add `land --no-verify` and the direct-run usage docstring to `merge_worktree.py` → verify: a test with a failing pre-push hook is `refused` without the flag and `landed` with it
- [x] Make `cleanup` drop ignored files and report them in `dropped`; remove `--drop-ignored` → verify: one `cleanup` removes a worktree holding an ignored file; untracked files still refuse
- [x] Mark `merge_worktree.py` executable → verify: `script_runs_directly` passes, and fails without the exec bit
- [x] Update `SKILL.md`: `allowed-tools`, the bare-command rule, the hook-skip picker on a hook-refused `land`, and cleanup with no question → verify: `scripts/check --impacted` passes
- [x] Simplify, then run `scripts/check --full` and the cohesion, bug and security reviews → verify: confirmed findings fixed
- [x] Run `/merge-worktree` end to end in auto mode in a scratch repository → verify: no prompt after gate ②; merge on the remote; worktree and branch gone

## Files Touched

- `skills/merge-worktree/SKILL.md`
- `skills/merge-worktree/scripts/merge_worktree.py`
- `skills/merge-worktree/scripts/test_merge_worktree.py`
