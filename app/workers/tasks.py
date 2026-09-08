from __future__ import annotations

from datetime import date
from uuid import UUID

from app.clients.apple_podcasts_client import ApplePodcastsClient
from app.clients.rss_client import RSSClient
from app.clients.spotify_client import SpotifyClient
from app.db.session import SessionLocal
from app.services.ingestion_service import ChartIngestionService
from app.services.episode_service import EpisodeService
from app.services.podcast_service import PodcastService
from app.repositories.podcast_repository import PodcastRepository
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
            podcast_ids = ChartIngestionService(session).ingest(
                entries,
                source="spotify",
                country=country,
                category=category,
                snapshot_date=date.today(),
            )

        # Queue enrichment only after the ingestion transaction has committed.
        for podcast_id in podcast_ids:
            enrich_podcast.delay(str(podcast_id))
        return len(podcast_ids)
    finally:
        client.close()


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
    rate_limit="20/m",
)
def enrich_podcast(self, podcast_id: str) -> bool:
    client = ApplePodcastsClient()
    try:
        with SessionLocal.begin() as session:
            podcast = PodcastService(session).repository.get_by_id(UUID(podcast_id))
            if podcast is None:
                return False

            metadata = client.fetch_metadata(
                title=podcast.title,
                apple_id=podcast.apple_id,
            )
            if metadata is None:
                return False

            PodcastService(session).enrich_podcast(podcast.id, metadata)
            enriched_podcast_id = podcast.id

        sync_podcast_episodes.delay(str(enriched_podcast_id))
        return True
    finally:
        client.close()


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
    rate_limit="30/m",
)
def sync_podcast_episodes(self, podcast_id: str) -> int:
    rss_client = RSSClient()
    try:
        with SessionLocal.begin() as session:
            podcast = PodcastService(session).repository.get_by_id(UUID(podcast_id))
            if podcast is None or not podcast.rss_url:
                return 0

            episodes = rss_client.fetch_episodes(podcast.rss_url)
            return EpisodeService(session).sync_episodes(podcast.id, episodes)
    finally:
        rss_client.close()


@celery_app.task
def sync_all_podcast_episodes() -> int:
    """Queue one rate-limited RSS sync task for every enriched podcast."""
    with SessionLocal.begin() as session:
        podcast_ids = PodcastRepository(session).list_ids_with_rss()

    for podcast_id in podcast_ids:
        sync_podcast_episodes.delay(str(podcast_id))
    return len(podcast_ids)
