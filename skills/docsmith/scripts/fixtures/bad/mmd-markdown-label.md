<!--
Purpose: Fixture.
Type: explanation
-->

# Markdown Label

Audience: maintainers, to see one rule fail.

A step number is written as a Markdown list marker.

```mermaid
graph TD
  One["One<br/>[SERVICE]"]
  Two["Two<br/>[SERVICE]"]
  Three["Three<br/>[SERVICE]"]
  Four["Four<br/>[SERVICE]"]
  One -->|"1. calls"| Two
  Two -->|"calls"| Three
  Three -->|"calls"| Four

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
