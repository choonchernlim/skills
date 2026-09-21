<!--
Purpose: Fixture.
Type: explanation
-->

# Frontmatter Stray

Audience: maintainers, to see one rule fail.

No boundary needs the margin here.

```mermaid
---
config:
  flowchart:
    subGraphTitleMargin:
      top: 4
      bottom: 32
---
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
