from typing import Literal

from pydantic import BaseModel, Field


class RetailIntent(BaseModel):
    intent: Literal[
        "PRODUCT_SEARCH",
        "INVENTORY_CHECK",
        "SMART_CART",
        "SUPPORT",
        "UNKNOWN"
    ]

    product_name: str | None = None
    brand: str | None = None
    variant: str | None = None
    color: str | None = None
    branch: str | None = None

    quantity: int | None = Field(
        default=None,
        gt=0
    )

    maximum_price: float | None = Field(
        default=None,
        gt=0
    )

    auto_buy_enabled: bool | None = None