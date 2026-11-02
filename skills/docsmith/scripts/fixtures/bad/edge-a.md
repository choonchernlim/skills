<!--
Purpose: Fixture.
Type: explanation
-->

# Edge Owner

Audience: maintainers, to see one rule fail.

The first file owns the relationship.

```mermaid
graph TD
  Alpha["Alpha<br/>[SERVICE]"]
  Beta["Beta<br/>[SERVICE]"]
  Gamma["Gamma<br/>[SERVICE]"]
  Delta["Delta<br/>[SERVICE]"]
  Alpha -->|"calls"| Beta
  Beta -->|"calls"| Gamma
  Gamma -->|"calls"| Delta

  class Alpha,Beta,Gamma,Delta own
  classDef own fill:#1a73e833,stroke:#1a73e8
```

**Legend:** 🟦 Example team

| Node | Source |
| --- | --- |
| Alpha | - |
| Beta | - |
| Gamma | - |
| Delta | - |
