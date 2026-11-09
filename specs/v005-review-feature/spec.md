# v005: Review Feature

A `/review-feature` skill that reviews everything merged into a feature branch since its last
review, as one change, before the pull request. The
[v002 design](../v002-layered-agent-workflow/spec.md#review-feature) decided the flow.

## Shared Understanding

- **Runs in the feature checkout**, on the feature branch, after the worktrees you want in the pull request have merged.
- **One script, four commands.**
  - `start` catches the branch up with its remote, merges the remote parent, and prints the range to review.
  - `continue` concludes a resolved conflict with `Clash-resolved:` trailers; `abort` backs out.
  - `finish` commits the staged fixes, pushes leased on the remote commit it started from, and moves the marker.
- **The range** runs from the `refs/reviewed/<branch>` marker to HEAD. With no marker, it starts where the branch left its parent.
- **Reviewers.** Simplify and architecture always run. Dead code joins when the range removes lines of code, docs when it edits documentation.
- **Gate ③.** The fixer applies confirmed findings and shows the diff with every `Clash-resolved:` line in the range. Approval commits, pushes and moves the marker.
- **No unpushed work of yours.** `start` refuses local commits it did not make, so catching up merges only the remote and its own unpushed merges. Its own commits carry a `Review-feature:` trailer.
- **Dotfiles rule.** `start` may make its merges locally; approving gate ③ approves that one fixes commit and the push of the feature branch, merges included.

## Assumptions

- The marker is a local ref: each clone reviews from its own last review.
- The feature branch and its parent were set up as `/merge-worktree` expects, with `branch.<feature>.parent` stored or asked once.

## Definition of Done

- A feature with two merged worktrees is reviewed, fixed and pushed in a scratch repository, and a second review starts at the marker.
- Each refusal, conflict phase and push path has a self-test case that fails without its rule.
- `scripts/check --full` passes but for the known tokenminator docs-lint findings, and the dotfiles flake check passes.
