from __future__ import annotations

from datetime import date
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Category, ChartSnapshot


class ChartRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_snapshot(self, **values: object) -> ChartSnapshot:
        snapshot = ChartSnapshot(**values)
        self.session.add(snapshot)
        self.session.flush()
        return snapshot

    def upsert_snapshot(self, **values: object) -> ChartSnapshot:
        statement = select(ChartSnapshot).where(
            ChartSnapshot.source == values["source"],
            ChartSnapshot.country == values["country"],
            ChartSnapshot.category_id == values["category_id"],
            ChartSnapshot.snapshot_date == values["snapshot_date"],
            ChartSnapshot.chart_type == values["chart_type"],
            ChartSnapshot.rank == values["rank"],
        )
        snapshot = self.session.scalar(statement)
        if snapshot is None:
            snapshot = ChartSnapshot(**values)
            self.session.add(snapshot)
        else:
            for field, value in values.items():
                setattr(snapshot, field, value)
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

    def latest_date(
        self, *, source: str, country: str, category_name: str | None, chart_type: str
    ) -> date | None:
        statement = select(func.max(ChartSnapshot.snapshot_date)).where(
            ChartSnapshot.source == source,
            ChartSnapshot.country == country,
            ChartSnapshot.chart_type == chart_type,
        )
        if category_name is None:
            statement = statement.where(ChartSnapshot.category_id.is_(None))
        else:
            statement = statement.join(Category, ChartSnapshot.category_id == Category.id).where(
                Category.name == category_name
            )
        return self.session.scalar(statement)

    def list_chart_by_category(
        self,
        *,
        source: str,
        country: str,
        snapshot_date: date,
        category_name: str | None,
        chart_type: str,
        limit: int,
    ) -> list[ChartSnapshot]:
        statement = (
            select(ChartSnapshot)
            .where(
                ChartSnapshot.source == source,
                ChartSnapshot.country == country,
                ChartSnapshot.snapshot_date == snapshot_date,
                ChartSnapshot.chart_type == chart_type,
            )
            .order_by(ChartSnapshot.rank)
            .limit(limit)
        )
        if category_name is None:
            statement = statement.where(ChartSnapshot.category_id.is_(None))
        else:
            statement = statement.join(Category, ChartSnapshot.category_id == Category.id).where(
                Category.name == category_name
            )
        return list(self.session.scalars(statement))
