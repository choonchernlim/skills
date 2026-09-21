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
- [Portable Syntax](#portable-syntax)
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

## Portable Syntax

A diagram must render in every viewer a reader opens it in: an IDE preview,
GitHub, and the Azure DevOps repository browser. Those viewers embed different
Mermaid releases, and Azure DevOps reads the first line of a block as the
diagram type. Use only syntax that every one of them accepts.

| Rule | What Breaks Otherwise |
| --- | --- |
| The first line is `graph TD`, `sequenceDiagram`, or `erDiagram`. | Frontmatter or a `%%{init}%%` directive on line one shows "Unsupported diagram type". |
| Draw a flowchart with `graph TD`, never `flowchart TD`. | Azure DevOps documents the `flowchart` keyword as unsupported. |
| `<br/>` is the only HTML in a label. | Other tags and inline styles are stripped or shown as text. |
| Write a step number as `1: text`. | Mermaid 11 parses a label as Markdown, and `1. text` draws "Unsupported markdown: list". |
| Never open a label with `-`, `*`, `+`, `>`, `#`, `1.`, or `1)`, and never use a backtick Markdown string. | The same Markdown parsing. |
| Use `-->`, `-.->`, and `==>` at their normal length. | Azure DevOps rejects lengthened arrows such as `---->`. |
| Link nodes, never a boundary. | Azure DevOps rejects an edge that starts or ends on a subgraph. |
| Never set configuration, themes, colors, styles, or classes. | Each renderer supplies its own theme in light and dark mode. |

The local renderer runs the newest Mermaid, so a clean PNG does not prove
portability. The lint enforces this table; trust it over the render.

## Shared Visual Language

- Read top to bottom at normal IDE and repository preview width.
- Use short noun labels and verb-led edges.
- Put order numbers on edges or messages as `1: text`, never on nodes.
- Use rectangles for actors and services, cylinders for persisted data, and parallelograms for APIs.
- Keep one connected graph per block.
- Prefer three siblings abreast; four is the maximum after rendering proves they remain readable.
- Split by boundary or phase before text becomes too small to read without zooming.

## Boundaries

A boundary is a subgraph. It always represents a real boundary: repository,
ownership, deployment, trust, network, environment, or physical location. It
never exists only to arrange nodes.

Every boundary has a plain one-line title and declares its direction. Its
type goes in the Node table, as a `Name [TYPE]` row above the node rows:

```text
graph TD
  subgraph Boundary["Boundary name"]
    direction TB
```

```text
| Node | Source |
| --- | --- |
| Boundary name [TYPE] | - |
```

- A title holds the name only, in 24 characters or fewer. Mermaid wraps a
  longer title and hides its second line behind the first node.
- The title has no `[TYPE]`, no `<br/>`, and no markup, so it needs no
  configuration to make room for it.
- Without `direction TB`, a boundary with no outside edges renders left to right.
- An edge that enters a boundary from above may cross its centered title.
  Keep the title short so it stays legible.

The family reference defines allowed boundary types.

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
