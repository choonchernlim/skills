# v004: Plan

- [x] Write `skills/merge-worktree/scripts/merge_worktree.py` with `prepare`, `continue`, `land` and `cleanup`, standard library only → verify: each prints JSON with a `status`
- [x] Write `test_merge_worktree.py` against scratch repositories with a bare remote → verify: two worktrees merge, one after a rejected push; each rule's case fails when the rule is removed
- [x] Write `skills/merge-worktree/SKILL.md`: refuse, parent, conflicts, checks and reviews, packet, gate ②, land, report, cleanup → verify: under 70 lines
- [x] Register the check; update `README.md` and the `AGENTS.md` table; mark v004 ready in the v002 command tables → verify: `scripts/check --full` passes but for known findings
- [x] Add the four rules to the dotfiles `home/ai/AGENTS.md` → verify: `nix flake check --impure --no-build` passes
- [x] Simplify, then cohesion, bug and security reviews → verify: confirmed findings fixed

## Files Touched

- `skills/merge-worktree/SKILL.md`
- `skills/merge-worktree/scripts/merge_worktree.py` and `test_merge_worktree.py`
- `scripts/checks.json`, `README.md`, `AGENTS.md`
- `specs/v002-layered-agent-workflow/spec.md`: the Ready column
- dotfiles: `home/ai/AGENTS.md`
