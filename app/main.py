import io
import os
import re
import httpx
from datetime import datetime
from typing import Optional, List
from fastapi import FastAPI
from pydantic import BaseModel
from PIL import Image, ImageDraw, ImageFont
from app.models.request_models import PosterGenerationRequest, EventDetails, SpeakerInfo
from app.services.poster_composer import PosterComposer

app = FastAPI()

def extract_city_country(venue: str) -> (str, str):
    parts = [p.strip() for p in venue.split(",")]
    if len(parts) >= 2:
        city = parts[-2].title()
        country = parts[-1].title()
        return city, country
    return "Unknown", "Unknown"

@app.post("/generate-posters")
async def generate_posters(payload: dict):
    # Parse incoming payload to PosterGenerationRequest
    title = payload.get("title", "")
    description = payload.get("description", "")
    date = payload.get("date", "")
    time = payload.get("time", "")
    venue = payload.get("venue", "")
    community_leader = payload.get("community_leader", "")
    theme = payload.get("theme", "")
    speakers_raw = payload.get("speakers", "")
    city, country = extract_city_country(venue)

    event_details = EventDetails(
        title=title,
        description=description,
        date=datetime.fromisoformat(date.replace("Z", "+00:00")),
        time=time,
        venue=venue,
        city=city,
        country=country,
        theme=theme,
        registration_url=None
    )

    # Parse speakers
    speakers = []
    for line in speakers_raw.split("\n"):
        match = re.match(r"([A-Za-z ]+),\s*(.*)", line)
        if match:
            name = match.group(1).strip()
            bio = match.group(2).strip()
            speakers.append(SpeakerInfo(name=name, bio=bio))
        elif line.strip():
            speakers.append(SpeakerInfo(name=line.strip(), bio=""))
    if not speakers and community_leader:
        speakers.append(SpeakerInfo(name=community_leader, bio="Community Leader"))

    poster_request = PosterGenerationRequest(
        event_details=event_details,
        speakers=speakers,
        poster_types=["general"]
    )

    composer = PosterComposer()
    posters = await composer.generate_posters(poster_request)
    return {"success": True, "posters": posters}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def root():
    return {"message": "CMT Poster Generator Minimal API", "status": "ok"}
