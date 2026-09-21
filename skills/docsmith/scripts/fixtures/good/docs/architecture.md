<!--
Purpose: The deployments, who owns each, and the one allowed dependency direction.
Type: explanation
-->

# Architecture

Audience: all teams, to answer what exists and who owns it.

## Deployments

Two teams ship independently, and only a versioned contract crosses the line
between them.

```mermaid
graph TD
  subgraph Web["Web Team"]
    direction TB
    Browser["Storefront UI<br/>[UI]"]
  end

  subgraph Orders["Order Team"]
    direction TB
    Route[/"Order API<br/>[API]"/]
    Inventory["Inventory Client<br/>[SERVICE]"]
    Store[("Order Store<br/>[DATABASE]")]
  end

  Identity["Identity Provider<br/>[SYSTEM]"]
  Warehouse["Warehouse System<br/>[SYSTEM]"]

  Browser -->|"signs in"| Identity
  Browser -->|"sends orders"| Route
  Route -->|"reserves stock"| Inventory
  Route -->|"stores orders"| Store
  Inventory -->|"queries"| Warehouse
```

| Node | Source |
| --- | --- |
| Web Team [DEPLOYMENT] | - |
| Order Team [DEPLOYMENT] | - |
| Storefront UI | [../src/](../src/) |
| Order API | [../src/api.ts](../src/api.ts) |
| Inventory Client | [../src/inventory/client.ts](../src/inventory/client.ts) |
| Order Store | - |
| Identity Provider | - |
| Warehouse System | - |

The UI never writes inventory directly. The order API coordinates the
reservation so one component owns the transaction boundary.

Sign-in has its own guide: [authentication.md](authentication.md).
