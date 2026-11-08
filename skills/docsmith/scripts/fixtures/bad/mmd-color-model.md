<!--
Purpose: Fixture.
Type: explanation
-->

# Color Model

> **Audience:** maintainers, to see one rule fail.

The block marks a deterministic service as a model call.

```mermaid
graph TD
  %%{init: {"themeCSS": ".cluster-label, .cluster-label div, .cluster-label span, .cluster-label p { text-align: center !important; }", "flowchart": {"curve": "rounded", "subGraphTitleMargin": {"top": 6, "bottom": 30}}}}%%
  One["One<br/>[SERVICE]"]
  Two["Two<br/>[SERVICE]"]
  Three["Three<br/>[SERVICE]"]
  Four["Four<br/>[SERVICE]"]
  One -->|"calls"| Two
  Two -->|"calls"| Three
  Three -->|"calls"| Four
  class One,Two,Three own
  class Four model
  classDef own fill:#2563eb33,stroke:#2563eb
  classDef model fill:#c026d333,stroke:#c026d3,stroke-width:3px
```

> **Legend:** *🟦 Platform team · 🟪 model call*
