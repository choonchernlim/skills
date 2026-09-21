<!--
Purpose: Fixture.
Type: explanation
-->

# Boundary Direction

Audience: maintainers, to see one rule fail.

The boundary declares no direction.

```mermaid
---
config:
  flowchart:
    subGraphTitleMargin:
      top: 4
      bottom: 32
---
flowchart TD
  subgraph App["<span style='display:inline-block;width:480px;text-align:left'>Application<br/>[DEPLOYMENT]</span>"]
    One["One<br/>[SERVICE]"]
    Two["Two<br/>[SERVICE]"]
    Three["Three<br/>[SERVICE]"]
    Four["Four<br/>[SERVICE]"]
  end
  One -->|"calls"| Two
  Two -->|"calls"| Three
  Three -->|"calls"| Four
```

| Node | Source |
| --- | --- |
| One | - |
| Two | - |
| Three | - |
| Four | - |
