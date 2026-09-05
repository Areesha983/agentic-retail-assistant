from pydantic import BaseModel


class CreateSupportRequest(BaseModel):
    user_id: int
    message: str
    reason: str | None = None
    priority: str = "MEDIUM"


class UpdateSupportRequest(BaseModel):
    status: str
    resolution: str | None = None