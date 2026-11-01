<!--
Purpose: Fixture.
Type: explanation
-->

# Title

Audience: nobody.

## Section

Nodes B, C, and E to K each break the shape rule once.

```mermaid
graph TD
  A["One<br/>[UI]"]
  B["Two<br/>[DATABASE]"]
  C[("Three<br/>[API]")]
  D["Four<br/>[SERVICE]"]
  E(["Five<br/>[SERVICE]"])
  F[/"Six<br/>[API]"\]
  G("Seven<br/>[SERVICE]")
  H(("Eight<br/>[SERVICE]"))
  I{"Nine<br/>[SERVICE]"}
  J((("Ten<br/>[SERVICE]")))
  K@{ shape: circle, label: "Eleven" }
  A -->|"calls"| C
  C -->|"stores"| B
  C -->|"notifies"| D
  D -->|"calls"| E
  D -->|"calls"| F
  D -->|"calls"| G
  D -->|"calls"| H
  D -->|"calls"| I
  D -->|"calls"| J
  D -->|"calls"| K
```

| Node | Source |
| --- | --- |
| One | - |
| Two | - |
| Three | - |
| Four | - |
| Five | - |
| Six | - |
| Seven | - |
| Eight | - |
| Nine | - |
| Ten | - |
| Eleven | - |
