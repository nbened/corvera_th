from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field, computed_field

from controllers.erp.verdano.orders.model import OrderDraft, OrderDraftItem
Status = Literal["safe", "supply_risk", "needs_review", "blocked"]
BlockReason = Literal[
    "no_match",
    "ambiguous_match",
    "routing_unresolved",
    "insufficient_stock",
]


class MatchInfo(BaseModel):
    method: Literal["current_gtin", "legacy_gtin", "alias", "exact_name"]
    reason: str
    confidence: Literal["high", "medium"]


class ErpContext(BaseModel):
    available_cases: int = Field(description="Total physical stock on hand across all warehouses.")
    allocated_cases: int = Field(description="Stock already reserved against confirmed orders — locked, cannot be promised elsewhere.")
    open_order_cases: int = Field(description="Cases in placed but unfulfilled orders — committed future demand that will draw down stock when picked.")
    as_of: str = Field(description="ISO datetime of the most recent inventory snapshot across all warehouse rows — provenance indicator.")


class FulfillmentLine(BaseModel):
    # step 1 — from_forecast: copy identity from the source row (demand side, before any ERP work)  (demand)
    retailer: str
    retailer_product_id: str
    name: str
    week: str
    required_date: str

    # step 2 — resolve_product: map retailer row to a Verdano SKU and convert qty to cases (supply)
    erp_sku: str | None = None
    match: MatchInfo | None = None
    candidates: list[str] = []
    quantity_cases: int  # initialized at step 1 from row.qty_raw, finalized here using product.case_pack

    # step 3 — attach_erp_context: snapshot inventory and committed open orders for the resolved SKU
    erp_context: ErpContext | None = None

    # step 4 — attach_routing: resolve sold_to/bill_to/ship_to from the retailer + product's temperature band
    sold_to_customer_id: str | None = None
    bill_to_customer_id: str | None = None
    ship_to_location_id: str | None = None

    # step 5 — attach_drift: compute (this week's forecast - last week's actuals) / last week's actuals
    drift_pct: float | None = None

    # step 6 — classify: decide safe / supply_risk / needs_review / blocked based on everything above
    #   may be upgraded from "safe" → "supply_risk" by apply_contention's second pass
    status: Status = Field(description=(
        "safe — stock covers demand, routing complete, ready to submit. "
        "supply_risk — stock partially covers demand, review quantity. "
        "needs_review — matched via legacy GTIN, confirm SKU mapping. "
        "blocked — cannot submit without human intervention (see block_reason)."
    ))
    block_reason: BlockReason | None = Field(default=None, description=(
        "no_match — product not found in ERP. "
        "ambiguous_match — multiple ERP SKUs match; see candidates. "
        "routing_unresolved — sold_to/ship_to customer IDs could not be resolved from ERP config. "
        "insufficient_stock — net available stock is zero or negative."
    ))

    # derived — preview of what gets submitted to the ERP as the unique key
    @computed_field
    @property
    def external_reference(self) -> str:
        pid = self.retailer_product_id or self.name
        return f"{self.retailer}-{self.week}-{pid}"

    # projection — condense the analytical line into the transactional draft the ERP accepts
    def to_order_draft(self) -> OrderDraft:
        if self.status in ("blocked", "needs_review"):
            raise ValueError(f"Cannot draft {self.retailer_product_id!r}: status is {self.status!r}")
        missing = [
            f for f, v in (
                ("erp_sku", self.erp_sku),
                ("sold_to_customer_id", self.sold_to_customer_id),
                ("bill_to_customer_id", self.bill_to_customer_id),
                ("ship_to_location_id", self.ship_to_location_id),
            ) if v is None
        ]
        if missing:
            raise ValueError(f"Cannot draft {self.retailer_product_id!r}: missing {missing}")
        return OrderDraft(
            external_reference=self.external_reference,
            sold_to_customer_id=self.sold_to_customer_id,
            bill_to_customer_id=self.bill_to_customer_id,
            ship_to_location_id=self.ship_to_location_id,
            required_date=self.required_date,
            lines=[OrderDraftItem(sku=self.erp_sku, quantity_cases=self.quantity_cases)],
        )