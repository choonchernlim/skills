<!--
Purpose: Conventions for ordered request, lifecycle, authentication, and orchestration diagrams.
Type: reference
-->

# Runtime Diagrams

> **Audience:** the writer, when a reader needs to trace events in order.

Use `sequenceDiagram`. Put the initiating person first, then participants in
call order, kept together by owner band. Every participant uses
`participant`, a `PERSON` included. Never use `actor`: its figure collides
with a two-line label.

## Participants and Messages

Use the application node vocabulary. Label every participant as
`Title<br/>[TYPE]`. Number every message as `1: text` and keep its text to one action.

- Solid arrows are calls or commands.
- Dashed arrows are responses.
- Use `opt` for optional behavior and `alt` for mutually exclusive outcomes.
- Split by phase before exceeding seven participants or twelve messages.
- Do not add a participant only to hold a note.

Sequence diagrams draw no deployment or trust boundaries. When those matter
more than order, create a separate application or infrastructure diagram.

## Owner Bands

Every participant sits in one owner band, so a box keeps the owner color it
has in every flowchart. A band is `box <color> <owner name>`, its participant
lines, then `end`. Mermaid reads `#` in a `box` line as a comment, so a band
takes the `rgba` form of its owner's [palette](mermaid-visual.md#color) fill.

| Class | Band Color |
| --- | --- |
| `own` | `rgba(37,99,235,0.2)` |
| `peer` | `rgba(13,148,136,0.2)` |
| `platform` | `rgba(217,119,6,0.2)` |
| `external` | `rgba(100,116,139,0.2)` |
| `person` | `rgba(225,29,72,0.2)` |

- Declare every participant inside a band; a band holds participant lines only.
  Never use `create`: Mermaid places a created participant outside every band.
- Name the real owner in the band title. The titles are the key, so a
  sequence diagram needs no legend line.
- An `[AGENT]` participant sits in its owner's band; its tag marks the model call.
- Every `[PERSON]` participant sits in a person band, and nothing else does.
  Name the people in its title, such as `Store staff`.
- Two bands may share an owner when call order separates its participants.

A participant takes no class, so its box would wear the viewer theme's color.
Copy this line exactly as the second line of every sequence diagram. It makes
each box see-through, so it shows its band's tint, and draws borders and
lifelines in slate. Azure DevOps reads only the first line as the diagram type.

```text
%%{init: {"themeVariables": {"actorBkg": "transparent", "actorBorder": "#7d8799", "actorLineColor": "#7d8799", "labelBoxBorderColor": "#7d8799"}}}%%
```

````markdown
```mermaid
sequenceDiagram
  %%{init: {"themeVariables": {"actorBkg": "transparent", "actorBorder": "#7d8799", "actorLineColor": "#7d8799", "labelBoxBorderColor": "#7d8799"}}}%%
  box rgba(225,29,72,0.2) Store staff
    participant Clerk as Store Clerk<br/>[PERSON]
  end
  box rgba(37,99,235,0.2) Orders team
    participant Api as Order<br/>[API]
    participant Plan as Planner<br/>[AGENT]
  end
  Clerk->>Api: 1: places an order
  Api->>Plan: 2: asks for a plan
```

> **Sources:** *Order [orders.ts](../src/api/orders.ts) · Planner [planner.ts](../src/planner/planner.ts)*
````

## Sources and Steps

List participants on the [Sources line](mermaid.md#source-links) in
declaration order. A numbered list may combine adjacent request and response
messages when one explanation covers both without losing an authorization,
validation, or persistence boundary.
