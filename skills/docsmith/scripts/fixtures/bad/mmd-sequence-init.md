<!--
Purpose: Fixture.
Type: explanation
-->

# Sequence Init

> **Audience:** maintainers, to see one rule fail.

The first block omits the participant line.

```mermaid
sequenceDiagram
  box rgba(37,99,235,0.2) Platform team
    participant A as Alpha<br/>[SERVICE]
    participant B as Beta<br/>[SERVICE]
  end
  A->>B: 1: calls
```

The second block changes the participant line.

```mermaid
sequenceDiagram
  %%{init: {"themeVariables": {"actorBkg": "#ffffff", "actorBorder": "#7d8799", "actorLineColor": "#7d8799", "labelBoxBorderColor": "#7d8799"}}}%%
  box rgba(37,99,235,0.2) Platform team
    participant A as Alpha<br/>[SERVICE]
    participant B as Beta<br/>[SERVICE]
  end
  A->>B: 1: calls
```
