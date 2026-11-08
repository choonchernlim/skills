<!--
Purpose: Fixture.
Type: explanation
-->

# Color Legend

> **Audience:** maintainers, to see one rule fail.

The block uses color but has no legend under the diagram.

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
  class One,Two own
  class Three,Four peer
  classDef own fill:#2563eb33,stroke:#2563eb
  classDef peer fill:#0d948833,stroke:#0d9488
```
