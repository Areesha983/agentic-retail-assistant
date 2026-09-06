from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    user_id: int = Field(
        ...,
        description="Customer/user identifier"
    )

    message: str = Field(
        ...,
        min_length=1,
        description="Customer message for the retail assistant"
    )