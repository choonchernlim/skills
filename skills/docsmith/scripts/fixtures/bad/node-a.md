<!--
Purpose: Fixture.
Type: explanation
-->

# Node Owner

> **Audience:** maintainers, to see one rule fail.

The title has no source here.

```mermaid
graph TD
  %%{init: {"themeCSS": ".cluster-label, .cluster-label div, .cluster-label span, .cluster-label p { text-align: center !important; }", "flowchart": {"curve": "rounded", "subGraphTitleMargin": {"top": 6, "bottom": 30}}}}%%
  Omega["Omega<br/>[SERVICE]"]
  Pi["Pi<br/>[SERVICE]"]
  Rho["Rho<br/>[SERVICE]"]
  Tau["Tau<br/>[SERVICE]"]
  Omega -->|"calls"| Pi
  Pi -->|"calls"| Rho
  Rho -->|"calls"| Tau

  class Omega,Pi,Rho,Tau own
  classDef own fill:#2563eb33,stroke:#2563eb
```

> **Legend:** *🟦 Example team*
