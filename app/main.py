import time
import json
import asyncio
from typing import List
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config.settings import settings
from app.models.request_models import PosterGenerationRequest, PowerAutomateRequest
from app.models.response_models import PosterGenerationResponse
from app.services.service_factory import (
    initialize_services, cleanup_services, get_services_status,
    get_rate_limiter, get_image_generator, get_text_processor
)
from app.services.poster_composer import PosterComposer

# Global variables for uptime tracking
start_time = time.time()

# Store last received payload for debugging
last_payload = {"timestamp": None, "data": None, "url": None}

def extract_city_country(venue: str, title: str) -> tuple:
    """Extract city and country from venue and title"""
    venue_lower = venue.lower()
    title_lower = title.lower()
    
    # City mappings based on common venue patterns
    city_mappings = {
        "kuala lumpur": ("Kuala Lumpur", "Malaysia"),
        "kl": ("Kuala Lumpur", "Malaysia"),
        "mumbai": ("Mumbai", "India"),
        "vaswani": ("Mumbai", "India"),  # WeWork Vaswani Chambers
        "bangalore": ("Bangalore", "India"),
        "bengaluru": ("Bangalore", "India"),
        "delhi": ("Delhi", "India"),
        "gurgaon": ("Gurgaon", "India"),
        "manila": ("Manila", "Philippines"),
        "metro manila": ("Manila", "Philippines"),
        "singapore": ("Singapore", "Singapore"),
        "bangkok": ("Bangkok", "Thailand"),
        "jakarta": ("Jakarta", "Indonesia"),
        "hong kong": ("Hong Kong", "Hong Kong"),
        "ho chi minh": ("Ho Chi Minh City", "Vietnam"),
        "saigon": ("Ho Chi Minh City", "Vietnam"),
        "hanoi": ("Hanoi", "Vietnam"),
        "taipei": ("Taipei", "Taiwan"),
        "seoul": ("Seoul", "South Korea"),
        "tokyo": ("Tokyo", "Japan"),
        "osaka": ("Osaka", "Japan"),
        "sydney": ("Sydney", "Australia"),
        "melbourne": ("Melbourne", "Australia"),
        "auckland": ("Auckland", "New Zealand"),
        "london": ("London", "UK"),
        "new york": ("New York", "USA"),
        "san francisco": ("San Francisco", "USA"),
        "chicago": ("Chicago", "USA"),
    }
    
    # Check venue first, then title
    for key, (city, country) in city_mappings.items():
        if key in venue_lower or key in title_lower:
            return city, country
    
    # Default fallback
    return "Manila", "Philippines"

def parse_speakers_from_text(speakers_text: str, community_leader: str) -> List:
    """Parse speakers from the Power Automate speakers text"""
    from app.models.request_models import SpeakerInfo
    import re
    
    speakers = []
    
    if not speakers_text:
        return speakers
    
    # Look for LinkedIn URLs to extract speaker info
    linkedin_pattern = r'https?://[^\s]*linkedin[^\s]*'
    linkedin_matches = re.findall(linkedin_pattern, speakers_text)
    
    # Add community leader first
    if community_leader:
        speakers.append(SpeakerInfo(
            name=community_leader,
            bio="Community Leader",
            title="Community Leader",
            organization="CMT Association",
            linkedin_url=linkedin_matches[0] if linkedin_matches else None,
            photo_url=None
        ))
    
    # Enhanced speaker name extraction
    # Look for patterns like "Joel Pannikot, the Managing Director at Chartered Market"
    name_patterns = [
        r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)(?:,|\s+(?:the|is|was))',  # "Joel Pannikot, the" or "Joel Pannikot is"
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)(?:\s+(?:boasts|has|brings))',  # "Joel Pannikot boasts"
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)(?:\s+continues)',  # "Joel Pannikot continues"
    ]
    
    lines = speakers_text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Try each pattern to extract speaker name
        for pattern in name_patterns:
            name_match = re.search(pattern, line)
            if name_match:
                speaker_name = name_match.group(1).strip()
                
                # Skip if it's the community leader (already added)
                if speaker_name == community_leader:
                    continue
                
                # Extract title and organization if possible
                title = "Speaker"
                organization = ""
                
                # Look for title patterns
                if "managing director" in line.lower():
                    title = "Managing Director"
                elif "director" in line.lower():
                    title = "Director"
                elif "manager" in line.lower():
                    title = "Manager"
                elif "ceo" in line.lower():
                    title = "CEO"
                elif "strategist" in line.lower():
                    title = "Strategist"
                
                # Look for organization patterns
                org_match = re.search(r'at\s+([A-Z][^,\.\n]+)', line)
                if org_match:
                    organization = org_match.group(1).strip()
                
                speakers.append(SpeakerInfo(
                    name=speaker_name,
                    bio=line.strip(),
                    title=title,
                    organization=organization,
                    linkedin_url=linkedin_matches[0] if linkedin_matches else None,
                    photo_url=None
                ))
                break  # Found a match, move to next line
    
    return speakers

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

