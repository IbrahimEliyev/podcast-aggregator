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
