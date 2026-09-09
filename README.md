# Podcast Aggregator

Podcast Aggregator is a Dockerized Python backend for collecting podcast
rankings, enriching podcast metadata, synchronizing RSS episodes, preserving
chart history, and exposing the data through REST APIs.

## Technology

- Python 3.12
- FastAPI and Uvicorn
- PostgreSQL 16
- SQLAlchemy and Alembic
- Celery and Redis
- `httpx`, BeautifulSoup, and `feedparser`
- `uv` with `pyproject.toml`

## Architecture

```text
Spotify / Apple / Podchaser / RSS
              |
              v
       Provider clients
              |
              v
   Normalized ingestion schemas
              |
              v
       Celery background tasks
              |
              v
   Services -> Repositories
              |
              v
          PostgreSQL
              |
              v
        FastAPI REST API
```

Docker Compose runs five components:

- `api`: FastAPI application and Swagger UI.
- `worker`: Celery background task worker.
- `beat`: Celery periodic-task scheduler.
- `db`: PostgreSQL database.
- `redis`: Celery broker and result backend.

The code is divided into these layers:

- `app/clients`: external chart, metadata, and RSS clients.
- `app/schemas`: API and provider-independent data structures.
- `app/services`: business logic and orchestration.
- `app/repositories`: database queries and persistence operations.
- `app/db/models`: SQLAlchemy models and relationships.
- `app/api/v1`: HTTP route handlers.
- `app/workers`: Celery tasks and schedules.

## Project structure

```text
app/
├── api/v1/                 # FastAPI routes
├── clients/                # External providers and RSS
├── db/models/              # SQLAlchemy models
├── db/partitioning.py      # Partition maintenance
├── repositories/           # Database access layer
├── schemas/                # API and normalized schemas
├── services/               # Business logic
└── workers/                # Celery application and tasks

migrations/versions/       # Alembic migrations
tests/                      # Automated tests
docker-compose.yaml         # Docker services
pyproject.toml              # Project metadata and dependencies
```

## Collection pipeline

### Spotify

`SpotifyClient` fetches podcast charts for a country and optional category. It
normalizes provider data into `NormalizedChartEntry` objects.

`collect_spotify_chart` then creates or updates podcasts, assigns categories,
saves the rank in `chart_snapshots`, and queues enrichment after the database
transaction commits.

Spotify currently provides podcast rankings. It is not used as the episode
ranking source.

### Apple

`AppleChartsClient` reads Apple’s public chart pages:

- Top Shows for podcast rankings.
- Trending Episodes for episode rankings.

The chart type determines stored identifiers:

```text
Podcast chart:  podcast_id populated, episode_id null
Episode chart:  podcast_id populated, episode_id populated
```

Apple supports country markets. Its public pages do not expose a stable
category URL, so Apple collection is currently country-wide.

### Podchaser

The Podchaser client and task are preserved for later activation. The public
charts page returns `403 Forbidden`, and official chart API access requires a
plan with chart permissions.

Podchaser is disabled by default:

```env
PODCHASER_ENABLED=false
```

When access is available, the HTML client can be replaced with an authenticated
API request without changing the normalization or database pipeline.

## Normalization and enrichment

Provider clients do not write provider-specific dictionaries directly to the
database. They produce a common schema:

```python
NormalizedChartEntry(
    rank=1,
    title="Example Podcast",
    chart_type="podcast",
    external_id="provider-id",
    apple_id=None,
    episode_title=None,
    episode_external_id=None,
)
```

`ChartIngestionService` maps provider identities, assigns categories, creates
episode records for episode charts, and writes historical chart snapshots.

The `enrich_podcast` task uses Apple’s public lookup API to populate title,
description, author, publisher, artwork, Apple ID, RSS URL, ratings, and
categories. It is queued only after chart ingestion commits.

```text
Chart collection
    -> podcast identity saved
    -> Apple metadata lookup
    -> podcast metadata updated
    -> RSS synchronization queued
```

## Episode synchronization

`sync_podcast_episodes` downloads and parses RSS feeds using `feedparser`.
Episodes store their GUID, title, description, audio URL, publication date, and
duration.

Episodes use `podcast_id + guid` as their unique identity. Repeated RSS syncs
therefore update existing episodes instead of inserting duplicates.

## Database model

```text
Podcast 1 ──────── * Episode
Podcast * ──────── * Category
Podcast 1 ──────── * ChartSnapshot
Episode 1 ──────── * ChartSnapshot
```

