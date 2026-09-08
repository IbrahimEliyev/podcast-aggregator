from __future__ import annotations

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db.models import Category, Podcast, PodcastCategory
from app.schemas.ingestion import EnrichedPodcastData


class PodcastRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, podcast_id: uuid.UUID) -> Podcast | None:
        return self.session.get(Podcast, podcast_id)

    def get_by_external_id(self, field: str, value: str) -> Podcast | None:
        allowed_fields = {"spotify_id", "apple_id", "podchaser_id", "podcast_index_id"}
        if field not in allowed_fields:
            raise ValueError(f"Unsupported external ID field: {field}")
        return self.session.scalar(select(Podcast).where(getattr(Podcast, field) == value))

    def get_by_rss_url(self, rss_url: str) -> Podcast | None:
        return self.session.scalar(select(Podcast).where(Podcast.rss_url == rss_url))

    def list_ids_with_rss(self) -> list[uuid.UUID]:
        statement = select(Podcast.id).where(Podcast.rss_url.is_not(None)).order_by(Podcast.id)
        return list(self.session.scalars(statement))

    def list(self, *, search: str | None, category_name: str | None, limit: int, offset: int) -> list[Podcast]:
        statement = select(Podcast).order_by(Podcast.title).limit(limit).offset(offset)
        if search:
            search_pattern = f"%{search}%"
            statement = statement.where(
                or_(Podcast.title.ilike(search_pattern), Podcast.author.ilike(search_pattern))
            )
        if category_name:
            statement = (
                statement.join(PodcastCategory, Podcast.id == PodcastCategory.podcast_id)
                .join(Category, PodcastCategory.category_id == Category.id)
                .where(Category.name == category_name)
                .distinct()
            )
        return list(self.session.scalars(statement))

    def count(self, *, search: str | None, category_name: str | None) -> int:
        statement = select(func.count(func.distinct(Podcast.id)))
        if search:
            search_pattern = f"%{search}%"
            statement = statement.where(
                or_(Podcast.title.ilike(search_pattern), Podcast.author.ilike(search_pattern))
            )
        if category_name:
            statement = (
                statement.join(PodcastCategory, Podcast.id == PodcastCategory.podcast_id)
                .join(Category, PodcastCategory.category_id == Category.id)
                .where(Category.name == category_name)
            )
        return int(self.session.scalar(statement) or 0)

    def create(self, **values: object) -> Podcast:
        podcast = Podcast(**values)
        self.session.add(podcast)
        self.session.flush()
        return podcast

    def save(self, podcast: Podcast) -> Podcast:
        self.session.add(podcast)
        self.session.flush()
        return podcast

    def update_metadata(
        self, podcast: Podcast, metadata: EnrichedPodcastData
    ) -> Podcast:
        values = {
            "description": metadata.description,
            "author": metadata.author,
            "publisher": metadata.publisher,
            "cover_image_url": metadata.cover_image_url,
            "rss_url": metadata.rss_url,
            "language": metadata.language,
            "rating": metadata.rating,
            "rating_count": metadata.rating_count,
            "episode_frequency": metadata.episode_frequency,
            "apple_id": metadata.apple_id,
            "podcast_index_id": metadata.podcast_index_id,
        }
        for field, value in values.items():
            if value is not None:
                setattr(podcast, field, value)
        return self.save(podcast)

    def get_or_create_category(self, name: str) -> Category:
        category = self.session.scalar(select(Category).where(Category.name == name))
        if category is None:
            category = Category(name=name)
            self.session.add(category)
            self.session.flush()
        return category

    def add_category(self, podcast: Podcast, category: Category) -> None:
        link = self.session.get(PodcastCategory, (podcast.id, category.id))
        if link is None:
            self.session.add(PodcastCategory(podcast_id=podcast.id, category_id=category.id))
            self.session.flush()
