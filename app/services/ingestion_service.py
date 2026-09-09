from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from app.repositories.chart_repository import ChartRepository
from app.schemas.ingestion import NormalizedChartEntry
from app.services.episode_service import EpisodeService
from app.services.podcast_service import PodcastService


class ChartIngestionService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.podcast_service = PodcastService(session)
        self.chart_repository = ChartRepository(session)

    def ingest(
        self,
        entries: list[NormalizedChartEntry],
        *,
        source: str,
        country: str,
        category: str | None,
        snapshot_date: date,
    ) -> list[UUID]:
        category_id = None
        podcast_ids: list[UUID] = []
        if category:
            category_id = self.podcast_service.repository.get_or_create_category(category).id

        for entry in entries:
            if source == "podchaser":
                provider_id_field = "podchaser_id"
            elif source == "apple":
                provider_id_field = "apple_id"
            else:
                provider_id_field = "spotify_id"
            podcast = self.podcast_service.upsert_podcast(
                {
                    "title": entry.title,
                    "publisher": entry.publisher,
                    "description": entry.description,
                    "cover_image_url": entry.image_url,
                    provider_id_field: entry.apple_id or entry.external_id,
                }
            )
            if podcast.id not in podcast_ids:
                podcast_ids.append(podcast.id)
            if category:
                self.podcast_service.assign_categories(podcast.id, [category])
            episode_id = None
            if entry.chart_type == "episode":
                if not entry.episode_external_id or not entry.episode_title:
                    raise ValueError(
                        "Episode chart entries require episode_external_id and episode_title"
                    )
                episode = EpisodeService(self.session).upsert_episode(
                    podcast.id,
                    entry.episode_external_id,
                    {"title": entry.episode_title},
                )
                episode_id = episode.id
            self.chart_repository.upsert_snapshot(
                source=source,
                country=country.upper(),
                category_id=category_id,
                snapshot_date=snapshot_date,
                chart_type=entry.chart_type,
                rank=entry.rank,
                podcast_id=podcast.id,
                episode_id=episode_id,
            )
        return podcast_ids
