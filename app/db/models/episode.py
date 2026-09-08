from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base


class Episode(Base):
    __tablename__ = "episodes"
    __table_args__ = (
        UniqueConstraint("podcast_id", "guid", name="uq_episode_podcast_guid"),
        Index("ix_episodes_podcast_published_at", "podcast_id", "published_at", "id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    podcast_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("podcasts.id", ondelete="CASCADE"), nullable=False, index=True)
    guid: Mapped[str] = mapped_column(String(1000), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    audio_url: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    podcast: Mapped[Podcast] = relationship(back_populates="episodes")


from app.db.models.podcast import Podcast  # noqa: E402
