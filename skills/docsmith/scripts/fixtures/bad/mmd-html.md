<!--
Purpose: Fixture.
Type: explanation
-->

# Markup

Audience: maintainers, to see one rule fail.

An edge label holds markup other than a line break.

```mermaid
graph TD
  One["One<br/>[SERVICE]"]
  Two["Two<br/>[SERVICE]"]
  Three["Three<br/>[SERVICE]"]
  Four["Four<br/>[SERVICE]"]
  One -->|"<b>calls</b>"| Two
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
