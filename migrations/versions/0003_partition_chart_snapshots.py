"""Partition chart snapshots by snapshot date.

Revision ID: 0003_partition_chart_snapshots
Revises: 0002_add_apple_id
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0003_partition_chart_snapshots"
down_revision: str | None = "0002_add_apple_id"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def _month_start(value: date) -> date:
    return value.replace(day=1)


def _add_month(value: date, months: int = 1) -> date:
    month = value.month - 1 + months
    return date(value.year + month // 12, month % 12 + 1, 1)


def _create_partition(name: str, start: date, end: date) -> None:
    op.execute(
        sa.text(
            f"CREATE TABLE {name} PARTITION OF chart_snapshots "
            f"FOR VALUES FROM ('{start.isoformat()}') TO ('{end.isoformat()}')"
        )
    )


def upgrade() -> None:
    bind = op.get_bind()
    bounds = bind.execute(
        sa.text("SELECT min(snapshot_date), max(snapshot_date) FROM chart_snapshots")
    ).one()
    today_month = _month_start(date.today())
    first_month = min(today_month, _month_start(bounds[0])) if bounds[0] else today_month
    last_existing_month = _month_start(bounds[1]) if bounds[1] else today_month
    last_month = max(today_month, last_existing_month)

    op.rename_table("chart_snapshots", "chart_snapshots_legacy")
    op.execute(
        sa.text(
            "ALTER TABLE chart_snapshots_legacy "
            "DROP CONSTRAINT chart_snapshots_pkey, "
            "DROP CONSTRAINT uq_chart_snapshot_rank"
        )
    )
    for index_name in (
        "ix_chart_snapshots_category_id",
        "ix_chart_snapshots_podcast_id",
        "ix_chart_snapshots_episode_id",
        "ix_chart_snapshots_lookup",
    ):
        op.execute(sa.text(f"DROP INDEX IF EXISTS {index_name}"))

    uuid = postgresql.UUID(as_uuid=True)
    op.create_table(
        "chart_snapshots",
        sa.Column("id", uuid, nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("country", sa.String(length=2), nullable=False),
        sa.Column("category_id", uuid, nullable=True),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("chart_type", sa.String(length=20), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("podcast_id", uuid, nullable=False),
        sa.Column("episode_id", uuid, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["episode_id"], ["episodes.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["podcast_id"], ["podcasts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", "snapshot_date"),
        sa.UniqueConstraint(
            "source", "country", "category_id", "snapshot_date", "chart_type", "rank",
            name="uq_chart_snapshot_rank",
        ),
        postgresql_partition_by="RANGE (snapshot_date)",
    )

    current = first_month
    while current <= last_month:
        _create_partition(
            f"chart_snapshots_{current:%Y_%m}",
            current,
            _add_month(current),
        )
        current = _add_month(current)

    op.execute(sa.text("CREATE TABLE chart_snapshots_default PARTITION OF chart_snapshots DEFAULT"))
    op.create_index("ix_chart_snapshots_category_id", "chart_snapshots", ["category_id"])
    op.create_index("ix_chart_snapshots_podcast_id", "chart_snapshots", ["podcast_id"])
    op.create_index("ix_chart_snapshots_episode_id", "chart_snapshots", ["episode_id"])
    op.create_index(
        "ix_chart_snapshots_lookup",
        "chart_snapshots",
        ["source", "country", "category_id", "snapshot_date", "chart_type", "rank"],
    )

    op.execute(
        sa.text(
            "INSERT INTO chart_snapshots "
            "(id, source, country, category_id, snapshot_date, chart_type, rank, "
            "podcast_id, episode_id, created_at) "
            "SELECT id, source, country, category_id, snapshot_date, chart_type, rank, "
            "podcast_id, episode_id, created_at FROM chart_snapshots_legacy"
        )
    )
    op.drop_table("chart_snapshots_legacy")


def downgrade() -> None:
    op.rename_table("chart_snapshots", "chart_snapshots_partitioned")
    uuid = postgresql.UUID(as_uuid=True)
    op.create_table(
        "chart_snapshots",
        sa.Column("id", uuid, nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("country", sa.String(length=2), nullable=False),
        sa.Column("category_id", uuid, nullable=True),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("chart_type", sa.String(length=20), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("podcast_id", uuid, nullable=False),
        sa.Column("episode_id", uuid, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["episode_id"], ["episodes.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["podcast_id"], ["podcasts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source", "country", "category_id", "snapshot_date", "chart_type", "rank",
            name="uq_chart_snapshot_rank",
        ),
    )
    op.create_index("ix_chart_snapshots_category_id", "chart_snapshots", ["category_id"])
    op.create_index("ix_chart_snapshots_podcast_id", "chart_snapshots", ["podcast_id"])
    op.create_index("ix_chart_snapshots_episode_id", "chart_snapshots", ["episode_id"])
    op.create_index(
        "ix_chart_snapshots_lookup",
        "chart_snapshots",
        ["source", "country", "category_id", "snapshot_date", "chart_type", "rank"],
    )
    op.execute(
        sa.text(
            "INSERT INTO chart_snapshots "
            "SELECT id, source, country, category_id, snapshot_date, chart_type, rank, "
            "podcast_id, episode_id, created_at FROM chart_snapshots_partitioned"
        )
    )
    op.drop_table("chart_snapshots_partitioned")
