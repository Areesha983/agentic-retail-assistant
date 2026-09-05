from pydantic import BaseModel, Field


class CreateSaleEventRequest(BaseModel):
    product_id: int
    new_price: float = Field(gt=0)