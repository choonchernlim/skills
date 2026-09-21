# Skills Repository

Agent skills, one folder each. Nothing is built or published; a skill is
Markdown plus standard-library Python scripts.

## Project Rules

- This checkout is live: the author's agents load skills straight from it, so
  an edit to a skill takes effect at once. Never leave a skill half edited.
- Keep every skill project agnostic. Templates, examples, and fixtures use
  invented names, never names from a real repository.
- Scripts use the Python standard library only.
- `README.md` and each skill's reference files follow the docsmith house
  style. The `docs-lint` check enforces it.
- A rule change in a script needs a fixture that proves it.
- Run `scripts/check --impacted` while working and `scripts/check --full`
  before handing work back. Exit 2 means the environment is not ready.
- Run a skill's script; do not read it unless the task is to change it. To
  change one, run `scripts/outline <file>` first, then read only the range
  you need: the audit and lint scripts cost over 10,000 tokens each to open.

<!-- BEGIN:tokenminator-rules v3 | managed by the tokenminator skill; never edit by hand; refresh with its audit script and --fix-rules-block -->
## Token Discipline

- Run checks with `scripts/check`. Read its summary first, then only the failing check's log.
- Read files in slices with offset and limit. Search first, then open the matching range.
- Never open lockfiles, generated files, or anything under Do Not Read.
- Prefer quiet and JSON flags over prose output. Send long output to a file and read only the part you need.
- Hand wide searches to a subagent and keep only its conclusion.
- Ask git for the short form first: `git status --short`, `git diff --stat`, `git log --oneline`.
<!-- END:tokenminator-rules -->

## Where Things Live

| What | Path | Check |
| --- | --- | --- |
| Install and usage guide | `README.md` | docsmith lint |
| Docs skill | `skills/docsmith/SKILL.md` | `skills/docsmith/scripts/test_lint_docs.py` |
| Docs skill rules, one file per topic | `skills/docsmith/references/` | docsmith lint |
| Interview skill, one file | `skills/grill-me/SKILL.md` | none |
| Token audit skill | `skills/tokenminator/SKILL.md` | `skills/tokenminator/scripts/test_audit_tokens.py` |
| Token audit playbooks, one per area | `skills/tokenminator/references/` | docsmith lint |
| Templates the token audit skill ships | `skills/tokenminator/assets/` | `skills/tokenminator/scripts/test_assets.py` |
| Check that this table's paths exist | `scripts/test_agents_md.py` | itself |
| Check entry point, one line per check | `scripts/check` | runs all of the above |
| The checks it runs, as data | `scripts/checks.json` | `scripts/check doctor` |

On a `[FAIL]` line, read the findings printed under it first. Open
`.check/summary.json` or that check's log under `.check/logs/` only for more.

`scripts/check`, `scripts/outline`, `scripts/read_guard.py`, and
`scripts/test_agents_md.py` are unedited copies of the templates. Change the
template, then copy it again; `tokenminator-assets` fails when they differ.

## Do Not Read

- `skills/docsmith/scripts/fixtures/` and `skills/tokenminator/scripts/fixtures/`:
  test inputs. Open only the fixture a failing self-test names.
- `skills/.trash/` and every other git-ignored folder under `skills/`: agent
  runtime state, not part of this project.
- `.idea/`: IDE settings.
