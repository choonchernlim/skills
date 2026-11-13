# Run the Herdr handoff itself

## Shared understanding

In grill-me step 4, when `new_worktree.py` returns `method: herdr` with `handoff`
set, agents sometimes print the command for the user instead of running it (seen
in a real repo on Sonnet 5.5, after leaving plan mode). The agent cited step 3,
"confirmed again there", as the reason. `SKILL.md` must say that the agent runs
`handoff` itself with its shell tool right after writing the pair, that the
step 3 phrase means the gate runs in the new worktree's session, and that the
command is printed only when it fails, with the error.

## Assumptions

- Confirmed by the request: wording change in `skills/grill-me/SKILL.md` only.
- No script change, so no new fixture.

## Definition of done

- Step 3 and step 4 of `skills/grill-me/SKILL.md` state the three points above.
- `scripts/check --full` passes.
