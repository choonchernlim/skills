<!--
Purpose: The visual language every Mermaid diagram shares: edges, shapes, titles, future parts, colors and boundaries.
Type: reference
-->

# Mermaid Visual Language

> **Audience:** the writer, before drawing or editing any diagram, with [mermaid.md](mermaid.md).

Every diagram shares these shapes, titles and colors, so a reader learns them once.

## Table of Contents

- [Shared Visual Language](#shared-visual-language)
- [Node Titles](#node-titles)
- [Future Parts](#future-parts)
- [Color](#color)
- [Boundaries](#boundaries)

## Shared Visual Language

### Layout

- Read top to bottom at normal IDE and repository preview width.
- Prefer three siblings abreast; go up to the [size budget](mermaid.md#size-budget) only after
  rendering proves them readable.
- Split a diagram by boundary or phase before text becomes too small to read without zooming.

### Edges

These rules hold in a `graph TD`; the [runtime reference](mermaid-runtime.md) sets sequence arrows.

- Label every edge, quoted, in one to four words: `-->|"validates"|`.
- Use short noun labels and verb-led edges. Put order numbers on edges or messages as `1: text`,
  never on nodes.
- Link only with `-->`, `-.->`, or `==>`, or their [one-character-longer forms](mermaid.md#portable-syntax),
  so every edge reads in one direction.
- Draw one edge per line, so every relationship gets its own label.
- Place every edge label on a straight vertical run, never on a bend, except as the last bullet allows.
  - Mermaid draws a label at its own point halfway down the edge, so the edge bends there whenever
    its two nodes are not aligned.
  - Lengthen that link by one character (`--->`, `===>`, or `-..->`). The bend moves up to the
    source, and the label sits on the straight run below it.
  - Lengthen every edge of a fan-out or fan-in together, so its sibling nodes stay on one row.
  - Lengthen an edge that enters a boundary too, so its label sits above the frame, not over its title.
  - An edge between two boundaries can still bend at its label; accept that rather than reorder the diagram.

### Shapes

- Draw each node in its TYPE's shape from the family reference. The shape repeats the tag, so a
  diagram where every node shares one owner still reads.
- Stack a node that stands for several things, on its own line, wherever it is drawn.
  - Its title ends in a plural noun ("Warehouses") or lists things with "and" or commas.
  - When the plural noun would repeat the tag, the stack alone says "several": a set of search
    tools is a stacked "Search [TOOL]".
  - A cylinder TYPE, such as data or a store, stacks as `id@{ shape: docs, label: "..." }`.
  - Every other TYPE stacks as `id@{ shape: st-rect, label: "..." }`. Mermaid stacks no other
    shape, so a stacked tool or agent loses its own shape, and its tag and color name the type.
- Keep one thing as one flat node, even when it holds many records, with a singular title.
- Title a boundary in the singular, because Mermaid cannot stack a frame.
  - Name the one thing it frames, "Order Service", or the repo or project that holds several,
    such as "shop-prod".

## Node Titles

A title names the thing in plain words; the tag says what kind of thing it is.

### Wording

- Never repeat the tag's noun: "Search [TOOL]", not "Search Tool [TOOL]", and "Planner [AGENT]",
  not "Planner Agent [AGENT]".
- Write words, never a code name: "Order Planner", not `order_planner`, and "Order History", not
  `order-history`. Drop every hyphen, except inside an acronym such as X12-EDI.
- Use Title Case, with joining words such as "and", "of" and "via" in lower case. Keep acronyms
  and product names as written: SDK, API, X12-EDI.
- A `[REPO]` or `[GCP PROJECT]` boundary keeps its real name, such as `shop-prod`, so a reader can
  search for it.

### Identity

- A node's name is its title and its tag together, so "Order [API]" and "Order [DATA]" are two
  things.
- When shortening titles makes another document draw the same relationship, keep it in the
  document that explains it, and [compress the other](mermaid.md#ownership).

## Future Parts

A diagram may show a part that is not built yet, so a reader sees where the design can grow.

- Its title ends in "(Future)", written exactly so: "Fraud Check (Future)".
  - The title rules and the node's cross-file identity judge the words before the suffix.
  - Once built, the part drops the suffix and the `future` class.
- It keeps its TYPE's shape but takes the `future` class instead of an owner's class.
  - The class draws a gray box with a dashed outline, so no reader mistakes it for a running part.
  - The suffix and the class always go together.
- Every edge to or from it is dotted, `-.->` or `-..->`.
  - A diagram with a future part draws no other edge dotted, so a dotted line means only "not built yet".
- A sequence diagram draws no future participant.
- A boundary is never a future part. Frame what exists, and draw the future part inside it.
- Its title links the ADR or guide that describes it, when one exists, never a plan or spec, which may move.
- The legend says `dashed gray = future`.

## Color

Every `graph TD` node takes its owner's color, so a reader sees who owns what
without reading every tag, and the same box reads the same in every diagram.
Color adds to the `[TYPE]` tag; it never replaces it. A sequence diagram
carries the same owner colors as bands, see the
[runtime reference](mermaid-runtime.md#owner-bands). An `erDiagram` stays plain.

| Class | Swatch | Marks | Definition |
| --- | --- | --- | --- |
| `own` | 🟦 | the team that owns this repository | `fill:#2563eb33,stroke:#2563eb` |
| `peer` | 🟩 | another team in the organization | `fill:#0d948833,stroke:#0d9488` |
| `platform` | 🟧 | the organization outside both teams: its shared platforms and systems | `fill:#d9770633,stroke:#d97706` |
| `external` | ⬜ | anything outside the organization: a cloud vendor or a third-party service | `fill:#64748b33,stroke:#64748b` |
| `person` | 🟥 | a human, whoever employs them | `fill:#e11d4833,stroke:#e11d48` |
| `model` | 🟪 | a model call, whoever owns it | `fill:#c026d333,stroke:#c026d3,stroke-width:3px` |
| `boundary` | none | every subgraph: a dashed slate outline over a near-clear fill | `fill:#7d879914,stroke:#7d8799,stroke-dasharray:6` |
| `future` | none | a [future part](#future-parts), whoever will own it: a dashed gray outline over a faint fill | `fill:#6b72801a,stroke:#6b7280,stroke-dasharray:5` |

Each stroke keeps 3:1 contrast on a white and on a near-black page. The four
team owners stay apart under red-green color blindness, and `person` and
`model` differ by shape as well.

- Color every node and every boundary. A plain node has no owner to read.
- Give every `[AGENT]` node the `model` class and every `[PERSON]` node the
  `person` class, unless it is a future part. No other node takes either.
- Give every subgraph the `boundary` class, and no node. Its near-clear fill
  keeps the tinted nodes inside it readable.
- Assign each node one class with a `class id,id name` line, and copy each used
  `classDef` exactly. Never use `:::`, `style`, or `linkStyle`.
- Never color an edge. Line weight and dashes carry edge meaning.
- Never fix a node's text color. Each owner fill is a 20% tint, and `future` fainter, so the
  viewer theme's text color stays readable.
  - JetBrains previews override a fixed label color anyway.
- Follow the diagram directly with one `> **Legend:** *...*` line, so the reader
  meets the key with the colors. It names each palette swatch used, and no
  other, with real owner names.
  - `boundary` has no swatch; each boundary's title names its TYPE.
  - `future` has no swatch; the legend says `dashed gray = future` instead.

```text
> **Legend:** *🟦 Orders team · 🟪 model call*
```

## Boundaries

A boundary is a subgraph. It always represents a real boundary: repository,
ownership, deployment, trust, network, environment, or physical location. It
never exists only to arrange nodes.

Every boundary has a two-line title, its name then its type, and declares its
direction. The name may [link its source](mermaid.md#source-links).

```text
graph TD
  %%{init: ...}%%
  subgraph Boundary["Boundary name<br/>[TYPE]"]
    direction TB
```

- The name holds 24 characters or fewer. Mermaid wraps a longer name and
  hides the extra line behind the first node.
- Without `direction TB`, a boundary with no outside edges renders left to right.
- An edge that enters a boundary from above may cross its centered title.
  Keep the title short so it stays legible.

The family reference defines allowed boundary types.
