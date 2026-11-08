<!--
Purpose: How a customer proves who they are and how the order API trusts each request.
Type: explanation
-->

# Authentication

> **Audience:** all teams, to answer how a request proves who sent it.

Every request carries proof of who sent it. This guide shows how a customer gets that proof and how the API checks it.

## Customer Login

The storefront trades a login for a token, and the API verifies that token on
every call.

```mermaid
sequenceDiagram
  %%{init: {"themeVariables": {"actorBkg": "transparent", "actorBorder": "#7d8799", "actorLineColor": "#7d8799", "labelBoxBorderColor": "#7d8799"}}}%%
  box rgba(225,29,72,0.2) Customers
    participant Customer as Customer<br/>[PERSON]
  end
  box rgba(37,99,235,0.2) Example team
    participant Browser as Storefront<br/>[UI]
    participant Identity as Identity Provider<br/>[SYSTEM]
    participant Route as Order<br/>[API]
  end

  Customer->>Browser: 1: Enter credentials
  Browser->>Identity: 2: Request a token
  Identity-->>Browser: 3: Issue the token
  Browser->>Route: 4: Send the token
  Route->>Identity: 5: Verify the token
  Identity-->>Route: 6: Confirm the customer
```

> **Sources:** *Storefront [../../src/README.md](../../src/README.md) · Order [../../src/api.ts](../../src/api.ts)*

The API holds no passwords. It rejects any call whose token the identity
provider does not confirm.
