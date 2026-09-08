from __future__ import annotations

from datetime import date
import uuid

from sqlalchemy.orm import Session

from app.db.models import ChartSnapshot
from app.repositories.chart_repository import ChartRepository


class ChartService:
    def __init__(self, session: Session) -> None:
        self.repository = ChartRepository(session)

    def record_snapshot(self, *, source: str, country: str, snapshot_date: date, rank: int, podcast_id: uuid.UUID, category_id: uuid.UUID | None = None, episode_id: uuid.UUID | None = None, chart_type: str = "podcast") -> ChartSnapshot:
        return self.repository.create_snapshot(
            source=source,
            country=country.upper(),
            category_id=category_id,
            snapshot_date=snapshot_date,
            chart_type=chart_type,
            rank=rank,
            podcast_id=podcast_id,
            episode_id=episode_id,
        )
