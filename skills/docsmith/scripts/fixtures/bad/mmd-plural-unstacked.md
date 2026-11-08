<!--
Purpose: Fixture.
Type: explanation
-->

# Plural Unstacked

> **Audience:** maintainers, to see one rule fail.

The block stacks a tool set and a worker pool, but leaves two plural nodes flat and stacks a tool as documents.

```mermaid
graph TD
  %%{init: {"themeCSS": ".cluster-label, .cluster-label div, .cluster-label span, .cluster-label p { text-align: center !important; }", "flowchart": {"curve": "rounded", "subGraphTitleMargin": {"top": 6, "bottom": 30}}}}%%
  Agent{{"Planner<br/>[AGENT]"}}
  Search@{ shape: st-rect, label: "Search<br/>[TOOL]" }
  Workers@{ shape: st-rect, label: "Pickers<br/>[AGENT]" }
  Notify@{ shape: docs, label: "Notify<br/>[TOOL]" }
  Mail["Mailers<br/>[SERVICE]"]
  Store[("Orders and Returns<br/>[DATA]")]
  Agent -->|"calls"| Search
  Agent -->|"fans out to"| Workers
  Agent -->|"calls"| Notify
  Search -->|"reads"| Store
  Notify -->|"sends through"| Mail
  class Search,Notify,Mail,Store own
  class Agent,Workers model
  classDef own fill:#2563eb33,stroke:#2563eb
  classDef model fill:#c026d333,stroke:#c026d3,stroke-width:3px
```

> **Legend:** *🟦 Orders team · 🟪 model call*
