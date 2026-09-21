<!--
Purpose: Fixture.
Type: explanation
-->

# Boundary Width

Audience: maintainers, to see one rule fail.

The boundary label width is a hand-tuned guess.

```mermaid
---
config:
  flowchart:
    subGraphTitleMargin:
      top: 4
      bottom: 32
---
flowchart TD
  subgraph App["<span style='display:inline-block;width:320px;text-align:left'>Application<br/>[DEPLOYMENT]</span>"]
    direction TB
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
