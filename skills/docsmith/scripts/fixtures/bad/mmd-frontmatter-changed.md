<!--
Purpose: Fixture.
Type: explanation
-->

# Frontmatter Changed

Audience: maintainers, to see one rule fail.

The title margin was tuned by hand.

```mermaid
---
config:
  flowchart:
    subGraphTitleMargin:
      top: 4
      bottom: 40
---
flowchart TD
  subgraph App["<span style='display:inline-block;width:480px;text-align:left'>Application<br/>[DEPLOYMENT]</span>"]
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
