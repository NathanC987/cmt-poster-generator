import time
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config.settings import settings
from app.models.request_models import PosterGenerationRequest, LandmarkRequest, TextProcessingRequest
from app.models.response_models import (
    PosterGenerationResponse, LandmarkResponse, TextProcessingResponse,
    HealthResponse, ErrorResponse
)
from app.services.service_factory import (
    initialize_services, cleanup_services, get_services_status,
    get_rate_limiter, get_image_generator, get_text_processor
)
from app.services.poster_composer import PosterComposer

# Global variables for uptime tracking
start_time = time.time()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    try:
        await initialize_services()
        print("Services initialized successfully")
    except Exception as e:
        print(f"Failed to initialize services: {e}")
    
    yield
    
    # Shutdown
    try:
        await cleanup_services()
        print("Services cleaned up successfully")
    except Exception as e:
        print(f"Failed to cleanup services: {e}")

app = FastAPI(
    title=settings.API_TITLE,
    description="AI-powered poster generation API for CMT Association events",
    version=settings.API_VERSION,
    lifespan=lifespan
)

# Configure CORS for Power Automate
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting dependency
async def check_rate_limit(request: Request):
    """Rate limiting middleware"""
    rate_limiter = get_rate_limiter()
    client_ip = request.client.host
    
    if not await rate_limiter.check_rate_limit(
        key=f"api:{client_ip}",
        limit=settings.RATE_LIMIT_REQUESTS,
        window=settings.RATE_LIMIT_WINDOW
    ):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    # Increment counter
    await rate_limiter.increment_counter(
        key=f"api:{client_ip}",
        window=settings.RATE_LIMIT_WINDOW
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error_code="INTERNAL_ERROR",
            message=str(exc),
            timestamp=datetime.now()
        ).dict()
    )

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "CMT Poster Generator API",
        "version": settings.API_VERSION,
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "generate_posters": "/generate-posters",
            "landmarks": "/landmarks",
            "process_text": "/process-text"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint with service status"""
    current_time = datetime.now()
    uptime = time.time() - start_time
    
    # Get status of all services
    dependencies = await get_services_status()
    
    # Determine overall health
    all_healthy = all(
        dep.get("status") == "healthy" 
        for dep in dependencies.values()
    )
    
    return HealthResponse(
        status="healthy" if all_healthy else "degraded",
        timestamp=current_time,
        version=settings.API_VERSION,
        uptime=uptime,
        dependencies=dependencies
    )

@app.post("/generate-posters", response_model=PosterGenerationResponse, dependencies=[Depends(check_rate_limit)])
async def generate_posters(request: PosterGenerationRequest):
    """Main poster generation endpoint for Power Automate integration"""
    start_time_req = time.time()
    errors = []
    
    try:
        # Initialize poster composer
        composer = PosterComposer()
        
        # Generate posters
        posters = await composer.generate_posters(request)
        
        generation_time = time.time() - start_time_req
        event_id = composer._generate_event_id(request.event_details)
        
        # Check if landmark was cached
        cache_key = composer.storage.generate_cache_key(
            request.event_details.city,
            request.event_details.country
        )
        cached_landmark = await composer.storage.file_exists(cache_key)
        
        return PosterGenerationResponse(
            success=True,
            message=f"Successfully generated {len(posters)} posters",
            event_id=event_id,
            posters=posters,
            generation_time=generation_time,
            cached_landmark=cached_landmark,
            errors=errors
        )
        
    except Exception as e:
        generation_time = time.time() - start_time_req
        error_msg = str(e)
        errors.append(error_msg)
        
        return PosterGenerationResponse(
            success=False,
            message=f"Failed to generate posters: {error_msg}",
            event_id="",
            posters=[],
            generation_time=generation_time,
            cached_landmark=False,
            errors=errors
        )

@app.post("/landmarks", response_model=LandmarkResponse, dependencies=[Depends(check_rate_limit)])
async def generate_landmark(request: LandmarkRequest):
    """Generate or retrieve landmark image"""
    start_time_req = time.time()
    
    try:
        image_generator = get_image_generator()
        
        # Generate landmark image
        landmark_url = await image_generator.generate_landmark_image(
            request.city,
            request.country,
            request.style
        )
        
        generation_time = time.time() - start_time_req
        
        return LandmarkResponse(
            success=True,
            landmark_name=f"Famous landmark in {request.city}",
            city=request.city,
            country=request.country,
            image_url=landmark_url,
            cached=False,  # Direct generation
            generation_time=generation_time
        )
        
    except Exception as e:
        generation_time = time.time() - start_time_req
        
        return LandmarkResponse(
            success=False,
            landmark_name="",
            city=request.city,
            country=request.country,
            image_url="",
            cached=False,
            generation_time=generation_time
        )

@app.post("/process-text", response_model=TextProcessingResponse, dependencies=[Depends(check_rate_limit)])
async def process_text(request: TextProcessingRequest):
    """Process and summarize text"""
    start_time_req = time.time()
    
    try:
        text_processor = get_text_processor()
        
        # Process text
        processed_text = await text_processor.summarize_text(
            request.original_text,
            request.target_length,
            request.style
        )
        
        processing_time = time.time() - start_time_req
        
        return TextProcessingResponse(
            success=True,
            processed_text=processed_text,
            original_length=len(request.original_text),
            processed_length=len(processed_text),
            processing_time=processing_time
        )
        
    except Exception as e:
        processing_time = time.time() - start_time_req
        
        return TextProcessingResponse(
            success=False,
            processed_text="",
            original_length=len(request.original_text),
            processed_length=0,
            processing_time=processing_time
        )

@app.get("/services/status")
async def get_service_status():
    """Get detailed status of all services"""
    return await get_services_status()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
