<!--
Purpose: Shows a valid infrastructure diagram with repository provisioning boundaries.
Type: explanation
-->

# Infrastructure

Audience: platform engineers, to identify provisioning ownership.

The repositories provision a workload and its database inside separate ownership boundaries.

```mermaid
---
config:
  flowchart:
    subGraphTitleMargin:
      top: 4
      bottom: 32
---
flowchart TD
  subgraph Foundation["<span style='display:inline-block;width:480px;text-align:left'>foundation<br/>[REPO]</span>"]
    direction TB
    Project["Project<br/>[GCP PROJECT]"]
  end
  subgraph Workload["<span style='display:inline-block;width:480px;text-align:left'>workload<br/>[REPO]</span>"]
    direction TB
    App["Application<br/>[CLOUD RUN]"]
    Job["Migrator<br/>[CLOUD RUN JOB]"]
    Store[("Database<br/>[POSTGRES]")]
  end
  Project -->|"hosts"| App
  App -->|"writes"| Store
  Job -->|"migrates"| Store
```

| Node | Source |
| --- | --- |
| Project | - |
| Application | - |
| Migrator | - |
| Database | - |
