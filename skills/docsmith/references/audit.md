<!--
Purpose: The method that grades documentation against its audiences, finds bloat and stale claims, and keeps every guide at grade A+.
Type: reference
-->

# Audit Method

> **Audience:** the writer, before rewriting a set of docs and again before every handoff.

An audit answers one question for each reader: can they get what they came for, quickly, and is it true?
The lint proves the shape. The audit proves the content: density, accuracy, cohesion, and the path a reader takes.

## Table of Contents

- [When to Audit](#when-to-audit)
- [Audiences](#audiences)
- [Per-File Verdicts](#per-file-verdicts)
- [Claim Checks](#claim-checks)
- [Duplication and Owners](#duplication-and-owners)
- [Reader Journeys](#reader-journeys)
- [Grades](#grades)
- [Fixing Without Losing Meaning](#fixing-without-losing-meaning)
- [Report](#report)

## When to Audit

| Trigger | Scope |
| --- | --- |
| Every docsmith run | The touched files, plus every reading path that passes through them |
| A source file a guide links changes | The linked guides, which `doc_impact.py` lists |
| Before a release or the first full audit, and once 10 guides other than ADRs changed since the last (`audit_due.py`) | Every file, every audience |
| A reader reports a doc that misled them | That doc, its owner docs, and its journey |

A full audit's commit subject starts with `docs audit`, and `audit_due.py` prints the last one.
The report goes to the handoff, never into a committed file, because a stored grade goes stale.

## Audiences

Grade nothing until you know who reads the docs. Take the audiences from the project README's Reading Paths table: each row names a reader, their role, and what they read first.

> ⚠️ **Warning:** When the table is missing, or a row does not say what its reader does, stop and ask the user before any grade.

- Ask who reads the docs, what each reader's role is, and what they come to do.
- Offer the four readers below as options, and let the user rename, drop or add readers.
- Write the answer into the README as the Reading Paths table in the same change, so the next run reads it instead of asking again.

| Reader | Came For | Fails When |
| --- | --- | --- |
| Decision-maker | What the system does, why, its design, risks and cost, in ten minutes | They must read code-level detail to find a risk |
| New engineer | Clone, run, and make a first change in one day | A prerequisite or step is missing, hidden, or wrong |
| Integrator | Build a part that plugs in, and get it accepted | The hand-off to the owning team is missing or circular |
| Operator | Deploy, observe, and recover | A symptom has no listed cause and fix |

## Per-File Verdicts

Read every file in scope in full. Give each one verdict and a one-line reason.

| Verdict | When |
| --- | --- |
| Keep | Accurate, dense enough, opens with what and why |
| Trim | Accurate but carries bloat; name what to cut and a rough percentage |
| Merge | Its unique content fits in one paragraph of another file; name the file |
| Split | It serves two audiences or two types and is past its cap |
| Rewrite | The reader cannot tell what it is for, or the prose is a wall |
| Delete | Nothing in it is unique, true, and needed |

Bloat is anything a reader must skip to reach the point. The [style reference](style.md#bloat) lists the patterns and the codes that catch them.
Quote 2 or 3 lines from each of the 5 worst files, so the verdict can be checked.

## Claim Checks

Spot-check 2 or 3 concrete claims per file against the source: paths, commands, ports, variables, limits, and behavior.
Record each wrong claim with the doc line and the source line that disproves it.

- A claim that something is enforced names its enforcer: the check, the hook, or the pipeline step.
  - "A change cannot merge until X" is false unless a merge gate checks X.
- A number is true only if the code that owns it says so. Prefer a link to the code over the number.
- Two docs that state the same fact differently mean at least one is wrong. Check both.
- List every frozen marker (`<!-- frozen: ... -->`) and re-check its value and its reason ([frozen facts](style.md#frozen-facts)).

## Duplication and Owners

Group the facts that appear in more than one file into clusters.
Before any edit, write an owner map: for each cluster, the one file that owns it.
Every other file keeps one sentence and a link, as the [fact-ownership table](guides.md#fact-ownership) says.

| Fact | Owner | Others Link To It |
| --- | --- | --- |
| How a request is authenticated | `security.md` | `architecture.md`, `runtime-flows.md` |

The owner map is also the contract when several writers edit in parallel: one writer per domain folder, and the owner map settles where each fact lands.

## Reader Journeys

Walk each audience's path through the docs as that reader, using only the docs.
Write where they get stuck, with the doc and line.

| Reader | Journey |
| --- | --- |
| Decision-maker | README, then any brief, then the risks. Can they name the top three risks and what each costs? |
| New engineer | Prerequisites, install, run, then a first change in each component. Does every step work as written? |
| Integrator | Build, test, deploy, register, and update a part. Who do they hand off to, and what do they send? |
| Operator | Deploy, roll back, and fix the top symptoms. Is every symptom in the troubleshooting table? |

A hidden prerequisite, such as a hardware or account requirement, moves to the first screen of the journey that needs it.

## Grades

Grade each audience, not each file. The lowest unmet row sets the grade.

| Grade | Every Guide on That Audience's Path Meets This |
| --- | --- |
| A+ | Lint is clean, every journey completes, no checked claim is wrong, and no frozen value lacks a reason |
| A | One journey step needs a second doc that the first does not link |
| B | A claim is wrong or overstated, or one guide opens with detail before its purpose |
| C | A journey stalls, or a fact repeats in three or more files |
| D | A reader must read code to finish a journey |
| F | The docs mislead: a reader who follows them does the wrong thing |

Give each grade a one-sentence reason. Fix everything below A+ before the handoff, or list exactly what blocks it.

An audience earns A+ only after two consecutive fresh audits find no confirmed blocker on its path.
A fresh audit starts from a reader with no memory of the earlier audit or its fixes, so it cannot grade its own repairs.
A confirmed blocker in either audit resets the count to zero.

## Fixing Without Losing Meaning

- Cut a copy of code-owned facts, such as fields, columns, or events, down to what a reader needs to reason, then link the source.
- Never drop a rule, an invariant, or a command. Move it to its owner and leave a link.
- After a cut, check each removed rule still has a home: `git grep` a distinctive phrase from it.
- Merge and move files as the [domain folder rules](guides.md#domain-folders) say, and update the domain index row too.
- Review a large pass twice: one reader for cohesion, and one who checks the changed claims against the source.

## Report

```markdown
## Docs Audit - <scope>

| Audience | Grade | Why |
| --- | --- | --- |

| File | Lines | Verdict | Reason |
| --- | --- | --- | --- |

### Worst Files
### Wrong Claims (doc line, source line)
### Duplication Clusters and Owners
### Journeys: Where Each Reader Gets Stuck
### Frozen Markers to Re-Check
```
