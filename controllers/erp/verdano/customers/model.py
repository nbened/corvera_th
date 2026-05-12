from pydantic import BaseModel, Field, field_validator


class Customer(BaseModel):
    id: str
    type: str = Field(description="sold_to, bill_to, or ship_to")
    name: str
    parent_id: str | None = Field(default=None, description="Links bill_to and ship_to back to their sold_to customer")
    warehouse_id: str | None = None

    @field_validator("parent_id", "warehouse_id", mode="before")
    @classmethod
    def empty_str_to_none(cls, v: str | None) -> str | None:
        return v or None
