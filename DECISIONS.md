# Design principle

- Limited time. Optimizing for "easy to add features" over "add features." 
- North star: what won't change in 6 months?
- I'd rather have the up-front checks in the first tool and let the agent be the double check, than the other way around.


# Tool shape

- Two coarse tools (read_data, submit_order), not five fine-grained ones.
- This is a Monday-morning batch workflow. Agent wants the whole picture per call, not five round-trips to assemble one.
- What won't change in 6 months? Let's build that today.
  - We'll keep adding deterministic checks and heuristics as we find them, in the first tool — GTIN match, inventory check, cross-retailer contention.
    - (And we'll need a way to add checks that we find tomorrow, easily)
  - We'll have the agent doing the judgment stuff in the second tool — resolving ambiguous mappings, deciding if drift is real.
    - Mispellings and context-driven aliases we haven't seen yet are real, and we need to handle them


# Typing

- Problem is bridging data from different sources, so I wanted strict typing to keep it solid.
- Pydantic for the built-in conversion and aliases — removes boilerplate when shifting between source shapes.
- @computed_field on each retailer's source model. The model keeps its original fields for provenance and exposes the normalized contract via computed properties. So a TescoForecast row is also a RetailerForecast without a separate conversion step.


# Controllers

- All strong solutions start with strong typing and abstracted boundaries imo. Built the controllers (services, adapters — heard them called a lot of things) first to give the methods tight, typed I/O.
- Three controllers, each owns one concern. RetailerController for source ingest, ERPController for master data, FulfillmentController for the join and decision pipeline.
- Inside FulfillmentController, each check is (line) → line. from_forecast, resolve_product, attach_erp_context, attach_routing, attach_drift, classify. Adding a check is one new method, optionally one new field on the line.


# Adapters

- First considered making a universal Product to sit on top of the source types.
- Then realized the core thing all these questions are answering is "does the retailer's row map to a Verdano SKU, and can we fulfill it." Not "what is a product abstractly."
- So the unit of work became FulfillmentLine. One forecast row in, one annotated line out. Adding a retailer is a new adapter (forecast model + actual model with @computed_field), not a new entity.


# From 2 to 200

- Add the schema of whatever you're working with. New retailer = one folder (forecast model, actual model, controller subclass) + one registry entry. Zero edits to FulfillmentController or anywhere else.
- FulfillmentLine.retailer is str, not Literal. Open-set. Unknown retailers handled gracefully at lookup time.
- More deterministic checks? Add a method on the controller, slot it into evaluate_row, optionally add a field on the line.
- More data to sift through? Add filters to the request shape. retailer today, week / sku / exceptions_only next.


# Tradeoffs

- Warehouse-temperature mismatch as a pre-check. Skipped. The ERP validates this on POST /erp/order-drafts. Surfacing pre-emptively duplicates ERP logic; let structural validation happen at the boundary.
- Drift as a block reason. Skipped. Drift annotates (drift_pct), never blocks. The agent decides whether the number matters; the MCP doesn't second-guess.


# Limitations and assumptions

- Didn't touch warehouse types. The ERP catches temperature mismatches; my routing resolution picks the right ship-to band but doesn't pre-validate.
- Submitting orders doesn't save us from a bad agent decision. The MCP trusts the agent's status. Structural validation (missing routing, missing erp_sku) happens at the MCP boundary; semantic validation (SKU exists, temperature compatible) happens at the ERP boundary. No third layer.
- No ERP state freshness check in submit_order. Inventory could change between read_data and submit_order. Today it's acceptable because read→submit is a tight loop in one session.
- Don't account for promos. The forecast row carries promo_flag from Tesco but I don't surface it on the line or use it to contextualize drift.


# Improvements

- Each tool call is a round trip and the agent stores all that data in context. Fine now; at scale, return a snapshot key and let the agent reference cached data on subsequent calls.
- Can check the agent input to verify hallucination on the second tool call
- Drift thresholding. Could ship a default is_drift_significant flag at 25%, but I'd rather the agent decide.
- More filters on read_data. retailer today; add week, sku, exceptions_only.


# Approach, in order (experimental → solidifying)

1. Hit the API on all endpoints to build sample data, understand what the ERP knows.
2. Agent-only tool dumping the data, answering objective 1.
3. Considered a unified data object early on, but couldn't figure out what it would be unified by.
4. Shifted from "universal product" to what the user actually cares about — a fulfillment line, with all the data of why and how the decision was derived.
5. Built out the controllers and data shapes around that, knowing the line is the unit of work and everything else feeds it.
6. Built out the fulfillment as a controller and object, with each method as a step in a pipeline
7. Kept testing against claude with requirements to anchor on drift
8. Visciously cut code and checks to whittle down to requirements and clear code and format