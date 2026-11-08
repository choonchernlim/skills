<!--
Purpose: Routes a diagram to one Mermaid family and its owner file, and defines the portable syntax and the verification contract.
Type: reference
-->

# Mermaid Diagrams

> **Audience:** the writer, before drawing or editing any diagram.

Load [mermaid-visual.md](mermaid-visual.md) with this file: it holds the shapes, titles, colors and
boundaries every diagram shares.

## Table of Contents

- [Families](#families)
- [Ownership](#ownership)
- [Diagram Block](#diagram-block)
- [Portable Syntax](#portable-syntax)
- [Flowchart Line](#flowchart-line)
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
- A relationship is drawn in one file. Every other file compresses it to one labeled edge and links
  that diagram from its lead sentence or numbered list.
- One name, title and tag together, maps to one source in every diagram, nodes and boundaries apart.
- One component keeps one title in every diagram `[judgement]`.

The lint fails a family in the wrong owner file (`VIEW`), a relationship
redrawn in a second file (`DUP`), and a title with two sources (`NODE`). It
reports every other mechanical rule in this reference and
[mermaid-visual.md](mermaid-visual.md) as `MMD`.

## Diagram Block

Every diagram appears in this order:

1. One lead sentence states what the reader will learn.
2. One fenced `mermaid` block contains one connected idea.
3. Under a `graph TD`, one `> **Legend:** *...*` line names each [color](mermaid-visual.md#color) swatch and each line style to learn, such as a thick line `[judgement]`.
   Band titles key a sequence diagram.
4. A numbered list explains numbered messages or edges.
5. Under a sequence or ER diagram, one `> **Sources:** *...*` line [links each participant or entity](#source-links) that has a source.

### Source Links

A node or boundary with a source in a repository links it from its title. The
whole title sits inside one link, and a globe after it marks the box as one to
click:

```text
Api["<a href='../src/api/orders.ts'>Order 🌐</a><br/>[API]"]
subgraph Web["<a href='../src/web/README.md'>Web App 🌐</a><br/>[DEPLOYMENT]"]
```

- Link a file in this repository with a relative path, as in any Markdown
  link. Link anything else, such as another repository, with a full `https://` URL.
- Link a file, never a folder: an IDE preview cannot open a folder, so the
  click does nothing. For a folder, link its README or its entry point.
- Use single quotes inside the label. A node with no source, such as a person
  or a vendor service, keeps a plain title.
- A sequence participant or ER entity cannot hold a link, so its diagram
  lists them on its Sources line:

```text
> **Sources:** *Order [orders.ts](../src/api/orders.ts) · Planner [planner.ts](../src/planner/planner.ts)*
```

- Each item is the title, a space, and its link. Join several links for one
  title with `, `.
- The same name links the same source in every diagram (`NODE`), so a name
  linked in one diagram is linked wherever it appears.
  - A node and a boundary are matched apart, since a frame often shares its
    name with a node it holds.
- A table or paragraph cites its sources on the same boxed line, with no
  titles: `> **Sources:** *[orders.ts](../src/api/orders.ts) · [Spec](https://example.com)*`.

## Portable Syntax

A diagram must render in every viewer a reader opens it in: an IDE preview,
GitHub, and the Azure DevOps repository browser. Those viewers embed different
Mermaid releases, and Azure DevOps reads the first line of a block as the
diagram type. Use only syntax that every one of them accepts.

| Rule | What Breaks Otherwise |
| --- | --- |
| The first line is `graph TD`, `sequenceDiagram`, or `erDiagram`; no frontmatter or directive comes before it. | Frontmatter or a `%%{init}%%` directive on line one shows "Unsupported diagram type". |
| Draw a flowchart with `graph TD`, never `flowchart TD`. | Azure DevOps documents the `flowchart` keyword as unsupported. |
| A label holds only `<br/>` and one [title link](#source-links). | Other tags and inline styles are stripped or shown as text. |
| Write a step number as `1: text`. | Mermaid 11 parses a label as Markdown, and `1. text` draws "Unsupported markdown: list". |
| Never open a label with `-`, `*`, `+`, `>`, `#`, `1.`, or `1)`, and never use a backtick Markdown string. | The same Markdown parsing. |
| Lengthen a link by one character at most, and only one with a piped label: `--->`, `===>`, or `-..->`. | Longer arrows and lengthened inline labels are not drawn alike in every viewer. |
| Never give a node or edge an `@` id or `@{ }` properties, except a [stacked node](mermaid-visual.md#shared-visual-language). | Older Mermaid releases reject the syntax and drop that line's edge. Azure DevOps and IntelliJ draw both stacked shapes. |
| Link nodes, never a boundary. | Azure DevOps rejects an edge that starts or ends on a subgraph. |
| Never use `click` or the sequence `link` directive. | Viewers ignore them, and the tooltip is hidden or unreadable. |
| Never set configuration, themes, `style`, or `linkStyle`, except the [participant](mermaid-runtime.md#owner-bands) and [flowchart](#flowchart-line) lines. Color only through the [palette](mermaid-visual.md#color). | Each renderer supplies its own light or dark theme; only the palette's see-through fills read in both. |

The local renderer runs Mermaid 11, which may be newer than a viewer's release, so a clean PNG
does not prove portability. The lint enforces this table; trust it over the render.

Before any diagram uses a new construct or setting, prove it in the viewers. Write a probe page to a
file, since a probe pasted from terminal output wraps long lines and breaks parsing. Check it in Azure
DevOps and the IDE preview, then migrate one document and check that too, before applying it everywhere.

## Flowchart Line

Every `graph TD` has this exact second line:

```text
graph TD
  %%{init: {"themeCSS": ".cluster-label, .cluster-label div, .cluster-label span, .cluster-label p { text-align: center !important; }", "flowchart": {"curve": "rounded", "subGraphTitleMargin": {"top": 6, "bottom": 30}}}}%%
```

- `curve: rounded` draws straight edges with rounded corners, so a label sits
  on a straight run instead of a sweeping curve.
- `themeCSS` and `subGraphTitleMargin` center a [boundary](mermaid-visual.md#boundaries) title
  and keep it clear of the first node.
- A viewer that reads only the first line as the diagram type still accepts it.

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
python3 scripts/render_mermaid.py docs/*.md docs/*/*.md README.md
```

The script prints one PNG path per diagram. Open each PNG at its normal
display size. The script renders at double scale so a thin line through a
label is visible. It renders with the mermaid-cli version [`render_mermaid.py`](../scripts/render_mermaid.py) pins, which honors each
block's [flowchart line](#flowchart-line), so curves, label positions and
boundary titles look as they do in the viewers.

Reject a diagram with any of these:

- an edge or node that touches a boundary label
- an [edge label on a bend](mermaid-visual.md#edges), except on an edge between two boundaries
- clipped text, tiny text, or a diagram that needs zooming
- crossing edges or excess empty space
