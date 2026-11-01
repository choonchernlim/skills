<!--
Purpose: Fixture.
Type: explanation
-->

# Color Palette

Audience: maintainers, to see one rule fail.

The block defines a color outside the palette.

```mermaid
graph TD
  One["One<br/>[SERVICE]"]
  Two["Two<br/>[SERVICE]"]
  Three["Three<br/>[SERVICE]"]
  Four["Four<br/>[SERVICE]"]
  One -->|"calls"| Two
  Two -->|"calls"| Three
  Three -->|"calls"| Four
  class One,Two,Three own
  class Four red
  classDef own fill:#1a73e833,stroke:#1a73e8
  classDef red fill:#ff0000
```

**Legend:** 🟦 Platform team

| Node | Source |
| --- | --- |
| One | - |
| Two | - |
| Three | - |
| Four | - |
