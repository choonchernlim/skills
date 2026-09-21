<!--
Purpose: Fixture.
Type: explanation
-->

# Boundary Width

Audience: maintainers, to see one rule fail.

The boundary title is long enough to wrap behind its first node.

```mermaid
graph TD
  subgraph App["Application Deployment Boundary"]
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
| Application Deployment Boundary [DEPLOYMENT] | - |
| One | - |
| Two | - |
| Three | - |
| Four | - |
