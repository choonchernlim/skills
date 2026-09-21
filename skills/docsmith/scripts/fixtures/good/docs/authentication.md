<!--
Purpose: How a customer proves who they are and how the order API trusts each request.
Type: explanation
-->

# Authentication

Audience: all teams, to answer how a request proves who sent it.

## Customer Login

The storefront trades a login for a token, and the API verifies that token on
every call.

```mermaid
sequenceDiagram
  participant Customer as Customer<br/>[PERSON]
  participant Browser as Storefront UI<br/>[UI]
  participant Identity as Identity Provider<br/>[SYSTEM]
  participant Route as Order API<br/>[API]

  Customer->>Browser: 1: Enter credentials
  Browser->>Identity: 2: Request a token
  Identity-->>Browser: 3: Issue the token
  Browser->>Route: 4: Send the token
  Route->>Identity: 5: Verify the token
  Identity-->>Route: 6: Confirm the customer
```

| Node | Source |
| --- | --- |
| Customer | - |
| Storefront UI | [../src/](../src/) |
| Identity Provider | - |
| Order API | [../src/api.ts](../src/api.ts) |

The API holds no passwords. It rejects any call whose token the identity
provider does not confirm.
