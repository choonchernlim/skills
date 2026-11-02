<!--
Purpose: Fixture.
Type: explanation
-->

# Node Drift

Audience: maintainers, to see one rule fail.

The same title points at a file here.

```mermaid
graph TD
  Omega["Omega<br/>[SERVICE]"]
  Phi["Phi<br/>[SERVICE]"]
  Chi["Chi<br/>[SERVICE]"]
  Psi["Psi<br/>[SERVICE]"]
  Omega -->|"calls"| Phi
  Phi -->|"calls"| Chi
  Chi -->|"calls"| Psi

  class Omega,Phi,Chi,Psi own
  classDef own fill:#1a73e833,stroke:#1a73e8
```

**Legend:** 🟦 Example team

| Node | Source |
| --- | --- |
| Omega | [link.md](link.md) |
| Phi | - |
| Chi | - |
| Psi | - |
