<!--
Purpose: Fixture.
Type: explanation
-->

# Color Model

Audience: maintainers, to see one rule fail.

The block marks a deterministic service as a model call.

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
  class Four model
  classDef own fill:#1a73e833,stroke:#1a73e8
  classDef model fill:#9334e633,stroke:#9334e6,stroke-width:3px
```

**Legend:** 🟦 Platform team · 🟪 model call

| Node | Source |
| --- | --- |
| One | - |
| Two | - |
| Three | - |
| Four | - |
