from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base

if TYPE_CHECKING:
    from app.models.debit_card import DebitCard
    from app.models.deposit import Deposit
    from app.models.transaction import Transaction


class HSAAccount(Base):
    """Primary HSA account with current available balance."""

    __tablename__ = "hsa_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_holder_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # One account can have at most one virtual debit card.
    debit_card: Mapped[Optional[DebitCard]] = relationship(
        back_populates="account",
        uselist=False,
    )

    # One account can have many deposit ledger entries.
    deposits: Mapped[list[Deposit]] = relationship(back_populates="account")

    # One account can have many purchase transactions.
    transactions: Mapped[list[Transaction]] = relationship(back_populates="account")
