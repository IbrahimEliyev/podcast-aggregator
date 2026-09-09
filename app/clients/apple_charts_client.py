from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse

import httpx
from bs4 import BeautifulSoup, Tag

from app.schemas.ingestion import NormalizedChartEntry


class AppleChartParseError(RuntimeError):
    pass


class AppleChartsClient:
    """Reads the public Apple Podcasts Trending Episodes page.

    Apple does not expose this chart through the public iTunes Search API. The
    public web page is ordered by rank, so the parser deliberately preserves
    document order and derives the Apple show/episode IDs from each link.
    """

    base_url = "https://podcasts.apple.com"

    def __init__(self, client: httpx.Client | None = None) -> None:
        self.client = client or httpx.Client(
            base_url=self.base_url,
            timeout=30.0,
            follow_redirects=True,
            headers={"User-Agent": "PodcastAggregator/0.1"},
        )

    def close(self) -> None:
        self.client.close()

    def fetch_trending_episodes(
        self, *, country: str = "US", category: str | None = None
    ) -> list[NormalizedChartEntry]:
        # The page currently exposes the market in its path. Category filtering
        # is intentionally left to Apple’s UI until a stable public URL exists.
        response = self.client.get(f"/{country.lower()}/browse/top-charts/episodes")
        response.raise_for_status()
        entries = self.parse_trending_episodes(response.text, category=category)
        if not entries:
            raise AppleChartParseError("No Apple Trending Episodes found")
        return entries

    def fetch_top_shows(
        self, *, country: str = "US", category: str | None = None
    ) -> list[NormalizedChartEntry]:
        response = self.client.get(f"/{country.lower()}/browse/top-charts/shows")
        response.raise_for_status()
        entries = self.parse_top_shows(response.text, category=category)
        if not entries:
            raise AppleChartParseError("No Apple Top Shows found")
        return entries

    @classmethod
    def parse_top_shows(
        cls, html: str, *, category: str | None = None
    ) -> list[NormalizedChartEntry]:
        soup = BeautifulSoup(html, "html.parser")
        entries: list[NormalizedChartEntry] = []
        seen: set[str] = set()
        for link in soup.select('a[href*="/podcast/"]:not([href*="?i="])'):
            href = link.get("href")
            title = link.get_text(" ", strip=True)
            if not isinstance(href, str) or not title:
                continue
            match = re.search(r"/id(\d+)(?:\?|$)", urlparse(href).path)
            if not match or match.group(1) in seen:
                continue
            seen.add(match.group(1))
            entries.append(
                NormalizedChartEntry(
                    rank=len(entries) + 1,
                    title=title,
                    chart_type="podcast",
                    apple_id=match.group(1),
                    podcast_url=href,
                    categories=[category] if category else [],
                )
            )
        return entries

    @classmethod
    def parse_trending_episodes(
        cls, html: str, *, category: str | None = None
    ) -> list[NormalizedChartEntry]:
        soup = BeautifulSoup(html, "html.parser")
        entries: list[NormalizedChartEntry] = []
        seen: set[str] = set()

        for link in soup.select('a[href*="/podcast/"][href*="?i="]'):
            href = link.get("href")
            if not isinstance(href, str):
                continue
            parsed = urlparse(href)
            episode_id = parse_qs(parsed.query).get("i", [None])[0]
            show_match = re.search(r"/id(\d+)(?:\?|$)", parsed.path)
            if not episode_id or not show_match or episode_id in seen:
                continue

            heading = link.find(["h2", "h3", "h4"])
            episode_title = (
                heading.get_text(" ", strip=True)
                if heading is not None
                else link.get_text(" ", strip=True)
            )
            if not episode_title:
                continue
            show_title = cls._find_show_title(link)
            if not show_title:
                # This fallback still gives us a stable show key. The normal
                # enrichment task will replace the title using Apple lookup.
                show_title = episode_title

            seen.add(episode_id)
            entries.append(
                NormalizedChartEntry(
                    rank=len(entries) + 1,
                    title=show_title,
                    chart_type="episode",
                    apple_id=show_match.group(1),
                    episode_title=episode_title,
                    episode_external_id=episode_id,
                    podcast_url=f"{parsed.scheme}://{parsed.netloc}{parsed.path}",
                    categories=[category] if category else [],
                )
            )
        return entries

    @staticmethod
    def _find_show_title(link: Tag) -> str | None:
        for parent in link.parents:
            if not isinstance(parent, Tag):
                continue
            show_link = parent.select_one('a[href*="/podcast/"]:not([href*="?i="])')
            if show_link is not None:
                title = show_link.get_text(" ", strip=True)
                if title:
                    return title
            if parent.name in {"body", "html"}:
                break
        return None
