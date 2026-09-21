<!--
Purpose: Shows a valid infrastructure diagram with repository provisioning boundaries.
Type: explanation
-->

# Infrastructure

Audience: platform engineers, to identify provisioning ownership.

The repositories provision a workload and its database inside separate ownership boundaries.

```mermaid
graph TD
  subgraph Foundation["foundation"]
    direction TB
    Project["Project<br/>[GCP PROJECT]"]
  end
  subgraph Workload["workload"]
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
| foundation [REPO] | - |
| workload [REPO] | - |
| Project | - |
| Application | - |
| Migrator | - |
| Database | - |
