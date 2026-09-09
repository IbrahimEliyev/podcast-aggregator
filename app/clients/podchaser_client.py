from __future__ import annotations

import json
import os
import re
from typing import Any
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.schemas.ingestion import NormalizedChartEntry


class PodchaserClient:
    """Fetch Podchaser chart pages and normalize chart entries."""

    def __init__(self) -> None:
        self._client = httpx.Client(
            timeout=30,
            follow_redirects=True,
            headers={
                "User-Agent": os.getenv("PODCHASER_USER_AGENT", "PodcastAggregator/0.1"),
                "Accept": "text/html,application/xhtml+xml,application/json",
            },
        )
        self.base_url = os.getenv(
            "PODCHASER_CHARTS_URL", "https://www.podchaser.com/charts"
        )

    def close(self) -> None:
        self._client.close()

    def fetch_chart(
        self, *, country: str = "US", category: str | None = None
    ) -> list[NormalizedChartEntry]:
        params = {"country": country.lower()}
        if category:
            params["category"] = category
        response = self._client.get(self.base_url, params=params)
        response.raise_for_status()
        return self.parse_chart(response.text, country=country, category=category)

    @classmethod
    def parse_chart(
        cls, html: str, *, country: str, category: str | None = None
    ) -> list[NormalizedChartEntry]:
        entries = cls._parse_embedded_json(html, country=country, category=category)
        return entries or cls._parse_podcast_links(html, country=country, category=category)

    @classmethod
    def _parse_embedded_json(
        cls, html: str, *, country: str, category: str | None
    ) -> list[NormalizedChartEntry]:
        soup = BeautifulSoup(html, "html.parser")
        candidates: list[dict[str, Any]] = []
        for script in soup.find_all("script"):
            raw = script.string or script.get_text()
            if not raw.strip() or not raw.lstrip().startswith(("{", "[")):
                continue
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                continue
            cls._collect_candidates(payload, candidates)
        return cls._normalize_candidates(candidates, country=country, category=category)

    @classmethod
    def _collect_candidates(cls, value: Any, output: list[dict[str, Any]]) -> None:
        if isinstance(value, dict):
            rank = value.get("rank", value.get("rankPosition", value.get("position")))
            title = value.get("title") or value.get("name") or value.get("podcastName")
            if rank is not None and title:
                output.append(value)
            for child in value.values():
                cls._collect_candidates(child, output)
        elif isinstance(value, list):
            for child in value:
                cls._collect_candidates(child, output)

    @classmethod
    def _normalize_candidates(
        cls, candidates: list[dict[str, Any]], *, country: str, category: str | None
    ) -> list[NormalizedChartEntry]:
        entries: list[NormalizedChartEntry] = []
        seen: set[str] = set()
        for candidate in candidates:
            title = str(
                candidate.get("title")
                or candidate.get("name")
                or candidate.get("podcastName")
            ).strip()
            external_id = candidate.get("podchaserId") or candidate.get("id")
            if not external_id:
                external_id = cls._id_from_url(candidate.get("url"))
            key = str(external_id or title).lower()
            if not title or key in seen:
                continue
            seen.add(key)
            rank = candidate.get("rank", candidate.get("rankPosition", candidate.get("position")))
            try:
                rank_number = int(rank)
            except (TypeError, ValueError):
                continue
            entries.append(
                NormalizedChartEntry(
                    rank=rank_number,
                    title=title,
                    external_id=str(external_id) if external_id else None,
                    podcast_url=cls._absolute_url(candidate.get("url")),
                    image_url=candidate.get("image") or candidate.get("imageUrl"),
                    publisher=candidate.get("publisher") or candidate.get("author"),
                    description=candidate.get("description"),
                    categories=[category] if category else [],
                )
            )
        return sorted(entries, key=lambda entry: entry.rank)

    @classmethod
    def _parse_podcast_links(
        cls, html: str, *, country: str, category: str | None
    ) -> list[NormalizedChartEntry]:
        soup = BeautifulSoup(html, "html.parser")
        entries: list[NormalizedChartEntry] = []
        seen: set[str] = set()
        for anchor in soup.select("a[href*='/podcasts/']"):
            href = anchor.get("href")
            title = anchor.get_text(" ", strip=True)
            if not href or not title or href in seen:
                continue
            seen.add(href)
            image = anchor.find("img")
            entries.append(
                NormalizedChartEntry(
                    rank=len(entries) + 1,
                    title=title,
                    external_id=cls._id_from_url(href),
                    podcast_url=cls._absolute_url(href),
                    image_url=image.get("src") if image else None,
                    categories=[category] if category else [],
                )
            )
        return entries

    @staticmethod
    def _id_from_url(url: str | None) -> str | None:
        if not url:
            return None
        match = re.search(r"/podcasts/[^/]+/([^/?#]+)", url)
        return match.group(1) if match else None

    @staticmethod
    def _absolute_url(url: str | None) -> str | None:
        return urljoin("https://www.podchaser.com", url) if url else None
