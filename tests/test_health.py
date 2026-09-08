from app.main import app


def test_project_test_placeholder() -> None:
    assert True


def test_chart_endpoint_is_registered() -> None:
    assert "/api/v1/charts" in app.openapi()["paths"]


def test_podcast_endpoints_are_registered() -> None:
    paths = app.openapi()["paths"]
    assert "/api/v1/podcasts" in paths
    assert "/api/v1/podcasts/{podcast_id}" in paths
