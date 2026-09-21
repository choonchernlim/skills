<!--
Purpose: Fixture.
Type: adr
-->

# ADR 0005: Title

| Status | Date | Supersedes | Superseded By |
| --- | --- | --- | --- |
| Proposed | 2026-09-13 | - | - |

## Context and Problem Statement

The scheduler retries every failed delivery with a growing delay because the downstream broker drops connections under load and the operators asked for a bounded queue that never blocks the intake path at peak.
