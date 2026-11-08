<!--
Purpose: Fixture.
Type: explanation
-->

# Title

> **Audience:** maintainers, to see one rule fail.

## Section

A Sources line sits below a paragraph instead of under the diagram.

```mermaid
sequenceDiagram
  %%{init: {"themeVariables": {"actorBkg": "transparent", "actorBorder": "#7d8799", "actorLineColor": "#7d8799", "labelBoxBorderColor": "#7d8799"}}}%%
  box rgba(37,99,235,0.2) Example team
    participant A as Alpha<br/>[SERVICE]
    participant B as Beta<br/>[SERVICE]
  end
  A->>B: 1: calls
```

The two services talk once.

> **Sources:** *Alpha [mmd-click.md](mmd-click.md)*

A diagram takes a second Sources line.

```mermaid
sequenceDiagram
  %%{init: {"themeVariables": {"actorBkg": "transparent", "actorBorder": "#7d8799", "actorLineColor": "#7d8799", "labelBoxBorderColor": "#7d8799"}}}%%
  box rgba(37,99,235,0.2) Example team
    participant A as Alpha<br/>[SERVICE]
    participant B as Beta<br/>[SERVICE]
  end
  A->>B: 1: calls
```

> **Sources:** *Alpha [mmd-click.md](mmd-click.md)*

> **Sources:** *Beta [mmd-click.md](mmd-click.md)*

A legend is not boxed.

```mermaid
graph TD
  %%{init: {"themeCSS": ".cluster-label, .cluster-label div, .cluster-label span, .cluster-label p { text-align: center !important; }", "flowchart": {"curve": "rounded", "subGraphTitleMargin": {"top": 6, "bottom": 30}}}}%%
  A["One<br/>[SERVICE]"]
  B["Two<br/>[SERVICE]"]
  C["Three<br/>[SERVICE]"]
  D["Four<br/>[SERVICE]"]
  A -->|"calls"| B
  B -->|"calls"| C
  C -->|"calls"| D

  class A,B,C,D own
  classDef own fill:#2563eb33,stroke:#2563eb
```

**Legend:** *🟦 Example team*

A legend runs onto a second line.

```mermaid
graph TD
  %%{init: {"themeCSS": ".cluster-label, .cluster-label div, .cluster-label span, .cluster-label p { text-align: center !important; }", "flowchart": {"curve": "rounded", "subGraphTitleMargin": {"top": 6, "bottom": 30}}}}%%
  A["One<br/>[SERVICE]"]
  B["Two<br/>[SERVICE]"]
  C["Three<br/>[SERVICE]"]
  D["Four<br/>[SERVICE]"]
  A -->|"calls"| B
  B -->|"calls"| C
  C -->|"calls"| D

  class A,B,C,D own
  classDef own fill:#2563eb33,stroke:#2563eb
```

> **Legend:** *🟦 Example team*
> *and more*
