# v004: Merge Worktree

A `/merge-worktree` skill that merges a finished worktree into its remote feature branch after
gate ②, and the user-level AGENTS.md rules that go with it. The
[v002 design](../v002-layered-agent-workflow/spec.md#merge-worktree) decided the flow.

## Shared Understanding

- **Runs in the worktree.** `/merge-worktree` runs where the work was done, and pushes to the remote feature branch, which no folder has checked out.
- **One script, five commands.**
  - `prepare` builds a fresh base, rebases the worktree onto it, and prints the packet's facts.
  - `continue` concludes a resolved conflict, with a `Clash-resolved:` trailer for each judgment call; `abort` backs out.
  - `land` merges the approved tip with `--no-ff` and pushes, leased on the remote commit the packet was built from.
  - `cleanup` removes the worktree and its branch.
- **The fresh base** is the remote feature branch with its remote parent merged in, so `develop` arrives at each merge.
- **Branches are found, never named.**
  - The feature branch comes from `branch.worktree-vN.parent`, falling back to the main checkout's branch.
  - The feature's parent comes from `branch.<feature>.parent`. When it is unset, the skill asks once, suggesting the remote's default branch, and stores the answer.
- **Gate ② is a review packet.** The agent runs the project's checks and the review passes, then shows the packet and waits.
  - Feedback: the agent revises and commits, then runs `prepare` again.
  - Approve: `land`.
- **A rejected push loses nothing.** Another merge got there first, so `prepare` builds a new base and the packet is shown again.
- **Cleanup goes last**, after the agent has reported. Under Herdr, it removes the workspace through Herdr, which ends the agent's own pane.
- **Dotfiles rules.** Four rules in `home/ai/AGENTS.md`: merge shared branches, gate ② covers its push, free commits in a grill-me worktree, and a packet counts as the diff.

## Assumptions

- The feature branch has an upstream on a remote; a feature never pushed is refused.
- A worktree branch is linear. A plain rebase drops merge commits inside it.
- Git 2.32 or later, for `git commit --trailer`; the script refuses older versions.

## Definition of Done

- Two worktrees merge in a scratch repository, one after a rejected push, in the self-test.
- Each refusal, conflict phase and cleanup path has a self-test case that fails without its rule.
- `scripts/check --full` passes but for the known tokenminator docs-lint findings.
- The dotfiles rules are written and the flake check passes. `home/` is live, so no rebuild is needed.
