from app.clients.podchaser_client import PodchaserClient


def test_parse_podchaser_embedded_chart() -> None:
    html = """
    <html><body>
      <script type="application/json">
        {"charts": [{
          "rank": 1,
          "podcastName": "Example Podcast",
          "podchaserId": "pc-123",
          "publisher": "Example Publisher",
          "url": "/podcasts/example-podcast/pc-123"
        }]}
      </script>
    </body></html>
    """

    entries = PodchaserClient.parse_chart(html, country="US", category="Comedy")

    assert len(entries) == 1
    assert entries[0].rank == 1
    assert entries[0].title == "Example Podcast"
    assert entries[0].external_id == "pc-123"
    assert entries[0].categories == ["Comedy"]
