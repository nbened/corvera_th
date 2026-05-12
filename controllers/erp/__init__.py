from controllers.erp.verdano import VerdanoERPController

_REGISTRY: dict[str, type] = {
    "verdano": VerdanoERPController,
}


class ERPController:
    def __new__(cls, erp: str = "verdano"):
        if erp not in _REGISTRY:
            raise ValueError(f"Unknown ERP: {erp!r}. Known: {list(_REGISTRY)}")
        return _REGISTRY[erp]()
