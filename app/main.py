import logging
from fastapi import FastAPI
from app.api.poster import router as poster_router
from app.core.config import settings

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.API_TITLE, version=settings.API_VERSION)

app.include_router(poster_router, prefix="/generate-posters", tags=["Poster Generation"], include_in_schema=True)

@app.on_event("startup")
async def startup_event():
    logger.info("CMT Poster Generator FastAPI app started.")

@app.get("/health")
def health_check():
    logger.info("Health check endpoint called.")
    return {"status": "ok"}
