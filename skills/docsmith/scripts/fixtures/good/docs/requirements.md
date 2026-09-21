<!--
Purpose: The functional and non-functional requirements, grouped by domain, with status and evidence.
Type: requirements
-->

# Requirements

Audience: product owners and maintainers checking what the product must do.

## Checkout

### Functional

| ID | Requirement | Status | Evidence |
| --- | --- | --- | --- |
| CHECKOUT-001 | A customer MUST be able to submit an order from the cart. | Implemented | [api.ts](../src/api.ts) |

### Non-Functional

| ID | Requirement | Status | Evidence |
| --- | --- | --- | --- |
| CHECKOUT-N01 | The system MUST reject duplicate order submissions. | Implemented | [api.ts](../src/api.ts) |
