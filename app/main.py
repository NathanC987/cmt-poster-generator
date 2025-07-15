import io
import os
import re
import hashlib
import httpx
from datetime import datetime
from typing import Optional, List
from fastapi import FastAPI
from pydantic import BaseModel
from PIL import Image, ImageDraw, ImageFont

# --- CONFIGURATION ---
WORDPRESS_URL = os.getenv("WORDPRESS_URL", "https://cmtpl.org")
WORDPRESS_USERNAME = os.getenv("WORDPRESS_USERNAME")
WORDPRESS_PASSWORD = os.getenv("WORDPRESS_PASSWORD")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4")
FONT_PATH_BOLD = "app/fonts/GlacialIndifference-Bold.ttf"
FONT_PATH_REGULAR = "app/fonts/GlacialIndifference-Regular.ttf"
POSTER_WIDTH = 1200
POSTER_HEIGHT = 1600

# --- MODELS ---
class PowerAutomateRequest(BaseModel):
    title: str
    format: Optional[str]
    date: datetime
    time: Optional[str]
    venue: str
    community_leader: Optional[str]
    co_volunteers: Optional[str]
    theme: Optional[str]
    description: str
    speakers: str

# --- FASTAPI APP ---
app = FastAPI()

def extract_city_country(venue: str) -> (str, str):
    parts = [p.strip() for p in venue.split(",")]
    if len(parts) >= 2:
        city = parts[-2].title()
        country = parts[-1].title()
        return city, country
    return "Unknown", "Unknown"

async def get_wordpress_media_url(search_term: str, endswith: Optional[str] = None) -> Optional[str]:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{WORDPRESS_URL}/wp-json/wp/v2/media",
            params={"search": search_term, "media_type": "image", "per_page": 50},
            auth=(WORDPRESS_USERNAME, WORDPRESS_PASSWORD)
        )
        if resp.status_code == 200:
            for item in resp.json():
                url = item.get("source_url", "")
                if (not endswith or url.lower().endswith(endswith)) and search_term in url:
                    return url
    return None

async def get_speaker_photo_url(speaker_name: str) -> Optional[str]:
    variants = [
        speaker_name.lower().replace(" ", "-"),
        speaker_name.lower().replace(" ", "_"),
        speaker_name.lower().replace(" ", ""),
        speaker_name.lower(),
    ]
    for variant in variants:
        url = await get_wordpress_media_url(variant)
        if url:
            return url
    return None

async def summarize_text(text: str, target_length: int = 200) -> str:
    import openai
    client = openai.AsyncAzureOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        api_version="2024-02-01",
        azure_endpoint=AZURE_OPENAI_ENDPOINT
    )
    prompt = (
        f"Summarize the following event description for a poster. "
        f"Focus on what the event is about and why it is being held. "
        f"Do NOT include the date, time, venue, speaker names, or LinkedIn links. "
        f"The summary should be concise, engaging, and suitable for a poster. "
        f"Target length: {target_length} characters.\n\n"
        f"Description:\n{text}\n\nSummary:"
    )
    resp = await client.chat.completions.create(
        model=AZURE_OPENAI_DEPLOYMENT,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=target_length + 50,
        temperature=0.3
    )
    return resp.choices[0].message.content.strip()

async def extract_speaker_credentials(speaker_bio: str) -> (str, str, str):
    import openai
    client = openai.AsyncAzureOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        api_version="2024-02-01",
        azure_endpoint=AZURE_OPENAI_ENDPOINT
    )
    prompt = (
        "From the following speaker bio, extract only the speaker's full name, designation/title, and organization in this format (each on a new line):\n\n"
        "[Speaker Name]\n[Designation/Title]\n[Organization]\n\n"
        "Bio:\n"
        f"{speaker_bio}\n\n"
        "Output:"
    )
    resp = await client.chat.completions.create(
        model=AZURE_OPENAI_DEPLOYMENT,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100,
        temperature=0.1
    )
    lines = resp.choices[0].message.content.strip().splitlines()
    name = lines[0].strip() if len(lines) > 0 else ""
    title = lines[1].strip() if len(lines) > 1 else ""
    org = lines[2].strip() if len(lines) > 2 else ""
    return name, title, org

def wrap_text(text, font, max_width):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = current + (" " if current else "") + word
        if font.getbbox(test)[2] - font.getbbox(test)[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines

async def download_image(url: str) -> Image.Image:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return Image.open(io.BytesIO(resp.content)).convert("RGBA")

async def upload_to_wordpress(image: Image.Image, filename: str) -> str:
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    buf.seek(0)
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Content-Type": "image/png"
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{WORDPRESS_URL}/wp-json/wp/v2/media",
            data=buf.read(),
            headers=headers,
            auth=(WORDPRESS_USERNAME, WORDPRESS_PASSWORD)
        )
        resp.raise_for_status()
        return resp.json()["source_url"]

def resize_and_crop(img, target_w, target_h):
    img_ratio = img.width / img.height
    target_ratio = target_w / target_h
    if img_ratio > target_ratio:
        new_height = target_h
        new_width = int(new_height * img_ratio)
    else:
        new_width = target_w
        new_height = int(new_width / img_ratio)
    img = img.resize((new_width, new_height), Image.LANCZOS)
    left = (new_width - target_w) // 2
    top = (new_height - target_h) // 2
    return img.crop((left, top, left + target_w, top + target_h))

def circle_crop(img, size):
    img = img.resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size, size), fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(img, (0, 0), mask)
    return out

