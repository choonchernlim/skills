<!--
Purpose: Fixture.
Type: explanation
-->

# Shape Type

> **Audience:** maintainers, to see one rule fail.

The block draws a person, an agent, a tool, a decision, and a Cloud SQL store as rectangles.

```mermaid
graph TD
  %%{init: {"themeCSS": ".cluster-label, .cluster-label div, .cluster-label span, .cluster-label p { text-align: center !important; }", "flowchart": {"curve": "rounded", "subGraphTitleMargin": {"top": 6, "bottom": 30}}}}%%
  One["One<br/>[PERSON]"]
  Two["Two<br/>[AGENT]"]
  Three["Three<br/>[TOOL]"]
  Four["Four<br/>[CLOUD SQL]"]
  Five["Five<br/>[CLOUD RUN]"]
  Six["Six?<br/>[DECISION]"]
  One -->|"calls"| Two
  Two -->|"calls"| Three
  Three -->|"reads"| Four
  Five -->|"writes"| Four
  Five -->|"checks"| Six
  class Five,Three,Four,Six own
  class One person
  class Two model
  classDef own fill:#2563eb33,stroke:#2563eb
  classDef person fill:#e11d4833,stroke:#e11d48
  classDef model fill:#c026d333,stroke:#c026d3,stroke-width:3px
```

> **Legend:** *🟦 Platform team · 🟥 customers · 🟪 model call*
