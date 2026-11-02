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

  class Project,App,Job,Store own
  classDef own fill:#1a73e833,stroke:#1a73e8
```

**Legend:** 🟦 Example team

| Node | Source |
| --- | --- |
| Project | - |
| Application | - |
| Migrator | - |
| Database | - |
