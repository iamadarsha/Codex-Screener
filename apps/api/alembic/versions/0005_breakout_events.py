"""create breakout_events table

Revision ID: 0005_breakout_events
Revises: 0004_indexes
Create Date: 2026-09-13 00:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "0005_breakout_events"
down_revision = "0004_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "breakout_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "symbol",
            sa.String(),
            sa.ForeignKey("stocks.symbol", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("trigger_type", sa.String(32), nullable=False),
        sa.Column("direction", sa.String(8), nullable=False),
        sa.Column("reference_level", sa.Numeric(18, 4), nullable=False),
        sa.Column("trigger_price", sa.Numeric(18, 4), nullable=False),
        sa.Column("confirmation_price", sa.Numeric(18, 4), nullable=True),
        sa.Column("score", sa.Numeric(6, 2), nullable=True),
        sa.Column(
            "extra",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("triggered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_breakout_events_symbol_confirmed_at", "breakout_events", ["symbol", "confirmed_at"]
    )
    op.create_index("ix_breakout_events_trigger_type", "breakout_events", ["trigger_type"])


def downgrade() -> None:
    op.drop_index("ix_breakout_events_trigger_type", table_name="breakout_events")
    op.drop_index("ix_breakout_events_symbol_confirmed_at", table_name="breakout_events")
    op.drop_table("breakout_events")
