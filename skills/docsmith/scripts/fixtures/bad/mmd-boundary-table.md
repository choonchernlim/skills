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

  class One,Two,Three,Four own
  class App boundary
  classDef own fill:#1a73e833,stroke:#1a73e8
  classDef boundary fill:#f9ab0014,stroke:#f9ab00
```

**Legend:** 🟦 Example team

| Node | Source |
| --- | --- |
| One | - |
| Two | - |
| Three | - |
| Four | - |
