from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.chart import ChartResponse
from app.services.chart_service import ChartService


router = APIRouter(prefix="/charts", tags=["charts"])


@router.get("", response_model=ChartResponse)
def get_chart(
    country: str = Query(min_length=2, max_length=2),
    category: str | None = Query(default=None, min_length=1, max_length=255),
    snapshot_date: date | None = Query(default=None, alias="date"),
    source: str = Query(pattern="^(spotify|podchaser)$"),
    chart_type: str = Query(default="podcast", pattern="^(podcast|episode)$"),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
) -> ChartResponse:
    selected_date, snapshots = ChartService(db).get_chart(
        source=source,
        country=country,
        category_name=category,
        snapshot_date=snapshot_date,
        chart_type=chart_type,
        limit=limit,
    )
    if selected_date is None:
        raise HTTPException(status_code=404, detail="No chart data found for the requested filters")

    return ChartResponse(
        source=source,
        country=country.upper(),
        category=category,
        date=selected_date,
        chart_type=chart_type,
        items=[
            {
                "rank": snapshot.rank,
                "podcast_id": snapshot.podcast_id,
                "episode_id": snapshot.episode_id,
            }
            for snapshot in snapshots
        ],
    )
