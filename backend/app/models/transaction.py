from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base

if TYPE_CHECKING:
    from app.models.debit_card import DebitCard
    from app.models.hsa_account import HSAAccount


class Transaction(Base):
    """Purchase attempt record, including approved and declined outcomes."""

    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("hsa_accounts.id"), nullable=False)
    card_id: Mapped[Optional[int]] = mapped_column(ForeignKey("debit_cards.id"), nullable=True)
    merchant_name: Mapped[str] = mapped_column(String(255), nullable=False)
    merchant_category: Mapped[str] = mapped_column(String(100), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    decline_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Each transaction belongs to one account.
    account: Mapped[HSAAccount] = relationship(back_populates="transactions")

    # A transaction may optionally reference a debit card.
    card: Mapped[Optional[DebitCard]] = relationship(back_populates="transactions")
