from __future__ import annotations

from datetime import date
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ChartSnapshot


class ChartRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_snapshot(self, **values: object) -> ChartSnapshot:
        snapshot = ChartSnapshot(**values)
        self.session.add(snapshot)
        self.session.flush()
        return snapshot

    def list_chart(self, *, source: str, country: str, snapshot_date: date, category_id: uuid.UUID | None = None, chart_type: str = "podcast", limit: int = 100) -> list[ChartSnapshot]:
        statement = (
            select(ChartSnapshot)
            .where(
                ChartSnapshot.source == source,
                ChartSnapshot.country == country,
                ChartSnapshot.snapshot_date == snapshot_date,
                ChartSnapshot.chart_type == chart_type,
                ChartSnapshot.category_id == category_id,
            )
            .order_by(ChartSnapshot.rank)
            .limit(limit)
        )
        return list(self.session.scalars(statement))
