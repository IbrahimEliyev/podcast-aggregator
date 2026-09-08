import os

from celery import Celery


celery_app = Celery(
    "podcast_aggregator",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2"),
)

celery_app.conf.beat_schedule = {
    "collect-us-spotify-top-podcasts-daily": {
        "task": "app.workers.tasks.collect_spotify_chart",
        "schedule": 86400,
        "args": ("US", None),
    }
}
celery_app.autodiscover_tasks(["app.workers"])
