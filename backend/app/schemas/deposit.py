from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class DepositCreateRequest(BaseModel):
    amount: Decimal = Field(gt=0)


class DepositResponse(BaseModel):
    id: int
    account_id: int
    amount: Decimal
    created_at: datetime
    account_balance: Decimal

    model_config = ConfigDict(from_attributes=True)
