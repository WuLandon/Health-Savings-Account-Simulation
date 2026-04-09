from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base

if TYPE_CHECKING:
    from app.models.hsa_account import HSAAccount
    from app.models.transaction import Transaction


class DebitCard(Base):
    """Simulated virtual debit card tied to one HSA account."""

    __tablename__ = "debit_cards"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("hsa_accounts.id"),
        nullable=False,
        unique=True,
    )
    card_token: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Each card belongs to exactly one account.
    account: Mapped[HSAAccount] = relationship(back_populates="debit_card")

    # A card can be referenced by many transactions over time.
    transactions: Mapped[list[Transaction]] = relationship(back_populates="card")
