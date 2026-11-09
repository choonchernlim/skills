# v005: Plan

- [x] Write `skills/review-feature/scripts/review_feature.py` with `start`, `continue`, `abort` and `finish`, standard library only → verify: each prints JSON with a `status`
- [x] Write `test_review_feature.py` against scratch repositories with a bare remote → verify: a reviewed range moves the marker; each rule's case fails when the rule is removed
- [x] Write `skills/review-feature/SKILL.md`: start, conflicts, reviewers by trigger, fixer, gate ③, finish → verify: under 70 lines
- [x] Register the check; update `README.md` and the `AGENTS.md` table; mark v005 ready in the v002 command table → verify: `scripts/check --full` passes but for known findings
- [x] Add the gate ③ rule to the dotfiles `home/ai/AGENTS.md` → verify: `nix flake check --impure --no-build` passes
- [x] Simplify, then cohesion, bug and security reviews → verify: confirmed findings fixed

## Files Touched

- `skills/review-feature/SKILL.md`
- `skills/review-feature/scripts/review_feature.py` and `test_review_feature.py`
- `scripts/checks.json`, `README.md`, `AGENTS.md`
- `specs/v002-layered-agent-workflow/spec.md`: the Ready column
- dotfiles: `home/ai/AGENTS.md`
