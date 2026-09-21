<!--
Purpose: Fixture.
Type: explanation
-->

# Architecture

Audience: maintainers, to see one rule fail.

The owner file holds another family.

```mermaid
sequenceDiagram
  participant Customer as Customer<br/>[PERSON]
  participant Route as Order API<br/>[API]
  Customer->>Route: 1: Create the order
```

| Node | Source |
| --- | --- |
| Customer | - |
| Order API | - |
