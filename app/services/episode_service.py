from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.db.models import Episode
from app.repositories.episode_repository import EpisodeRepository
from app.schemas.ingestion import NormalizedEpisode


class EpisodeService:
    def __init__(self, session: Session) -> None:
        self.repository = EpisodeRepository(session)

    def upsert_episode(self, podcast_id: uuid.UUID, guid: str, values: dict[str, object]) -> Episode:
        return self.repository.upsert(podcast_id, guid, **values)

    def sync_episodes(
        self, podcast_id: uuid.UUID, episodes: list[NormalizedEpisode]
    ) -> int:
        for episode in episodes:
            self.repository.upsert(
                podcast_id,
                episode.guid,
                title=episode.title,
                description=episode.description,
                audio_url=episode.audio_url,
                published_at=episode.published_at,
                duration_seconds=episode.duration_seconds,
            )
        return len(episodes)
