<!--
Purpose: Conventions for readable relational data diagrams with keys, cardinality, and source ownership.
Type: reference
-->

# Data Diagrams

> **Audience:** the writer, when a reader needs stored entities and their relationships.

Use `erDiagram` for a physical relational model. Use an application flowchart
with `DATA` nodes for payloads, transient state, or a conceptual data flow.

## Entity Rules

- Use physical singular table names exactly as defined in DDL.
- Show primary keys, foreign keys, business unique keys, and fields needed to explain lifecycle.
- Omit routine columns when they add no relationship or lifecycle information.
- Put nullability or index tags in quoted attribute comments.
- Label every relationship with a short verb.
- Keep one aggregate or closely coupled group per diagram.

Prefer four to eight entities, and never more than eight. An entity named only
in a relationship still draws as a box, so it counts. Separate aggregates when
labels shrink below normal Markdown preview size.

## Boundaries

ER diagrams do not use boundaries. Put schema, service, or repository
ownership in the lead sentence. If physical placement across
networks or platforms matters, create a separate infrastructure diagram.

## Sources Line

List each entity that has a source on the shared
[Sources line](mermaid.md#source-links), in diagram order, and link it to its
owning migration or schema definition.
