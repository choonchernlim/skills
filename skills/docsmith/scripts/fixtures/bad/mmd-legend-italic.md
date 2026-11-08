<!--
Purpose: Fixture.
Type: explanation
-->

# Title

> **Audience:** nobody.

## Section

The legend is not in italics.

```mermaid
graph TD
  %%{init: {"themeCSS": ".cluster-label, .cluster-label div, .cluster-label span, .cluster-label p { text-align: center !important; }", "flowchart": {"curve": "rounded", "subGraphTitleMargin": {"top": 6, "bottom": 30}}}}%%
  A["One<br/>[SERVICE]"] -->|"calls"| B["Two<br/>[SERVICE]"]
  B -->|"calls"| C["Three<br/>[SERVICE]"]
  C -->|"calls"| D["Four<br/>[SERVICE]"]

  class A,B,C,D own
  classDef own fill:#2563eb33,stroke:#2563eb
```

> **Legend:** 🟦 Example team
