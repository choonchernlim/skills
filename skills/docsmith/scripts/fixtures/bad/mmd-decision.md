<!--
Purpose: Fixture.
Type: explanation
-->

# Decision

> **Audience:** maintainers, to see one rule fail.

The block draws one decision that asks nothing and one that asks too much.

```mermaid
graph TD
  %%{init: {"themeCSS": ".cluster-label, .cluster-label div, .cluster-label span, .cluster-label p { text-align: center !important; }", "flowchart": {"curve": "rounded", "subGraphTitleMargin": {"top": 6, "bottom": 30}}}}%%
  Start["Start<br/>[SERVICE]"]
  Two{"Stock check<br/>[DECISION]"}
  Three{"Is it in stock?<br/>[DECISION]"}
  Done["Done<br/>[SERVICE]"]
  Start -->|"checks"| Two
  Two -->|"yes"| Three
  Three -->|"yes"| Done
  class Start,Two,Three,Done own
  classDef own fill:#2563eb33,stroke:#2563eb
```

> **Legend:** *🟦 Orders team*
