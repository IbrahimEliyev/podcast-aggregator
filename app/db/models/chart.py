from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base


class ChartSnapshot(Base):
    __tablename__ = "chart_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "source", "country", "category_id", "snapshot_date", "chart_type", "rank",
            name="uq_chart_snapshot_rank",
        ),
        Index("ix_chart_snapshots_lookup", "source", "country", "category_id", "snapshot_date", "rank"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    country: Mapped[str] = mapped_column(String(2), nullable=False)
    category_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"), index=True)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    chart_type: Mapped[str] = mapped_column(String(20), nullable=False, default="podcast")
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    podcast_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("podcasts.id", ondelete="CASCADE"), nullable=False, index=True)
    episode_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("episodes.id", ondelete="SET NULL"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    podcast: Mapped[Podcast] = relationship(back_populates="chart_snapshots")


from app.db.models.podcast import Podcast  # noqa: E402
