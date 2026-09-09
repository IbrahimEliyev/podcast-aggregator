from __future__ import annotations

import json
import re
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.schemas.ingestion import NormalizedChartEntry


class ChartParseError(RuntimeError):
    pass


class SpotifyClient:
    base_url = "https://podcastcharts.byspotify.com"

    def __init__(self, client: httpx.Client | None = None) -> None:
        self.client = client or httpx.Client(
            base_url=self.base_url,
            timeout=20.0,
            follow_redirects=True,
            headers={"User-Agent": "PodcastAggregator/0.1"},
        )

    def close(self) -> None:
        self.client.close()

    def fetch_chart(
        self, country: str, category: str | None = None
    ) -> list[NormalizedChartEntry]:
        country = country.lower()
        category_slug = self._category_slug(category)
        api_response = self.client.get(
            f"/api/charts/{category_slug}",
            params={"region": country, "limit": 100},
            headers={"Accept": "application/json"},
        )
        if api_response.is_success:
            entries = self.parse_api_chart(api_response.json(), category=category)
        else:
            page_response = self.client.get(f"/{country}/{category_slug}")
            page_response.raise_for_status()
            entries = self.parse_chart(page_response.text, country=country, category=category)
        if not entries:
            raise ChartParseError(f"No chart entries found for {country}/{category_slug}")
        return entries

    @staticmethod
    def _category_slug(category: str | None) -> str:
        if not category:
            return "top-podcasts"
        return re.sub(r"[^a-z0-9]+", "-", category.lower()).strip("-")

    @classmethod
    def parse_api_chart(
        cls, payload: object, *, category: str | None = None
    ) -> list[NormalizedChartEntry]:
        if not isinstance(payload, list):
            return []
        entries: list[NormalizedChartEntry] = []
        for rank, item in enumerate(payload, start=1):
            if not isinstance(item, dict):
                continue
            show_uri = cls._string_value(item.get("showUri"))
            external_id = show_uri.removeprefix("spotify:show:") if show_uri else None
            episode_uri = cls._string_value(
                item.get("episodeUri") or item.get("episodeUrl")
            )
            episode_external_id = (
                episode_uri.removeprefix("spotify:episode:") if episode_uri else None
            )
            episode_external_id = episode_external_id or cls._string_value(
                item.get("episodeId") or item.get("episodeGuid")
            )
            episode_title = cls._string_value(item.get("episodeName") or item.get("episodeTitle"))
            chart_type = "episode" if episode_external_id and episode_title else "podcast"
            podcast_url = (
                f"https://open.spotify.com/show/{external_id}" if external_id else None
            )
            title = cls._string_value(item.get("showName"))
            if not title:
                continue
            entries.append(
                NormalizedChartEntry(
                    rank=rank,
                    title=title,
                    chart_type=chart_type,
                    external_id=external_id,
                    podcast_url=podcast_url,
                    image_url=cls._string_value(item.get("showImageUrl")),
                    publisher=cls._string_value(item.get("showPublisher")),
                    description=cls._string_value(item.get("showDescription")),
                    categories=[category] if category else [],
                    episode_title=episode_title,
                    episode_external_id=episode_external_id,
                )
            )
        return entries

    @classmethod
    def parse_chart(
        cls, html: str, *, country: str, category: str | None = None
    ) -> list[NormalizedChartEntry]:
        soup = BeautifulSoup(html, "html.parser")
        entries = cls._parse_json_payloads(soup, category)
        if entries:
            return entries
        return cls._parse_html_cards(soup, category)

    @classmethod
    def _parse_json_payloads(
        cls, soup: BeautifulSoup, category: str | None
    ) -> list[NormalizedChartEntry]:
        entries: list[NormalizedChartEntry] = []
        for script in soup.find_all("script"):
            text = script.string or script.get_text()
            if not text or not text.strip().startswith(("{", "[")):
                continue
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                continue
            cls._collect_json_entries(payload, entries, category)
        return sorted(entries, key=lambda item: item.rank)

    @classmethod
    def _collect_json_entries(
        cls, value: object, entries: list[NormalizedChartEntry], category: str | None
    ) -> None:
        if isinstance(value, list):
            for item in value:
                cls._collect_json_entries(item, entries, category)
            return
        if not isinstance(value, dict):
            return

        rank = value.get("rank") or value.get("position") or value.get("chartPosition")
        title = value.get("title") or value.get("name")
        if isinstance(rank, int | float) and isinstance(title, str):
            external_id = value.get("id") or value.get("spotifyId") or value.get("uri")
            episode_external_id = value.get("episodeId") or value.get("episodeGuid")
            episode_title = value.get("episodeTitle") or value.get("episodeName")
            chart_type = "episode" if episode_external_id and episode_title else "podcast"
            image = value.get("image") or value.get("imageUrl") or value.get("coverImageUrl")
            if isinstance(image, dict):
                image = image.get("url")
            entries.append(
                NormalizedChartEntry(
                    rank=int(rank),
                    title=title.strip(),
                    chart_type=chart_type,
                    external_id=str(external_id) if external_id else None,
                    podcast_url=cls._string_value(value.get("url") or value.get("href")),
                    image_url=cls._string_value(image),
                    publisher=cls._string_value(value.get("publisher") or value.get("author")),
                    description=cls._string_value(value.get("description")),
                    categories=[category] if category else [],
                    episode_title=cls._string_value(episode_title),
                    episode_external_id=cls._string_value(episode_external_id),
                )
            )
        for child in value.values():
            cls._collect_json_entries(child, entries, category)

    @classmethod
    def _parse_html_cards(
        cls, soup: BeautifulSoup, category: str | None
    ) -> list[NormalizedChartEntry]:
        entries: list[NormalizedChartEntry] = []
        for index, link in enumerate(soup.select("a[href*='/show/']"), start=1):
            title = link.get_text(" ", strip=True)
            if not title:
                continue
            image = link.find("img")
            entries.append(
                NormalizedChartEntry(
                    rank=index,
                    title=title,
                    podcast_url=urljoin(cls.base_url, link.get("href", "")),
                    image_url=image.get("src") if image else None,
                    categories=[category] if category else [],
                )
            )
        return entries

    @staticmethod
    def _string_value(value: object) -> str | None:
        return value.strip() if isinstance(value, str) and value.strip() else None
