from mcp.server.fastmcp import FastMCP

from controllers.erp import ERPController
from controllers.retailer import RetailerController
from models.https import ReadDataRequest, ReadDataResponse, SubmitOrderResponse, SubmitOrderRequest
from controllers.fulfillment import FulfillmentController, check_all_supply_lines

mcp = FastMCP("verdano-ops")


@mcp.tool()
def read_data(request: ReadDataRequest) -> ReadDataResponse:
    """Evaluate retailer forecast demand against ERP inventory and open orders. Returns one annotated FulfillmentLine per forecast row. Call submit_order after if user desires creating the orders."""
    erp = ERPController(erp="verdano")
    r = RetailerController(retailer=request.retailer)

    actuals = [a for rows in r.actuals.get().values() for a in rows]

    fc = FulfillmentController(
        products=erp.products.get(),
        inventory=erp.inventory.get(),
        open_orders=erp.orders.open.get(),
        customers=erp.customers.get(),
        warehouses=erp.warehouse.get(),
        actuals=actuals,
    )

    lines = []
    for rows in r.forecast.get().values():
        lines.extend(fc.evaluate(rows))

    lines = check_all_supply_lines(lines)

    return ReadDataResponse(lines=lines)


@mcp.tool()
def submit_order(request: SubmitOrderRequest) -> SubmitOrderResponse:
    """Submit evaluated fulfillment lines to the ERP. Safe and supply_risk lines are posted as order drafts; blocked and needs_review lines are escalated without ERP contact. Call read_data before."""
    erp = ERPController(erp="verdano")
    submitted, escalated, failed = [], [], []

    for line in request.lines:
        if line.status in ("blocked", "needs_review"):
            escalated.append(line)
            continue
        try:
            draft = line.to_order_draft()
            result = erp.orders.drafts.write(draft.model_dump(mode="json"))
            submitted.append(result)
        except Exception as e:
            failed.append({"line": line.model_dump(mode="json"), "error": str(e)})

    return SubmitOrderResponse(submitted=submitted, escalated=escalated, failed=failed)


if __name__ == "__main__":
    mcp.run(transport="stdio")
