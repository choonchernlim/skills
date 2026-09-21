<!--
Purpose: Fixture.
Type: explanation
-->

# Boundary Table

Audience: maintainers, to see one rule fail.

The Node table never states the boundary type.

```mermaid
graph TD
  subgraph App["Application"]
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
