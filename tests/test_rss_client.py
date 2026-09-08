import feedparser

from app.clients.rss_client import RSSClient


def test_parse_rss_episode() -> None:
    rss = b"""<?xml version="1.0"?>
    <rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
      <channel><title>Example</title>
        <item>
          <guid>episode-1</guid>
          <title>First episode</title>
          <description>Show notes</description>
          <pubDate>Tue, 01 Jan 2025 12:00:00 GMT</pubDate>
          <enclosure url="https://audio.test/episode.mp3" type="audio/mpeg" />
          <itunes:duration>01:02:03</itunes:duration>
        </item>
      </channel>
    </rss>"""

    feed = feedparser.parse(rss)
    entry = feed.entries[0]

    assert entry.guid == "episode-1"
    assert RSSClient._duration_seconds(entry) == 3723
    assert RSSClient._audio_url(entry) == "https://audio.test/episode.mp3"


def test_clean_text_repairs_common_utf8_mojibake() -> None:
    broken = "He said: â\x80\x9cHelloâ\x80\x9d"

    assert RSSClient._clean_text(broken) == "He said: “Hello”"
