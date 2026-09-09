from app.clients.apple_charts_client import AppleChartsClient


def test_parse_trending_episode_chart_preserves_rank_and_ids() -> None:
    html = """
    <main>
      <article>
        <a href="/us/podcast/the-show/id123">The Show</a>
        <a href="/us/podcast/the-show/id123?i=987"><h3>First episode</h3><p>description</p></a>
      </article>
      <article>
        <a href="/us/podcast/another-show/id456">Another Show</a>
        <a href="/us/podcast/another-show/id456?i=654"><h3>Second episode</h3></a>
      </article>
    </main>
    """

    entries = AppleChartsClient.parse_trending_episodes(html)

    assert [entry.rank for entry in entries] == [1, 2]
    assert entries[0].apple_id == "123"
    assert entries[0].episode_external_id == "987"
    assert entries[0].title == "The Show"
    assert entries[0].episode_title == "First episode"
    assert entries[1].apple_id == "456"


def test_parse_top_shows_preserves_rank_and_apple_ids() -> None:
    html = """
    <main>
      <a href="/us/podcast/example/id123">Example Podcast</a>
      <a href="/us/podcast/second/id456">Second Podcast</a>
      <a href="/us/podcast/example/id123">Duplicate link</a>
    </main>
    """

    entries = AppleChartsClient.parse_top_shows(html)

    assert [(entry.rank, entry.title, entry.apple_id) for entry in entries] == [
        (1, "Example Podcast", "123"),
        (2, "Second Podcast", "456"),
    ]
