from datetime import date

from app.db.partitioning import add_month, monthly_partition_name, month_start


def test_month_helpers() -> None:
    value = date(2026, 12, 19)

    assert month_start(value) == date(2026, 12, 1)
    assert add_month(month_start(value)) == date(2027, 1, 1)
    assert monthly_partition_name(value) == "chart_snapshots_2026_12"
