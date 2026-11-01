<!--
Purpose: Fixture.
Type: explanation
-->

# Color Rules

Audience: maintainers, to see each color and legend rule fail.

A ':::' shorthand colors a node.

```mermaid
graph TD
  One["One<br/>[SERVICE]"]
  Two["Two<br/>[SERVICE]"]
  Three["Three<br/>[SERVICE]"]
  Four["Four<br/>[SERVICE]"]
  One -->|"calls"| Two
  Two -->|"calls"| Three
  Three -->|"calls"| Four
  class One,Two,Three own
  Four:::own
  classDef own fill:#1a73e833,stroke:#1a73e8
```

**Legend:** 🟦 Platform team

| Node | Source |
| --- | --- |
| One | - |
| Two | - |
| Three | - |
| Four | - |

A 'linkStyle' line colors an edge.

```mermaid
graph TD
  One["One<br/>[SERVICE]"]
  Two["Two<br/>[SERVICE]"]
  Three["Three<br/>[SERVICE]"]
  Four["Four<br/>[SERVICE]"]
  One -->|"calls"| Two
  Two -->|"calls"| Three
  Three -->|"calls"| Four
  class One,Two,Three,Four own
  linkStyle 0 stroke:#ff0000
  classDef own fill:#1a73e833,stroke:#1a73e8
```

**Legend:** 🟦 Platform team

| Node | Source |
| --- | --- |
| One | - |
| Two | - |
| Three | - |
| Four | - |

A palette class has the wrong definition.

```mermaid
graph TD
  One["One<br/>[SERVICE]"]
  Two["Two<br/>[SERVICE]"]
  Three["Three<br/>[SERVICE]"]
  Four["Four<br/>[SERVICE]"]
  One -->|"calls"| Two
  Two -->|"calls"| Three
  Three -->|"calls"| Four
  class One,Two,Three,Four own
  classDef own fill:#1a73e833
```

**Legend:** 🟦 Platform team

| Node | Source |
| --- | --- |
| One | - |
| Two | - |
| Three | - |
| Four | - |

A boundary takes a color.

```mermaid
graph TD
  subgraph Box["Box"]
    direction TB
  One["One<br/>[SERVICE]"]
  Two["Two<br/>[SERVICE]"]
  Three["Three<br/>[SERVICE]"]
  Four["Four<br/>[SERVICE]"]
  end
  One -->|"calls"| Two
  Two -->|"calls"| Three
  Three -->|"calls"| Four
  class Box,One,Two,Three,Four own
  classDef own fill:#1a73e833,stroke:#1a73e8
```

**Legend:** 🟦 Platform team

| Node | Source |
| --- | --- |
| Box [DEPLOYMENT] | - |
| One | - |
| Two | - |
| Three | - |
| Four | - |

An agent node takes an owner class.

```mermaid
graph TD
  One["One<br/>[SERVICE]"]
  Two["Two<br/>[SERVICE]"]
  Three["Three<br/>[SERVICE]"]
  Four["Four<br/>[AGENT]"]
  One -->|"calls"| Two
  Two -->|"calls"| Three
  Three -->|"calls"| Four
  class One,Two,Three,Four own
  classDef own fill:#1a73e833,stroke:#1a73e8
```

**Legend:** 🟦 Platform team

| Node | Source |
| --- | --- |
| One | - |
| Two | - |
| Three | - |
| Four | - |

The legend misses a swatch.

```mermaid
graph TD
  One["One<br/>[SERVICE]"]
  Two["Two<br/>[SERVICE]"]
  Three["Three<br/>[SERVICE]"]
  Four["Four<br/>[SERVICE]"]
  One -->|"calls"| Two
  Two -->|"calls"| Three
  Three -->|"calls"| Four
  class One,Two own
  class Three,Four peer
  classDef own fill:#1a73e833,stroke:#1a73e8
  classDef peer fill:#18803833,stroke:#188038
```

**Legend:** 🟦 Platform team

| Node | Source |
| --- | --- |
| One | - |
| Two | - |
| Three | - |
| Four | - |

The legend names a swatch the diagram does not use.

```mermaid
graph TD
  One["One<br/>[SERVICE]"]
  Two["Two<br/>[SERVICE]"]
  Three["Three<br/>[SERVICE]"]
  Four["Four<br/>[SERVICE]"]
  One -->|"calls"| Two
  Two -->|"calls"| Three
  Three -->|"calls"| Four
  class One,Two,Three,Four own
  classDef own fill:#1a73e833,stroke:#1a73e8
```

