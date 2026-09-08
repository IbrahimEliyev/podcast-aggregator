from __future__ import annotations

import re
from typing import Any

import httpx

from app.schemas.ingestion import EnrichedPodcastData


class ApplePodcastsClient:
    """Client for Apple's public podcast search and lookup endpoints."""

    def __init__(self) -> None:
        self._client = httpx.Client(
            base_url="https://itunes.apple.com",
            timeout=20,
            headers={"User-Agent": "PodcastAggregator/0.1"},
        )

    def close(self) -> None:
        self._client.close()

    def fetch_metadata(
        self,
        *,
        title: str,
        apple_id: str | None = None,
        country: str = "US",
    ) -> EnrichedPodcastData | None:
        if apple_id:
            response = self._client.get(
                "/lookup",
                params={"id": apple_id, "entity": "podcast"},
            )
            response.raise_for_status()
            results = response.json().get("results", [])
            if results:
                return self._normalize(results[0])

        response = self._client.get(
            "/search",
            params={
                "term": title,
                "country": country.upper(),
                "media": "podcast",
                "entity": "podcast",
                "limit": 5,
            },
        )
        response.raise_for_status()
        results = response.json().get("results", [])
        if not results:
            return None

        normalized_title = self._normalize_text(title)
        result = next(
            (
                item
                for item in results
                if self._normalize_text(
                    item.get("collectionName") or item.get("trackName") or ""
                )
                == normalized_title
            ),
            results[0],
        )
        return self._normalize(result)

    @staticmethod
    def _normalize_text(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()

    @staticmethod
    def _normalize(result: dict[str, Any]) -> EnrichedPodcastData:
        categories = []
        for category in result.get("genres", []):
            if category and category != "Podcasts":
                categories.append(str(category))
        if result.get("primaryGenreName") and result["primaryGenreName"] not in categories:
            categories.append(str(result["primaryGenreName"]))

        return EnrichedPodcastData(
            title=result.get("collectionName") or result.get("trackName"),
            description=result.get("description") or result.get("longDescription"),
            author=result.get("artistName"),
            publisher=result.get("artistName"),
            cover_image_url=result.get("artworkUrl600") or result.get("artworkUrl100"),
            rss_url=result.get("feedUrl"),
            rating=result.get("averageUserRating"),
            rating_count=result.get("userRatingCount"),
            apple_id=str(result["collectionId"]) if result.get("collectionId") else None,
            categories=categories,
        )
