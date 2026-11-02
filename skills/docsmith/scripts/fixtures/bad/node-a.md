<!--
Purpose: Fixture.
Type: explanation
-->

# Node Owner

Audience: maintainers, to see one rule fail.

The title has no source here.

```mermaid
graph TD
  Omega["Omega<br/>[SERVICE]"]
  Pi["Pi<br/>[SERVICE]"]
  Rho["Rho<br/>[SERVICE]"]
  Tau["Tau<br/>[SERVICE]"]
  Omega -->|"calls"| Pi
  Pi -->|"calls"| Rho
  Rho -->|"calls"| Tau

  class Omega,Pi,Rho,Tau own
  classDef own fill:#1a73e833,stroke:#1a73e8
```

**Legend:** 🟦 Example team

| Node | Source |
| --- | --- |
| Omega | - |
| Pi | - |
| Rho | - |
| Tau | - |
