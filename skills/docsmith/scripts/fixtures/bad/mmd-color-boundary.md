<!--
Purpose: Fixture.
Type: explanation
-->

# Color Boundary

Audience: maintainers, to see one rule fail.

The block leaves one boundary plain and gives a node the boundary class.

```mermaid
graph TD
  subgraph App["Application"]
    direction TB
    One["One<br/>[SERVICE]"]
    Two["Two<br/>[SERVICE]"]
  end
  subgraph Data["Data"]
    direction TB
    Three["Three<br/>[SERVICE]"]
    Four["Four<br/>[SERVICE]"]
  end
  One -->|"calls"| Two
  Two -->|"calls"| Three
  Three -->|"calls"| Four
  class One,Two,Three own
  class Four boundary
  class Data boundary
  classDef own fill:#1a73e833,stroke:#1a73e8
  classDef boundary fill:#f9ab0014,stroke:#f9ab00
```

**Legend:** 🟦 Platform team

| Node | Source |
| --- | --- |
| Application [DEPLOYMENT] | - |
| Data [DEPLOYMENT] | - |
| One | - |
| Two | - |
| Three | - |
| Four | - |
