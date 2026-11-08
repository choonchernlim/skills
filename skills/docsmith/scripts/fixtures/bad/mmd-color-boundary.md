<!--
Purpose: Fixture.
Type: explanation
-->

# Color Boundary

> **Audience:** maintainers, to see one rule fail.

The block leaves one boundary plain and gives a node the boundary class.

```mermaid
graph TD
  %%{init: {"themeCSS": ".cluster-label, .cluster-label div, .cluster-label span, .cluster-label p { text-align: center !important; }", "flowchart": {"curve": "rounded", "subGraphTitleMargin": {"top": 6, "bottom": 30}}}}%%
  subgraph App["Application<br/>[DEPLOYMENT]"]
    direction TB
    One["One<br/>[SERVICE]"]
    Two["Two<br/>[SERVICE]"]
  end
  subgraph Data["Data<br/>[DEPLOYMENT]"]
    direction TB
    Three["Three<br/>[SERVICE]"]
    Four["Four<br/>[SERVICE]"]
  end
  One -->|"calls"| Two
  Two -->|"calls"| Three
  Three -->|"calls"| Four
  class One,Two,Three own
  class Four boundary
  class Data boundary
  classDef own fill:#2563eb33,stroke:#2563eb
  classDef boundary fill:#7d879914,stroke:#7d8799,stroke-dasharray:6
```

> **Legend:** *🟦 Platform team*
