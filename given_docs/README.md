# Verdano Foods — MCP Work Trial

Verdano Foods is a UK plant-based CPG brand selling through Tesco and Sainsbury's. Every Monday, the ops team compares retailer forecasts, recent EPOS sales, ERP inventory, and open orders to answer a simple question:

> **What can we fulfill next week, what is at risk, and what needs human review?**

Today that work is spreadsheet-driven. Tesco and Sainsbury's represent the same products, dates, locations, and quantities differently. The ERP has products, customers, stock, and orders — but it does not understand retailer-specific spreadsheet shapes or forecast quality.

---

## Task

Build an MCP server that gives general-purpose AI tools like Claude/ChatGPT useful tools for this workflow.

**At a minimum, the AI system should be able to use your MCP server to:**

- Compare next week's retailer forecast demand against ERP inventory and open orders
- Identify SKU/retailer lines that are safe, at risk, or blocked by ambiguous mappings

**Optional extensions for additional inspiration:**

- Create ERP order drafts for clean lines
- Compare recent EPOS actuals against retailer forecasts to flag likely forecast drift
- Expose mapping confidence and human-review exceptions
- Explain assumptions and source provenance

---

## What You'll Receive

- Mock retailer forecast and EPOS CSVs
- Access to a small mock ERP API
  - **Base URL:** `https://erp.corvera.ai`
  - **API Key:** `trial_P113hqDp9-yaZGRtz_s-tC4QQfdOBvB6`

---

## What We Care About

You have full flexibility in tool design and implementation approach. That said, we evaluate on:


| Area               | What We're Looking For                                            |
| ------------------ | ----------------------------------------------------------------- |
| **Tool design**    | Reasoning behind your choice of abstraction level and tool shapes |
| **OOP principles** | Use of polymorphism to define core entities and interfaces        |
| **Adapters**       | Converting messy source data into clean core business entities    |


---

## Evaluation Criteria

- **Code quality** — types, naming, error handling, extensibility (does your solution scale from 2 customers to 200?)
- **Abstraction quality** — tool shapes, decomposition, reusability
- **Articulation & tradeoffs** — a log of decisions and judgements made, along with presentation

---

## Submission

We anticipate this work trial to take ~8 hours, for which you will be compensated pro-rata. Balance the tension of shipping fast and setting a rigorous, scalable foundation.

Submit here: [https://forms.gle/U5YhJuY7MaubdFTY9](https://forms.gle/U5YhJuY7MaubdFTY9)

