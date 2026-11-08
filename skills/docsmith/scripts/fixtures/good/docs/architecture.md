<!--
Purpose: The deployments, who owns each, and the one allowed dependency direction.
Type: explanation
-->

# Architecture

> **Audience:** all teams, to answer what exists and who owns it.

The shop runs as a storefront and an API that two teams own. This guide shows each deployment and the one contract between them.

## Deployments

Two teams ship independently, and only a versioned contract crosses the line
between them.

```mermaid
graph TD
  %%{init: {"themeCSS": ".cluster-label, .cluster-label div, .cluster-label span, .cluster-label p { text-align: center !important; }", "flowchart": {"curve": "rounded", "subGraphTitleMargin": {"top": 6, "bottom": 30}}}}%%
  subgraph Web["<a href='../src/README.md'>Web Team 🌐</a><br/>[DEPLOYMENT]"]
    direction TB
    Browser("<a href='../src/README.md'>Storefront 🌐</a><br/>[UI]")
  end

  subgraph Orders["Order Team<br/>[DEPLOYMENT]"]
    direction TB
    Route[/"<a href='../src/api.ts'>Order 🌐</a><br/>[API]"/]
    Inventory["<a href='../src/inventory/client.ts'>Inventory Client 🌐</a><br/>[SERVICE]"]
    Store[("Order Store<br/>[POSTGRES]")]
  end

  Identity["Identity Provider<br/>[SYSTEM]"]
  Warehouse["Warehouse<br/>[SYSTEM]"]
  Fraud["Fraud Check (Future)<br/>[SERVICE]"]
  Recs{{"Recommender (Future)<br/>[AGENT]"}}

  Browser --->|"signs in"| Identity
  Browser -->|"sends orders"| Route
  Route -->|"reserves stock"| Inventory
  Route -->|"stores orders"| Store
  Inventory -->|"queries"| Warehouse
  Route -..->|"screens orders"| Fraud
  Browser -.->|"suggests through"| Recs

  class Browser,Route,Inventory,Store,Identity,Warehouse own
  class Fraud,Recs future
  class Web,Orders boundary
  classDef own fill:#2563eb33,stroke:#2563eb
  classDef boundary fill:#7d879914,stroke:#7d8799,stroke-dasharray:6
  classDef future fill:#6b72801a,stroke:#6b7280,stroke-dasharray:5
```

> **Legend:** *🟦 Example team · dashed gray = future*

The UI never writes inventory directly. The order API coordinates the
reservation so one component owns the transaction boundary.

Sign-in has its own guide: [security/authentication.md](security/authentication.md).
