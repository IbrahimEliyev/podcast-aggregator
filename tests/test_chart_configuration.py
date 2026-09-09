from app.workers.tasks import configured_chart_categories


def test_configured_chart_categories_include_overall_chart(monkeypatch) -> None:
    monkeypatch.setenv("CHART_CATEGORIES", "Comedy, News, Comedy")

    assert configured_chart_categories() == [None, "Comedy", "News"]
