from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from controllers.retailer.base import BaseRetailerController
from controllers.retailer.tesco.model import TescoActual, TescoForecast

if TYPE_CHECKING:
    from controllers.retailer.model import RetailerActual, RetailerForecast


class TescoController(BaseRetailerController):
    def __init__(self, actuals_path: Path, forecast_path: Path):
        self._actuals = self._load(actuals_path, TescoActual)
        self._forecast = self._load(forecast_path, TescoForecast)

    def get_forecast(self, week: str | None = None) -> list[RetailerForecast]:
        if week:
            return [r for r in self._forecast if r.week == week]
        return self._forecast

    def get_actuals(self) -> list[RetailerActual]:
        return self._actuals
