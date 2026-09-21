<!--
Purpose: Bad generic infrastructure type fixture.
Type: explanation
-->

# Generic Infrastructure

Audience: maintainers, to see a generic platform type fail.

The infrastructure diagram hides one deployed technology behind a generic label.

```mermaid
graph TD
  Project["Project<br/>[GCP PROJECT]"]
  App["Application<br/>[SYSTEM]"]
  Job["Migrator<br/>[CLOUD RUN JOB]"]
  Store[("Database<br/>[POSTGRES]")]
  Project -->|"hosts"| App
  App -->|"writes"| Store
  Job -->|"migrates"| Store
```

| Node | Source |
| --- | --- |
| Project | - |
| Application | - |
| Migrator | - |
| Database | - |
