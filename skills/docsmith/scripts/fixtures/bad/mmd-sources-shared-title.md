<!--
Purpose: Fixture.
Type: explanation
-->

# Sources Shared Title

> **Audience:** maintainers, to see one rule fail.

## Place an Order

The API reserves stock before it accepts the cart.

```mermaid
sequenceDiagram
  %%{init: {"themeVariables": {"actorBkg": "transparent", "actorBorder": "#7d8799", "actorLineColor": "#7d8799", "labelBoxBorderColor": "#7d8799"}}}%%
  box rgba(225,29,72,0.2) Customers
    participant Customer as Customer<br/>[PERSON]
  end
  box rgba(37,99,235,0.2) Example team
    participant Browser as Storefront<br/>[UI]
    participant Route as Order<br/>[API]
    participant Inventory as Inventory Client<br/>[SERVICE]
    participant Store as Order<br/>[DATA]
  end

  Customer->>Browser: 1: Submit the cart
  Browser->>Route: 2: Create the order
  Route->>Inventory: 3: Reserve stock
  Inventory-->>Route: 4: Confirm the reservation
  Route->>Store: 5: Save the order
```

1. The customer submits the current cart.
2. The storefront asks the API to create an order.
3. The API asks the inventory client to reserve stock.
4. The inventory client confirms the reservation.
5. The API saves the order.

> **Sources:** *Storefront [mmd-sources.md](mmd-sources.md) · Order [mmd-sources.md](mmd-sources.md) · Inventory Client [mmd-sources.md](mmd-sources.md) · Order [mmd-sources.md](mmd-sources.md)*
