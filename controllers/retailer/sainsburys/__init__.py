from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from controllers.retailer.base import BaseRetailerController
from controllers.retailer.sainsburys.model import SainsburysActual, SainsburysForecast

if TYPE_CHECKING:
    from controllers.retailer.model import RetailerActual, RetailerForecast


class SainsburysController(BaseRetailerController):
    def __init__(self, actuals_path: Path, forecast_path: Path):
        self._actuals = self._load(actuals_path, SainsburysActual)
        self._forecast = self._load(forecast_path, SainsburysForecast)

    def get_forecast(self, week: str | None = None) -> list[RetailerForecast]:
        if week:
            return [r for r in self._forecast if r.week == week]
        return self._forecast

    def get_actuals(self) -> list[RetailerActual]:
        return self._actuals
