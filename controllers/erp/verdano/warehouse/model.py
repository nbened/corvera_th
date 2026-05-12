from pydantic import BaseModel


class Warehouse(BaseModel):
    id: str
    name: str
    temperature_band: str
