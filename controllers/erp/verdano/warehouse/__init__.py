import requests
from controllers.erp.verdano.warehouse.model import Warehouse


class WarehouseController():
    def __init__(self, session: requests.Session, base_url: str):
        self._session = session
        self._base_url = base_url

    def get(self) -> list[Warehouse]:
        resp = self._session.get(f"{self._base_url}/erp/warehouses")
        resp.raise_for_status()
        return [Warehouse(**w) for w in resp.json()]
