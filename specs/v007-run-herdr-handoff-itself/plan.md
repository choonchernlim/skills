# Plan

- [x] Reword the last sentence of step 3 so "confirmed again there" means the gate runs in the new worktree's session, not here → verify: `rg "confirmed" skills/grill-me/SKILL.md`
- [x] Reword the `herdr` bullet of step 4: run `handoff` yourself with the shell tool right after writing the pair, never print it for the user, print it with the error only on failure → verify: read the bullet
- [x] Run the repo checks → verify: `scripts/check --impacted`, then `scripts/check --full`

## Files touched

- `skills/grill-me/SKILL.md` (step 3 last sentence, step 4 first bullet)