def get_speaker_circle_size(num_speakers: int) -> int:
    if num_speakers == 1:
        return 260
    elif num_speakers == 2:
        return 180
    elif num_speakers == 3:
        return 140
    else:
        return 110

@app.post("/generate-posters")
async def generate_posters(payload: PowerAutomateRequest):
    print("Received payload:", payload)
    city, country = extract_city_country(payload.venue)
    print("Extracted city/country:", city, country)
    city_slug = city.lower().replace(" ", "-")
    country_slug = country.lower().replace(" ", "-")
    landmark_name = f"{city_slug}-{country_slug}"
    print("Landmark search term:", landmark_name)

    # 1. Get landmark image
    landmark_url = await get_wordpress_media_url(landmark_name)
    if not landmark_url:
        return {"success": False, "message": f"Landmark image not found for {city}, {country}"}
    print("Landmark URL:", landmark_url)
    landmark_img = await download_image(landmark_url)
    landmark_img = resize_and_crop(landmark_img, POSTER_WIDTH, POSTER_HEIGHT)

    # 2. Get overlay image
    overlay_url = await get_wordpress_media_url("overlay", endswith="overlay.png")
    if not overlay_url:
        return {"success": False, "message": "Overlay image not found"}
    print("Overlay URL:", overlay_url)
    overlay_img = await download_image(overlay_url)
    if overlay_img.size != (POSTER_WIDTH, POSTER_HEIGHT):
        overlay_img = overlay_img.resize((POSTER_WIDTH, POSTER_HEIGHT), Image.LANCZOS)
    poster = Image.alpha_composite(landmark_img.convert("RGBA"), overlay_img)

    # 3. Summarize description
    summary = await summarize_text(payload.description, 200)
    print("Summary:", summary)

    # 4. Speaker extraction (improved for single speaker)
    speakers = []
    for line in payload.speakers.split("\n"):
        match = re.match(r"([A-Za-z ]+),\s*(.*)", line)
        if match:
            name = match.group(1).strip()
            bio = match.group(2).strip()
            speakers.append({"bio": line.strip(), "name": name, "title_org": bio})
        elif line.strip():
            speakers.append({"bio": line.strip(), "name": line.strip(), "title_org": ""})
    if not speakers and payload.community_leader:
        speakers.append({"bio": payload.community_leader, "name": payload.community_leader, "title_org": "Community Leader"})

    # 5. Speaker photo(s) and credentials
    for speaker in speakers:
        speaker["photo_url"] = await get_speaker_photo_url(speaker["name"])
        name, title, org = await extract_speaker_credentials(speaker["bio"])
        speaker["name"] = name
        speaker["title"] = title
        speaker["org"] = org

    # 6. Compose poster
    draw = ImageDraw.Draw(poster)
    # Margins
    left_margin = 100
    right_margin = 100
    top_margin = 180
    y = top_margin

    # Fonts (larger)
    title_font = ImageFont.truetype(FONT_PATH_BOLD, 96)
    desc_font = ImageFont.truetype(FONT_PATH_REGULAR, 48)
    cred_font = ImageFont.truetype(FONT_PATH_REGULAR, 44)
    details_font = ImageFont.truetype(FONT_PATH_BOLD, 48)

    # Title
    for line in wrap_text(payload.title, title_font, POSTER_WIDTH - left_margin - right_margin):
        draw.text((left_margin, y), line, font=title_font, fill="white")
        y += 110
    y += 30

    # Description
    for line in wrap_text(summary, desc_font, POSTER_WIDTH - left_margin - right_margin):
        draw.text((left_margin, y), line, font=desc_font, fill="white")
        y += 62
    y += 60

    # Speaker grid
    num_speakers = len(speakers)
    circle_size = get_speaker_circle_size(num_speakers)
    grid_y = y
    grid_x = (POSTER_WIDTH - (circle_size * num_speakers + 80 * (num_speakers - 1))) // 2
    for speaker in speakers:
        if speaker.get("photo_url"):
            photo = await download_image(speaker["photo_url"])
            photo = circle_crop(photo, circle_size)
            poster.paste(photo, (grid_x, grid_y), photo)
        else:
            draw.ellipse([grid_x, grid_y, grid_x+circle_size, grid_y+circle_size], fill="#3498DB")
        # Credentials
        cred_y = grid_y + circle_size + 30
        draw.text((grid_x, cred_y), speaker["name"], font=cred_font, fill="white")
        draw.text((grid_x, cred_y+50), speaker["title"], font=cred_font, fill="white")
        draw.text((grid_x, cred_y+100), speaker["org"], font=cred_font, fill="white")
        grid_x += circle_size + 80
    y = grid_y + circle_size + 180

    # Event details below speaker grid, with more space
    details_y = y + 60
    date_str = payload.date.strftime("%B %d, %Y")
    venue_str = payload.venue
    # Use a uniform, formal icon for all details
    icon = "●"
    draw.text((left_margin, details_y), f"{icon}  {date_str}", font=details_font, fill="white")
    draw.text((left_margin, details_y+70), f"{icon}  {payload.time}", font=details_font, fill="white")
    draw.text((left_margin, details_y+140), f"{icon}  {venue_str}", font=details_font, fill="white")

    # 7. Upload to WordPress
    filename = f"poster-{city_slug}-{country_slug}-{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
    poster_url = await upload_to_wordpress(poster, filename)
    print("Poster uploaded:", poster_url)

    return {"success": True, "poster_url": poster_url}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def root():
    return {"message": "CMT Poster Generator Minimal API", "status": "ok"}
