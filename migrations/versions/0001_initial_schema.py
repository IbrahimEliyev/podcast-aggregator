"""Create the initial podcast aggregation schema.

Revision ID: 0001_initial_schema
Revises:
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    uuid = postgresql.UUID(as_uuid=True)

    op.create_table(
        "podcasts",
        sa.Column("id", uuid, nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("author", sa.String(length=500), nullable=True),
        sa.Column("publisher", sa.String(length=500), nullable=True),
        sa.Column("cover_image_url", sa.Text(), nullable=True),
        sa.Column("rss_url", sa.Text(), nullable=True),
        sa.Column("language", sa.String(length=20), nullable=True),
        sa.Column("rating", sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column("rating_count", sa.Integer(), nullable=True),
        sa.Column("episode_frequency", sa.String(length=100), nullable=True),
        sa.Column("spotify_id", sa.String(length=255), nullable=True),
        sa.Column("podchaser_id", sa.String(length=255), nullable=True),
        sa.Column("podcast_index_id", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("rss_url"),
        sa.UniqueConstraint("spotify_id"),
        sa.UniqueConstraint("podchaser_id"),
        sa.UniqueConstraint("podcast_index_id"),
    )

    op.create_table(
        "categories",
        sa.Column("id", uuid, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "episodes",
        sa.Column("id", uuid, nullable=False),
        sa.Column("podcast_id", uuid, nullable=False),
        sa.Column("guid", sa.String(length=1000), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("audio_url", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["podcast_id"], ["podcasts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("podcast_id", "guid", name="uq_episode_podcast_guid"),
    )
    op.create_index("ix_episodes_podcast_id", "episodes", ["podcast_id"])
    op.create_index("ix_episodes_published_at", "episodes", ["published_at"])
    op.create_index("ix_episodes_podcast_published_at", "episodes", ["podcast_id", "published_at", "id"])

    op.create_table(
        "podcast_categories",
        sa.Column("podcast_id", uuid, nullable=False),
        sa.Column("category_id", uuid, nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["podcast_id"], ["podcasts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("podcast_id", "category_id"),
        sa.UniqueConstraint("podcast_id", "category_id", name="uq_podcast_category"),
    )

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
        sa.UniqueConstraint("source", "country", "category_id", "snapshot_date", "chart_type", "rank", name="uq_chart_snapshot_rank"),
    )
    op.create_index("ix_chart_snapshots_category_id", "chart_snapshots", ["category_id"])
    op.create_index("ix_chart_snapshots_podcast_id", "chart_snapshots", ["podcast_id"])
    op.create_index("ix_chart_snapshots_episode_id", "chart_snapshots", ["episode_id"])
    op.create_index("ix_chart_snapshots_lookup", "chart_snapshots", ["source", "country", "category_id", "snapshot_date", "rank"])


def downgrade() -> None:
    op.drop_table("chart_snapshots")
    op.drop_table("podcast_categories")
    op.drop_index("ix_episodes_podcast_published_at", table_name="episodes")
    op.drop_index("ix_episodes_published_at", table_name="episodes")
    op.drop_index("ix_episodes_podcast_id", table_name="episodes")
    op.drop_table("episodes")
    op.drop_table("categories")
    op.drop_table("podcasts")
