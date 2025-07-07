from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class PosterInfo(BaseModel):
    poster_type: str = Field(..., description="Type of poster (general, speaker, theme)")
    url: str = Field(..., description="URL to the generated poster")
    speaker_name: Optional[str] = Field(None, description="Speaker name for speaker-specific posters")
    dimensions: Dict[str, int] = Field(..., description="Poster dimensions (width, height)")
    file_size: int = Field(..., description="File size in bytes")
    format: str = Field(..., description="Image format (PNG, JPEG, etc.)")

class PosterGenerationResponse(BaseModel):
    success: bool = Field(..., description="Whether the generation was successful")
    message: str = Field(..., description="Status message")
    event_id: str = Field(..., description="Unique identifier for the event")
    posters: List[PosterInfo] = Field(default=[], description="List of generated posters")
    generation_time: float = Field(..., description="Time taken to generate posters in seconds")
    cached_landmark: bool = Field(..., description="Whether landmark was retrieved from cache")
    errors: List[str] = Field(default=[], description="List of any errors encountered")

class LandmarkResponse(BaseModel):
    success: bool = Field(..., description="Whether the landmark generation was successful")
    landmark_name: str = Field(..., description="Name of the landmark")
    city: str = Field(..., description="City name")
    country: str = Field(..., description="Country name")
    image_url: str = Field(..., description="URL to the landmark image")
    cached: bool = Field(..., description="Whether the image was retrieved from cache")
    generation_time: float = Field(..., description="Time taken to generate/retrieve image")

class TextProcessingResponse(BaseModel):
    success: bool = Field(..., description="Whether text processing was successful")
    processed_text: str = Field(..., description="Processed text")
    original_length: int = Field(..., description="Original text length")
    processed_length: int = Field(..., description="Processed text length")
    processing_time: float = Field(..., description="Time taken to process text")

class HealthResponse(BaseModel):
    status: str = Field(..., description="Service health status")
    timestamp: datetime = Field(..., description="Current timestamp")
    version: str = Field(..., description="API version")
    uptime: float = Field(..., description="Service uptime in seconds")
    dependencies: Dict[str, str] = Field(..., description="Status of external dependencies")

class ErrorResponse(BaseModel):
    success: bool = Field(False, description="Always false for error responses")
    error_code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(..., description="Error timestamp")
