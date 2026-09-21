<!--
Purpose: The requirements profile: functional and non-functional requirements grouped by domain, one short user-perspective sentence each.
Type: reference
-->

# Requirements Profile

Audience: the writer, when the target is `docs/requirements.md`.

Requirements state what the product does for its users and what qualities
the system holds. Each one is a single sentence a product owner can read
aloud. Explanation, design, and procedure live elsewhere.

## Shape

Cap: 300 lines. Past that, one file per domain under `docs/requirements/`
with `docs/requirements.md` as the index.

```markdown
<!--
Purpose: The functional and non-functional requirements, grouped by domain, with status and evidence.
Type: requirements
-->

# Requirements

Audience: product owners and maintainers checking what the product must do.

## Table of Contents

(Only past 100 lines or 5 H2 sections.)

## Checkout

### Functional

| ID | Requirement | Status | Evidence |
| --- | --- | --- | --- |
| CHECKOUT-001 | A customer MUST be able to submit an order from the cart. | Implemented | [checkout.spec.ts](../tests/checkout.spec.ts) |

### Non-Functional

| ID | Requirement | Status | Evidence |
| --- | --- | --- | --- |
| CHECKOUT-N01 | The system MUST reject duplicate order submissions. | Implemented | [test_orders.py](../tests/test_orders.py) |
```

## Rules

| Rule | Detail |
| --- | --- |
| Domains | One H2 per domain, named with a glossary term. Each has a Functional and a Non-Functional H3. |
| Sentence | One sentence, at most 25 words. Functional ones start with the user: "A customer MUST be able to". |
| Keywords | RFC 2119 words in capitals: MUST, MUST NOT, SHALL, SHOULD, MAY. One keyword per requirement. |
| ID | `DOMAIN-001` for functional, `DOMAIN-N01` for non-functional. Never reused. |
| Status | `Implemented`, `Gap`, or `Future`. |
| Evidence | One link to a test, spec, or source file. Not a list, not prose. |
| Prose | At most one sentence between a heading and its table. |

A requirement that needs two sentences is two requirements. A requirement
that names a file, class, or function is describing a design; move that
detail to the evidence link and restate the behavior the user sees.

## Non-Functional Domains

Non-functional rows cover qualities, not features: performance, security,
reliability, accessibility, and operability. They still read from the
outside: "The system MUST respond to an order submission within 10 seconds
or show an error for that order."
