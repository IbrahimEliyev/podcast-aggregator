from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class NormalizedChartEntry:
    rank: int
    title: str
    external_id: str | None = None
    podcast_url: str | None = None
    image_url: str | None = None
    publisher: str | None = None
    description: str | None = None
    categories: list[str] = field(default_factory=list)
    episode_title: str | None = None
    episode_external_id: str | None = None


@dataclass(frozen=True)
class EnrichedPodcastData:
    """Provider-independent podcast metadata."""

    title: str | None = None
    description: str | None = None
    author: str | None = None
    publisher: str | None = None
    cover_image_url: str | None = None
    rss_url: str | None = None
    language: str | None = None
    rating: float | None = None
    rating_count: int | None = None
    episode_frequency: str | None = None
    apple_id: str | None = None
    podcast_index_id: str | None = None
    categories: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class NormalizedEpisode:
    guid: str
    title: str
    description: str | None = None
    audio_url: str | None = None
    published_at: datetime | None = None
    duration_seconds: int | None = None
