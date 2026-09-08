FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

COPY --from=ghcr.io/astral-sh/uv:0.4.29 /uv /uvx /bin/

COPY pyproject.toml uv.lock ./
COPY app ./app
RUN uv sync --locked --no-dev --no-cache

COPY . .
