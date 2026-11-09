# v003: Plan

- [x] Write `skills/research/SKILL.md`: when to run, frame, search, spot-check, write, check, report → verify: under 60 lines; no step duplicates grill-me
- [x] Write `skills/research/scripts/check_research.py`, standard library only → verify: it passes v002's `research.md`
- [x] Write `test_check_research.py` with one fixture per rule → verify: each fixture fails when its rule is removed
- [x] Add the grill-me lines that run the skill and keep `research.md` beside the spec → verify: grill-me self-tests pass
- [x] Register the check; update `README.md` and the `AGENTS.md` table → verify: `scripts/check --full` passes but for known findings
- [x] Simplify, then cohesion, bug and security reviews → verify: confirmed findings fixed

## Files Touched

- `skills/research/SKILL.md`
- `skills/research/scripts/check_research.py` and `test_check_research.py`
- `skills/grill-me/SKILL.md`
- `scripts/checks.json`, `README.md`, `AGENTS.md`
