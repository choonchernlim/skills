<!--
Purpose: Entry point for the sample shop: what it is, how to run it, where the guides live.
Type: readme-project
-->

# Sample Shop

A storefront that checks inventory before accepting an order.

## Introduction

Customers need current inventory while placing an order. This project checks
the warehouse system before it stores each order.

The shop sits between its customers and two outside systems.

```mermaid
graph TD
  %%{init: {"themeCSS": ".cluster-label, .cluster-label div, .cluster-label span, .cluster-label p { text-align: center !important; }", "flowchart": {"curve": "rounded", "subGraphTitleMargin": {"top": 6, "bottom": 30}}}}%%
  Customer(["Customer<br/>[PERSON]"])
  Shop["<a href='docs/architecture.md'>Sample Shop 🌐</a><br/>[SYSTEM]"]
  Warehouse["Warehouse<br/>[SYSTEM]"]
  Identity["Identity Provider<br/>[SYSTEM]"]

  Customer -->|"places orders"| Shop
  Shop -->|"checks stock"| Warehouse
  Shop -->|"verifies customers"| Identity

  class Customer person
  class Shop,Warehouse,Identity own
  classDef own fill:#2563eb33,stroke:#2563eb
  classDef person fill:#e11d4833,stroke:#e11d48
```

> **Legend:** *🟦 Example team · 🟥 customers*

## Getting Started

### Prerequisites

- Node.js 22 or newer.

### Installation

1. Copy the environment template: `cp .env.example .env`.

### Usage

```bash
./run.sh
```

## Resources

| Resource | What It Answers |
| --- | --- |
| [docs/README.md](docs/README.md) | Where to start and which guide answers which task |
| [docs/architecture.md](docs/architecture.md) | Deployments, ownership, and dependency direction |
