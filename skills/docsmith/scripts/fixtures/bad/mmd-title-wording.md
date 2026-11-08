<!--
Purpose: Fixture.
Type: explanation
-->

# Title Wording

> **Audience:** maintainers, to see one rule fail.

The block names one node by its code name, one in lower case, and asks a question in lower case; the repository keeps its real name.

```mermaid
graph TD
  %%{init: {"themeCSS": ".cluster-label, .cluster-label div, .cluster-label span, .cluster-label p { text-align: center !important; }", "flowchart": {"curve": "rounded", "subGraphTitleMargin": {"top": 6, "bottom": 30}}}}%%
  subgraph Repo["shop-web<br/>[REPO]"]
    direction TB
    Bridge[/"X12-EDI Bridge<br/>[API]"/]
    Check{"in stock?<br/>[DECISION]"}
    Label["shipping label<br/>[SERVICE]"]
  end
  Store[("order_store<br/>[DATA]")]
  Bridge -->|"asks"| Check
  Check -->|"yes, prints"| Label
  Check -->|"no, records"| Store
  class Bridge,Check,Label,Store own
  class Repo boundary
  classDef own fill:#2563eb33,stroke:#2563eb
  classDef boundary fill:#7d879914,stroke:#7d8799,stroke-dasharray:6
```

> **Legend:** *🟦 Orders team*
