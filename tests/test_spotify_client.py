from app.clients.spotify_client import SpotifyClient


def test_parse_chart_html_cards() -> None:
    html = """
    <html><body>
      <a href="/show/spotify-show-1"><img src="https://img.test/one.jpg" />The First Podcast</a>
      <a href="/show/spotify-show-2"><img src="https://img.test/two.jpg" />The Second Podcast</a>
    </body></html>
    """

    entries = SpotifyClient.parse_chart(html, country="us", category="Comedy")

    assert len(entries) == 2
    assert entries[0].rank == 1
    assert entries[0].title == "The First Podcast"
    assert entries[0].podcast_url == "https://podcastcharts.byspotify.com/show/spotify-show-1"
    assert entries[0].categories == ["Comedy"]


def test_parse_chart_json_payload() -> None:
    html = """
    <script type="application/json">
      [{"rank": 1, "title": "JSON Podcast", "spotifyId": "show-1", "publisher": "Publisher"}]
    </script>
    """

    entries = SpotifyClient.parse_chart(html, country="us")

    assert entries[0].external_id == "show-1"
    assert entries[0].publisher == "Publisher"


def test_parse_spotify_api_chart() -> None:
    payload = [
        {
            "showUri": "spotify:show:show-1",
            "showName": "Spotify Podcast",
            "showPublisher": "Spotify Publisher",
            "showImageUrl": "https://img.test/show.jpg",
            "showDescription": "A podcast.",
        }
    ]

    entries = SpotifyClient.parse_api_chart(payload, category="Comedy")

    assert entries[0].rank == 1
    assert entries[0].external_id == "show-1"
    assert entries[0].podcast_url == "https://open.spotify.com/show/show-1"


def test_parse_spotify_episode_chart_entry() -> None:
    payload = [
        {
            "showUri": "spotify:show:show-1",
            "showName": "Spotify Podcast",
            "episodeUri": "spotify:episode:episode-1",
            "episodeName": "Episode One",
        }
    ]

    entries = SpotifyClient.parse_api_chart(payload)

    assert entries[0].chart_type == "episode"
    assert entries[0].episode_external_id == "episode-1"
    assert entries[0].episode_title == "Episode One"
