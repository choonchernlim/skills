<!--
Purpose: Fixture.
Type: explanation
-->

# Architecture

Audience: maintainers, to see one rule fail.

The owner file, inside a domain folder, holds another family.

```mermaid
sequenceDiagram
  box rgba(26,115,232,0.2) Example team
    participant Customer as Customer<br/>[PERSON]
    participant Route as Order API<br/>[API]
  end
  Customer->>Route: 1: Create the order
```

| Node | Source |
| --- | --- |
| Customer | - |
| Order API | - |
