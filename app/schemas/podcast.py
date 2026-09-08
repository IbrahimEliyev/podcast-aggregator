from datetime import datetime
from decimal import Decimal
import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.episode import EpisodeResponse


class PodcastListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    author: str | None = None
    publisher: str | None = None
    cover_image_url: str | None = None
    rating: Decimal | None = None


class PodcastListResponse(BaseModel):
    items: list[PodcastListItem]
    page: int
    page_size: int
    total: int


class PodcastDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str | None = None
    author: str | None = None
    publisher: str | None = None
    cover_image_url: str | None = None
    rss_url: str | None = None
    language: str | None = None
    rating: Decimal | None = None
    rating_count: int | None = None
    episode_frequency: str | None = None
    categories: list[str] = Field(default_factory=list)
    episodes: list[EpisodeResponse]
    episodes_page: int
    episodes_page_size: int
    episodes_total: int