**Legend:** 🟦 Platform team · 🟩 Partner team

| Node | Source |
| --- | --- |
| One | - |
| Two | - |
| Three | - |
| Four | - |

A sequence diagram takes a color.

```mermaid
sequenceDiagram
  participant A as Alpha<br/>[SERVICE]
  participant B as Beta<br/>[SERVICE]
  A->>B: 1: calls
  classDef own fill:#1a73e833,stroke:#1a73e8
```

| Node | Source |
| --- | --- |
| Alpha | - |
| Beta | - |

A class has no classDef.

```mermaid
graph TD
  One["One<br/>[SERVICE]"]
  Two["Two<br/>[SERVICE]"]
  Three["Three<br/>[SERVICE]"]
  Four["Four<br/>[SERVICE]"]
  One -->|"calls"| Two
  Two -->|"calls"| Three
  Three -->|"calls"| Four
  class One,Two,Three,Four own
```

| Node | Source |
| --- | --- |
| One | - |
| Two | - |
| Three | - |
| Four | - |

A class line names a missing node.

```mermaid
graph TD
  One["One<br/>[SERVICE]"]
  Two["Two<br/>[SERVICE]"]
  Three["Three<br/>[SERVICE]"]
  Four["Four<br/>[SERVICE]"]
  One -->|"calls"| Two
  Two -->|"calls"| Three
  Three -->|"calls"| Four
  class One,Two,Three,Four,Five own
  classDef own fill:#1a73e833,stroke:#1a73e8
```

**Legend:** 🟦 Platform team

| Node | Source |
| --- | --- |
| One | - |
| Two | - |
| Three | - |
| Four | - |

A class line puts a space after a comma.

```mermaid
graph TD
  One["One<br/>[SERVICE]"]
  Two["Two<br/>[SERVICE]"]
  Three["Three<br/>[SERVICE]"]
  Four["Four<br/>[SERVICE]"]
  One -->|"calls"| Two
  Two -->|"calls"| Three
  Three -->|"calls"| Four
  class One, Two own
  class Three,Four own
  classDef own fill:#1a73e833,stroke:#1a73e8
```

**Legend:** 🟦 Platform team

| Node | Source |
| --- | --- |
| One | - |
| Two | - |
| Three | - |
| Four | - |

A node takes two classes.

```mermaid
graph TD
  One["One<br/>[SERVICE]"]
  Two["Two<br/>[SERVICE]"]
  Three["Three<br/>[SERVICE]"]
  Four["Four<br/>[SERVICE]"]
  One -->|"calls"| Two
  Two -->|"calls"| Three
  Three -->|"calls"| Four
  class One,Two,Three,Four own
  class Four peer
  classDef own fill:#1a73e833,stroke:#1a73e8
  classDef peer fill:#18803833,stroke:#188038
```

**Legend:** 🟦 Platform team · 🟩 Partner team

| Node | Source |
| --- | --- |
| One | - |
| Two | - |
| Three | - |
| Four | - |

The legend sits under the Node table instead of the diagram.

```mermaid
graph TD
  One["One<br/>[SERVICE]"]
  Two["Two<br/>[SERVICE]"]
  Three["Three<br/>[SERVICE]"]
  Four["Four<br/>[SERVICE]"]
  One -->|"calls"| Two
  Two -->|"calls"| Three
  Three -->|"calls"| Four
  class One,Two,Three,Four own
  classDef own fill:#1a73e833,stroke:#1a73e8
```

| Node | Source |
| --- | --- |
| One | - |
| Two | - |
| Three | - |
| Four | - |

**Legend:** 🟦 Platform team

A classDef is never assigned.

```mermaid
graph TD
  One["One<br/>[SERVICE]"]
  Two["Two<br/>[SERVICE]"]
  Three["Three<br/>[SERVICE]"]
  Four["Four<br/>[SERVICE]"]
  One -->|"calls"| Two
  Two -->|"calls"| Three
  Three -->|"calls"| Four
  class One,Two,Three,Four own
  classDef own fill:#1a73e833,stroke:#1a73e8
  classDef peer fill:#18803833,stroke:#188038
```

