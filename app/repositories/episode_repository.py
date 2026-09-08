from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Episode


class EpisodeRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_guid(self, podcast_id: uuid.UUID, guid: str) -> Episode | None:
        return self.session.scalar(select(Episode).where(Episode.podcast_id == podcast_id, Episode.guid == guid))

    def upsert(self, podcast_id: uuid.UUID, guid: str, **values: object) -> Episode:
        episode = self.get_by_guid(podcast_id, guid)
        if episode is None:
            episode = Episode(podcast_id=podcast_id, guid=guid, **values)
            self.session.add(episode)
        else:
            for field, value in values.items():
                setattr(episode, field, value)
        self.session.flush()
        return episode

    def list_for_podcast(self, podcast_id: uuid.UUID, *, limit: int = 20, offset: int = 0) -> list[Episode]:
        statement = (
            select(Episode)
            .where(Episode.podcast_id == podcast_id)
            .order_by(Episode.published_at.desc().nullslast(), Episode.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.session.scalars(statement))

    def count_for_podcast(self, podcast_id: uuid.UUID) -> int:
        return int(self.session.scalar(select(func.count(Episode.id)).where(Episode.podcast_id == podcast_id)) or 0)
