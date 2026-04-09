from decimal import Decimal
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DebitCard, HSAAccount, Transaction

APPROVED_CATEGORIES = {"pharmacy", "hospital", "clinic", "medical"}
DECLINED_CATEGORIES = {"restaurant", "electronics", "entertainment"}


def process_transaction(
    db: Session,
    account_id: int,
    card_id: Optional[int],
    merchant_name: str,
    merchant_category: str,
    amount: Decimal,
) -> tuple[Transaction, HSAAccount]:
    if amount <= Decimal("0"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid transaction amount",
        )

    normalized_category = merchant_category.strip().lower()

    with db.begin():
        account = db.scalar(
            select(HSAAccount)
            .where(HSAAccount.id == account_id)
            .with_for_update()
        )
        if account is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="account not found",
            )

        resolved_card_id = card_id
        decline_reason: Optional[str] = None

        if card_id is not None:
            card = db.scalar(select(DebitCard).where(DebitCard.id == card_id))
            if card is None:
                resolved_card_id = None
                decline_reason = "card not found"
            elif card.account_id != account.id:
                resolved_card_id = None
                decline_reason = "card does not belong to account"
            elif card.status.lower() != "active":
                decline_reason = "inactive card"

        if decline_reason is None:
            if normalized_category in APPROVED_CATEGORIES:
                pass
            elif normalized_category in DECLINED_CATEGORIES:
                decline_reason = "non-qualified medical expense"
            else:
                decline_reason = "invalid merchant category"

        status_value = "approved"
        if decline_reason is None and account.balance < amount:
            decline_reason = "insufficient funds"

        if decline_reason is not None:
            status_value = "declined"
        else:
            account.balance = account.balance - amount

        transaction = Transaction(
            account_id=account.id,
            card_id=resolved_card_id,
            merchant_name=merchant_name,
            merchant_category=normalized_category,
            amount=amount,
            status=status_value,
            decline_reason=decline_reason,
        )
        db.add(transaction)

    db.refresh(transaction)
    db.refresh(account)
    return transaction, account
