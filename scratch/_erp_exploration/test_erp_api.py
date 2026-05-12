"""
Verdano ERP API — endpoint test suite.

Usage:
    export ERP_API_KEY="your_api_key_here"
    python test_erp_api.py

Each test function prints a PASS / FAIL status and key response data.
"""

import os
import json
import requests

BASE_URL = "https://erp.corvera.ai"
API_KEY = os.environ.get("ERP_API_KEY", "")

HEADERS = {"Authorization": f"Bearer {API_KEY}"}


def _print_result(name: str, resp: requests.Response, show_keys: list[str] | None = None) -> dict:
    ok = resp.status_code < 400
    status = "PASS" if ok else "FAIL"
    print(f"\n{'='*60}")
    print(f"[{status}] {name}  (HTTP {resp.status_code})")
    if not ok:
        print("  Response:", resp.text[:400])
        return {}
    data = resp.json()
    if show_keys and isinstance(data, dict):
        for k in show_keys:
            print(f"  {k}: {json.dumps(data.get(k), indent=2)[:200]}")
    elif isinstance(data, list):
        print(f"  Records returned: {len(data)}")
        if data:
            print(f"  First record keys: {list(data[0].keys())}")
    else:
        print(f"  Response: {json.dumps(data)[:400]}")
    return data


# ---------------------------------------------------------------------------
# 1. GET /health
# ---------------------------------------------------------------------------
def test_health():
    resp = requests.get(f"{BASE_URL}/health")  # no auth required
    _print_result("GET /health", resp)


# ---------------------------------------------------------------------------
# 2. GET /erp/products
# ---------------------------------------------------------------------------
def test_products():
    resp = requests.get(f"{BASE_URL}/erp/products", headers=HEADERS)
    data = _print_result("GET /erp/products", resp)
    return data  # return for use in downstream tests


# ---------------------------------------------------------------------------
# 3. GET /erp/customers
# ---------------------------------------------------------------------------
def test_customers():
    resp = requests.get(f"{BASE_URL}/erp/customers", headers=HEADERS)
    data = _print_result("GET /erp/customers", resp)
    return data


# ---------------------------------------------------------------------------
# 4. GET /erp/warehouses
# ---------------------------------------------------------------------------
def test_warehouses():
    resp = requests.get(f"{BASE_URL}/erp/warehouses", headers=HEADERS)
    data = _print_result("GET /erp/warehouses", resp)
    return data


# ---------------------------------------------------------------------------
# 5. GET /erp/inventory  (unfiltered, then filtered)
# ---------------------------------------------------------------------------
def test_inventory(first_sku: str | None = None, first_warehouse: str | None = None):
    # unfiltered
    resp = requests.get(f"{BASE_URL}/erp/inventory", headers=HEADERS)
    _print_result("GET /erp/inventory (unfiltered)", resp)

    # filtered by SKU
    if first_sku:
        resp = requests.get(
            f"{BASE_URL}/erp/inventory",
            headers=HEADERS,
            params={"sku": first_sku},
        )
        _print_result(f"GET /erp/inventory?sku={first_sku}", resp)

    # filtered by warehouse
    if first_warehouse:
        resp = requests.get(
            f"{BASE_URL}/erp/inventory",
            headers=HEADERS,
            params={"warehouse_id": first_warehouse},
        )
        _print_result(f"GET /erp/inventory?warehouse_id={first_warehouse}", resp)


# ---------------------------------------------------------------------------
# 6. GET /erp/open-orders  (unfiltered, retailer filter, SKU filter)
# ---------------------------------------------------------------------------
def test_open_orders(first_sku: str | None = None):
    resp = requests.get(f"{BASE_URL}/erp/open-orders", headers=HEADERS)
    _print_result("GET /erp/open-orders (unfiltered)", resp)

    resp = requests.get(
        f"{BASE_URL}/erp/open-orders",
        headers=HEADERS,
        params={"retailer": "sainsbury"},
    )
    _print_result("GET /erp/open-orders?retailer=sainsbury", resp)

    if first_sku:
        resp = requests.get(
            f"{BASE_URL}/erp/open-orders",
            headers=HEADERS,
            params={"sku": first_sku},
        )
        _print_result(f"GET /erp/open-orders?sku={first_sku}", resp)


# ---------------------------------------------------------------------------
# 7. POST /erp/order-drafts
# ---------------------------------------------------------------------------
def test_create_order_draft(
    sold_to: str,
    bill_to: str,
    ship_to: str,
    sku: str,
):
    import time
    ref = f"TEST-{int(time.time())}"
    payload = {
        "external_reference": ref,
        "sold_to_customer_id": sold_to,
        "bill_to_customer_id": bill_to,
        "ship_to_location_id": ship_to,
        "required_date": "2026-05-20",
        "lines": [{"sku": sku, "quantity_cases": 5}],
        "notes": "Automated test draft — safe to delete",
    }
    resp = requests.post(f"{BASE_URL}/erp/order-drafts", headers=HEADERS, json=payload)
    _print_result("POST /erp/order-drafts", resp, show_keys=["draft_id", "external_reference", "status"])

    # idempotency check: same ref should return the same draft
    resp2 = requests.post(f"{BASE_URL}/erp/order-drafts", headers=HEADERS, json=payload)
    data2 = resp2.json() if resp2.status_code < 400 else {}
    same = data2.get("external_reference") == ref
    print(f"\n  Idempotency check (same external_reference): {'PASS' if same else 'FAIL'}")

    return ref


# ---------------------------------------------------------------------------
# 8. GET /erp/order-drafts
# ---------------------------------------------------------------------------
def test_list_order_drafts():
    resp = requests.get(f"{BASE_URL}/erp/order-drafts", headers=HEADERS)
    _print_result("GET /erp/order-drafts", resp)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------
def _first(records, key: str) -> str | None:
    if isinstance(records, list) and records:
        return records[0].get(key)
    return None


def main():
    if not API_KEY:
        print("ERROR: set ERP_API_KEY environment variable before running.")
        return

    print("Verdano ERP API — test suite")
    print(f"Base URL : {BASE_URL}")
    print(f"API key  : {API_KEY[:8]}{'*' * max(0, len(API_KEY) - 8)}")

    test_health()

    products = test_products()
    customers = test_customers()
    warehouses = test_warehouses()

    # pull first known values to drive parameterised tests
    first_sku = _first(products, "sku")
    first_warehouse_id = _first(warehouses, "warehouse_id")

    test_inventory(first_sku, first_warehouse_id)
    test_open_orders(first_sku)

    # build minimal valid customer IDs from the customer list
    sold_to = bill_to = ship_to = None
    if isinstance(customers, list):
        for c in customers:
            t = c.get("customer_type")
            if t == "sold_to" and not sold_to:
                sold_to = c.get("customer_id")
            elif t == "bill_to" and not bill_to:
                bill_to = c.get("customer_id")
            elif t == "ship_to" and not ship_to:
                ship_to = c.get("customer_id") or c.get("location_id")

    if sold_to and bill_to and ship_to and first_sku:
        test_create_order_draft(sold_to, bill_to, ship_to, first_sku)
    else:
        print("\n[SKIP] POST /erp/order-drafts — could not determine valid customer IDs from /erp/customers")

    test_list_order_drafts()

    print(f"\n{'='*60}")
    print("Test run complete.")


if __name__ == "__main__":
    main()