**Legend:** 🟦 Platform team

| Node | Source |
| --- | --- |
| One | - |
| Two | - |
| Three | - |
| Four | - |

A node drawn only on an edge stays plain.

```mermaid
graph TD
  One["One<br/>[SERVICE]"]
  Two["Two<br/>[SERVICE]"]
  Three["Three<br/>[SERVICE]"]
  Four["Four<br/>[SERVICE]"]
  One -->|"calls"| Two
  Two -->|"calls"| Three
  Three -->|"calls"| Four
  Four -->|"calls"| Five
  class One,Two,Three,Four own
  classDef own fill:#1a73e833,stroke:#1a73e8
```

**Legend:** 🟦 Platform team

| Node | Source |
| --- | --- |
| One | - |
| Two | - |
| Three | - |
| Four | - |

A valid colored diagram sits above one without a lead sentence.

```mermaid
graph TD
  One["One<br/>[SERVICE]"]
  Two["Two<br/>[SERVICE]"]
  Three["Three<br/>[SERVICE]"]
  Four["Four<br/>[SERVICE]"]
  One -->|"calls"| Two
  Two -->|"calls"| Three
  Three -->|"calls"| Four
  class One,Two,Three,Four own
  classDef own fill:#1a73e833,stroke:#1a73e8
```

**Legend:** 🟦 Platform team

| Node | Source |
| --- | --- |
| One | - |
| Two | - |
| Three | - |
| Four | - |

```mermaid
graph TD
  One["One<br/>[SERVICE]"]
  Two["Two<br/>[SERVICE]"]
  Three["Three<br/>[SERVICE]"]
  Four["Four<br/>[SERVICE]"]
  One -->|"calls"| Two
  Two -->|"calls"| Three
  Three -->|"calls"| Four
```

| Node | Source |
| --- | --- |
| One | - |
| Two | - |
| Three | - |
| Four | - |

A legend runs on past one line.

```mermaid
graph TD
  One["One<br/>[SERVICE]"]
  Two["Two<br/>[SERVICE]"]
  Three["Three<br/>[SERVICE]"]
  Four["Four<br/>[SERVICE]"]
  One -->|"calls"| Two
  Two -->|"calls"| Three
  Three -->|"calls"| Four
  class One,Two,Three,Four own
  classDef own fill:#1a73e833,stroke:#1a73e8
```

**Legend:** 🟦 Platform team
and a second line that explains more.

| Node | Source |
| --- | --- |
| One | - |
| Two | - |
| Three | - |
| Four | - |

A diagram without color carries a swatch legend.

```mermaid
graph TD
  One["One<br/>[SERVICE]"]
  Two["Two<br/>[SERVICE]"]
  Three["Three<br/>[SERVICE]"]
  Four["Four<br/>[SERVICE]"]
  One -->|"calls"| Two
  Two -->|"calls"| Three
  Three -->|"calls"| Four
```

**Legend:** 🟦 Platform team

| Node | Source |
| --- | --- |
| One | - |
| Two | - |
| Three | - |
| Four | - |

A second legend sits under the Node table.

```mermaid
graph TD
  One["One<br/>[SERVICE]"]
  Two["Two<br/>[SERVICE]"]
  Three["Three<br/>[SERVICE]"]
  Four["Four<br/>[SERVICE]"]
  One -->|"calls"| Two
  Two -->|"calls"| Three
  Three -->|"calls"| Four
  class One,Two,Three,Four own
  classDef own fill:#1a73e833,stroke:#1a73e8
```

**Legend:** 🟦 Platform team

| Node | Source |
| --- | --- |
| One | - |
| Two | - |
| Three | - |
| Four | - |

**Legend:** 🟦 Platform team

The legend sits between the numbered list and the Node table.

```mermaid
graph TD
  One["One<br/>[SERVICE]"]
  Two["Two<br/>[SERVICE]"]
  Three["Three<br/>[SERVICE]"]
  Four["Four<br/>[SERVICE]"]
  One -->|"1: calls"| Two
  Two -->|"calls"| Three
  Three -->|"calls"| Four
  class One,Two,Three,Four own
  classDef own fill:#1a73e833,stroke:#1a73e8
```

1. One calls two.

**Legend:** 🟦 Platform team

| Node | Source |
| --- | --- |
| One | - |
| Two | - |
| Three | - |
| Four | - |
