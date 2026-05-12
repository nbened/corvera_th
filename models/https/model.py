from pydantic import BaseModel, Field

from controllers.retailer import RetailerName
from controllers.fulfillment.model import FulfillmentLine


class ReadDataRequest(BaseModel):
    retailer: RetailerName | None = Field(default=None, description="Filter to a single retailer. Evaluates all if omitted.")


class ReadDataResponse(BaseModel):
    lines: list[FulfillmentLine] = Field(description="One FulfillmentLine per forecast row, annotated with ERP product match, stock context, routing IDs, and status.")


class SubmitOrderRequest(BaseModel):
    lines: list[FulfillmentLine] = Field(description="Evaluated FulfillmentLines from read_data. The agent may override status/block_reason before submitting.")


class SubmitOrderResponse(BaseModel):
    submitted: list[dict] = Field(description="ERP draft confirmation objects for lines successfully posted (status safe or supply_risk).")
    escalated: list[FulfillmentLine] = Field(description="Lines skipped without ERP contact because status is blocked or needs_review.")
    failed: list[dict] = Field(description="Lines the ERP rejected. Each entry is {line: FulfillmentLine, error: str}.")
