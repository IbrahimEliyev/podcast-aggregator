from dataclasses import dataclass, field


@dataclass(frozen=True)
class NormalizedChartEntry:
    rank: int
    title: str
    external_id: str | None = None
    podcast_url: str | None = None
    image_url: str | None = None
    publisher: str | None = None
    description: str | None = None
    categories: list[str] = field(default_factory=list)
    episode_title: str | None = None
    episode_external_id: str | None = None
