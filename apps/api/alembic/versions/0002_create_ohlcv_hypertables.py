"""convert ohlcv_1min into a Timescale hypertable

Revision ID: 0002_hyper
Revises: 0001_core
Create Date: 2026-03-12 13:31:00
"""

from __future__ import annotations

from alembic import op


# revision identifiers, used by Alembic.
revision = "0002_hyper"
down_revision = "0001_core"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        SELECT create_hypertable(
          'ohlcv_1min',
          by_range('ts', INTERVAL '1 day'),
          if_not_exists => TRUE
        )
        """
    )
    op.execute(
        """
        SELECT add_dimension(
          'ohlcv_1min',
          by_hash('symbol', 4),
          if_not_exists => TRUE
        )
        """
    )


def downgrade() -> None:
    pass
