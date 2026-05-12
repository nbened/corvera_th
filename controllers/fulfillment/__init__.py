from collections import defaultdict

from controllers.erp.verdano.customers.model import Customer
from controllers.erp.verdano.inventory.model import InventoryLine
from controllers.erp.verdano.orders.model import OpenOrderLine
from controllers.erp.verdano.products.model import Product
from controllers.erp.verdano.warehouse.model import Warehouse
from controllers.fulfillment.model import ErpContext, FulfillmentLine, MatchInfo
from controllers.retailer.model import RetailerActual, RetailerForecast


class FulfillmentController:
    # Index ERP master data (products, inventory, orders, customers) for fast lookup during forecast evaluation.
    def __init__(
        self,
        products: list[Product],
        inventory: list[InventoryLine],
        open_orders: list[OpenOrderLine],
        customers: list[Customer],
        warehouses: list[Warehouse],
        actuals: list[RetailerActual] | None = None,
    ):
        self._products = products
        self._current_gtin: dict[str, Product] = {}
        self._legacy_gtin: dict[str, Product] = {}
        self._by_name: dict[str, list[Product]] = defaultdict(list)
        self._by_alias: dict[str, list[Product]] = defaultdict(list)
        self._inventory_by_sku: dict[str, dict] = defaultdict(
            lambda: {"available_cases": 0, "allocated_cases": 0, "as_of": None}
        )
        self._open_orders_by_sku: dict[str, int] = defaultdict(int)
        self._product_band: dict[str, str] = {p.sku: p.temperature_band for p in products}

        # step 1 - create our product catalog map from to immediately see if we have a sku or not
        for p in products:
            for g in p.current_gtins:
                self._current_gtin[g] = p
            for g in p.legacy_gtins:
                self._legacy_gtin[g] = p
            self._by_name[p.name.lower()].append(p)
            for a in p.aliases:
                self._by_alias[a.lower()].append(p)

        # step 2 - create instant lookup of 
        for line in inventory:
            self._inventory_by_sku[line.sku]["available_cases"] += line.available_cases
            self._inventory_by_sku[line.sku]["allocated_cases"] += line.allocated_cases
            prev = self._inventory_by_sku[line.sku]["as_of"]
            if prev is None or line.as_of > prev:
                self._inventory_by_sku[line.sku]["as_of"] = line.as_of

        # step 3 - create a lookup of orders by sku immediately
        for line in open_orders:
            self._open_orders_by_sku[line.sku] += line.quantity_cases

        warehouse_band: dict[str, str] = {w.id: w.temperature_band for w in warehouses}
        self._sold_to: dict[str, str] = {}
        self._bill_to: dict[str, str] = {}
        self._ship_to: dict[tuple[str, str], str] = {}

        # step 4 - make instant lookup of customers
        for c in customers:
            key = c.name.lower().replace("'", "").replace(" ", "")
            if c.type == "sold_to":
                self._sold_to[key] = c.id
            elif c.type == "bill_to" and c.parent_id:
                self._bill_to[c.parent_id] = c.id
            elif c.type == "ship_to" and c.parent_id and c.warehouse_id:
                band = warehouse_band.get(c.warehouse_id)
                if band:
                    self._ship_to[(c.parent_id, band)] = c.id

        self._case_pack: dict[str, int] = {p.sku: p.case_pack for p in products}
        self._last_week_units: dict[tuple[str, str], int] = defaultdict(int)
        for a in (actuals or []):
            self._last_week_units[(a.retailer, a.retailer_product_id)] += a.qty_units

    # for this, we're just in order looking for a match in our records for: gtin, legacy gtin, exact name, alias
    def _lookup_product(self, gtin: str | None, name: str) -> tuple[Product | None, MatchInfo | None, list[str]]:

        # a, b - test barcode and legacy
        if gtin:
            p = self._current_gtin.get(gtin)
            if p:
                return p, MatchInfo(method="current_gtin", reason=f"GTIN {gtin} → {p.sku}", confidence="high"), []
            p = self._legacy_gtin.get(gtin)
            if p:
                return p, MatchInfo(method="legacy_gtin", reason=f"Legacy GTIN {gtin} → {p.sku}", confidence="medium"), []

        # c - test exact names
        name_hits = self._by_name.get(name.lower(), [])
        if len(name_hits) == 1:
            p = name_hits[0]
            return p, MatchInfo(method="exact_name", reason=f"Name {name!r} → {p.sku}", confidence="high"), []
        if len(name_hits) > 1:
            return None, None, [p.sku for p in name_hits]

        # d - test aliases that vendors sometimes use
        alias_hits = self._by_alias.get(name.lower(), [])
        if len(alias_hits) == 1:
            p = alias_hits[0]
            return p, MatchInfo(method="alias", reason=f"Alias {name!r} → {p.sku}", confidence="medium"), []
        if len(alias_hits) > 1:
            return None, None, [p.sku for p in alias_hits]

        return None, None, []

    # 1. we already mapped our data, so all we've gotta do now is look up the retailer's product in our inventory and return what we have
    def find_sku(self, line: FulfillmentLine, row: RetailerForecast) -> FulfillmentLine:
        
        # find our product by barcode or name
        product, match, candidates = self._lookup_product(row.gtin, row.name)
        line.erp_sku = product.sku if product else None
        line.match = match
        line.candidates = candidates
        line.quantity_cases = (
            int(row.qty_raw / product.case_pack)
            if row.qty_unit == "units" and product
            else int(row.qty_raw)
        )
        return line

    # 2. we don't do anything here other than take our product and look up to find how much we've got
    def attach_erp_context(self, line: FulfillmentLine) -> FulfillmentLine:
        if line.erp_sku is None:
            return line
        i = self._inventory_by_sku.get(line.erp_sku, {"available_cases": 0, "allocated_cases": 0, "as_of": None})
        line.erp_context = ErpContext(
                available_cases=i["available_cases"],
                allocated_cases=i["allocated_cases"],
                open_order_cases=self._open_orders_by_sku.get(line.erp_sku, 0),
                as_of=i["as_of"].isoformat() if i["as_of"] else "",
            )
        return line

    # 3. retailer from forecast row, product has temp band - with these you know who to look up, and what info to grab for our order
    def attach_routing(self, line: FulfillmentLine) -> FulfillmentLine:
        temperature_band = self._product_band.get(line.erp_sku) if line.erp_sku else None
        retailer_key = line.retailer.lower().replace("'", "").replace(" ", "")
        sold_to_id = next(
            (cid for name_key, cid in self._sold_to.items() if name_key.startswith(retailer_key)),
            None,
        )
        if sold_to_id is None:
            return line
        line.sold_to_customer_id = sold_to_id
        line.bill_to_customer_id = self._bill_to.get(sold_to_id)
        line.ship_to_location_id = self._ship_to.get((sold_to_id, temperature_band)) if temperature_band else None
        return line

    # 4. drift is a simple signal 
    def attach_drift(self, line: FulfillmentLine) -> FulfillmentLine:
        if line.erp_sku is None:
            return line
        actual_units = self._last_week_units.get((line.retailer, line.retailer_product_id), 0)
        case_pack = self._case_pack.get(line.erp_sku)
        if actual_units == 0 or not case_pack:
            return line
        actual_cases = actual_units / case_pack
        line.drift_pct = round((line.quantity_cases - actual_cases) / actual_cases, 3)
        return line

    # 5. now we just take all our derivations and make a call
    def attach_status(self, line: FulfillmentLine) -> FulfillmentLine:
        if line.erp_sku is None:
            line.status = "blocked"
            line.block_reason = "ambiguous_match" if line.candidates else "no_match"
            return line
        if line.sold_to_customer_id is None or line.ship_to_location_id is None:
            line.status = "blocked"
            line.block_reason = "routing_unresolved"
            return line
        if line.match and line.match.method == "legacy_gtin":
            line.status = "needs_review"
            return line
        if line.erp_context:
            net = line.erp_context.available_cases - line.erp_context.allocated_cases - line.erp_context.open_order_cases
            if net <= 0:
                line.status = "blocked"
                line.block_reason = "insufficient_stock"
                return line
            if net < line.quantity_cases:
                line.status = "supply_risk"
                return line
        line.status = "safe"
        return line

    # Evaluate a single retailer forecast row end-to-end: resolve product, compute case quantity, check stock, and attach ERP routing.
    def evaluate_row(self, row: RetailerForecast) -> FulfillmentLine:
        line = FulfillmentLine(
            retailer=row.retailer,
            retailer_product_id=row.retailer_product_id,
            name=row.name,
            week=row.week,
            required_date=row.required_date,
            quantity_cases=0,
            status="needs_review",
        )
        line = self.find_sku(line, row)
        line = self.attach_erp_context(line)
        line = self.attach_routing(line)
        line = self.attach_drift(line)
        line = self.attach_status(line)
        return line

    # Batch-evaluate all forecast rows for a retailer, producing the full list of annotated FulfillmentLines.
    def evaluate(self, rows: list[RetailerForecast]) -> list[FulfillmentLine]:
        return [self.evaluate_row(row) for row in rows]


# indicate at risk if wew were good for two seperate filings but not in total
def check_all_supply_lines(lines: list[FulfillmentLine]) -> list[FulfillmentLine]:
    demand: dict[str, int] = defaultdict(int)
    supply: dict[str, int] = {}

    for line in lines:
        if line.erp_sku and line.erp_context:
            demand[line.erp_sku] += line.quantity_cases
            if line.erp_sku not in supply:
                ctx = line.erp_context
                supply[line.erp_sku] = ctx.available_cases - ctx.allocated_cases - ctx.open_order_cases

    for line in lines:
        if line.status == "safe" and line.erp_sku in supply and demand[line.erp_sku] > supply[line.erp_sku]:
            line.status = "supply_risk"
    return lines
