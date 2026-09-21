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
```

| Node | Source |
| --- | --- |
| Alpha | - |
| Beta | - |
| Gamma | - |
| Delta | - |
