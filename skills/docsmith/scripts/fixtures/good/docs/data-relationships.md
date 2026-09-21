<!--
Purpose: Shows a valid relational data diagram with source ownership.
Type: reference
-->

# Data Relationships

Audience: backend developers, to understand account ownership.

An account owns projects through a required foreign key.

```mermaid
erDiagram
  account ||--o{ project : "owns"
  account {
    bigint account_id PK
    text name UK
  }
  project {
    bigint project_id PK
    bigint account_id FK
  }
```

| Node | Source |
| --- | --- |
| account | - |
| project | - |
