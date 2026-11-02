<!--
Purpose: Fixture.
Type: explanation
-->

# Edge Copy

Audience: maintainers, to see one rule fail.

A second file draws it again.

```mermaid
graph TD
  Alpha["Alpha<br/>[SERVICE]"]
  Beta["Beta<br/>[SERVICE]"]
  Kappa["Kappa<br/>[SERVICE]"]
  Sigma["Sigma<br/>[SERVICE]"]
  Alpha -->|"invokes"| Beta
  Beta -->|"notifies"| Kappa
  Kappa -->|"notifies"| Sigma

  class Alpha,Beta,Kappa,Sigma own
  classDef own fill:#1a73e833,stroke:#1a73e8
```

**Legend:** 🟦 Example team

| Node | Source |
| --- | --- |
| Alpha | - |
| Beta | - |
| Kappa | - |
| Sigma | - |
