<!--
Purpose: Fixture.
Type: explanation
-->

# Edge Owner

> **Audience:** maintainers, to see one rule fail.

The first file owns the relationship.

```mermaid
graph TD
  %%{init: {"themeCSS": ".cluster-label, .cluster-label div, .cluster-label span, .cluster-label p { text-align: center !important; }", "flowchart": {"curve": "rounded", "subGraphTitleMargin": {"top": 6, "bottom": 30}}}}%%
  Alpha["Alpha<br/>[SERVICE]"]
  Beta["Beta<br/>[SERVICE]"]
  Gamma["Gamma<br/>[SERVICE]"]
  Delta["Delta<br/>[SERVICE]"]
  Alpha -->|"calls"| Beta
  Beta -->|"calls"| Gamma
  Gamma -->|"calls"| Delta

  class Alpha,Beta,Gamma,Delta own
  classDef own fill:#2563eb33,stroke:#2563eb
```

> **Legend:** *🟦 Example team*
