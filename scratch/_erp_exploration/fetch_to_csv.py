"""
Fetches every Verdano ERP endpoint and writes one CSV per endpoint.

Usage:
    export ERP_API_KEY="..."
    uv run python3 fetch_to_csv.py
"""

import csv
import os
import requests

BASE_URL = "https://erp.corvera.ai"
API_KEY = os.environ.get("ERP_API_KEY", "")
HEADERS = {"Authorization": f"Bearer {API_KEY}"}
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def get(path, params=None):
    resp = requests.get(f"{BASE_URL}{path}", headers=HEADERS, params=params)
    resp.raise_for_status()
    return resp.json()


def write_csv(filename, rows):
    if not rows:
        print(f"  [empty] {filename}")
        return
    path = os.path.join(OUT_DIR, filename)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  [ok] {filename}  ({len(rows)} rows)")


def flatten_list(val):
    if isinstance(val, list):
        return "; ".join(str(v) for v in val)
    return val


# ---------------------------------------------------------------------------
# products — join array fields with semicolons
# ---------------------------------------------------------------------------
def fetch_products():
    data = get("/erp/products")
    rows = []
    for p in data:
        rows.append({
            "sku": p.get("sku"),
            "name": p.get("name"),
            "category": p.get("category"),
            "temperature_band": p.get("temperature_band"),
            "case_pack": p.get("case_pack"),
            "status": p.get("status"),
            "current_gtins": flatten_list(p.get("current_gtins", [])),
            "legacy_gtins": flatten_list(p.get("legacy_gtins", [])),
            "aliases": flatten_list(p.get("aliases", [])),
        })
    write_csv("products.csv", rows)
    return data


# ---------------------------------------------------------------------------
# customers — flat, one row per record
# ---------------------------------------------------------------------------
def fetch_customers():
    data = get("/erp/customers")
    write_csv("customers.csv", data)
    return data


# ---------------------------------------------------------------------------
# warehouses — flat
# ---------------------------------------------------------------------------
def fetch_warehouses():
    data = get("/erp/warehouses")
    write_csv("warehouses.csv", data)
    return data


# ---------------------------------------------------------------------------
# inventory — flat
# ---------------------------------------------------------------------------
def fetch_inventory():
    data = get("/erp/inventory")
    write_csv("inventory.csv", data)


# ---------------------------------------------------------------------------
# open-orders — expand one row per line item, repeat order header columns
# ---------------------------------------------------------------------------
def fetch_open_orders():
    data = get("/erp/open-orders")
    rows = []
    for order in data:
        base = {
            "order_id": order.get("order_id"),
            "sold_to_customer_id": order.get("sold_to_customer_id"),
            "bill_to_customer_id": order.get("bill_to_customer_id"),
            "ship_to_location_id": order.get("ship_to_location_id"),
            "required_date": order.get("required_date"),
            "notes": order.get("notes", ""),
        }
        for line in order.get("lines", []):
            rows.append({**base, "sku": line.get("sku"), "quantity_cases": line.get("quantity_cases")})
    write_csv("open_orders.csv", rows)


# ---------------------------------------------------------------------------
# order-drafts — same expansion as open-orders
# ---------------------------------------------------------------------------
def fetch_order_drafts():
    data = get("/erp/order-drafts")
    rows = []
    for draft in data:
        base = {
            "draft_id": draft.get("draft_id"),
            "external_reference": draft.get("external_reference"),
            "sold_to_customer_id": draft.get("sold_to_customer_id"),
            "bill_to_customer_id": draft.get("bill_to_customer_id"),
            "ship_to_location_id": draft.get("ship_to_location_id"),
            "required_date": draft.get("required_date"),
            "status": draft.get("status"),
            "notes": draft.get("notes", ""),
        }
        for line in draft.get("lines", []):
            rows.append({**base, "sku": line.get("sku"), "quantity_cases": line.get("quantity_cases")})
    write_csv("order_drafts.csv", rows)


def main():
    if not API_KEY:
        print("ERROR: set ERP_API_KEY before running.")
        return

    print("Fetching Verdano ERP data → CSV files")
    fetch_products()
    fetch_customers()
    fetch_warehouses()
    fetch_inventory()
    fetch_open_orders()
    fetch_order_drafts()
    print("Done.")


if __name__ == "__main__":
    main()
