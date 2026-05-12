import importlib
import inspect
from enum import StrEnum
from pathlib import Path

from controllers.retailer.base import BaseRetailerController
from controllers.retailer.model import RetailerActual, RetailerForecast

_ROOT = Path(__file__).parent.parent.parent
_EPOS = _ROOT / "epos"
_HERE = Path(__file__).parent


def _discover() -> dict[str, BaseRetailerController]:
    retailers: dict[str, BaseRetailerController] = {}
    for folder in sorted(_HERE.iterdir()):
        if not folder.is_dir() or folder.name.startswith("_"):
            continue
        name = folder.name
        module = importlib.import_module(f"controllers.retailer.{name}")
        controller_cls = next(
            (cls for _, cls in inspect.getmembers(module, inspect.isclass)
             if issubclass(cls, BaseRetailerController) and cls is not BaseRetailerController),
            None,
        )
        if controller_cls is None:
            raise RuntimeError(f"No BaseRetailerController subclass found in controllers.retailer.{name}")
        actuals = next(_EPOS.glob(f"{name}_*actuals*.csv"), None)
        if actuals is None:
            raise RuntimeError(f"No actuals CSV found in epos/ for retailer '{name}' (expected {name}_*actuals*.csv)")
        forecast = next(_EPOS.glob(f"{name}_*forecast*.csv"), None)
        if forecast is None:
            raise RuntimeError(f"No forecast CSV found in epos/ for retailer '{name}' (expected {name}_*forecast*.csv)")
        retailers[name] = controller_cls(actuals_path=actuals, forecast_path=forecast)
    return retailers


_RETAILERS = _discover()

RetailerName = StrEnum("RetailerName", {name: name for name in _RETAILERS})


class ForecastController():
    def __init__(self, retailers: dict[str, BaseRetailerController]):
        self._retailers = retailers

    def get(self, week: str | None = None) -> dict[str, list[RetailerForecast]]:
        return {name: ctrl.get_forecast(week=week) for name, ctrl in self._retailers.items()}


class ActualsController():
    def __init__(self, retailers: dict[str, BaseRetailerController]):
        self._retailers = retailers

    def get(self) -> dict[str, list[RetailerActual]]:
        return {name: ctrl.get_actuals() for name, ctrl in self._retailers.items()}


class RetailerController():
    def __init__(self, retailer: str | None = None):
        targets = {retailer: _RETAILERS[retailer]} if retailer else _RETAILERS
        self.forecast = ForecastController(targets)
        self.actuals = ActualsController(targets)

    @staticmethod
    def list() -> list[str]:
        return list(_RETAILERS.keys())
