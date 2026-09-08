import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.podcast import PodcastDetailResponse, PodcastListResponse
from app.services.podcast_service import PodcastService


router = APIRouter(prefix="/podcasts", tags=["podcasts"])


@router.get("", response_model=PodcastListResponse)
def list_podcasts(
    search: str | None = Query(default=None, min_length=1, max_length=255),
    category: str | None = Query(default=None, min_length=1, max_length=255),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> PodcastListResponse:
    podcasts, total = PodcastService(db).list_podcasts(
        search=search,
        category_name=category,
        page=page,
        page_size=page_size,
    )
    return PodcastListResponse(
        items=podcasts,
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get("/{podcast_id}", response_model=PodcastDetailResponse)
def get_podcast(
    podcast_id: uuid.UUID,
    episodes_page: int = Query(default=1, ge=1),
    episodes_page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> PodcastDetailResponse:
    podcast, episodes, episodes_total = PodcastService(db).get_detail(
        podcast_id,
        episodes_page=episodes_page,
        episodes_page_size=episodes_page_size,
    )
    if podcast is None:
        raise HTTPException(status_code=404, detail="Podcast not found")

    return PodcastDetailResponse(
        id=podcast.id,
        title=podcast.title,
        description=podcast.description,
        author=podcast.author,
        publisher=podcast.publisher,
        cover_image_url=podcast.cover_image_url,
        rss_url=podcast.rss_url,
        language=podcast.language,
        rating=podcast.rating,
        rating_count=podcast.rating_count,
        episode_frequency=podcast.episode_frequency,
        categories=[link.category.name for link in podcast.categories],
        episodes=episodes,
        episodes_page=episodes_page,
        episodes_page_size=episodes_page_size,
        episodes_total=episodes_total,
    )
