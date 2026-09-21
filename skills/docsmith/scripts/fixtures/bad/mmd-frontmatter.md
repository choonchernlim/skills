<!--
Purpose: Fixture.
Type: explanation
-->

# Frontmatter

Audience: maintainers, to see one rule fail.

The boundary has no title margin.

```mermaid
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
