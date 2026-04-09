from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import TransactionCreateRequest, TransactionResponse
from app.services import process_transaction

router = APIRouter(tags=["transactions"])


@router.post("/transactions", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def process_transaction_endpoint(
    payload: TransactionCreateRequest,
    db: Session = Depends(get_db),
) -> TransactionResponse:
    transaction, account = process_transaction(
        db=db,
        account_id=payload.account_id,
        card_id=payload.card_id,
        merchant_name=payload.merchant_name,
        merchant_category=payload.merchant_category,
        amount=payload.amount,
    )

    return TransactionResponse(
        id=transaction.id,
        account_id=transaction.account_id,
        card_id=transaction.card_id,
        merchant_name=transaction.merchant_name,
        merchant_category=transaction.merchant_category,
        amount=transaction.amount,
        status=transaction.status,
        decline_reason=transaction.decline_reason,
        created_at=transaction.created_at,
        account_balance=account.balance,
    )
