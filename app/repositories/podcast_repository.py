from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Category, Podcast, PodcastCategory


class PodcastRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, podcast_id: uuid.UUID) -> Podcast | None:
        return self.session.get(Podcast, podcast_id)

    def get_by_external_id(self, field: str, value: str) -> Podcast | None:
        allowed_fields = {"spotify_id", "podchaser_id", "podcast_index_id"}
        if field not in allowed_fields:
            raise ValueError(f"Unsupported external ID field: {field}")
        return self.session.scalar(select(Podcast).where(getattr(Podcast, field) == value))

    def get_by_rss_url(self, rss_url: str) -> Podcast | None:
        return self.session.scalar(select(Podcast).where(Podcast.rss_url == rss_url))

    def create(self, **values: object) -> Podcast:
        podcast = Podcast(**values)
        self.session.add(podcast)
        self.session.flush()
        return podcast

    def save(self, podcast: Podcast) -> Podcast:
        self.session.add(podcast)
        self.session.flush()
        return podcast

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
