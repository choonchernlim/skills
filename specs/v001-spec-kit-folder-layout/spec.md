# v001: Spec Kit Folder Layout for grill-me

## Shared Understanding

grill-me records every approved plan as a spec and plan pair in GitHub Spec
Kit's per-feature folder shape, without installing Spec Kit:
`specs/vNNN-topic/spec.md` and `specs/vNNN-topic/plan.md`.

- The user never states a version. A linked worktree named `vN` or `vNNN`
  supplies it; anywhere else the script reserves the next free number as the
  create-only git ref `refs/grill-me/vN`, so parallel sessions never share one.
- Numbers keep the `v` prefix and are padded to three digits, so folders sort
  in order: `v007`, `v126`.
- `specs/` sits at the repository root by default, flat, with no archive
  folder; `--dir` serves a repository that keeps its specs elsewhere. Specs are
  history; a repository's guides hold the current truth.
- `--version N` revises an existing pair after a plan changes mid-run.
- Approving a plan to leave a host's plan mode counts as the Proceed, so a
  session started in plan mode runs on without a second confirmation.
- Lightweight: no `tasks.md`, no templates, no constitution. `plan.md` keeps
  checkbox steps.

## Assumptions

- Confirmed: no `tasks.md`; three-digit padding; flat `specs/`; no install;
  versions of 9000 and up stay running lists that never count.
- Moving an existing repository's older spec files into this layout is a separate
  change in that repository.

## Definition of Done

- In a fresh repository the script prints `specs/v001-<topic>/spec.md`; in a
  worktree on branch `worktree/v126` it prints `specs/v126-<topic>/spec.md`.
- `grill-me-selftest` and every other check pass, apart from the 70 docs-lint
  findings that predate this change.
- The review passes leave no open confirmed finding, and the diff is shown
  before any commit.
