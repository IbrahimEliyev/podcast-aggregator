from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.db.models import Podcast
from app.repositories.podcast_repository import PodcastRepository


class PodcastService:
    def __init__(self, session: Session) -> None:
        self.repository = PodcastRepository(session)

    def upsert_podcast(self, values: dict[str, object]) -> Podcast:
        podcast = None
        for field in ("spotify_id", "podchaser_id", "podcast_index_id"):
            value = values.get(field)
            if value:
                podcast = self.repository.get_by_external_id(field, str(value))
                if podcast:
                    break
        if podcast is None and values.get("rss_url"):
            podcast = self.repository.get_by_rss_url(str(values["rss_url"]))

        if podcast is None:
            return self.repository.create(**values)

        for field, value in values.items():
            setattr(podcast, field, value)
        return self.repository.save(podcast)

    def assign_categories(self, podcast_id: uuid.UUID, category_names: list[str]) -> Podcast:
        podcast = self.repository.get_by_id(podcast_id)
        if podcast is None:
            raise ValueError(f"Podcast not found: {podcast_id}")
        for name in category_names:
            category = self.repository.get_or_create_category(name)
            self.repository.add_category(podcast, category)
        return podcast
