import logging
from fastapi import APIRouter, Request, HTTPException
from app.poster.generator import PosterGenerator
from app.services.wordpress_service import WordPressService
from app.services.openai_service import OpenAIService
from app.services.image_service import ImageService
from app.core.rate_limiter import rate_limiter
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/")
@rate_limiter
async def generate_poster(request: Request):
    payload = await request.json()
    logger.info(f"Received poster generation request: {payload}")
    try:
        generator = PosterGenerator(
            openai_service=OpenAIService(),
            wordpress_service=WordPressService(),
            image_service=ImageService()
        )
        poster_urls = await generator.generate(payload)
        logger.info(f"Poster(s) generated and uploaded: {poster_urls}")
        return {"poster_urls": poster_urls}
    except Exception as e:
        logger.error(f"Poster generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
