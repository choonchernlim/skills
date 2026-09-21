<!--
Purpose: Fixture.
Type: explanation
-->

# Node Drift

Audience: maintainers, to see one rule fail.

The same title points at a file here.

```mermaid
flowchart TD
  Omega["Omega<br/>[SERVICE]"]
  Phi["Phi<br/>[SERVICE]"]
  Chi["Chi<br/>[SERVICE]"]
  Psi["Psi<br/>[SERVICE]"]
  Omega -->|"calls"| Phi
  Phi -->|"calls"| Chi
  Chi -->|"calls"| Psi
```

| Node | Source |
| --- | --- |
| Omega | [link.md](link.md) |
| Phi | - |
| Chi | - |
| Psi | - |
