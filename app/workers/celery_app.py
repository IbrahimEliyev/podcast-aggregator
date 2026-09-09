import os

from celery import Celery


celery_app = Celery(
    "podcast_aggregator",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2"),
)

celery_app.conf.beat_schedule = {
    "collect-configured-chart-countries-daily": {
        "task": "app.workers.tasks.collect_configured_chart_countries",
        "schedule": 86400,
    },
    "sync-podcast-episodes-daily": {
        "task": "app.workers.tasks.sync_all_podcast_episodes",
        "schedule": 86400,
    },
}
celery_app.autodiscover_tasks(["app.workers"])
