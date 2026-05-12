# Verdano ERP API — Test Scripts

Quick Python scripts for hitting every endpoint of the Verdano ERP mock API.

## Requirements

```bash
pip install requests
```

## Setup

```bash
export ERP_API_KEY="trial_P113hqDp9-yaZGRtz_s-tC4QQfdOBvB6"
```

## Run the full test suite

```bash
python test_erp_api.py
```

The script runs every endpoint in dependency order (products → customers → warehouses → inventory → open-orders → order-drafts), pulling real IDs from earlier responses so the parameterised calls are always valid.

---

## Hit individual endpoints manually

### 1. Health check (no auth)

```python
import requests
resp = requests.get("https://erp.corvera.ai/health")
print(resp.json())
```

---

### 2. Products

```python
import requests, os
API_KEY = os.environ["ERP_API_KEY"]
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

resp = requests.get("https://erp.corvera.ai/erp/products", headers=HEADERS)
products = resp.json()
for p in products:
    print(p["sku"], p["name"], "— case pack:", p["case_pack"])
```

---

### 3. Customers

```python
resp = requests.get("https://erp.corvera.ai/erp/customers", headers=HEADERS)
customers = resp.json()
for c in customers:
    print(c["customer_type"], c.get("customer_id") or c.get("location_id"), c.get("name"))
```

---

### 4. Warehouses

```python
resp = requests.get("https://erp.corvera.ai/erp/warehouses", headers=HEADERS)
for wh in resp.json():
    print(wh["warehouse_id"], wh.get("temperature_band"))
```

---

### 5. Inventory

```python
# Unfiltered
resp = requests.get("https://erp.corvera.ai/erp/inventory", headers=HEADERS)

# Filter by SKU
resp = requests.get("https://erp.corvera.ai/erp/inventory", headers=HEADERS,
                    params={"sku": "VG-FALA-500"})

# Filter by warehouse
resp = requests.get("https://erp.corvera.ai/erp/inventory", headers=HEADERS,
                    params={"warehouse_id": "WH-AMB-01"})

print(resp.json())
```

---

### 6. Open orders

```python
# Unfiltered
resp = requests.get("https://erp.corvera.ai/erp/open-orders", headers=HEADERS)

# Filter by retailer (case-insensitive substring)
resp = requests.get("https://erp.corvera.ai/erp/open-orders", headers=HEADERS,
                    params={"retailer": "sainsbury"})

# Filter by SKU
resp = requests.get("https://erp.corvera.ai/erp/open-orders", headers=HEADERS,
                    params={"sku": "VG-FALA-500"})

print(resp.json())
```

---

### 7. Create an order draft

```python
import time

payload = {
    "external_reference": f"MY-REF-{int(time.time())}",   # must be unique per draft
    "sold_to_customer_id": "CUST-TESCO-UK",
    "bill_to_customer_id": "BILL-TESCO-HQ",
    "ship_to_location_id": "ESCO-DAV",
    "required_date": "2026-05-20",
    "lines": [
        {"sku": "VG-FALA-500", "quantity_cases": 8}
    ],
    "notes": "Optional note"
}

resp = requests.post("https://erp.corvera.ai/erp/order-drafts",
                     headers=HEADERS, json=payload)
print(resp.status_code, resp.json())
```

Posting the same `external_reference` twice returns the existing draft instead of creating a duplicate.

---

### 8. List order drafts

```python
resp = requests.get("https://erp.corvera.ai/erp/order-drafts", headers=HEADERS)
for draft in resp.json():
    print(draft.get("draft_id"), draft.get("external_reference"), draft.get("status"))
```

---

## Notes

- All endpoints except `/health` require the `Authorization: Bearer <key>` header.
- `sold_to`, `bill_to`, and `ship_to` IDs must belong to the correct customer types and parent relationships — use `/erp/customers` to look them up before posting a draft.
- `ship_to` warehouse temperature must be compatible with the SKU's `temperature_band` — use `/erp/warehouses` and `/erp/products` to verify.


