<!--
Purpose: Conventions for ordered request, lifecycle, authentication, and orchestration diagrams.
Type: reference
-->

# Runtime Diagrams

Audience: the writer, when a reader needs to trace events in order.

Use `sequenceDiagram`. Put the initiating person first, then participants in
call order. Use `actor` only for `PERSON`; every other participant uses
`participant`.

## Participants and Messages

Use the application node vocabulary. Label every participant as
`Title<br/>[TYPE]`. Number every message and keep its text to one action.

- Solid arrows are calls or commands.
- Dashed arrows are responses.
- Use `opt` for optional behavior and `alt` for mutually exclusive outcomes.
- Split by phase before exceeding seven participants or twelve messages.
- Do not add a participant only to hold a note.

Sequence diagrams do not use yellow boxes. When ownership or deployment
boundaries matter more than order, create a separate application or
infrastructure diagram with the shared two-line boundary format.

## Source Table

List participants in declaration order. A numbered list may combine adjacent
request and response messages when one explanation covers both without losing
an authorization, validation, or persistence boundary.
