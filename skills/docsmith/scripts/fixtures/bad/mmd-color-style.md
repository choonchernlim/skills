<!--
Purpose: Fixture.
Type: explanation
-->

# Color Style

Audience: maintainers, to see one rule fail.

The block styles a node directly.

```mermaid
graph TD
  One["One<br/>[SERVICE]"]
  Two["Two<br/>[SERVICE]"]
  Three["Three<br/>[SERVICE]"]
  Four["Four<br/>[SERVICE]"]
  One -->|"calls"| Two
  Two -->|"calls"| Three
  Three -->|"calls"| Four
  class One,Two,Three,Four own
  style Four fill:#ff0000
  classDef own fill:#1a73e833,stroke:#1a73e8
```

**Legend:** 🟦 Platform team

| Node | Source |
| --- | --- |
| One | - |
| Two | - |
| Three | - |
| Four | - |
