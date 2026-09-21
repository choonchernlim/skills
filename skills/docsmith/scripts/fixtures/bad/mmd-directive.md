<!--
Purpose: Fixture.
Type: explanation
-->

# Directive

Audience: maintainers, to see one rule fail.

The block opens with an init directive instead of the diagram type.

```mermaid
%%{init: {'theme': 'neutral'}}%%
graph TD
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
