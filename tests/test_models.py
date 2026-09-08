from sqlalchemy import inspect

from app.db.base import Base
from app.db.models import ChartSnapshot, Episode


def test_expected_tables_are_registered() -> None:
    assert {"podcasts", "episodes", "chart_snapshots"}.issubset(Base.metadata.tables)


def test_episode_has_idempotency_constraint() -> None:
    constraints = {constraint.name for constraint in Episode.__table__.constraints}
    assert "uq_episode_podcast_guid" in constraints


def test_chart_has_lookup_index() -> None:
    indexes = {index.name for index in inspect(ChartSnapshot).mapper.local_table.indexes}
    assert "ix_chart_snapshots_lookup" in indexes
