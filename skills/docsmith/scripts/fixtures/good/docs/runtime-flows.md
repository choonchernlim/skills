<!--
Purpose: The order of events on each request path that crosses a component boundary.
Type: explanation
-->

# Runtime Flows

> **Audience:** all teams, to trace one request end to end.

A request crosses both deployments in a fixed order. This guide follows each flow step by step.

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

> **Sources:** *Storefront [../src/README.md](../src/README.md) · Order [API] [../src/api.ts](../src/api.ts) · Inventory Client [../src/inventory/client.ts](../src/inventory/client.ts) · Order [DATA] [../src/README.md](../src/README.md)*

An order moves through three states.

| State | Meaning |
| --- | --- |
| `open` | The cart holds items |
| `paid` | Payment cleared |
| `shipped` | The parcel left the warehouse |

> **Sources:** *[../src/api.ts](../src/api.ts) · [Order states](https://example.com/order-states)*

> ⚠️ **Warning:** A cancelled order keeps its payment until the refund clears.

- 🔐 The cart owner alone sees the order.
- 🧾 Each state change writes one history row.
- 📦 Orders stay for seven years.

| Check | Result |
| --- | --- |
| Refund | 🟡 Pending |
| Receipt | ✅ Sent |

> **Legend:** *✅ done · 🟡 pending*

Press ⌘ K to search the orders, and a ✓ beside a row marks it shipped.
