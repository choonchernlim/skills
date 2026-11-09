# v002: Plan

- [x] Record this spec and plan → verify: `specs/v002-layered-agent-workflow/` exists
- [x] Research in parallel: three subagents split questions 1+3, 2, and 4+5 → verify: every question has at least 3 cited sources
- [x] Spot-check a sample of the cited sources and drop any claim a source does not back → verify: no uncited or misattributed claim stays
- [x] Write `research.md` with one section per question and a decision scorecard → verify: docsmith lint reports no SENT, DUP or LINK finding
- [x] Write `spec.md` with the command sheet per layer, the design, the grill-me switch, and the risks → verify: every diagram renders cleanly; every claim links to `research.md`
- [x] Fresh-eyes review of the three artifacts → verify: confirmed findings fixed
- [x] Revise `spec.md` for your final flow, then hand off for review → verify: lint clean except HDR; diagrams render; nothing committed
  - Simplified to `/merge-worktree` and `/review-feature`, `develop` merged at events, three gates, files before gate ①, Herdr, `/research`, and opt-in.

## Build: Grill-me

Built in `.claude/worktrees/v2` on `worktree-v2`, so the live grill-me on `main` was never half edited.

- [x] Let a `worktree-vN` branch hold its version in `next_version.py` → verify: new fixtures fail without the change
- [x] Add `new_worktree.py`: offer check, Herdr or git creation, parent record, reservation release, carry → verify: each rule's fixture fails when the rule is removed
- [x] Rewrite grill-me's After the Interview section: files before gate ①, the worktree offer, hand-off, midway move → verify: each spec rule maps to a line; self-tests pass
- [x] Register the test; update `AGENTS.md` and `README.md` → verify: `scripts/check --full` passes but for the 51 known tokenminator docs-lint findings
- [x] End-to-end in a scratch repository with a remote, outside Herdr → verify: fetch, offer, one-call creation and a midway carry all work
- [x] Simplify, then cohesion, bug and security reviews → verify: confirmed findings fixed, each with a fixture
- [x] You review the diff and approve the commit

## Files Touched

- `specs/v002-layered-agent-workflow/research.md`
- `specs/v002-layered-agent-workflow/spec.md`
- `specs/v002-layered-agent-workflow/plan.md`
- `skills/grill-me/SKILL.md`
- `skills/grill-me/scripts/new_worktree.py` and `test_new_worktree.py`
- `skills/grill-me/scripts/next_version.py` and `test_next_version.py`
- `scripts/checks.json`, `AGENTS.md`, `README.md`
