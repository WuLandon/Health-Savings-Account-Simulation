from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DebitCardResponse(BaseModel):
    id: int
    account_id: int
    card_token: str
    status: str
    issued_at: datetime

    model_config = ConfigDict(from_attributes=True)
