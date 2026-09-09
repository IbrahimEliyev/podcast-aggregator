from app.clients.apple_podcasts_client import ApplePodcastsClient


def test_normalize_apple_podcast_result() -> None:
    metadata = ApplePodcastsClient._normalize(
        {
            "collectionId": 123,
            "collectionName": "Example Podcast",
            "artistName": "Example Publisher",
            "artworkUrl600": "https://img.test/podcast.jpg",
            "feedUrl": "https://feeds.test/podcast.xml",
            "language": "English",
            "genres": ["Podcasts", "Technology"],
            "averageUserRating": 4.5,
            "userRatingCount": 100,
        }
    )

    assert metadata.apple_id == "123"
    assert metadata.title == "Example Podcast"
    assert metadata.rss_url == "https://feeds.test/podcast.xml"
    assert metadata.language == "English"
    assert metadata.categories == ["Technology"]
