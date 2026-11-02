<!--
Purpose: Fixture.
Type: explanation
-->

# Title

Audience: nobody.

## Section

Each edge line below uses a link other than `-->`, `-.->`, or `==>`, draws more than one edge, or names an edge id.

```mermaid
graph TD
  A["One<br/>[SERVICE]"]
  B["Two<br/>[SERVICE]"]
  C["Three<br/>[SERVICE]"]
  D["Four<br/>[SERVICE]"]
  A --- B
  A === B
  A -.- B
  A --x B
  A --o B
  A <--> B
  A ~~~ B
  A -..-|"calls"| B
  A -. "calls" .- B
  A e1@-->|"calls"| B
  A -->|"calls"| B & C
  A -->|"calls"| B -->|"calls"| C

  class A,B,C,D own
  classDef own fill:#1a73e833,stroke:#1a73e8
```

**Legend:** 🟦 Example team

| Node | Source |
| --- | --- |
| One | - |
| Two | - |
| Three | - |
| Four | - |
