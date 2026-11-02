<!--
Purpose: Fixture.
Type: explanation
-->

# Band

Audience: maintainers, to see one rule fail.

The block leaves a participant outside a band, uses a hex and a model color, sends a message inside a band, calls an undeclared participant, and creates one mid-flow.

```mermaid
sequenceDiagram
  participant A as Alpha<br/>[SERVICE]
  box #1a73e833 Platform team
    participant B as Beta<br/>[SERVICE]
  end
  box rgba(147,52,230,0.2) Model team
    participant C as Gamma<br/>[AGENT]
  end
  box rgba(24,128,56,0.2) Partner team
    participant D as Delta<br/>[SERVICE]
    D->>A: 1: calls
  end
  A->>B: 2: calls
  B->>E: 3: calls
  create participant F as Phi<br/>[SERVICE]
  B->>F: 4: calls
```

| Node | Source |
| --- | --- |
| Alpha | - |
| Beta | - |
| Gamma | - |
| Delta | - |

The next block never closes its band.

```mermaid
sequenceDiagram
  box rgba(26,115,232,0.2) Platform team
    participant P as Pi<br/>[SERVICE]
    participant R as Rho<br/>[SERVICE]
  R->>P: 1: answers
```

| Node | Source |
| --- | --- |
| Pi | - |
| Rho | - |
