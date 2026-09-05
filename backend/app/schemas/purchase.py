from pydantic import BaseModel


class ValidatePurchaseRequest(BaseModel):
    smart_cart_item_id: int


class ExecutePurchaseRequest(BaseModel):
    smart_cart_item_id: int