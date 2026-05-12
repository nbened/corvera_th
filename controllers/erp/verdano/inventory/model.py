from datetime import datetime
from pydantic import BaseModel


class InventoryLine(BaseModel):
    sku: str
    warehouse_id: str
    available_cases: int
    allocated_cases: int
    as_of: datetime
