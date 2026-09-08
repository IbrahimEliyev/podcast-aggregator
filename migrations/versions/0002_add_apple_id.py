"""Add Apple Podcasts provider identity.

Revision ID: 0002_add_apple_id
Revises: 0001_initial_schema
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0002_add_apple_id"
down_revision: str | None = "0001_initial_schema"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("podcasts", sa.Column("apple_id", sa.String(length=255), nullable=True))
    op.create_unique_constraint("uq_podcasts_apple_id", "podcasts", ["apple_id"])


def downgrade() -> None:
    op.drop_constraint("uq_podcasts_apple_id", "podcasts", type_="unique")
    op.drop_column("podcasts", "apple_id")
