from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, computed_field


class TescoActual(BaseModel):
    week_ending: str
    tesco_item: str
    product_description: str
    store_group: str
    eaches_sold: int
    sales_value_gbp: Decimal

    @computed_field
    @property
    def retailer(self) -> str:
        return "tesco"

    @computed_field
    @property
    def retailer_product_id(self) -> str:
        return self.tesco_item

    @computed_field
    @property
    def qty_units(self) -> int:
        return self.eaches_sold


class TescoForecast(BaseModel):
    delivery_date: str
    tesco_item: str
    product_description: str
    depot: str
    forecast_cases: int
    promo_flag: str
    notes: str | None = None

    @computed_field
    @property
    def retailer(self) -> str:
        return "tesco"

    @computed_field
    @property
    def retailer_product_id(self) -> str:
        return self.tesco_item

    @computed_field
    @property
    def name(self) -> str:
        return self.product_description

    @computed_field
    @property
    def gtin(self) -> str | None:
        return None

    @computed_field
    @property
    def qty_raw(self) -> float:
        return float(self.forecast_cases)

    @computed_field
    @property
    def qty_unit(self) -> Literal["cases", "units"]:
        return "cases"

    @computed_field
    @property
    def week(self) -> str:
        d = date.fromisoformat(self.delivery_date)
        y, w, _ = d.isocalendar()
        return f"{y}-W{w:02d}"

    @computed_field
    @property
    def required_date(self) -> str:
        return self.delivery_date
