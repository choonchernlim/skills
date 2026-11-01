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
```

| Node | Source |
| --- | --- |
| One | - |
| Two | - |
| Three | - |
| Four | - |
