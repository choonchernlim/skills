# v001: Plan

- [x] Record this spec and plan → verify: both files exist
- [x] Write `next_version.py` for `specs/vNNN-topic/` with one `--dir` option → verify: self-test passes
- [x] Write the tests, with padding and half-pair cases → verify: `ok` from the self-test
- [x] Update grill-me's description and steps 3 to 5, the README row, the `AGENTS.md` rows, and the `grill-me-selftest` check → verify: `scripts/check --full` passes apart from the older docs-lint findings
- [x] Run `/simplify`, then cohesion, bug and security reviews; fix confirmed findings → verify: no open confirmed finding
- [x] Show the diff for commit approval → verify: nothing committed

## Files Touched

- `skills/grill-me/scripts/next_version.py`
- `skills/grill-me/scripts/test_next_version.py`
- `skills/grill-me/SKILL.md`
- `README.md`
- `AGENTS.md`
- `scripts/checks.json`
- `specs/v001-spec-kit-folder-layout/spec.md` and `plan.md`
