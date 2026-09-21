<!--
Purpose: Fixture.
Type: explanation
-->

# Node Owner

Audience: maintainers, to see one rule fail.

The title has no source here.

```mermaid
flowchart TD
  Omega["Omega<br/>[SERVICE]"]
  Pi["Pi<br/>[SERVICE]"]
  Rho["Rho<br/>[SERVICE]"]
  Tau["Tau<br/>[SERVICE]"]
  Omega -->|"calls"| Pi
  Pi -->|"calls"| Rho
  Rho -->|"calls"| Tau
```

| Node | Source |
| --- | --- |
| Omega | - |
| Pi | - |
| Rho | - |
| Tau | - |
