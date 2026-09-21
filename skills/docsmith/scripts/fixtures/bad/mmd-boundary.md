<!--
Purpose: Bad boundary fixture.
Type: explanation
-->

# Boundary

Audience: maintainers, to see a malformed boundary fail.

The components are grouped by a boundary with an untyped centered label.

```mermaid
flowchart TD
  subgraph App["Application"]
    One["One<br/>[SERVICE]"]
    Two["Two<br/>[SERVICE]"]
    Three["Three<br/>[SERVICE]"]
    Four["Four<br/>[SERVICE]"]
  end
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
