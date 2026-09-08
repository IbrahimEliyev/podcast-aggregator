from fastapi import FastAPI

from app.api.v1.charts import router as charts_router
from app.api.v1.podcasts import router as podcasts_router

app = FastAPI(title="Podcast Aggregator API", version="0.1.0")
app.include_router(charts_router, prefix="/api/v1")
app.include_router(podcasts_router, prefix="/api/v1")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
