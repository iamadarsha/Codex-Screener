from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Boolean, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Stock(Base):
    __tablename__ = "stocks"

    symbol: Mapped[str] = mapped_column(String(24), primary_key=True)
    isin: Mapped[str | None] = mapped_column(String(24), nullable=True)
    instrument_key: Mapped[str | None] = mapped_column(String(128), unique=True)
    company_name: Mapped[str] = mapped_column(Text, nullable=False)
    exchange: Mapped[str] = mapped_column(String(8), nullable=False, default="NSE")
    sector: Mapped[str | None] = mapped_column(String(128), nullable=True)
    market_cap: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    pe: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    pb: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    roe: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    debt_equity: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    div_yield: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    is_nifty50: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_nifty500: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_fno: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

