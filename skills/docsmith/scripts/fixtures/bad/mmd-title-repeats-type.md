<!--
Purpose: Fixture.
Type: explanation
-->

# Title Repeats Type

> **Audience:** maintainers, to see one rule fail.

The block names a tool "Tool" and a deployment "Deployment", which their tags already say.

```mermaid
graph TD
  %%{init: {"themeCSS": ".cluster-label, .cluster-label div, .cluster-label span, .cluster-label p { text-align: center !important; }", "flowchart": {"curve": "rounded", "subGraphTitleMargin": {"top": 6, "bottom": 30}}}}%%
  subgraph App["Orders Deployment<br/>[DEPLOYMENT]"]
    direction TB
    Agent{{"Planner<br/>[AGENT]"}}
    Search[["Search Tool<br/>[TOOL]"]]
  end
  Store[("Ledger<br/>[DATA]")]
  Mail["Mailer<br/>[SERVICE]"]
  Agent -->|"calls"| Search
  Search -->|"reads"| Store
  Agent -->|"notifies through"| Mail
  class Search,Store,Mail own
  class Agent model
  class App boundary
  classDef own fill:#2563eb33,stroke:#2563eb
  classDef model fill:#c026d333,stroke:#c026d3,stroke-width:3px
  classDef boundary fill:#7d879914,stroke:#7d8799,stroke-dasharray:6
```

> **Legend:** *🟦 Orders team · 🟪 model call*
