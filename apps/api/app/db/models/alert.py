from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    symbol: Mapped[str] = mapped_column(
        ForeignKey("stocks.symbol", ondelete="CASCADE"),
        nullable=False,
    )
    scan_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_scans.id", ondelete="SET NULL"),
        nullable=True,
    )
    notify_email: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notify_push: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notify_telegram: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    frequency: Mapped[str] = mapped_column(String(32), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

