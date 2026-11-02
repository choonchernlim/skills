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

  class One,Two,Three,Four own
  class App boundary
  classDef own fill:#1a73e833,stroke:#1a73e8
  classDef boundary fill:#f9ab0014,stroke:#f9ab00
```

**Legend:** 🟦 Example team

| Node | Source |
| --- | --- |
| Application Deployment Boundary [DEPLOYMENT] | - |
| One | - |
| Two | - |
| Three | - |
| Four | - |
