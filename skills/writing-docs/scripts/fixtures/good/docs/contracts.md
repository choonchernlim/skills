<!--
Purpose: The fields of each payload that crosses the team boundary, with eight sections so the table of contents outgrows the list cap.
Type: reference
-->

# Contracts

Audience: both teams, to answer which fields a payload carries.

## Table of Contents

- [Card Identity](#card-identity)
- [Card Views](#card-views)
- [Card Intents](#card-intents)
- [Tile Request](#tile-request)
- [Tile Response](#tile-response)
- [Filter Snapshot](#filter-snapshot)
- [Error Envelope](#error-envelope)
- [Version Header](#version-header)

## Card Identity

| Field | Type | Constraint |
| --- | --- | --- |
| `id` | string | Unique per registry |

## Card Views

| Field | Type | Constraint |
| --- | --- | --- |
| `views` | array | At least one entry |

## Card Intents

| Field | Type | Constraint |
| --- | --- | --- |
| `intents` | array | May be empty |

## Tile Request

| Field | Type | Constraint |
| --- | --- | --- |
| `tileId` | string | Must exist in the store |

## Tile Response

| Field | Type | Constraint |
| --- | --- | --- |
| `model` | object | Matches the declared view |

## Filter Snapshot

| Field | Type | Constraint |
| --- | --- | --- |
| `patientId` | string | Required before any tile loads |

## Error Envelope

| Field | Type | Constraint |
| --- | --- | --- |
| `code` | string | One of the published codes |

## Version Header

| Field | Type | Constraint |
| --- | --- | --- |
| `X-Contract-Version` | integer | Rises on a breaking change |