# Timeout middleware for preventing 502 errors
@app.middleware("http")
async def timeout_middleware(request: Request, call_next):
    """Add timeout protection to prevent 502 errors"""
    start_time_req = time.time()
    
    try:
        # Set a 25-second timeout (5 seconds buffer for Render's 30s limit)
        response = await asyncio.wait_for(call_next(request), timeout=25.0)
        return response
    except asyncio.TimeoutError:
        process_time = time.time() - start_time_req
        print(f"Request to {request.url.path} timed out after {process_time:.4f} seconds")
        return JSONResponse(
            status_code=408,
            content={
                "success": False,
                "error_code": "TIMEOUT",
                "message": "Request timed out. Please try again or contact support if this persists.",
                "generation_time": process_time
            }
        )

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests for debugging"""
    global last_payload
    start_time_req = time.time()
    
    # Capture request body for POST requests
    if request.method == "POST":
        body = await request.body()
        if body:
            try:
                json_body = json.loads(body.decode())
                
                # Store payload globally for easy access
                last_payload = {
                    "timestamp": datetime.now().isoformat(),
                    "url": str(request.url),
                    "data": json_body,
                    "headers": dict(request.headers)
                }
                
                print(f"\n=== INCOMING POST REQUEST ===")
                print(f"URL: {request.url}")
                print(f"Headers: {dict(request.headers)}")
                print(f"JSON Payload: {json.dumps(json_body, indent=2)}")
                print(f"=== END REQUEST ===\n")
            except:
                print(f"POST to {request.url} with non-JSON body: {body[:200]}...")
        
        # Recreate request with body for downstream processing
        request._body = body
    
    response = await call_next(request)
    
    process_time = time.time() - start_time_req
    print(f"Request to {request.url.path} took {process_time:.4f} seconds")
    
    return response

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
        content={
            "success": False,
            "error_code": "INTERNAL_ERROR",
            "message": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )

@app.get("/")
async def root():
    """Root endpoint with API information"""
    global last_payload
    
    return {
        "message": "CMT Poster Generator API",
        "version": settings.API_VERSION,
        "docs": "/docs",
        "health": "/health",
        "debug": {
            "last_payload_status": "payload_found" if last_payload["data"] is not None else "no_payload",
            "last_payload_timestamp": last_payload.get("timestamp"),
            "last_payload_url": last_payload.get("url"),
            "view_full_payload": "Visit /last-payload endpoint"
        },
        "endpoints": {
            "generate_posters": "/generate-posters",
            "generate_posters_structured": "/generate-posters-structured",
            "debug_payload": "/debug-payload",
            "last_payload": "/last-payload",
            "services_status": "/services/status"
        }
    }

@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    current_time = datetime.now()
    uptime = time.time() - start_time
    
    return {
        "status": "healthy",
        "timestamp": current_time.isoformat(),
        "version": settings.API_VERSION,
        "uptime": uptime,
        "message": "CMT Poster Generator is running"
    }

@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check endpoint with service status"""
    current_time = datetime.now()
    uptime = time.time() - start_time
    
    # Get status of all services
    try:
        dependencies = await get_services_status()
    except Exception as e:
        dependencies = {"error": str(e)}
    
    # Determine overall health
    all_healthy = all(
        dep.get("status") == "healthy" 
        for dep in dependencies.values()
        if isinstance(dep, dict)
    )
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "timestamp": current_time.isoformat(),
        "version": settings.API_VERSION,
        "uptime": uptime,
        "dependencies": dependencies
    }

