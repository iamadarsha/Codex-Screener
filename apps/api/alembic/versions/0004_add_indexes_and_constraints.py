"""add query indexes for screener and user tables

Revision ID: 0004_indexes
Revises: 0003_user_tables
Create Date: 2026-03-12 13:33:00
"""

from __future__ import annotations

from alembic import op


# revision identifiers, used by Alembic.
revision = "0004_indexes"
down_revision = "0003_user_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_stocks_exchange_symbol", "stocks", ["exchange", "symbol"])
    op.create_index("ix_stocks_market_cap", "stocks", ["market_cap"])
    op.create_index("ix_stocks_nifty50", "stocks", ["is_nifty50"])
    op.create_index("ix_stocks_nifty500", "stocks", ["is_nifty500"])
    op.create_index("ix_ohlcv_daily_symbol_date", "ohlcv_daily", ["symbol", "date"])
    op.execute(
        "CREATE INDEX ix_ohlcv_1min_symbol_ts_desc ON ohlcv_1min (symbol, ts DESC)"
    )
    op.create_index("ix_user_scans_user_id", "user_scans", ["user_id"])
    op.create_index("ix_scan_runs_scan_id", "scan_runs", ["scan_id"])
    op.create_index("ix_watchlist_user_id_position", "watchlist", ["user_id", "position"])
    op.create_index("ix_alerts_user_id_active", "alerts", ["user_id", "is_active"])
    op.create_index(
        "ix_alert_history_alert_id_triggered_at",
        "alert_history",
        ["alert_id", "triggered_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_alert_history_alert_id_triggered_at", table_name="alert_history")
    op.drop_index("ix_alerts_user_id_active", table_name="alerts")
    op.drop_index("ix_watchlist_user_id_position", table_name="watchlist")
    op.drop_index("ix_scan_runs_scan_id", table_name="scan_runs")
    op.drop_index("ix_user_scans_user_id", table_name="user_scans")
    op.execute("DROP INDEX IF EXISTS ix_ohlcv_1min_symbol_ts_desc")
    op.drop_index("ix_ohlcv_daily_symbol_date", table_name="ohlcv_daily")
    op.drop_index("ix_stocks_nifty500", table_name="stocks")
    op.drop_index("ix_stocks_nifty50", table_name="stocks")
    op.drop_index("ix_stocks_market_cap", table_name="stocks")
    op.drop_index("ix_stocks_exchange_symbol", table_name="stocks")
