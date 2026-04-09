from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import (
    AccountCreateRequest,
    AccountResponse,
    DebitCardResponse,
    DepositCreateRequest,
    DepositResponse,
)
from app.services import create_account, create_deposit, issue_card, list_accounts

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account_endpoint(payload: AccountCreateRequest, db: Session = Depends(get_db)) -> AccountResponse:
    account = create_account(
        db=db,
        account_holder_name=payload.account_holder_name,
        email=payload.email,
    )
    return AccountResponse.model_validate(account)


@router.get("", response_model=list[AccountResponse])
def list_accounts_endpoint(db: Session = Depends(get_db)) -> list[AccountResponse]:
    accounts = list_accounts(db=db)
    return [AccountResponse.model_validate(account) for account in accounts]


@router.post(
    "/{account_id}/deposits",
    response_model=DepositResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_deposit_endpoint(
    account_id: int,
    payload: DepositCreateRequest,
    db: Session = Depends(get_db),
) -> DepositResponse:
    deposit, account = create_deposit(db=db, account_id=account_id, amount=payload.amount)
    return DepositResponse(
        id=deposit.id,
        account_id=deposit.account_id,
        amount=deposit.amount,
        created_at=deposit.created_at,
        account_balance=account.balance,
    )


@router.post(
    "/{account_id}/card",
    response_model=DebitCardResponse,
    status_code=status.HTTP_201_CREATED,
)
def issue_card_endpoint(account_id: int, db: Session = Depends(get_db)) -> DebitCardResponse:
    card = issue_card(db=db, account_id=account_id)
    return DebitCardResponse.model_validate(card)
