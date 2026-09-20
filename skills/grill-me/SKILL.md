---
name: grill-me
description: Interviews the user relentlessly about a plan, design, or coding task until reaching shared understanding, one decision at a time with a recommended answer for each, then writes a plan and waits for confirmation before executing. Use when the user wants to stress-test a plan, "get grilled" on a design, or says "grill me" - and before writing, reviewing, or refactoring any non-trivial code.
---

# Grill Me

Surface every assumption, ambiguity, and tradeoff before any code is written. This biases caution over speed: for a trivial task, skip the interview - but never skip the confirmation gate at the end.

## How to Grill

- **One question at a time.** Wait for the answer before the next branch.
- **Resolve dependencies in order** - trunk before leaves.
- **Explore before asking.** If the codebase, docs, or context can answer it, look it up. Ask only what requires the user's intent or judgment.
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

## After the Interview: Plan, Display, Confirm

Always do these steps in order, even when the interview was skipped:

1. **Write the plan** as regular message text:
   - Shared understanding - goal and key decisions, in a few sentences.
   - Assumptions - confirmed, or clearly marked unconfirmed.
   - Numbered steps, each as `[Step] → verify: [check]`.
   - Files touched - exact files (and functions/regions where known).
   - Definition of done - the success criteria, stated verifiably.
2. **Display the full plan** every time it's created or revised. Never say "plan created" without showing its contents.
3. **Confirm (hard gate).** STOP - no writes, edits, or commands. Ask via picker:
   - **Proceed (Recommended)** - the only consent. On silence or an ambiguous reply, re-ask.
   - **Give feedback** - revise, re-display, re-confirm.
   - **Cancel** - make no changes.
4. **Execute and loop.** Run steps in order, verifying each check before the next. If a check can't be satisfied as planned, stop, grill on the new branch, and take the revised plan back through steps 1-3. Never silently deviate from the confirmed plan.
