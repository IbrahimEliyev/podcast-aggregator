from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base


class Podcast(Base):
    __tablename__ = "podcasts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    author: Mapped[str | None] = mapped_column(String(500))
    publisher: Mapped[str | None] = mapped_column(String(500))
    cover_image_url: Mapped[str | None] = mapped_column(Text)
    rss_url: Mapped[str | None] = mapped_column(Text, unique=True)
    language: Mapped[str | None] = mapped_column(String(20))
    rating: Mapped[Decimal | None] = mapped_column(Numeric(4, 2))
    rating_count: Mapped[int | None] = mapped_column()
    episode_frequency: Mapped[str | None] = mapped_column(String(100))
    spotify_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    podchaser_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    podcast_index_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    categories: Mapped[list[PodcastCategory]] = relationship(back_populates="podcast")
    episodes: Mapped[list[Episode]] = relationship(back_populates="podcast", cascade="all, delete-orphan")
    chart_snapshots: Mapped[list[ChartSnapshot]] = relationship(back_populates="podcast")


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    podcasts: Mapped[list[PodcastCategory]] = relationship(back_populates="category")


class PodcastCategory(Base):
    __tablename__ = "podcast_categories"
    __table_args__ = (UniqueConstraint("podcast_id", "category_id", name="uq_podcast_category"),)

    podcast_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("podcasts.id", ondelete="CASCADE"), primary_key=True)
    category_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True)

    podcast: Mapped[Podcast] = relationship(back_populates="categories")
    category: Mapped[Category] = relationship(back_populates="podcasts")


from app.db.models.episode import Episode  # noqa: E402
from app.db.models.chart import ChartSnapshot  # noqa: E402
