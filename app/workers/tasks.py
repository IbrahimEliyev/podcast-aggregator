from __future__ import annotations

from datetime import date

from app.clients.spotify_client import SpotifyClient
from app.db.session import SessionLocal
from app.services.ingestion_service import ChartIngestionService
from app.workers.celery_app import celery_app


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def collect_spotify_chart(
    self, country: str, category: str | None = None
) -> int:
    client = SpotifyClient()
    try:
        entries = client.fetch_chart(country=country, category=category)
        with SessionLocal.begin() as session:
            return ChartIngestionService(session).ingest(
                entries,
                source="spotify",
                country=country,
                category=category,
                snapshot_date=date.today(),
            )
    finally:
        client.close()
