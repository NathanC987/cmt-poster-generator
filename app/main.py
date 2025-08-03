import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.poster import router as poster_router
from app.core.config import settings

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("CMT Poster Generator FastAPI app started.")
    yield
    # Shutdown (if needed in future)
    logger.info("CMT Poster Generator FastAPI app shutting down.")

app = FastAPI(
    title=settings.API_TITLE, 
    version=settings.API_VERSION,
    lifespan=lifespan
)

app.include_router(poster_router, prefix="/generate-posters", tags=["Poster Generation"], include_in_schema=True)

@app.get("/health")
def health_check():
    logger.info("Health check endpoint called.")
    return {"status": "ok"}
