<!--
Purpose: Fixture.
Type: explanation
-->

# Keyword

Audience: maintainers, to see one rule fail.

The block uses the flowchart keyword.

```mermaid
flowchart TD
  One["One<br/>[SERVICE]"]
  Two["Two<br/>[SERVICE]"]
  Three["Three<br/>[SERVICE]"]
  Four["Four<br/>[SERVICE]"]
  One -->|"calls"| Two
  Two -->|"calls"| Three
  Three -->|"calls"| Four
```

| Node | Source |
| --- | --- |
| One | - |
| Two | - |
| Three | - |
| Four | - |
