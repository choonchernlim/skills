<!--
Purpose: Fixture.
Type: explanation
-->

# Stacked

> **Audience:** maintainers, to see one rule fail.

The block stacks data as rectangles, a service as documents, and uses another '@' shape.

```mermaid
graph TD
  %%{init: {"themeCSS": ".cluster-label, .cluster-label div, .cluster-label span, .cluster-label p { text-align: center !important; }", "flowchart": {"curve": "rounded", "subGraphTitleMargin": {"top": 6, "bottom": 30}}}}%%
  One@{ shape: st-rect, label: "One<br/>[DATA]" }
  Two@{ shape: docs, label: "Two<br/>[SERVICE]" }
  Three@{ shape: docs, label: "Three<br/>[DATA]" }
  Four["Four<br/>[SERVICE]"]
  Five@{ shape: circle, label: "Five<br/>[SERVICE]" }
  Four -->|"reads"| One
  Four -->|"calls"| Two
  Four -->|"reads"| Three
  Four -->|"calls"| Five
  class One,Two,Three,Four,Five own
  classDef own fill:#2563eb33,stroke:#2563eb
```

> **Legend:** *🟦 Platform team*
