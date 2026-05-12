import os
import requests
from dotenv import load_dotenv

from controllers.erp.verdano.warehouse import WarehouseController
from controllers.erp.verdano.inventory import InventoryController
from controllers.erp.verdano.orders import OrdersController
from controllers.erp.verdano.products import ProductsController
from controllers.erp.verdano.customers import CustomersController

load_dotenv()

BASE_URL = "https://erp.corvera.ai"


class VerdanoERPController:
    def __init__(self):
        self._session = requests.Session()
        self._session.headers["Authorization"] = f"Bearer {os.environ['ERP_API_KEY']}"

        self.warehouse = WarehouseController(self._session, BASE_URL)
        self.inventory = InventoryController(self._session, BASE_URL)
        self.orders = OrdersController(self._session, BASE_URL)
        self.products = ProductsController(self._session, BASE_URL)
        self.customers = CustomersController(self._session, BASE_URL)
