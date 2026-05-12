import requests
from controllers.erp.verdano.inventory.model import InventoryLine


class InventoryController():
    def __init__(self, session: requests.Session, base_url: str):
        self._session = session
        self._base_url = base_url

    def get(self, sku: str = None, warehouse_id: str = None) -> list[InventoryLine]:
        params = {}
        if sku:
            params["sku"] = sku
        if warehouse_id:
            params["warehouse_id"] = warehouse_id
        resp = self._session.get(f"{self._base_url}/erp/inventory", params=params)
        resp.raise_for_status()
        return [InventoryLine(**i) for i in resp.json()]
