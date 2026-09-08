from datetime import datetime
import uuid

from pydantic import BaseModel, ConfigDict


class EpisodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    guid: str
    title: str
    description: str | None = None
    audio_url: str | None = None
    published_at: datetime | None = None
    duration_seconds: int | None = None
