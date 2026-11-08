<!--
Purpose: Fixture.
Type: explanation
-->

# Title

> **Audience:** nobody.

## Section

Lead.

```mermaid
sequenceDiagram
  %%{init: {"themeVariables": {"actorBkg": "transparent", "actorBorder": "#7d8799", "actorLineColor": "#7d8799", "labelBoxBorderColor": "#7d8799"}}}%%
  box rgba(225,29,72,0.2) Shoppers
    actor Customer as Customer<br/>[PERSON]
  end
  box rgba(37,99,235,0.2) Example team
    participant Browser as 1. Storefront<br/>[UI]
    participant Route as Order<br/>[API]
  end

  Customer->>Browser: Submit the cart
  Browser->>Route: 2: Create the order
```
