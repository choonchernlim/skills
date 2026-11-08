<!--
Purpose: Fixture.
Type: explanation
-->

# Plural Boundary

> **Audience:** maintainers, to see one rule fail.

The block frames one order path in a plural boundary, which Mermaid cannot stack.

```mermaid
graph TD
  %%{init: {"themeCSS": ".cluster-label, .cluster-label div, .cluster-label span, .cluster-label p { text-align: center !important; }", "flowchart": {"curve": "rounded", "subGraphTitleMargin": {"top": 6, "bottom": 30}}}}%%
  subgraph Orders["Order Services<br/>[DEPLOYMENT]"]
    direction TB
    Route[/"Order<br/>[API]"/]
    Ledger[("Ledger<br/>[DATA]")]
    Pricing["Pricing<br/>[SERVICE]"]
  end
  Shop("Storefront<br/>[UI]")
  Shop -->|"sends orders"| Route
  Route -->|"records in"| Ledger
  Route -->|"prices through"| Pricing
  class Shop,Route,Ledger,Pricing own
  class Orders boundary
  classDef own fill:#2563eb33,stroke:#2563eb
  classDef boundary fill:#7d879914,stroke:#7d8799,stroke-dasharray:6
```

> **Legend:** *🟦 Orders team*
