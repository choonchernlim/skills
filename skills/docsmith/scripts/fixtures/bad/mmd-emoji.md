<!--
Purpose: Fixture.
Type: explanation
-->

# Title

> **Audience:** maintainers, to see one rule fail.

## Section

Alpha calls Beta once.

~~~mermaid
sequenceDiagram
  %%{init: {"themeVariables": {"actorBkg": "transparent", "actorBorder": "#7d8799", "actorLineColor": "#7d8799", "labelBoxBorderColor": "#7d8799"}}}%%
  box rgba(37,99,235,0.2) Example team
    participant A as Alpha<br/>[SERVICE]
    participant B as Beta<br/>[POSTGRES]
  end
  A->>B: 1: 📦 stores
~~~

> **Sources:** *Alpha [mmd-click.md](mmd-click.md)*
