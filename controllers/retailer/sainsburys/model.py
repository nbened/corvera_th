from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, computed_field


class SainsburysActual(BaseModel):
    week: str
    gtin: str
    item_name: str
    channel: str
    units_sold: int
    net_sales_gbp: Decimal

    @computed_field
    @property
    def retailer(self) -> str:
        return "sainsburys"

    @computed_field
    @property
    def retailer_product_id(self) -> str:
        return self.gtin

    @computed_field
    @property
    def qty_units(self) -> int:
        return self.units_sold


class SainsburysForecast(BaseModel):
    receipt_week: str
    gtin: str
    item_name: str
    geography: str
    forecast_units: int
    forecast_value_gbp: Decimal
    temperature_band: str

    @computed_field
    @property
    def retailer(self) -> str:
        return "sainsburys"

    @computed_field
    @property
    def retailer_product_id(self) -> str:
        return self.gtin or ""

    @computed_field
    @property
    def name(self) -> str:
        return self.item_name

    @computed_field
    @property
    def qty_raw(self) -> float:
        return float(self.forecast_units)

    @computed_field
    @property
    def qty_unit(self) -> Literal["cases", "units"]:
        return "units"

    @computed_field
    @property
    def week(self) -> str:
        return self.receipt_week

    @computed_field
    @property
    def required_date(self) -> str:
        yr, wk = self.receipt_week.split("-W")
        return date.fromisocalendar(int(yr), int(wk), 1).isoformat()
