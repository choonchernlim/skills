<!--
Purpose: The PROJECT and FOLDER README profiles, the minimum shape each README takes and the caps it stays under.
Type: reference
-->

# README Profiles

> **Audience:** the writer, when the target is a README.md at any level.

Pick the profile from the folder, not from the existing file. A repo,
package, or runnable-project root takes PROJECT. A directory inside the
source tree takes FOLDER.

## PROJECT Profile

Cap: 200 lines. The first runnable command appears within two screens.

```markdown
<!--
Purpose: Entry point for <project>: what it is, how to run it, where the guides live.
Type: readme-project
-->

# Project Name

One sentence, under 120 characters, saying what this project is.

## Table of Contents

(Only past 100 lines or 5 H2 sections.)

## Introduction

Two or three plain sentences: the problem, who has it, what this does about
it. No identifiers or paths yet.

(one context diagram block, see the mermaid reference)

| Inventory | Current Set |
| --- | --- |

### Reading Paths

| Reader | Read First | Then |
| --- | --- | --- |
| The role, such as a new engineer joining this repository | The first section or guide | The next one |

## Getting Started

### Prerequisites

Tools and versions, one bullet each, with install links.

### Installation

Numbered steps from clone to configured, one runnable command each.

### Usage

The run command, what to expect, and a "Run the Checks" subsection.

## Resources

| Resource | What It Answers |
| --- | --- |
| [docs/README.md](docs/README.md) | Where to start and which guide answers which task |
```

Fill guidance:

- The Introduction routes; depth lives in `docs/`. Every fact here is one
  sentence plus a link to its owner.
- The diagram shows context only: the project as one `SYSTEM` node among its
  users and external systems.
  - The node's Source is `docs/architecture.md`, which draws the inside.
  - Under four nodes, write a sentence instead.
- The Resources table lists the docs index, every guide, and the ADR
  directory, one row each.
  - Contributing, license, and security are rows that link their own files.
- A project that is also one runnable component may add a To Add table, as the FOLDER profile describes.
- No "Adding a Plugin" or similar recipe here. The how-to guide owns it;
  the Introduction links it in one sentence.
- Reading Paths names every reader by role, one row each. The
  [audit](audit.md#audiences) grades against these rows, and asks the user when they are missing.
- A project read by several audiences may add numbered chapters between
  Getting Started and Resources, routed from the Reading Paths table.
  - Each chapter is a short story, then a `Question You Might Ask | Read` table.
  - The chapters link the guides, so Resources keeps only the index, glossary,
    ADRs, and requirements.

## FOLDER Profile

Cap: 80 lines, at most one diagram. A folder README orients a developer who
is already inside the project, so it has no prerequisites or installation.

```markdown
<!--
Purpose: What <folder> owns, its entrypoints, and how to extend it.
Type: readme-folder
-->

# Folder Name

One sentence saying what this folder owns and what it does not.

## Entrypoints

- `file.ts`: what other code imports from it, in one line.

## File Ownership

| File | Owns | Direct Callers |
| --- | --- | --- |

## To Add

| To Add | Declare It In | Then |
| --- | --- | --- |
| A new <thing> | `path/to/registry.ts` | The test or check that proves it works |

## Verification

The commands that prove a change here is safe.
```

Fill guidance:

- Entrypoints: at most 7 bullets. Past that, the folder is two folders.
- To Add answers "where does my change go" for each thing a developer adds here, one row each. It is often the most read section.
- File Ownership lists hand-written runtime files only. Tests, styles, and
  generated artifacts are omitted.
- Cross-cutting facts (team ownership, extension rule, contracts) are one
  sentence plus a link to the owning `docs/` guide, never restated.
- The optional diagram shows this folder's internal dependencies only, never
  a relationship that `docs/architecture.md` already draws.
