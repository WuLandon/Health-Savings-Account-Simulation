from decimal import Decimal
import secrets

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DebitCard, Deposit, HSAAccount


def create_account(db: Session, account_holder_name: str, email: str) -> HSAAccount:
    account = HSAAccount(
        account_holder_name=account_holder_name,
        email=email,
        balance=Decimal("0.00"),
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def list_accounts(db: Session) -> list[HSAAccount]:
    return list(db.scalars(select(HSAAccount).order_by(HSAAccount.id)).all())


def create_deposit(db: Session, account_id: int, amount: Decimal) -> tuple[Deposit, HSAAccount]:
    if amount <= Decimal("0"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid deposit amount",
        )

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

        deposit = Deposit(account_id=account.id, amount=amount)
        db.add(deposit)

        account.balance = account.balance + amount

    db.refresh(deposit)
    db.refresh(account)
    return deposit, account


def issue_card(db: Session, account_id: int) -> DebitCard:
    account = db.scalar(select(HSAAccount).where(HSAAccount.id == account_id))
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="account not found",
        )

    existing_card = db.scalar(select(DebitCard).where(DebitCard.account_id == account_id))
    if existing_card is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="account already has a debit card",
        )

    card = DebitCard(
        account_id=account_id,
        card_token=secrets.token_urlsafe(24),
        status="active",
    )
    db.add(card)
    db.commit()
    db.refresh(card)
    return card
