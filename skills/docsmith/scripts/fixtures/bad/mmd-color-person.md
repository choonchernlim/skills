<!--
Purpose: Fixture.
Type: explanation
-->

# Color Person

> **Audience:** maintainers, to see one rule fail.

The block gives a person an owner class and a service the person class.

```mermaid
graph TD
  %%{init: {"themeCSS": ".cluster-label, .cluster-label div, .cluster-label span, .cluster-label p { text-align: center !important; }", "flowchart": {"curve": "rounded", "subGraphTitleMargin": {"top": 6, "bottom": 30}}}}%%
  One(["One<br/>[PERSON]"])
  Two["Two<br/>[SERVICE]"]
  Three["Three<br/>[SERVICE]"]
  Four["Four<br/>[SERVICE]"]
  One -->|"calls"| Two
  Two -->|"calls"| Three
  Three -->|"calls"| Four
  class One,Two,Three own
  class Four person
  classDef own fill:#2563eb33,stroke:#2563eb
  classDef person fill:#e11d4833,stroke:#e11d48
```

> **Legend:** *🟦 Platform team · 🟥 customers*
