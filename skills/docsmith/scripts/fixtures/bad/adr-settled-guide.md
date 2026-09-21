<!--
Purpose: Fixture.
Type: explanation
-->

# Guide

Audience: the self-test.

## Delivery

The scheduler retries every failed delivery with a growing delay because the downstream broker drops connections under load.
The operators asked for a bounded queue that never blocks the intake path at peak.
