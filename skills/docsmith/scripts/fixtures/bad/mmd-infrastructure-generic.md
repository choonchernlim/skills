<!--
Purpose: Bad generic infrastructure type fixture.
Type: explanation
-->

# Generic Infrastructure

> **Audience:** maintainers, to see a generic platform type fail.

The infrastructure diagram hides one deployed technology behind a generic label.

```mermaid
graph TD
  %%{init: {"themeCSS": ".cluster-label, .cluster-label div, .cluster-label span, .cluster-label p { text-align: center !important; }", "flowchart": {"curve": "rounded", "subGraphTitleMargin": {"top": 6, "bottom": 30}}}}%%
  Project["shop-prod<br/>[GCP PROJECT]"]
  App["Application<br/>[SYSTEM]"]
  Job["Migrator<br/>[CLOUD RUN JOB]"]
  Store[("Database<br/>[POSTGRES]")]
  Project -->|"hosts"| App
  App -->|"writes"| Store
  Job -->|"migrates"| Store

  class Project,App,Job,Store own
  classDef own fill:#2563eb33,stroke:#2563eb
```

> **Legend:** *🟦 Example team*
