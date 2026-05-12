from pydantic import BaseModel, Field


class OrderDraftItem(BaseModel):
    sku: str
    quantity_cases: int


class OrderDraft(BaseModel):
    external_reference: str = Field(description="Must be unique per draft — resubmitting the same ref returns the existing draft")
    sold_to_customer_id: str
    bill_to_customer_id: str
    ship_to_location_id: str
    required_date: str = Field(description="ISO date string, e.g. 2026-05-20")
    lines: list[OrderDraftItem]
    notes: str = ""
