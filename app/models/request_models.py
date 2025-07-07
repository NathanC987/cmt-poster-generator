from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class SpeakerInfo(BaseModel):
    name: str = Field(..., description="Speaker's full name")
    bio: Optional[str] = Field(None, description="Speaker's biography")
    title: Optional[str] = Field(None, description="Speaker's job title")
    organization: Optional[str] = Field(None, description="Speaker's organization")
    linkedin_url: Optional[str] = Field(None, description="Speaker's LinkedIn profile URL")
    photo_url: Optional[str] = Field(None, description="URL to speaker's photo")
    credentials: Optional[str] = Field(None, description="Speaker's credentials (e.g., CFA, CMT)")

class EventDetails(BaseModel):
    title: str = Field(..., description="Event title")
    description: str = Field(..., description="Event description")
    date: datetime = Field(..., description="Event date and time")
    venue: str = Field(..., description="Event venue")
    city: str = Field(..., description="Event city for landmark generation")
    country: str = Field(..., description="Event country")
    theme: Optional[str] = Field(None, description="Event theme")
    registration_url: Optional[str] = Field(None, description="Registration URL")

class PosterGenerationRequest(BaseModel):
    event_details: EventDetails
    speakers: List[SpeakerInfo] = Field(..., description="List of speakers")
    poster_types: List[str] = Field(
        default=["general", "speaker", "theme"],
        description="Types of posters to generate"
    )
    custom_overlay: Optional[str] = Field(None, description="Custom overlay template name")
    additional_requirements: Optional[Dict[str, Any]] = Field(None, description="Additional customization requirements")

class LandmarkRequest(BaseModel):
    city: str = Field(..., description="City name for landmark generation")
    country: str = Field(..., description="Country name")
    style: str = Field(default="realistic", description="Image style (realistic, artistic, etc.)")
    force_regenerate: bool = Field(default=False, description="Force regeneration even if cached")

class TextProcessingRequest(BaseModel):
    original_text: str = Field(..., description="Original text to process")
    target_length: int = Field(default=150, description="Target character length")
    style: str = Field(default="professional", description="Text style (professional, casual, etc.)")
    context: Optional[str] = Field(None, description="Additional context for processing")
