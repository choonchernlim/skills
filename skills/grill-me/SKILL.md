---
name: grill-me
description: Interviews the user relentlessly about a plan, design, or coding task until reaching shared understanding, one decision at a time with a recommended answer for each, then records the plan in the repository as a versioned spec and plan pair, in a new worktree when the plan is large, waits for confirmation, and executes it. Use when the user wants to stress-test a plan, "get grilled" on a design, or says "grill me" - and before writing, reviewing, or refactoring any non-trivial code.
---

# Grill Me

Surface every assumption, ambiguity, and tradeoff before any code is written. This biases caution over speed: for a trivial task, skip the interview - but never skip the confirmation gate at the end.

## How to Grill

- **One question at a time.** Wait for the answer before the next question.
- **Resolve dependencies in order** - trunk before leaves.
- **Explore before asking.** If the codebase, docs, or context can answer it, look it up. Ask only what requires the user's intent or judgment.
- **Cite the evidence.** When research backs an option, name its source in the option.
- **Ask via the host's interactive picker** (e.g. `AskUserQuestion` in Claude Code), never as a printed or code-fenced list.
  - At most 4 concrete options, the recommended one first and marked "(Recommended)".
  - Free-form answers are always allowed.
  - With no picker, print a numbered list and let the user reply with a number.

Example - _"How should the parser handle malformed input rows?"_ → **Reject the whole file with a clear error (Recommended)** / **Skip bad rows, log, continue** / **Coerce to defaults**.

## What to Interrogate

1. **Assumptions and interpretations.** State and confirm every silent assumption (inputs, environment, scale, intent). Present multiple plausible interpretations as options - never pick one silently. Name what's confusing instead of guessing.
2. **Scope and simplicity.** Cut or justify anything beyond what was asked: unrequested abstractions, config knobs, error handling for impossible cases. If a simpler approach exists, push back.
3. **Surgical changes.** Identify the exact files and lines to change; every changed line must trace to the request. Flag anything adjacent (formatting, architecture) before touching it.
4. **Success criteria.** Turn goals into verifiable checks: "fix the bug" → "write a failing repro test, make it pass"; "refactor X" → "same tests pass before and after".

## After the Interview: Plan, Record, Confirm

Always do these steps in order, even when the interview was skipped. Run this skill's scripts from the repository root as `python3 <this skill's folder>/scripts/<script>`; each prints JSON. When a script fails, or its `problem` is set, stop and ask how to proceed. Relay any `warnings`.

1. **Draft the plan.** First, when the `research` skill's When to Run fits a key decision, run it once over the answered decisions, and re-ask any it scores Weakened or Contradicted. Without that skill, search and cite sources inline. Then draft:
   - Shared understanding - goal and key decisions, in a few sentences.
   - Assumptions - confirmed, or clearly marked unconfirmed.
   - Numbered steps, each as `[Step] → verify: [check]`.
   - Files touched - exact files (and functions/regions where known).
   - Definition of done - the success criteria, stated verifiably.
   - A plan with more than one concern becomes one plan per concern; ask which goes first.
2. **Choose where.** Run `new_worktree.py --check`. When `offer` is true and the plan expects about 400 changed lines or touches a second top-level folder, ask via picker: **In a new worktree (Recommended)** / **Here**.
3. **Record the spec and plan** before any other change, with a two to six word topic. A host's plan mode blocks writes: there, show the plan, go to step 5, and record right after Proceed. A pair then handed to a new worktree is confirmed again there, now as files.
   - Here: `next_version.py --topic "Order Export"`.
   - In a new worktree: `new_worktree.py --topic "Order Export" --agent <this host, such as claude or codex>`. It reserves the version, creates the worktree, and prints the pair's paths inside its `path`.
   - The pair goes in GitHub Spec Kit's per-feature folder shape with a padded `v` number: `specs/v007-order-export/spec.md` and `plan.md`.
   - The scripts pick the version: a worktree named `vN` or on branch `worktree-vN` keeps N, and anywhere else the next free number is reserved as the git ref `refs/grill-me/vN`. Each `--topic` run uses up a number, so run it once per new pair; never write two specs under one number.
   - Write to the `spec` and `plan` paths printed, revising them when they already exist:
     - `spec` holds the what and why: shared understanding, assumptions, and the definition of done.
     - `plan` holds the how: each step as `- [ ] [Step] → verify: [check]`, then the files touched.
     - When research ran, have it save `research.md` in the same folder, and link it from `spec`.
   - Follow the repository's own spec rules where it has them; when it keeps spec folders elsewhere, pass `--dir` to `next_version.py`.
4. **Hand off** a pair written to a new worktree, so the gate and the work happen there:
   - When `method` is `herdr`, run `handoff` if set, which starts an agent in the worktree's Herdr workspace. Tell the user to switch to workspace `vN`, and stop.
   - Otherwise move with the host's worktree tool, such as Claude Code's `EnterWorktree` with the `path`. With none, print `cd <path>` and stop.
   - A session asked to resume a recorded pair skips the interview, reads both files, and goes to step 5.
5. **Confirm (hard gate).** Point to the `spec` and `plan` files and summarize them in a few lines, so the user reads the files themselves. STOP - no other writes, edits, or commands. Ask via picker:
   - **Proceed (Recommended)** - the only consent. On silence or an ambiguous reply, re-ask.
   - **Give feedback** - revise both files, point to them again, re-confirm.
   - **Cancel** - delete the pair's folder and run `git update-ref -d refs/grill-me/vN`. When the pair has its own worktree, offer to remove it and its `worktree-vN` branch: through `herdr worktree remove` when Herdr made it, else `git worktree remove` from the main checkout.
   - In a host's plan mode, approving the plan to leave plan mode is the Proceed.
6. **Execute and loop.** Run steps in order, verifying each check before the next, and mark each step `- [x]` in the plan file once its check passes. If a check can't be satisfied as planned, stop, grill on the new decision, and revise the recorded pair: run `next_version.py --version N`, where N is the `version` printed, so the version stays the same. Then take it back through step 5. Never silently deviate from the confirmed plan.
   - Apply step 2 to the revised plan. When it now calls for a worktree, offer **Continue in a new worktree**: run `new_worktree.py --version N --carry <the plan's changed paths> <its spec folder>`, then step 4.
