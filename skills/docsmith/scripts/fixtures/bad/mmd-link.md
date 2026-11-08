<!--
Purpose: Fixture.
Type: explanation
-->

# Title

> **Audience:** nobody.

## Section

Each edge line below uses a link other than `-->`, `-.->`, or `==>`, draws more than one edge, or names an edge id.

```mermaid
graph TD
  %%{init: {"themeCSS": ".cluster-label, .cluster-label div, .cluster-label span, .cluster-label p { text-align: center !important; }", "flowchart": {"curve": "rounded", "subGraphTitleMargin": {"top": 6, "bottom": 30}}}}%%
  A["One<br/>[SERVICE]"]
  B["Two<br/>[SERVICE]"]
  C["Three<br/>[SERVICE]"]
  D["Four<br/>[SERVICE]"]
  A --- B
  A === B
  A -.- B
  A --x B
  A --o B
  A <--> B
  A ~~~ B
  A -..-|"calls"| B
  A -. "calls" .- B
  A e1@-->|"calls"| B
  A -->|"calls"| B & C
  A -->|"calls"| B -->|"calls"| C

  class A,B,C,D own
  classDef own fill:#2563eb33,stroke:#2563eb
```

> **Legend:** *🟦 Example team*
