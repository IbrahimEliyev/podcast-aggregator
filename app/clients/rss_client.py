from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

import feedparser
import httpx

from app.schemas.ingestion import NormalizedEpisode


class RSSClient:
    """Fetch and normalize podcast episodes from an RSS or Atom feed."""

    def __init__(self) -> None:
        self._client = httpx.Client(
            timeout=30,
            follow_redirects=True,
            headers={"User-Agent": "PodcastAggregator/0.1"},
        )

    def close(self) -> None:
        self._client.close()

    def fetch_episodes(self, rss_url: str) -> list[NormalizedEpisode]:
        response = self._client.get(rss_url)
        response.raise_for_status()
        parsed = feedparser.parse(response.content)
        if parsed.bozo and not parsed.entries:
            raise ValueError(f"Could not parse RSS feed: {rss_url}")

        episodes: list[NormalizedEpisode] = []
        for entry in parsed.entries:
            guid = str(entry.get("guid") or entry.get("id") or entry.get("link") or "").strip()
            title = self._clean_text(entry.get("title"))
            if not guid or not title:
                continue
            episodes.append(
                NormalizedEpisode(
                    guid=guid,
                    title=title,
                    description=self._clean_text(
                        entry.get("summary") or entry.get("description")
                    ),
                    audio_url=self._audio_url(entry),
                    published_at=self._published_at(entry),
                    duration_seconds=self._duration_seconds(entry),
                )
            )
        return episodes

    @staticmethod
    def _clean_text(value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        if not any(marker in text for marker in ("Ã", "Â", "â")) and not any(
            0x80 <= ord(character) <= 0x9F for character in text
        ):
            return text
        try:
            repaired = text.encode("latin-1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            return text
        return repaired.strip()

    @staticmethod
    def _audio_url(entry: Any) -> str | None:
        enclosures = entry.get("enclosures", [])
        if enclosures and enclosures[0].get("href"):
            return str(enclosures[0]["href"])
        return entry.get("link")

    @staticmethod
    def _published_at(entry: Any) -> datetime | None:
        parsed_time = entry.get("published_parsed") or entry.get("updated_parsed")
        if parsed_time:
            return datetime(*parsed_time[:6], tzinfo=timezone.utc)

        raw_value = entry.get("published") or entry.get("updated")
        if not raw_value:
            return None
        try:
            parsed = parsedate_to_datetime(str(raw_value))
        except (TypeError, ValueError):
            return None
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)

    @staticmethod
    def _duration_seconds(entry: Any) -> int | None:
        raw_duration = entry.get("itunes_duration") or entry.get("duration")
        if raw_duration is None:
            return None
        if isinstance(raw_duration, (int, float)):
            return int(raw_duration)

        parts = str(raw_duration).strip().split(":")
        if not all(part.isdigit() for part in parts):
            return None
        values = [int(part) for part in parts]
        if len(values) == 3:
            return values[0] * 3600 + values[1] * 60 + values[2]
        if len(values) == 2:
            return values[0] * 60 + values[1]
        if len(values) == 1:
            return values[0]
        return None
