<!--
Purpose: Fixture.
Type: explanation
-->

# Future Parts

> **Audience:** maintainers, to see one rule fail.

The block marks future parts inconsistently, and its legend never explains the dashes.

```mermaid
graph TD
  %%{init: {"themeCSS": ".cluster-label, .cluster-label div, .cluster-label span, .cluster-label p { text-align: center !important; }", "flowchart": {"curve": "rounded", "subGraphTitleMargin": {"top": 6, "bottom": 30}}}}%%
  Route[/"Order<br/>[API]"/]
  Fraud["Fraud Check (Future)<br/>[SERVICE]"]
  Ledger[("Ledger<br/>[DATA]")]
  Mailer["Mailer<br/>[SERVICE]"]
  Route -.->|"screens orders"| Fraud
  Route -->|"records in"| Ledger
  Route -.->|"notifies through"| Mailer
  class Route,Fraud own
  class Ledger,Mailer future
  class Mailer own
  classDef own fill:#2563eb33,stroke:#2563eb
  classDef future fill:#6b72801a,stroke:#6b7280,stroke-dasharray:5
```

> **Legend:** *🟦 Orders team*

The next block has no future part, yet its legend still explains dashes.

```mermaid
graph TD
  %%{init: {"themeCSS": ".cluster-label, .cluster-label div, .cluster-label span, .cluster-label p { text-align: center !important; }", "flowchart": {"curve": "rounded", "subGraphTitleMargin": {"top": 6, "bottom": 30}}}}%%
  Cart[/"Cart<br/>[API]"/]
  Stock[("Stock<br/>[DATA]")]
  Pricing["Pricing<br/>[SERVICE]"]
  Tax["Tax<br/>[SERVICE]"]
  Cart -->|"reserves in"| Stock
  Cart -->|"prices through"| Pricing
  Pricing -->|"adds tax with"| Tax
  class Cart,Stock,Pricing,Tax own
  classDef own fill:#2563eb33,stroke:#2563eb
```

> **Legend:** *🟦 Orders team · dashed gray = future*
