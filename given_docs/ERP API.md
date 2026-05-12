# Verdano Trial — ERP API Reference

You have access to a small mock ERP API for Verdano Foods. The API is intentionally simple: it knows Verdano's products, customers, warehouses, inventory, open orders, and order drafts. It does not know how retailer spreadsheets map to those concepts.

**Base URL:** `https://erp.corvera.ai`

**Authentication:** Include the following header on every request (except `/health`):

```
Authorization: Bearer <your_api_key>
```

There is no OpenAPI page. Use the endpoint reference below.

---

## Endpoints

### `GET /health`

Returns service status. No auth required.

---

### `GET /erp/products`

Returns Verdano's product master.

| Field | Description |
|---|---|
| `sku` | Internal ERP SKU |
| `name` | Internal product name |
| `case_pack` | Consumer units per case |
| `current_gtins` | Product barcodes currently known by the ERP |
| `legacy_gtins` | Historical barcodes known by the ERP |
| `aliases` | Names the ERP knows but does not treat as primary |
| `temperature_band` | Useful for warehouse/ship-to selection |

---

### `GET /erp/customers`

Returns customer and location records. The ERP separates three customer types:

- **`sold_to`** — commercial customer
- **`bill_to`** — legal billing entity
- **`ship_to`** — delivery location

---

### `GET /erp/warehouses`

Returns warehouse IDs and temperature bands.

---

### `GET /erp/inventory`

Returns available and allocated cases by SKU and warehouse.

**Optional query params:**

| Param | Description |
|---|---|
| `sku` | Filter by SKU |
| `warehouse_id` | Filter by warehouse |

---

### `GET /erp/open-orders`

Returns current ERP sales orders. These are already committed and should be considered when assessing demand.

**Optional query params:**

| Param | Description |
|---|---|
| `retailer` | Case-insensitive substring of the sold-to customer name (e.g. `tesco` or `sainsbury`) |
| `sku` | Filter by SKU |

---

### `POST /erp/order-drafts`

Creates a draft sales order.

**Request body:**

```json
{
  "external_reference": "your-unique-reference",
  "sold_to_customer_id": "CUST-TESCO-UK",
  "bill_to_customer_id": "BILL-TESCO-HQ",
  "ship_to_location_id": "SHIP-TESCO-DAV",
  "required_date": "2026-05-13",
  "lines": [
    {
      "sku": "VG-FALA-500",
      "quantity_cases": 8
    }
  ],
  "notes": "Optional note"
}
```

The endpoint validates:
- Customer types and parent relationships
- Known SKUs and positive quantities
- Ship-to warehouse temperature compatibility

> Reusing the same `external_reference` returns the existing draft rather than creating a duplicate.

---

### `GET /erp/order-drafts`

Returns all order drafts created with your API key.
