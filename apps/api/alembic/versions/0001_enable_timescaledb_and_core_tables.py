"""enable extensions and create core market tables

Revision ID: 0001_core
Revises:
Create Date: 2026-03-12 13:30:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0001_core"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # TimescaleDB skipped — not available on Supabase free tier.
    # OHLCV tables work as regular PostgreSQL tables.
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.create_table(
        "stocks",
        sa.Column("symbol", sa.String(length=24), nullable=False),
        sa.Column("isin", sa.String(length=24), nullable=True),
        sa.Column("instrument_key", sa.String(length=128), nullable=True),
        sa.Column("company_name", sa.Text(), nullable=False),
        sa.Column("exchange", sa.String(length=8), nullable=False, server_default="NSE"),
        sa.Column("sector", sa.String(length=128), nullable=True),
        sa.Column("market_cap", sa.Numeric(20, 2), nullable=True),
        sa.Column("pe", sa.Numeric(12, 4), nullable=True),
        sa.Column("pb", sa.Numeric(12, 4), nullable=True),
        sa.Column("roe", sa.Numeric(12, 4), nullable=True),
        sa.Column("debt_equity", sa.Numeric(12, 4), nullable=True),
        sa.Column("div_yield", sa.Numeric(12, 4), nullable=True),
        sa.Column("is_nifty50", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_nifty500", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_fno", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.PrimaryKeyConstraint("symbol", name=op.f("pk_stocks")),
        sa.UniqueConstraint("instrument_key", name=op.f("uq_stocks_instrument_key")),
    )

    op.create_table(
        "ohlcv_1min",
        sa.Column("symbol", sa.String(length=24), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("open", sa.Numeric(18, 4), nullable=False),
        sa.Column("high", sa.Numeric(18, 4), nullable=False),
        sa.Column("low", sa.Numeric(18, 4), nullable=False),
        sa.Column("close", sa.Numeric(18, 4), nullable=False),
        sa.Column("volume", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(["symbol"], ["stocks.symbol"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("symbol", "ts", name=op.f("pk_ohlcv_1min")),
    )

    op.create_table(
        "ohlcv_daily",
        sa.Column("symbol", sa.String(length=24), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("open", sa.Numeric(18, 4), nullable=False),
        sa.Column("high", sa.Numeric(18, 4), nullable=False),
        sa.Column("low", sa.Numeric(18, 4), nullable=False),
        sa.Column("close", sa.Numeric(18, 4), nullable=False),
        sa.Column("volume", sa.BigInteger(), nullable=False),
        sa.Column("week_high_52", sa.Numeric(18, 4), nullable=True),
        sa.Column("week_low_52", sa.Numeric(18, 4), nullable=True),
        sa.ForeignKeyConstraint(["symbol"], ["stocks.symbol"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("symbol", "date", name=op.f("pk_ohlcv_daily")),
    )


def downgrade() -> None:
    op.drop_table("ohlcv_daily")
    op.drop_table("ohlcv_1min")
    op.drop_table("stocks")
    op.execute("DROP EXTENSION IF EXISTS pgcrypto")
    op.execute("DROP EXTENSION IF EXISTS timescaledb")
