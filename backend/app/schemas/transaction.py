from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TransactionCreateRequest(BaseModel):
    account_id: int
    card_id: Optional[int] = None
    merchant_name: str
    merchant_category: str
    amount: Decimal = Field(gt=0)


class TransactionResponse(BaseModel):
    id: int
    account_id: int
    card_id: Optional[int]
    merchant_name: str
    merchant_category: str
    amount: Decimal
    status: str
    decline_reason: Optional[str]
    created_at: datetime
    account_balance: Decimal

    model_config = ConfigDict(from_attributes=True)
