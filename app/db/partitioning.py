from __future__ import annotations

from datetime import date

from sqlalchemy import text
from sqlalchemy.orm import Session


def month_start(value: date) -> date:
    return value.replace(day=1)


def add_month(value: date, months: int = 1) -> date:
    month = value.month - 1 + months
    return date(value.year + month // 12, month % 12 + 1, 1)


def monthly_partition_name(value: date) -> str:
    return f"chart_snapshots_{value:%Y_%m}"


def ensure_chart_snapshot_partitions(
    session: Session, *, months_ahead: int = 2
) -> list[str]:
    """Create the current and upcoming monthly chart partitions if missing."""
    current = month_start(date.today())
    created_or_available: list[str] = []
    for offset in range(months_ahead + 1):
        start = add_month(current, offset)
        end = add_month(start)
        name = monthly_partition_name(start)
        session.execute(
            text(
                f"CREATE TABLE IF NOT EXISTS {name} PARTITION OF chart_snapshots "
                f"FOR VALUES FROM ('{start.isoformat()}') TO ('{end.isoformat()}')"
            )
        )
        created_or_available.append(name)
    return created_or_available
