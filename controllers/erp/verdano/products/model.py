from pydantic import BaseModel, Field, field_validator


class Product(BaseModel):
    sku: str
    name: str
    category: str
    temperature_band: str
    case_pack: int = Field(description="Units per case — use to convert retailer eaches to cases")
    status: str
    current_gtins: list[str] = Field(description="Active GTINs for this SKU")
    legacy_gtins: list[str] = Field(description="Retired GTINs, kept for historical matching")
    aliases: list[str] = Field(description="Known alternate product name strings used by retailers")

    @field_validator("current_gtins", "legacy_gtins", "aliases", mode="before")
    @classmethod
    def split_semicolon(cls, v: str | list) -> list[str]:
        if isinstance(v, list):
            return v
        return [item.strip() for item in v.split(";") if item.strip()]
