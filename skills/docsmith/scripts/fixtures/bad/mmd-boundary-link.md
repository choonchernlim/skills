<!--
Purpose: Fixture.
Type: explanation
-->

# Boundary Link

Audience: maintainers, to see one rule fail.

An edge ends on the boundary instead of a node inside it.

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
  Four -->|"reports to"| App
```

| Node | Source |
| --- | --- |
| Application [DEPLOYMENT] | - |
| One | - |
| Two | - |
| Three | - |
| Four | - |
