<!--
Purpose: Fixture.
Type: explanation
-->

# Long Arrow

> **Audience:** maintainers, to see one rule fail.

Four edges lengthen an arrow too far or lengthen an inline label.

```mermaid
graph TD
  %%{init: {"themeCSS": ".cluster-label, .cluster-label div, .cluster-label span, .cluster-label p { text-align: center !important; }", "flowchart": {"curve": "rounded", "subGraphTitleMargin": {"top": 6, "bottom": 30}}}}%%
  One["One<br/>[SERVICE]"]
  Two["Two<br/>[SERVICE]"]
  Three["Three<br/>[SERVICE]"]
  Four["Four<br/>[SERVICE]"]
  One -. "calls" ..-> Two
  Two ====>|"calls"| Three
  Three ---->|"calls"| Four
  Four -- "calls" ---> One

  class One,Two,Three,Four own
  classDef own fill:#2563eb33,stroke:#2563eb
```

> **Legend:** *🟦 Example team*
