from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.db.models import Podcast
from app.repositories.episode_repository import EpisodeRepository
from app.repositories.podcast_repository import PodcastRepository
from app.schemas.ingestion import EnrichedPodcastData


class PodcastService:
    def __init__(self, session: Session) -> None:
        self.repository = PodcastRepository(session)

    def upsert_podcast(self, values: dict[str, object]) -> Podcast:
        podcast = None
        for field in ("spotify_id", "apple_id", "podchaser_id", "podcast_index_id"):
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

    def enrich_podcast(
        self, podcast_id: uuid.UUID, metadata: EnrichedPodcastData
    ) -> Podcast:
        podcast = self.repository.get_by_id(podcast_id)
        if podcast is None:
            raise ValueError(f"Podcast not found: {podcast_id}")

        podcast = self.repository.update_metadata(podcast, metadata)
        if metadata.categories:
            self.assign_categories(podcast.id, metadata.categories)
        return podcast

    def list_podcasts(
        self, *, search: str | None, category_name: str | None, page: int, page_size: int
    ) -> tuple[list[Podcast], int]:
        offset = (page - 1) * page_size
        podcasts = self.repository.list(
            search=search,
            category_name=category_name,
            limit=page_size,
            offset=offset,
        )
        return podcasts, self.repository.count(search=search, category_name=category_name)

    def get_detail(
        self, podcast_id: uuid.UUID, *, episodes_page: int, episodes_page_size: int
    ) -> tuple[Podcast | None, list, int]:
        podcast = self.repository.get_by_id(podcast_id)
        if podcast is None:
            return None, [], 0
        episode_repository = EpisodeRepository(self.repository.session)
        episodes = episode_repository.list_for_podcast(
            podcast_id,
            limit=episodes_page_size,
            offset=(episodes_page - 1) * episodes_page_size,
        )
        return podcast, episodes, episode_repository.count_for_podcast(podcast_id)
