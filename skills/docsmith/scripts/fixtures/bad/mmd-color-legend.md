<!--
Purpose: Fixture.
Type: explanation
-->

# Color Legend

Audience: maintainers, to see one rule fail.

The block uses color but has no legend under the diagram.

```mermaid
graph TD
  One["One<br/>[SERVICE]"]
  Two["Two<br/>[SERVICE]"]
  Three["Three<br/>[SERVICE]"]
  Four["Four<br/>[SERVICE]"]
  One -->|"calls"| Two
  Two -->|"calls"| Three
  Three -->|"calls"| Four
  class One,Two own
  class Three,Four peer
  classDef own fill:#1a73e833,stroke:#1a73e8
  classDef peer fill:#18803833,stroke:#188038
```

| Node | Source |
| --- | --- |
| One | - |
| Two | - |
| Three | - |
| Four | - |
