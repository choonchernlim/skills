---
name: merge-worktree
description: Merges a finished git worktree branch into the remote feature branch it was cut from, as one reviewed --no-ff merge with the parent branch's latest changes, then removes the worktree. Use when the work in a worktree is done, or when asked to merge, land or finish a worktree.
allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/merge_worktree.py *)
---

# Merge Worktree

Bring one finished worktree into its feature branch as a single reviewed merge. Run it inside the worktree; it pushes to the remote feature branch, so the feature checkout is never touched.

Run `<this skill's folder>/scripts/merge_worktree.py <command>` as the whole Bash command, so the skill's pre-approval matches it: no `python3`, `cd`, environment variables, pipes or redirects; `--worktree <path>` acts on another folder. Single-quote `--title` and `--clash` values. Each command prints JSON with a `status`; relay any `problem` and `warnings`. Running this skill approves its one merge commit, its push and the cleanup, and nothing else; it asks for approval only when step 4 finds a red flag, and any later run needs a new approval. Skipping the pre-push hook needs its own yes.

## Steps

1. **Prepare.** Run `prepare`, then act on its `status`:
   - **refused** - relay the `problem` and any `files`, and stop. Uncommitted files were never reviewed; ask whether to commit or remove them.
   - **needs-parent** - ask via picker which branch the feature merges from, the `suggest`ed one first and marked "(Recommended)" when there is one. Run `prepare --parent <branch>`; it is stored for next time.
   - **conflict** - go to step 2.
   - **merged** - the work is already in the feature branch; go to step 6.
   - **ready** - go to step 3.
2. **Resolve conflicts.** `phase` says whether the parent branch is merging into the base or the worktree is rebasing onto it.
   - Inside the plan's scope, the plan decides. Elsewhere, keep the feature branch's behavior.
   - Check each file in `replayed` too: `rerere` reapplied a recorded resolution there. In the `base` phase, give its `--clash` note again, since each run rebuilds the base.
   - Stage each file, then run `continue` with one `--clash '<path>: <why>'` per judgment call. Repeat until `ready`.
   - When a conflict needs the user's intent, run `abort` and ask.
3. **Check and review.** On the rebased branch, run the project's checks and the review passes your instructions require.
   - Fix confirmed findings and commit, then run `prepare` again so the packet matches HEAD.
4. **Report, or stop on a red flag (gate ②).** One message, so the user can judge the worktree, or read the record of a clean run, without opening anything else:
   - where it goes: `feature`, pushed to `target`, and the `tip` to land
   - the spec and plan in `pair`, or that none changed; say so when `open_steps` is not zero
   - the size: `commits`, `added` and `removed` lines, and the `files`
   - `parent_commits` arriving from the parent branch
   - the check results, and the review findings fixed and still open
   - every `clashes` line, word for word
   - how to verify it: what to run or open, and what the user should see

   Red flags: a check failed or did not run, a review finding is still open, `clashes` is not empty, `open_steps` is not zero, or a `continue` warned that a conflict resolution dropped a commit.
   - **No red flag** - invoking the skill was the approval. Print the packet and go to step 5 without asking.
   - **Any red flag** - name it, then STOP. Ask via picker:
     - **Approve and merge** - the only consent once a red flag shows. On silence or an ambiguous reply, re-ask.
     - **Give feedback** - revise, commit, and go back to step 1.
     - **Cancel** - push nothing. The worktree stays, rebased onto the base.
5. **Land.** Run `land --tip <the packet's tip> --title '<topic from the spec>'`.
   - **rejected** - another merge reached the feature branch first. Go back to step 1, say what changed in the new packet, and apply step 4 again.
   - **stale** - the worktree is not the packet's tip. Go back to step 1.
   - **refused** - relay the `problem`. The packet still stands, so `land` may be retried once the cause is fixed. When it carries `hook`, the pre-push hook refused the push: relay its output and ask via picker, **Fix the cause (Recommended)** / **Land, skipping the hook**. Only that answer reruns `land` with `--no-verify`; on silence or an ambiguous reply, re-ask. Never turn hooks off any other way.
   - **landed** - report the `merge` commit and where it was `pushed`. The feature checkout is now behind; `git pull --ff-only` there catches it up.
6. **Clean up, last, without asking.** Report first: `cleanup` removes this folder with its ignored files, and under Herdr it closes this workspace with its agent. Relay `dropped` and `dropped_count` as soon as it returns; under Herdr this agent may close next.
   - A host that moved into the worktree, such as Claude Code after `EnterWorktree`, leaves it first (`ExitWorktree` with keep), then runs `--worktree <path> cleanup`.
   - **removed** - the worktree and its branch are gone.
   - **removing** - Herdr is closing the workspace; the branch goes after it, and the result lands in `log`.
   - **refused** - nothing was removed; relay the `problem` and `files`.

The fresh base is the remote feature branch with its remote parent merged in, so the parent's changes arrive at every merge. The script finds both branches in git config; none is named here.
