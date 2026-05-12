from __future__ import annotations

import csv
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Type, TypeVar

if TYPE_CHECKING:
    from controllers.retailer.model import RetailerActual, RetailerForecast

T = TypeVar("T")

# we have this for auto discovery in our folder - we test against this to make sure it's real
class BaseRetailerController(ABC):
    @staticmethod
    def _load(path: Path, model: Type[T]) -> list[T]:
        with open(path, newline="", encoding="utf-8") as f:
            return [model(**row) for row in csv.DictReader(f)]

    @abstractmethod
    def get_forecast(self, week: str | None = None) -> list[RetailerForecast]: ...

    @abstractmethod
    def get_actuals(self) -> list[RetailerActual]: ...
