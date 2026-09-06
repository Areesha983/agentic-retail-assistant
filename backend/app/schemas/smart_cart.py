from pydantic import BaseModel, Field
from typing import Optional


class CreateSmartCartRequest(BaseModel):
    user_id: int


class AddSmartCartItemRequest(BaseModel):
    cart_id: int
    product_id: int
    variant: Optional[str] = None
    color: Optional[str] = None
    quantity: int = Field(default=1, gt=0)
    maximum_price: Optional[float] = Field(default=None, gt=0)
    auto_buy_enabled: bool = False