from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

class SpeakerInfo(BaseModel):
    name: str
    bio: Optional[str] = ""
    title: Optional[str] = ""
    organization: Optional[str] = ""
    photo_url: Optional[str] = ""

class EventDetails(BaseModel):
    title: str
    description: str
    date: datetime
    time: Optional[str] = ""
    venue: str
    city: Optional[str] = ""
    country: Optional[str] = ""
    theme: Optional[str] = ""
    registration_url: Optional[str] = ""

class PosterGenerationRequest(BaseModel):
    event_details: EventDetails
    speakers: List[SpeakerInfo]
    poster_types: Optional[List[str]] = ["general"]
