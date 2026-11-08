<!--
Purpose: Fixture.
Type: explanation
-->

# Architecture

> **Audience:** maintainers, to see one rule fail.

The owner file holds another family.

```mermaid
sequenceDiagram
  %%{init: {"themeVariables": {"actorBkg": "transparent", "actorBorder": "#7d8799", "actorLineColor": "#7d8799", "labelBoxBorderColor": "#7d8799"}}}%%
  box rgba(37,99,235,0.2) Example team
    participant Customer as Customer<br/>[PERSON]
    participant Route as Order<br/>[API]
  end
  Customer->>Route: 1: Create the order
```