@app.post("/generate-posters", response_model=PosterGenerationResponse)
async def generate_posters_power_automate(request: PowerAutomateRequest):
    """Power Automate poster generation endpoint (handles direct payload format)"""
    start_time_req = time.time()
    errors = []
    
    print(f"=== POSTER GENERATION STARTED ===")
    print(f"Request received: {request.title}")
    print(f"Venue: {request.venue}")
    print(f"Community Leader: {request.community_leader}")
    print(f"Timestamp: {datetime.now()}")
    
    try:
        # Convert Power Automate format to internal format
        from app.models.request_models import EventDetails, SpeakerInfo, PosterGenerationRequest
        
        print("Step 1: Extracting city and country...")
        # Extract city and country from venue and title
        city, country = extract_city_country(request.venue, request.title)
        print(f"Extracted: {city}, {country}")
        
        print("Step 2: Creating event details...")
        # Create event details
        event_details = EventDetails(
            title=request.title,
            description=request.description,
            date=request.date,
            venue=request.venue,
            city=city,
            country=country,
            theme=request.theme,
            registration_url=None
        )
        
        print("Step 3: Parsing speakers...")
        # Parse speakers from text
        speakers = parse_speakers_from_text(request.speakers, request.community_leader)
        print(f"Found {len(speakers)} speakers: {[s.name for s in speakers]}")
        
        print("Step 4: Creating poster request...")
        # Create poster generation request
        poster_request = PosterGenerationRequest(
            event_details=event_details,
            speakers=speakers,
            poster_types=["general"]  # Only general poster for speed
        )
        
        print("Step 5: Initializing poster composer...")
        # Initialize poster composer
        composer = PosterComposer()
        
        print("Step 6: Starting poster generation...")
        # Generate posters
        posters = await composer.generate_posters(poster_request)
        
        generation_time = time.time() - start_time_req
        event_id = composer._generate_event_id(event_details)
        
        print(f"=== POSTER GENERATION COMPLETED ===")
        print(f"Generated {len(posters)} posters in {generation_time:.2f} seconds")
        
        return PosterGenerationResponse(
            success=True,
            message=f"Successfully generated {len(posters)} posters",
            event_id=event_id,
            posters=posters,
            generation_time=generation_time,
            cached_landmark=False,
            errors=errors
        )
        
    except Exception as e:
        generation_time = time.time() - start_time_req
        error_msg = str(e)
        errors.append(error_msg)
        
        print(f"=== POSTER GENERATION FAILED ===")
        print(f"Error: {error_msg}")
        import traceback
        traceback.print_exc()
        
        return PosterGenerationResponse(
            success=False,
            message=f"Failed to generate posters: {error_msg}",
            event_id="",
            posters=[],
            generation_time=generation_time,
            cached_landmark=False,
            errors=errors
        )

@app.post("/generate-posters-structured", response_model=PosterGenerationResponse, dependencies=[Depends(check_rate_limit)])
async def generate_posters_structured(request: PosterGenerationRequest):
    """Structured poster generation endpoint (for manual testing)"""
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

# Removed unused endpoints - landmarks and process-text
# These are not needed for the core poster generation flow

@app.post("/test-simple")
async def test_simple():
    """Ultra-simple test endpoint"""
    print("TEST SIMPLE ENDPOINT CALLED")
    return {"status": "success", "message": "Simple test works", "timestamp": datetime.now().isoformat()}

@app.post("/debug-payload")
async def debug_payload(request: Request):
    """Debug endpoint to capture and return any JSON payload"""
    try:
        body = await request.body()
        json_data = json.loads(body.decode())
        
        print(f"\n=== DEBUG ENDPOINT CALLED ===")
        print(f"Timestamp: {datetime.now()}")
        print(f"JSON Payload: {json.dumps(json_data, indent=2)}")
        print(f"=== END DEBUG ===\n")
        
        return {
            "status": "received",
            "timestamp": datetime.now().isoformat(),
            "payload": json_data,
            "message": "Payload logged successfully - check server logs"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to parse JSON payload"
        }

@app.get("/last-payload")
async def get_last_payload():
    """Get the last received POST payload for debugging"""
    global last_payload
    
    if last_payload["data"] is None:
        return {
            "status": "no_payload",
            "message": "No POST requests received yet",
            "note": "Make a POST request to any endpoint and check back here"
        }
    
    return {
        "status": "payload_found",
        "last_request": last_payload,
        "message": "This is the exact JSON that was last posted to your API"
    }

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
