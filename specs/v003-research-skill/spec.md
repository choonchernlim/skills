# v003: Research Skill

A `/research` skill that checks how proven sources solve a design question, and the grill-me line
that runs it. The [v002 design](../v002-layered-agent-workflow/spec.md#research) decided both.

## Shared Understanding

- **One job.** `/research` finds what peer-reviewed studies, surveys, standards, vendor docs and proven practice say about a design question, and keeps only claims a source backs.
- **Two callers.** You run `/research <question>` alone, and grill-me runs it when a decision has prior art: architecture, workflow, data model, algorithm or security.
- **One output.** `research.md` holds one section per sub-question, each finding with a link and an evidence label, a decision scorecard, and the gaps. Inside grill-me it sits beside `spec.md`.
- **The v002 process is the model.** Parallel searches, then a spot-check that opens the cited sources and drops any claim they do not back.
- **A script checks the shape.** `check_research.py` flags a finding with no source, a link with no evidence label, and a scorecard verdict outside the three allowed.

## Assumptions

- Hosts without subagents search one sub-question at a time; the rest of the process holds.
- Library and API questions stay with each library's own docs, not this skill.

## Definition of Done

- `/research` triggers from its description, on its own and from grill-me.
- `check_research.py` passes on v002's `research.md`, and each of its rules has a fixture that fails without it.
- `scripts/check --full` passes but for the known tokenminator docs-lint findings.
