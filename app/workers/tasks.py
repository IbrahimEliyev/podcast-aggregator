from __future__ import annotations

from datetime import date
import os
from uuid import UUID

from app.clients.apple_podcasts_client import ApplePodcastsClient
from app.clients.apple_charts_client import AppleChartsClient
from app.clients.podchaser_client import PodchaserClient
from app.clients.rss_client import RSSClient
from app.clients.spotify_client import SpotifyClient
from app.db.session import SessionLocal
from app.db.partitioning import ensure_chart_snapshot_partitions
from app.services.ingestion_service import ChartIngestionService
from app.services.episode_service import EpisodeService
from app.services.podcast_service import PodcastService
from app.repositories.podcast_repository import PodcastRepository
from app.workers.celery_app import celery_app


def configured_chart_countries() -> list[str]:
    """Return configured ISO-3166 alpha-2 markets, defaulting to US."""
    raw_countries = os.getenv("CHART_COUNTRIES", "US").split(",")
    countries = []
    for raw_country in raw_countries:
        country = raw_country.strip().upper()
        if len(country) == 2 and country.isalpha() and country not in countries:
            countries.append(country)
    if not countries:
        raise ValueError("CHART_COUNTRIES must contain at least one two-letter country code")
    return countries


def configured_spotify_countries() -> set[str]:
    """Return markets supported by Spotify's public chart endpoint."""
    raw_countries = os.getenv("CHART_SPOTIFY_COUNTRIES", "US,GB,CA,AU,DE").split(",")
    return {
        country.strip().upper()
        for country in raw_countries
        if len(country.strip()) == 2 and country.strip().isalpha()
    }


def configured_chart_categories() -> list[str | None]:
    """Return the overall chart plus configured category names."""
    raw_categories = os.getenv("CHART_CATEGORIES", "").split(",")
    categories: list[str | None] = [None]
    for raw_category in raw_categories:
        category = raw_category.strip()
        if category and category not in categories:
            categories.append(category)
    return categories


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
)
def collect_podchaser_chart(
    self, country: str = "US", category: str | None = None
) -> int:
    if os.getenv("PODCHASER_ENABLED", "false").lower() != "true":
        return 0

    client = PodchaserClient()
    try:
        entries = client.fetch_chart(country=country, category=category)
        with SessionLocal.begin() as session:
            podcast_ids = ChartIngestionService(session).ingest(
                entries,
                source="podchaser",
                country=country,
                category=category,
                snapshot_date=date.today(),
            )

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
    rate_limit="10/m",
)
def collect_apple_episode_chart(
    self, country: str = "US", category: str | None = None
) -> int:
    client = AppleChartsClient()
    try:
        entries = client.fetch_trending_episodes(country=country, category=category)
        with SessionLocal.begin() as session:
            podcast_ids = ChartIngestionService(session).ingest(
                entries,
                source="apple",
                country=country,
                category=category,
                snapshot_date=date.today(),
            )

        for podcast_id in podcast_ids:
            enrich_podcast.delay(str(podcast_id))
        return len(entries)
    finally:
        client.close()


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
    rate_limit="10/m",
)
def collect_apple_podcast_chart(
    self, country: str = "US", category: str | None = None
) -> int:
    client = AppleChartsClient()
    try:
        entries = client.fetch_top_shows(country=country, category=category)
        with SessionLocal.begin() as session:
            podcast_ids = ChartIngestionService(session).ingest(
                entries,
                source="apple",
                country=country,
                category=category,
                snapshot_date=date.today(),
            )

        for podcast_id in podcast_ids:
            enrich_podcast.delay(str(podcast_id))
        return len(entries)
    finally:
        client.close()


@celery_app.task
def collect_configured_chart_countries() -> int:
    """Queue provider-supported chart collection for every configured market."""
    countries = configured_chart_countries()
    spotify_countries = configured_spotify_countries()
    categories = configured_chart_categories()
    for country in countries:
        for category in categories:
            if country in spotify_countries:
                collect_spotify_chart.delay(country, category)
            if os.getenv("PODCHASER_ENABLED", "false").lower() == "true":
                collect_podchaser_chart.delay(country, category)
        collect_apple_podcast_chart.delay(country, None)
        collect_apple_episode_chart.delay(country, None)
    return len(countries)


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def maintain_chart_snapshot_partitions(self) -> int:
    with SessionLocal.begin() as session:
        partitions = ensure_chart_snapshot_partitions(session, months_ahead=2)
    return len(partitions)


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
            episode_service = EpisodeService(session)
            episode_count = episode_service.sync_episodes(podcast.id, episodes)
            frequency = episode_service.calculate_frequency(episodes)
            if frequency:
                podcast.episode_frequency = frequency
            return episode_count
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
