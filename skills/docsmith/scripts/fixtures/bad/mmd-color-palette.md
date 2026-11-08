<!--
Purpose: Fixture.
Type: explanation
-->

# Color Palette

> **Audience:** maintainers, to see one rule fail.

The block defines a color outside the palette.

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
  class Four red
  classDef own fill:#2563eb33,stroke:#2563eb
  classDef red fill:#ff0000
```

> **Legend:** *🟦 Platform team*
