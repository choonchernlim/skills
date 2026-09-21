# Fixture Project

Benign fixture for the tokenminator audit self-test.

## Workflow

Run `scripts/check` before handing work off.

<!-- BEGIN:tokenminator-rules v3 | managed by the tokenminator skill; never edit by hand; refresh with its audit script and --fix-rules-block -->
## Token Discipline

- Run checks with `scripts/check`. Read its summary first, then only the failing check's log.
- Read files in slices with offset and limit. Search first, then open the matching range.
- Never open lockfiles, generated files, or anything under Do Not Read. Ask the package manager instead (`npm ls`).
- Prefer quiet and JSON flags over prose output. Send long output to a file and read only the part you need.
- Hand wide searches to a subagent and keep only its conclusion.
- Ask git for the short form first: `git status --short`, `git diff --stat`, `git log --oneline`.
- Test browsers with the scripted Playwright suite. Open one named screenshot only for a visual judgment.
- Use a browser MCP only to explore an unscripted page once, then turn what you learned into a test.
<!-- END:tokenminator-rules -->

## Where Things Live

| Area | Path |
| --- | --- |
| Check entry point | `scripts/check` |
| Browser tests | `e2e/` |
| Infrastructure | `infra/` |

## Do Not Read

- `package-lock.json`. Use `npm ls` instead.
