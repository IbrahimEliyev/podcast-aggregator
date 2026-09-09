from __future__ import annotations

import uuid
from statistics import median

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

    @staticmethod
    def calculate_frequency(episodes: list[NormalizedEpisode]) -> str | None:
        """Estimate a human-readable publishing frequency from RSS dates."""
        dates = sorted(
            {
                episode.published_at
                for episode in episodes
                if episode.published_at is not None
            }
        )
        if len(dates) < 2:
            return None

        intervals = [
            (current - previous).total_seconds() / 86400
            for previous, current in zip(dates, dates[1:])
            if current > previous
        ]
        if not intervals:
            return None

        median_days = median(intervals)
        if median_days <= 1.5:
            return "daily"
        if median_days <= 8:
            return "weekly"
        if median_days <= 16:
            return "biweekly"
        if median_days <= 45:
            return "monthly"
        if median_days <= 100:
            return "quarterly"
        return "irregular"
