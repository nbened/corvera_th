import requests
from controllers.erp.verdano.customers.model import Customer


class CustomersController():
    def __init__(self, session: requests.Session, base_url: str):
        self._session = session
        self._base_url = base_url

    def get(self) -> list[Customer]:
        resp = self._session.get(f"{self._base_url}/erp/customers")
        resp.raise_for_status()
        return [Customer(**c) for c in resp.json()]
