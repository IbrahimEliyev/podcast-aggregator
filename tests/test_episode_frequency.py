from datetime import datetime, timedelta, timezone

from app.schemas.ingestion import NormalizedEpisode
from app.services.episode_service import EpisodeService


def _episode(published_at: datetime) -> NormalizedEpisode:
    return NormalizedEpisode(guid=published_at.isoformat(), title="Episode", published_at=published_at)


def test_calculate_frequency_returns_weekly() -> None:
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    episodes = [_episode(start + timedelta(days=days)) for days in (0, 7, 14, 21)]

    assert EpisodeService.calculate_frequency(episodes) == "weekly"


def test_calculate_frequency_requires_two_published_episodes() -> None:
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)

    assert EpisodeService.calculate_frequency([_episode(start)]) is None
