<!--
Purpose: What src/ owns, its entrypoints, and how to extend it.
Type: readme-folder
-->

# Source

Owns the order routes and inventory client; does not own persistence.

## Entrypoints

- `api.ts`: the order route other modules call.

## File Ownership

| File | Owns | Direct Callers |
| --- | --- | --- |
| [api.ts](api.ts) | Order route | Browser |
| [inventory/client.ts](inventory/client.ts) | Stock queries | Order route |

## To Add

| To Add | Declare It In | Then |
| --- | --- | --- |
| A warehouse | One adapter under `inventory/`; edit nothing else | `bun run test` |

## Verification

```bash
bun run test
```
