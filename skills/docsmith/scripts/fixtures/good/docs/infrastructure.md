<!--
Purpose: Shows a valid infrastructure diagram with repository provisioning boundaries.
Type: explanation
-->

# Infrastructure

> **Audience:** platform engineers, to identify provisioning ownership.

The repositories provision a workload and its database inside separate ownership boundaries.

```mermaid
graph TD
  %%{init: {"themeCSS": ".cluster-label, .cluster-label div, .cluster-label span, .cluster-label p { text-align: center !important; }", "flowchart": {"curve": "rounded", "subGraphTitleMargin": {"top": 6, "bottom": 30}}}}%%
  subgraph Foundation["foundation<br/>[REPO]"]
    direction TB
    Project["shop-prod<br/>[GCP PROJECT]"]
  end
  subgraph Workload["workload<br/>[REPO]"]
    direction TB
    App@{ shape: st-rect, label: "Application<br/>[CLOUD RUN]" }
    Job["Migrator<br/>[CLOUD RUN JOB]"]
    Store[("Database<br/>[POSTGRES]")]
  end
  Project -->|"hosts"| App
  App -->|"writes"| Store
  Job -->|"migrates"| Store

  class Project,App,Job,Store own
  class Foundation,Workload boundary
  classDef own fill:#2563eb33,stroke:#2563eb
  classDef boundary fill:#7d879914,stroke:#7d8799,stroke-dasharray:6
```

> **Legend:** *🟦 Example team*
