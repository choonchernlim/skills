<!--
Purpose: Fixture.
Type: explanation
-->

# Tool Dead End

> **Audience:** maintainers, to see one rule fail.

The block draws a tool that hands its result to nobody.

```mermaid
graph TD
  %%{init: {"themeCSS": ".cluster-label, .cluster-label div, .cluster-label span, .cluster-label p { text-align: center !important; }", "flowchart": {"curve": "rounded", "subGraphTitleMargin": {"top": 6, "bottom": 30}}}}%%
  Agent{{"Planner<br/>[AGENT]"}}
  Search[["Search<br/>[TOOL]"]]
  Notify[["Notify<br/>[TOOL]"]]
  Mail["Mailer<br/>[SERVICE]"]
  Agent -->|"calls"| Search
  Agent -->|"calls"| Notify
  Notify -->|"sends through"| Mail
  class Search,Notify,Mail own
  class Agent model
  classDef own fill:#2563eb33,stroke:#2563eb
  classDef model fill:#c026d333,stroke:#c026d3,stroke-width:3px
```

> **Legend:** *🟦 Orders team · 🟪 model call*
