import requests
from controllers.erp.verdano.products.model import Product


class ProductsController():
    def __init__(self, session: requests.Session, base_url: str):
        self._session = session
        self._base_url = base_url

    def get(self) -> list[Product]:
        resp = self._session.get(f"{self._base_url}/erp/products")
        resp.raise_for_status()
        return [Product(**p) for p in resp.json()]
