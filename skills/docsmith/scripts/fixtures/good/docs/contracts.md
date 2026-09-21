<!--
Purpose: The fields of each payload that crosses the team boundary, with eight sections so the table of contents outgrows the list cap.
Type: reference
-->

# Contracts

Audience: both teams, to answer which fields a payload carries.

## Table of Contents

- [Product Identity](#product-identity)
- [Product Price](#product-price)
- [Inventory Record](#inventory-record)
- [Order Request](#order-request)
- [Order Response](#order-response)
- [Cart Snapshot](#cart-snapshot)
- [Error Envelope](#error-envelope)
- [Version Header](#version-header)

## Product Identity

| Field | Type | Constraint |
| --- | --- | --- |
| `id` | string | Unique per catalog |

## Product Price

| Field | Type | Constraint |
| --- | --- | --- |
| `amount` | decimal | Greater than zero |

## Inventory Record

| Field | Type | Constraint |
| --- | --- | --- |
| `quantity` | integer | Zero or greater |

## Order Request

| Field | Type | Constraint |
| --- | --- | --- |
| `productId` | string | Must exist in the catalog |

## Order Response

| Field | Type | Constraint |
| --- | --- | --- |
| `orderId` | string | Unique per order |

## Cart Snapshot

| Field | Type | Constraint |
| --- | --- | --- |
| `items` | array | At least one entry |

## Error Envelope

| Field | Type | Constraint |
| --- | --- | --- |
| `code` | string | One of the published codes |

## Version Header

| Field | Type | Constraint |
| --- | --- | --- |
| `X-Contract-Version` | integer | Rises on a breaking change |
