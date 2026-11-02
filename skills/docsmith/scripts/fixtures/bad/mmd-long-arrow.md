<!--
Purpose: Fixture.
Type: explanation
-->

# Long Arrow

Audience: maintainers, to see one rule fail.

Three edges use a lengthened arrow.

```mermaid
graph TD
  One["One<br/>[SERVICE]"]
  Two["Two<br/>[SERVICE]"]
  Three["Three<br/>[SERVICE]"]
  Four["Four<br/>[SERVICE]"]
  One -. "calls" ..-> Two
  Two --->|"calls"| Three
  Three ---->|"calls"| Four

  class One,Two,Three,Four own
  classDef own fill:#1a73e833,stroke:#1a73e8
```

**Legend:** 🟦 Example team

| Node | Source |
| --- | --- |
| One | - |
| Two | - |
| Three | - |
| Four | - |
