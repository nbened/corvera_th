import requests
from controllers.erp.verdano.orders.model import OpenOrderLine, OrderDraftLine


class OpenOrdersController():
    def __init__(self, session: requests.Session, base_url: str):
        self._session = session
        self._base_url = base_url

    def get(self, retailer: str = None, sku: str = None) -> list[OpenOrderLine]:
        params = {}
        if retailer:
            params["retailer"] = retailer
        if sku:
            params["sku"] = sku
        resp = self._session.get(f"{self._base_url}/erp/open-orders", params=params)
        resp.raise_for_status()
        rows = []
        for order in resp.json():
            base = {k: order.get(k) for k in ("order_id", "sold_to_customer_id", "bill_to_customer_id", "ship_to_location_id", "required_date", "notes")}
            for line in order.get("lines", []):
                rows.append(OpenOrderLine(**base, **line))
        return rows


class DraftOrdersController():
    def __init__(self, session: requests.Session, base_url: str):
        self._session = session
        self._base_url = base_url

    def get(self) -> list[OrderDraftLine]:
        resp = self._session.get(f"{self._base_url}/erp/order-drafts")
        resp.raise_for_status()
        rows = []
        for draft in resp.json():
            base = {k: draft.get(k) for k in ("draft_id", "external_reference", "sold_to_customer_id", "bill_to_customer_id", "ship_to_location_id", "required_date", "status", "notes")}
            for line in draft.get("lines", []):
                rows.append(OrderDraftLine(**base, **line))
        return rows

    def write(self, payload: dict) -> dict:
        resp = self._session.post(f"{self._base_url}/erp/order-drafts", json=payload)
        resp.raise_for_status()
        return resp.json()


class OrdersController():
    open = None
    drafts = None

    def __init__(self, session: requests.Session, base_url: str):
        self.open = OpenOrdersController(session, base_url)
        self.drafts = DraftOrdersController(session, base_url)
