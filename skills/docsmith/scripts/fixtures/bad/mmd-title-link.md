<!--
Purpose: Fixture.
Type: explanation
-->

# Title

> **Audience:** maintainers, to see one rule fail.

## Section

Labels misuse the source link: no globe, a globe outside the link, a globe alone, a half-linked boundary, and a linked edge.

```mermaid
graph TD
  %%{init: {"themeCSS": ".cluster-label, .cluster-label div, .cluster-label span, .cluster-label p { text-align: center !important; }", "flowchart": {"curve": "rounded", "subGraphTitleMargin": {"top": 6, "bottom": 30}}}}%%
  subgraph App["Order <a href='mmd-click.md'>Service 🌐</a><br/>[DEPLOYMENT]"]
    direction TB
    A["<a href='mmd-click.md'>One</a><br/>[SERVICE]"]
    B["<a href='mmd-click.md'>Two</a> 🌐<br/>[SERVICE]"]
    C["Three 🌐<br/>[SERVICE]"]
  end
  D["<a href='mmd-click.md'>Four 🌐</a><br/>[SERVICE]"]
  A -->|"calls"| B
  B -->|"calls"| C
  C -->|"<a href='mmd-click.md'>calls</a>"| D

  class A,B,C,D own
  class App boundary
  classDef own fill:#2563eb33,stroke:#2563eb
  classDef boundary fill:#7d879914,stroke:#7d8799,stroke-dasharray:6
```

> **Legend:** *🟦 Example team*
