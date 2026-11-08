<!--
Purpose: Fixture.
Type: explanation
-->

# Flowchart Line

> **Audience:** maintainers, to see one rule fail twice.

The framed flowchart lacks its flowchart line.

```mermaid
graph TD
  subgraph App["Application<br/>[DEPLOYMENT]"]
    direction TB
    One["One<br/>[SERVICE]"]
    Two["Two<br/>[SERVICE]"]
    Three["Three<br/>[SERVICE]"]
    Four["Four<br/>[SERVICE]"]
  end
  One -->|"calls"| Two
  Two -->|"calls"| Three
  Three -->|"calls"| Four

  class One,Two,Three,Four own
  class App boundary
  classDef own fill:#2563eb33,stroke:#2563eb
  classDef boundary fill:#7d879914,stroke:#7d8799,stroke-dasharray:6
```

> **Legend:** *🟦 Example team*

The plain flowchart has a flowchart line without its curve.

```mermaid
graph TD
  %%{init: {"themeCSS": ".cluster-label, .cluster-label div, .cluster-label span, .cluster-label p { text-align: center !important; }", "flowchart": {"subGraphTitleMargin": {"top": 6, "bottom": 30}}}}%%
  Five["Five<br/>[SERVICE]"]
  Six["Six<br/>[SERVICE]"]
  Seven["Seven<br/>[SERVICE]"]
  Eight["Eight<br/>[SERVICE]"]
  Five -->|"calls"| Six
  Six -->|"calls"| Seven
  Seven -->|"calls"| Eight

  class Five,Six,Seven,Eight own
  classDef own fill:#2563eb33,stroke:#2563eb
```

> **Legend:** *🟦 Example team*
