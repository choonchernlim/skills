<!--
Purpose: Fixture.
Type: explanation
-->

# Title

Audience: nobody.

## Section

Each edge below hides an unquoted label from the other edge checks.

```mermaid
graph TD
  A["One<br/>[SERVICE]"]
  B["Two<br/>[SERVICE]"]
  C["Three<br/>[SERVICE]"]
  D["Four<br/>[SERVICE]"]
  A -->|calls| B
  B --calls--> C
  C -. calls .-> D
  A ==calls==> D
  B -->|"calls" more| D

  class A,B,C,D own
  classDef own fill:#1a73e833,stroke:#1a73e8
```

**Legend:** 🟦 Example team

| Node | Source |
| --- | --- |
| One | - |
| Two | - |
| Three | - |
| Four | - |
