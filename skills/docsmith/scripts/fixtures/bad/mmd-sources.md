<!--
Purpose: Fixture.
Type: explanation
-->

# Title

> **Audience:** maintainers, to see one rule fail.

## Section

A Sources line names a stranger, holds a bare path, and repeats a title.

```mermaid
sequenceDiagram
  %%{init: {"themeVariables": {"actorBkg": "transparent", "actorBorder": "#7d8799", "actorLineColor": "#7d8799", "labelBoxBorderColor": "#7d8799"}}}%%
  box rgba(37,99,235,0.2) Example team
    participant A as Alpha<br/>[SERVICE]
    participant B as Beta<br/>[SERVICE]
  end
  A->>B: 1: calls
```

> **Sources:** *Alpha [mmd-click.md](mmd-click.md) · Gamma [mmd-click.md](mmd-click.md) · Beta mmd-click.md · Alpha [mmd-click.md](mmd-click.md)*

A flowchart takes a Sources line.

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

> **Sources:** *One [mmd-click.md](mmd-click.md)*

A diagram keeps the retired Node table.

```mermaid
sequenceDiagram
  %%{init: {"themeVariables": {"actorBkg": "transparent", "actorBorder": "#7d8799", "actorLineColor": "#7d8799", "labelBoxBorderColor": "#7d8799"}}}%%
  box rgba(37,99,235,0.2) Example team
    participant A as Alpha<br/>[SERVICE]
    participant B as Beta<br/>[SERVICE]
  end
  A->>B: 1: calls
```

| Node | Source |
| --- | --- |
| Alpha | - |
| Beta | - |

A Sources list is not in italics.

```mermaid
sequenceDiagram
  %%{init: {"themeVariables": {"actorBkg": "transparent", "actorBorder": "#7d8799", "actorLineColor": "#7d8799", "labelBoxBorderColor": "#7d8799"}}}%%
  box rgba(37,99,235,0.2) Example team
    participant A as Alpha<br/>[SERVICE]
    participant B as Beta<br/>[SERVICE]
  end
  A->>B: 1: calls
```

> **Sources:** Alpha [mmd-click.md](mmd-click.md)
