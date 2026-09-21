<!--
Purpose: Routes a diagram to one Mermaid family and its owner file, and defines the shared visual and verification contract.
Type: reference
-->

# Mermaid Diagrams

Audience: the writer, before drawing or editing any diagram.

## Table of Contents

- [Families](#families)
- [Ownership](#ownership)
- [Diagram Block](#diagram-block)
- [Shared Visual Language](#shared-visual-language)
- [Boundaries](#boundaries)
- [Size Budget](#size-budget)
- [Render and Inspect](#render-and-inspect)

## Families

Choose one family by what the reader must learn. Load only its reference.

| Reader Question | Family | Owner File | Reference |
| --- | --- | --- | --- |
| What components exist and depend on each other? | Application | `docs/architecture.md` | [mermaid-application.md](mermaid-application.md) |
| What happens in order across participants? | Runtime | `docs/runtime-flows.md` | [mermaid-runtime.md](mermaid-runtime.md) |
| How do stored entities relate? | Data | `docs/data-model.md` | [mermaid-data.md](mermaid-data.md) |
| Which boundary provisions or hosts each resource? | Infrastructure | `docs/infrastructure.md` | [mermaid-infrastructure.md](mermaid-infrastructure.md) |

Do not combine families in one diagram. Put runtime order in a sequence
diagram and static structure in a flowchart, even when they describe the same
feature.

## Ownership

An owner file holds only its own family. A topic guide, such as
`docs/authentication.md`, may use any family, one diagram per section.

- The project README draws the context: the project as one `SYSTEM` node.
- The owner file draws the system-wide overview inside that node.
- A topic guide draws the zoom-in: it expands one overview edge into the
  nodes and messages between its two ends.
- A relationship is drawn in one file. Every other file links to that diagram.
- One title maps to one source in every diagram.
- One component keeps one title in every diagram `[judgement]`.

The lint fails a family in the wrong owner file (`VIEW`), a relationship
redrawn in a second file (`DUP`), and a title with two sources (`NODE`). It
reports every other mechanical rule in this reference as `MMD`.

## Diagram Block

Every diagram appears in this order:

1. One lead sentence states what the reader will learn.
2. One fenced `mermaid` block contains one connected idea.
3. A numbered list explains numbered messages or edges.
4. A `Node | Source` table maps every node or entity to its owner.

Use `-` when a node is a person, external system, or concept without a source
in the repository. Never use Mermaid `click` directives.

## Shared Visual Language

- Read top to bottom at normal IDE and repository preview width.
- Use short noun labels and verb-led edges.
- Put order numbers on edges or messages, never on nodes.
- Use rectangles for actors and services, cylinders for persisted data, and parallelograms for APIs.
- Keep one connected graph per block.
- Prefer three siblings abreast; four is the maximum after rendering proves they remain readable.
- Split by boundary or phase before text becomes too small to read without zooming.

## Boundaries

A boundary is a subgraph. It always represents a real boundary: repository,
ownership, deployment, trust, network, environment, or physical location. It
never exists only to arrange nodes.

A flowchart with a boundary opens with this frontmatter, unchanged. Every
boundary uses a left-aligned two-line label and declares its direction:

```text
---
config:
  flowchart:
    subGraphTitleMargin:
      top: 4
      bottom: 32
---
flowchart TD
  subgraph Boundary["<span style='display:inline-block;width:480px;text-align:left'>Boundary name<br/>[TYPE]</span>"]
    direction TB
```

| Nodes Abreast in the Boundary | Span Width |
| --- | ---: |
| 1 or 2 | `480px` |
| 3 | `720px` |
| 4 | `960px` |

- The narrow label sits top left, clear of every edge that enters from above.
- The margin makes room for the second label line.
- A span narrower than its boundary drifts right into the entry edges.
- Without `direction TB`, a boundary with no outside edges renders left to right.
- A diagram without a boundary has no frontmatter.

The family reference defines allowed boundary types. Never set colors or
styles; the theme of each renderer supplies them in light and dark mode.

## Size Budget

| Limit | Value |
| --- | ---: |
| Flowchart nodes | 4 to 12 |
| Siblings abreast | 4 |
| Sequence participants | 7 |
| Sequence messages | 12 |
| Connected graphs | 1 |

Under four flowchart nodes, write a sentence. Over a limit, split the diagram
and link the two explanations.

## Render and Inspect

Render every Mermaid block in the touched files before handoff. Run the
script; do not read it.

```bash
python3 scripts/render_mermaid.py docs/*.md README.md
```

The script prints one PNG path per diagram. Open each PNG at its normal
display size. The script renders at double scale so a thin line through a
label is visible.

Reject an edge or node that touches a boundary label, clipped text, crossing
edges, tiny text, excess empty space, or a diagram that needs zooming.
