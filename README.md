# Podcast Aggregator

Initial project scaffold for the podcast chart aggregation platform.

Dependencies are defined in `pyproject.toml` and managed with [uv](https://docs.astral.sh/uv/).

Database migrations are managed with Alembic:

```bash
alembic revision --autogenerate -m "create initial database models"
alembic upgrade head
```

## Start the services

Copy `.env.example` to `.env`, then run:

```bash
docker compose -f docker-compose.yaml up --build
```

The API health endpoint is available at `http://localhost:8000/health`.

## Chart history partitioning

`chart_snapshots` is partitioned by `snapshot_date` using monthly PostgreSQL
range partitions. Chart history grows on every collection run, so date
partitioning lets PostgreSQL prune unrelated historical partitions when the
API requests a particular day and keeps each partition's indexes smaller.

The application continues to query `chart_snapshots`; PostgreSQL routes each
insert to the correct monthly partition. The model uses `(id, snapshot_date)`
as its composite primary key because PostgreSQL requires a partition key to be
included in primary and unique constraints on a partitioned table. The chart
ranking uniqueness rule also includes `snapshot_date`, so repeated daily
ingestion remains idempotent.

The partition migration preserves existing rows and creates a default safety
partition for dates without a pre-created monthly partition. New monthly
partitions are maintained automatically by the daily
`maintain_chart_snapshot_partitions` Celery task. It creates the current month
and the next two months without changing API or repository code. The default
partition remains a safety net if a future partition is temporarily missing.

Daily chart collection is configured through environment variables. The
overall chart is always collected, and each category in `CHART_CATEGORIES` is
collected separately for every supported country:

```env
CHART_COUNTRIES=US,GB,CA,AU,DE,AZ,TR
CHART_SPOTIFY_COUNTRIES=US,GB,CA,AU,DE
CHART_CATEGORIES=Comedy,News,Sports
```

Spotify and Podchaser receive the category filter. Apple collection remains
country-wide because its public chart page does not expose a stable category
URL.
