<!--
Purpose: The docs/ guide roles, the profile for each Diátaxis type, the index and glossary shapes, and which guide owns which fact.
Type: reference
-->

# Docs Guides

> **Audience:** the writer, when the target is any file under `docs/` other than an ADR.

The README routes; `docs/` holds the depth. Each guide has exactly one type
and one topic. Generate only the roles that have content today; never
scaffold an empty guide so the set looks complete.

## Table of Contents

- [Roles](#roles)
- [Domain Folders](#domain-folders)
- [Type Profiles](#type-profiles)
- [Index Profile](#index-profile)
- [Domain Index Profile](#domain-index-profile)
- [Glossary Profile](#glossary-profile)
- [Brief Profile](#brief-profile)
- [ADR Start Here](#adr-start-here)
- [Fact Ownership](#fact-ownership)

## Roles

| Role | File | Type |
| --- | --- | --- |
| Index | `docs/README.md` | `index` |
| Glossary | `docs/glossary.md` | `glossary` |
| Brief | `docs/brief.md` | `explanation`, see the [brief profile](#brief-profile) |
| Architecture | `docs/architecture.md` | `explanation` |
| Runtime flows | `docs/runtime-flows.md` | `explanation` |
| Data model | `docs/data-model.md` | `reference` |
| Infrastructure | `docs/infrastructure.md` | `explanation` |
| Topic guide | `docs/<topic>.md` | `explanation` |
| Contracts | `docs/contracts.md` | `reference` |
| Operations | `docs/operations.md` | `how-to` |
| Task playbook | `docs/<task>-playbook.md` | `how-to` |
| Requirements | `docs/requirements.md` | `requirements`, see [requirements.md](requirements.md) |
| Decisions | `docs/adrs/` | `adr`, see [adr.md](adr.md) |
| Decision index | `docs/adrs/README.md` | `index`, one row per ADR, no line cap, a [Start Here](#adr-start-here) table past 30 ADRs |

When a repo satisfies a role under another name, rename that file to the
canonical name and fix its inbound links. The lint finds an owner file by name.

Architecture, runtime flows, data model, and infrastructure are the four
viewpoints. Each owns one diagram family, listed in the
[mermaid reference](mermaid.md#families), and draws the system-wide overview.

A topic guide owns one cross-cutting subject in full, such as
`docs/authentication.md`. It may use any diagram family.

- A viewpoint file spends one node or edge and one linked sentence on the topic.
- The topic guide never repeats an overview relationship; it expands one.
- Create a topic guide when a subject needs detail from two or more viewpoints.

## Domain Folders

Once `docs/` outgrows one screen of guides, group them into domain folders,
such as `docs/orders/` and `docs/operations/`. A domain is an area of the
product or of the work, never a Diátaxis type: its folder holds every how-to,
reference, and explanation about that area.

- The index, glossary, brief, requirements, and `adrs/` stay at the `docs/` root.
- A role file keeps its canonical name inside its domain, such as
  `docs/architecture/runtime-flows.md`. The lint finds it there by name.
- Each domain folder has a `README.md` of type `index`, in the
  [domain index profile](#domain-index-profile).
- A guide lives in exactly one domain. When two fit, pick the one whose
  readers change the code it describes, and link from the other.
- Move a guide with `git mv`, then fix every inbound link in the same change.

## Type Profiles

Every guide starts the same way, then follows its type.

```markdown
<!--
Purpose: <one sentence>.
Type: <how-to | reference | explanation>
-->

# Guide Title

> **Audience:** <who reads this> to <answer which question>.

One to three plain sentences: what this guide covers and why a reader needs it.
No identifiers yet.

## Table of Contents

(Only past 100 lines or 5 H2 sections.)
```

| Type | Contains | Never Contains |
| --- | --- | --- |
| `how-to` | Goal line, prerequisites, numbered steps with one command each, verification. | Background, rationale, field tables. One sentence of why per step, then a link. |
| `reference` | Tables, field by field. Constraints, defaults, owners. | Procedures, narrative, advice. |
| `explanation` | One diagram block per section, then at most two short paragraphs. | Commands, field tables, step lists other than the diagram's own. |

When a paragraph in a how-to starts explaining, it moves to the explanation
guide and leaves a link. When a reference starts instructing, the steps move
to the how-to guide.

## Index Profile

Cap: 120 lines. Three sections, in this order, after an optional Domains table.

```markdown
## First Week

1. Read [architecture.md](architecture.md). You can name the deployments and who owns each.
2. Read [glossary.md](glossary.md). You can use every domain noun correctly.
3. Read [runtime-flows.md](runtime-flows.md). You can trace one request end to end.
4. Run the checks in the [README](../README.md). You can prove the project is green.

## By Task

| Task | Start Here |
| --- | --- |

## Decisions and History

| Location | Purpose |
| --- | --- |
```

With domain folders, a `## Domains` table (Domain, Covers) comes first and
links each domain README; By Task rows then point into the domains.
The First Week list has 4 to 6 items, each "read X, then you can Y". The
index does not repeat the Resources table from the root README; it links to
it. Historical folders (`specs/`, `plans/`) get one row each and a sentence
saying the current guides win on conflict.

## Domain Index Profile

Cap: 120 lines. A domain folder's `README.md` routes inside that domain only.

```markdown
# Orders

> **Audience:** anyone looking for a guide about taking and fulfilling orders.

## Guides

| Guide | Type | Read It To |
| --- | --- | --- |
| [order-flow.md](order-flow.md) | explanation | Trace one order from cart to shipment |
```

List every guide in the folder, one row each, in reading order. The root
index links each domain folder by its README and never repeats a domain's
guide table; its By Task rows may still link one guide each.

## Glossary Profile

One alphabetical table, no other sections. No cap.

```markdown
| Term | Meaning | Owning Doc |
| --- | --- | --- |
| Order token | The opaque value that identifies one accepted order. | [contracts.md](contracts.md#order-token) |
```

Meaning is one sentence under 20 words. The term is the canonical noun;
every other document uses it and links here instead of redefining it.

## Brief Profile

Optional: write one only when the project's decision-makers want it, and never add one unasked. Cap: 120 lines. The brief gives a decision-maker the whole system in ten minutes: what it does, why, how the design works, the top risks, the cost, and how mature each part is.

- Every section is two to four sentences, then a link to the guide that owns the detail.
- Risks and maturity are tables with a status emoji, so a reader scans them first.
- It states no fact the owner guide does not hold, and adds no new ones.
- When one exists, the README's Reading Paths row for decision-makers lists it first.

## ADR Start Here

A decision index past 30 ADRs opens with a `## Start Here` table of 5 to 12 rows: the decisions a newcomer needs to read the code.
Each row is one ADR and the question it answers. Pick current decisions that shape the most code, never superseded ones.

## Fact Ownership

The owner of each category of fact, for the
[one home per fact](style.md#one-home-per-fact) rule:

| Fact | Owner |
| --- | --- |
| Extension recipe (how to add a thing) | The task playbook |
| Project context: users and external systems | The project README |
| Components, dependencies, team and deployment ownership | `architecture.md` |
| Order of events across components | `runtime-flows.md` |
| Stored entities and their relationships | `data-model.md` |
| Provisioning, hosting, and network boundaries | `infrastructure.md` |
| Every detail of one cross-cutting subject | That subject's topic guide |
| Troubleshooting symptoms | `operations.md` |
| Environment variables and ports | `operations.md` |
| Payload fields | `contracts.md` |
| Source map of a directory | That directory's folder README |
| Definitions | `glossary.md` |
| Requirement statements | `requirements.md` |
| Why a decision was made | The ADR |
| What the system is, its design, risks and cost, for decision-makers | `brief.md`, which only links the owners |
