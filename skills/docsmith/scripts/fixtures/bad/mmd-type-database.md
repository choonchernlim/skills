<!--
Purpose: Fixture.
Type: explanation
-->

# Title

> **Audience:** maintainers, to see one rule fail.

## Section

Alpha writes to two stores.

```mermaid
sequenceDiagram
  %%{init: {"themeVariables": {"actorBkg": "transparent", "actorBorder": "#7d8799", "actorLineColor": "#7d8799", "labelBoxBorderColor": "#7d8799"}}}%%
  box rgba(37,99,235,0.2) Example team
    participant A as Alpha<br/>[SERVICE]
    participant B as Orders<br/>[DATABASE]
    participant C as Carts<br/>[POSTGRESS]
  end
  A->>B: 1: writes
  A->>C: 2: writes
```

> **Sources:** *Alpha [mmd-click.md](mmd-click.md)*
