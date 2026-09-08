from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.repositories.chart_repository import ChartRepository
from app.schemas.ingestion import NormalizedChartEntry
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
    ) -> int:
        category_id = None
        if category:
            category_id = self.podcast_service.repository.get_or_create_category(category).id

        for entry in entries:
            podcast = self.podcast_service.upsert_podcast(
                {
                    "title": entry.title,
                    "publisher": entry.publisher,
                    "description": entry.description,
                    "cover_image_url": entry.image_url,
                    "spotify_id": entry.external_id,
                }
            )
            if category:
                self.podcast_service.assign_categories(podcast.id, [category])
            self.chart_repository.upsert_snapshot(
                source=source,
                country=country.upper(),
                category_id=category_id,
                snapshot_date=snapshot_date,
                chart_type="podcast",
                rank=entry.rank,
                podcast_id=podcast.id,
            )
        return len(entries)
