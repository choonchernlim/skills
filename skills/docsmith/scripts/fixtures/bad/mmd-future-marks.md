<!--
Purpose: Fixture.
Type: explanation
-->

# Future Marks

> **Audience:** maintainers, to see one rule fail.

The block marks a whole frame as future, and writes a node's suffix in lowercase without the class.

```mermaid
graph TD
  %%{init: {"themeCSS": ".cluster-label, .cluster-label div, .cluster-label span, .cluster-label p { text-align: center !important; }", "flowchart": {"curve": "rounded", "subGraphTitleMargin": {"top": 6, "bottom": 30}}}}%%
  subgraph Orders["Order Team (Future)<br/>[DEPLOYMENT]"]
    direction TB
    Route[/"Order<br/>[API]"/]
    Ledger[("Ledger<br/>[DATA]")]
  end
  Shop("Storefront<br/>[UI]")
  Fraud["Fraud Check (future)<br/>[SERVICE]"]
  Shop -->|"sends orders"| Route
  Route -->|"records in"| Ledger
  Route -->|"screens orders"| Fraud
  class Shop,Route,Ledger,Fraud own
  class Orders boundary
  classDef own fill:#2563eb33,stroke:#2563eb
  classDef boundary fill:#7d879914,stroke:#7d8799,stroke-dasharray:6
```

> **Legend:** *🟦 Orders team*
