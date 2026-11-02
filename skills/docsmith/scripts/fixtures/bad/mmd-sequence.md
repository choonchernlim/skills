<!--
Purpose: Fixture.
Type: explanation
-->

# Title

Audience: nobody.

## Section

Lead.

```mermaid
sequenceDiagram
  box rgba(26,115,232,0.2) Example team
    actor Customer as Customer<br/>[PERSON]
    participant Browser as 1. Storefront UI<br/>[UI]
    participant Route as Order API<br/>[API]
  end

  Customer->>Browser: Submit the cart
  Browser->>Route: 2: Create the order
```

| Node | Source |
| --- | --- |
| Customer | - |
| 1. Storefront UI | - |
| Order API | - |
