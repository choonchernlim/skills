<!--
Purpose: Fixture.
Type: explanation
-->

# Edge Copy

> **Audience:** maintainers, to see one rule fail.

A second file draws it again.

```mermaid
graph TD
  %%{init: {"themeCSS": ".cluster-label, .cluster-label div, .cluster-label span, .cluster-label p { text-align: center !important; }", "flowchart": {"curve": "rounded", "subGraphTitleMargin": {"top": 6, "bottom": 30}}}}%%
  Alpha["Alpha<br/>[SERVICE]"]
  Beta["Beta<br/>[SERVICE]"]
  Kappa["Kappa<br/>[SERVICE]"]
  Sigma["Sigma<br/>[SERVICE]"]
  Alpha -->|"invokes"| Beta
  Beta -->|"notifies"| Kappa
  Kappa -->|"notifies"| Sigma

  class Alpha,Beta,Kappa,Sigma own
  classDef own fill:#2563eb33,stroke:#2563eb
```

> **Legend:** *🟦 Example team*
