<!--
Purpose: Routes a diagram to one Mermaid family and defines the shared visual and verification contract.
Type: reference
-->

# Mermaid Diagrams

Audience: the writer, before drawing or editing any diagram.

Choose one family by what the reader must learn. Load only its reference.

| Reader Question | Family | Reference |
| --- | --- | --- |
| What components exist and depend on each other? | Application | [mermaid-application.md](mermaid-application.md) |
| What happens in order across participants? | Runtime | [mermaid-runtime.md](mermaid-runtime.md) |
| How do stored entities relate? | Data | [mermaid-data.md](mermaid-data.md) |
| Which boundary provisions or hosts each resource? | Infrastructure | [mermaid-infrastructure.md](mermaid-infrastructure.md) |

Do not combine families in one diagram. Put runtime order in a sequence
diagram and static structure in a flowchart, even when they describe the same
feature.

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

A yellow box always represents a real boundary: repository, ownership,
deployment, trust, network, environment, or physical location. It never exists
only to arrange nodes.

Every boundary label is left aligned and uses two lines:

```text
<boundary name>
[<TYPE>]
```

Use a fixed-width inline span so Mermaid keeps the label at the left edge of
the boundary. Choose the smallest width that clears the widest row of nodes:

```text
subgraph Boundary["<span style='display:inline-block;width:420px;text-align:left'>Boundary name<br/>[TYPE]</span>"]
```

The family reference defines allowed boundary types. Nodes remain lavender
unless a family defines a data shape.

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

Extract every Mermaid block and render it before handoff.

```bash
bunx --yes @mermaid-js/mermaid-cli -i /tmp/diagram.mmd -o /tmp/diagram.png
```

Fall back to `npx --yes @mermaid-js/mermaid-cli`. Inspect the PNG at its normal
display size. Reject obscured boundary labels, clipped text, crossing edges,
tiny text, excess empty space, or a diagram that needs zooming.
