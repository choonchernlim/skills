<!--
Purpose: Conventions for readable relational data diagrams with keys, cardinality, and source ownership.
Type: reference
-->

# Data Diagrams

Audience: the writer, when a reader needs stored entities and their relationships.

Use `erDiagram` for a physical relational model. Use an application flowchart
with `DATA` nodes for payloads, transient state, or a conceptual data flow.

## Entity Rules

- Use physical singular table names exactly as defined in DDL.
- Show primary keys, foreign keys, business unique keys, and fields needed to explain lifecycle.
- Omit routine columns when they add no relationship or lifecycle information.
- Put nullability or index tags in quoted attribute comments.
- Label every relationship with a short verb.
- Keep one aggregate or closely coupled group per diagram.

Prefer four to eight entities. Separate aggregates when labels shrink below
normal Markdown preview size.

## Boundaries

ER diagrams do not use yellow boxes. Put schema, service, or repository
ownership in the lead sentence and source table. If physical placement across
networks or platforms matters, create a separate infrastructure diagram.

## Source Table

Use the shared `Node | Source` header. List each entity in diagram order and
link to its owning migration or schema definition.
