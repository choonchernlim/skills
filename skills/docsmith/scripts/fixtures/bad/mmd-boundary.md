<!--
Purpose: Fixture.
Type: explanation
-->

# Boundary

Audience: maintainers, to see one rule fail.

The boundary title carries its type.

```mermaid
graph TD
  subgraph App["Application [DEPLOYMENT]"]
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
