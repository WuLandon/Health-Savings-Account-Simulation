from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class AccountCreateRequest(BaseModel):
    account_holder_name: str
    email: str


class AccountResponse(BaseModel):
    id: int
    account_holder_name: str
    email: str
    balance: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
