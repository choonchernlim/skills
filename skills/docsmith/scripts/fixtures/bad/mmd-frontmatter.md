<!--
Purpose: Fixture.
Type: explanation
-->

# Frontmatter

Audience: maintainers, to see one rule fail.

The block opens with configuration instead of the diagram type.

```mermaid
---
config:
  flowchart:
    subGraphTitleMargin:
      top: 4
      bottom: 32
---
graph TD
  subgraph App["Application"]
    direction TB
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
| Application [DEPLOYMENT] | - |
| One | - |
| Two | - |
| Three | - |
| Four | - |
