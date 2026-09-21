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
```

| Node | Source |
| --- | --- |
| Alpha | - |
| Beta | - |
| Kappa | - |
| Sigma | - |