Main tables:

- `podcasts`: common metadata and provider identifiers.
- `episodes`: RSS episodes belonging to podcasts.
- `categories`: normalized category names.
- `podcast_categories`: podcast/category many-to-many relationship.
- `chart_snapshots`: daily historical rankings.

## Chart history partitioning

`chart_snapshots` is partitioned by `snapshot_date` with monthly PostgreSQL
range partitions. This allows PostgreSQL to prune unrelated history and keeps
partition indexes smaller as daily data grows.

```text
chart_snapshots
├── chart_snapshots_2026_09
├── chart_snapshots_2026_10
├── chart_snapshots_2026_11
└── chart_snapshots_default
```

The application still queries `chart_snapshots`; PostgreSQL routes rows to the
correct partition. The SQLAlchemy model uses `(id, snapshot_date)` as its
composite primary key because PostgreSQL requires the partition key in primary
and unique constraints.

Ranking uniqueness is based on:

```text
source + country + category_id + snapshot_date + chart_type + rank
```

This allows the same rank on different days and prevents duplicate ranks in a
single chart snapshot. Migration `0003_partition_chart_snapshots` preserves
existing rows and creates a default safety partition.

The daily `maintain_chart_snapshot_partitions` task creates the current month
and the next two months automatically.

## Country and category configuration

```env
CHART_COUNTRIES=US,GB,CA,AU,DE,AZ,TR
CHART_SPOTIFY_COUNTRIES=US,GB,CA,AU,DE
CHART_CATEGORIES=Comedy,News,Sports
```

The daily dispatcher collects the overall chart and every configured category.
Spotify receives country and category filters. Podchaser receives the same
filters when enabled. Apple receives country filters but currently does not
receive category filters.

Provider country support is independent. Spotify’s public endpoint does not
currently provide the configured Azerbaijan and Turkey markets, while Apple
does.

## REST API

Swagger UI is available at:

```text
http://127.0.0.1:8000/docs
```

### Health

```http
GET /health
```

### Chart API

```http
GET /api/v1/charts
```

Parameters are `source`, `country`, optional `category`, optional `date`,
`chart_type`, and `limit`.

Examples:

```text
/api/v1/charts?source=spotify&country=US&chart_type=podcast
/api/v1/charts?source=spotify&country=US&category=Comedy&chart_type=podcast
/api/v1/charts?source=apple&country=TR&chart_type=podcast
/api/v1/charts?source=apple&country=AZ&chart_type=episode
```

Podcast chart results contain `podcast_id` and null `episode_id`. Episode chart
results contain both the parent `podcast_id` and ranked `episode_id`.

### Podcast APIs

```http
GET /api/v1/podcasts
GET /api/v1/podcasts/{podcast_id}
```

The list endpoint supports pagination, search, and category filtering. The
detail endpoint returns metadata and paginated episodes.

## Celery tasks

Main tasks include:

- `collect_spotify_chart`
- `collect_apple_podcast_chart`
- `collect_apple_episode_chart`
- `collect_podchaser_chart`
- `collect_configured_chart_countries`
- `maintain_chart_snapshot_partitions`
- `enrich_podcast`
- `sync_podcast_episodes`
- `sync_all_podcast_episodes`

The daily flow is:

```text
Celery Beat
    -> country/category dispatcher
    -> chart collection
    -> chart snapshots
    -> metadata enrichment
    -> RSS episode synchronization
```

## Running the application

Copy the example environment file and start Docker Compose:

```powershell
Copy-Item .env.example .env
docker compose up --build -d
```

Check services and endpoints:

```powershell
docker compose ps
docker compose exec api alembic upgrade head
```

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/docs
```

Run tests:

```powershell
uv run pytest -q
```

Run one chart collection manually:

```powershell
docker compose exec worker python -c "from app.workers.tasks import collect_spotify_chart; print(collect_spotify_chart.run('US', 'Comedy'))"
```

## Migrations

Alembic migrations are stored in `migrations/versions`:

1. `0001_initial_schema`: creates the core tables.
2. `0002_add_apple_id`: adds Apple provider identity.
3. `0003_partition_chart_snapshots`: partitions chart history and preserves existing rows.

Create and apply migrations with:

```bash
alembic revision --autogenerate -m "describe the change"
```

Apply the migrations inside the running API container:

```powershell
docker compose exec api alembic upgrade head
```
