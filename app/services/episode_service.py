from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.db.models import Episode
from app.repositories.episode_repository import EpisodeRepository


class EpisodeService:
    def __init__(self, session: Session) -> None:
        self.repository = EpisodeRepository(session)

    def upsert_episode(self, podcast_id: uuid.UUID, guid: str, values: dict[str, object]) -> Episode:
        return self.repository.upsert(podcast_id, guid, **values)
