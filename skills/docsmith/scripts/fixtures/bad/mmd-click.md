<!--
Purpose: Fixture.
Type: explanation
-->

# Title

> **Audience:** nobody.

## Section

Lead.

```mermaid
graph TD
  %%{init: {"themeCSS": ".cluster-label, .cluster-label div, .cluster-label span, .cluster-label p { text-align: center !important; }", "flowchart": {"curve": "rounded", "subGraphTitleMargin": {"top": 6, "bottom": 30}}}}%%
  A["One<br/>[SERVICE]"] -->|"calls"| B["Two<br/>[SERVICE]"]
  B -->|"calls"| C["Three<br/>[SERVICE]"]
  C -->|"calls"| D["Four<br/>[SERVICE]"]
  click A "x.md"

  class A,B,C,D own
  classDef own fill:#2563eb33,stroke:#2563eb
```

> **Legend:** *🟦 Example team*

A sequence diagram links a participant with the 'link' directive.

```mermaid
sequenceDiagram
  %%{init: {"themeVariables": {"actorBkg": "transparent", "actorBorder": "#7d8799", "actorLineColor": "#7d8799", "labelBoxBorderColor": "#7d8799"}}}%%
  box rgba(37,99,235,0.2) Example team
    participant A as Alpha<br/>[SERVICE]
    participant B as Beta<br/>[SERVICE]
  end
  link A: Source @ mmd-html.md
  A->>B: 1: calls
```
