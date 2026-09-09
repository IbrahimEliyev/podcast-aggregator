from datetime import date as Date
from typing import Literal
import uuid

from pydantic import BaseModel, Field


ChartSource = Literal["spotify", "podchaser", "apple"]
ChartType = Literal["podcast", "episode"]


class ChartQuery(BaseModel):
    country: str = Field(min_length=2, max_length=2, pattern="^[A-Za-z]{2}$")
    category: str | None = Field(default=None, min_length=1, max_length=255)
    date: Date | None = None
    source: ChartSource
    chart_type: ChartType = "podcast"
    limit: int = Field(default=100, ge=1, le=100)


class ChartItem(BaseModel):
    rank: int
    podcast_id: uuid.UUID
    episode_id: uuid.UUID | None = None


class ChartResponse(BaseModel):
    source: ChartSource
    country: str
    category: str | None
    date: Date
    chart_type: ChartType
    items: list[ChartItem]
