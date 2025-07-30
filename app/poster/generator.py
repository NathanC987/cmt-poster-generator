import os
import tempfile
from app.services.openai_service import OpenAIService
from app.services.wordpress_service import WordPressService
from app.services.image_service import ImageService
from app.core.config import settings
from PIL import Image, ImageDraw, ImageFont

class PosterGenerator:
    def __init__(self, openai_service, wordpress_service, image_service):
        self.openai = openai_service
        self.wp = wordpress_service
        self.imgsvc = image_service

    async def generate(self, payload):
        # 1. Get landmark slug
        venue = payload.get("venue", "")
        landmark_slug = await self.openai.get_landmark_slug(venue)
        # 2. Get images
        landmark_url = await self.wp.search_media(landmark_slug)
        overlay_url = await self.wp.search_media("overlay")
        # 3. Speaker photos
        import re
        speakers_text = payload.get("speakers", "")
        speaker_lines = (await self.openai.extract_speakers_and_credentials(speakers_text)).split("\n")
        speaker_names = []
        for line in speaker_lines:
            # Remove leading numbering and punctuation (e.g., '1. ', '2) ', etc.)
            name = re.sub(r"^\s*\d+\s*[\.|\)]?\s*", "", line)
            name = name.split(",")[0].strip()
            if name:
                speaker_names.append(name)

        async def find_speaker_photo(name):
            # Try several variants for best match
            variants = set()
            base = name.strip()
            variants.add(base)
            variants.add(base.lower())
            variants.add(base.replace(" ", "-").lower())
            variants.add(base.replace(" ", "_").lower())
            variants.add(base.replace(" ", ""))
            variants.add(base.replace(" ", "-").replace("_", "-").lower())
            variants.add(base.replace(" ", "_").replace("-", "_").lower())
            for variant in variants:
                photo = await self.wp.search_media(variant)
                if photo:
                    return photo
            return None

        speaker_photos = [await find_speaker_photo(name) for name in speaker_names]
        # 4. Text formatting
        event_details = await self.openai.format_event_details(payload.get("date", ""), payload.get("time", ""), payload.get("venue", ""))
        summary = await self.openai.summarize_description(payload.get("description", ""))
        credentials = (await self.openai.extract_speakers_and_credentials(speakers_text)).split("\n")
        # 5. Compose poster
        poster_path = await self.compose_poster(
            title=payload.get("title", ""),
            summary=summary,
            event_details=event_details,
            speaker_photos=speaker_photos,
            credentials=credentials,
            landmark_url=landmark_url,
            overlay_url=overlay_url
        )
        # 6. Upload poster
        poster_url = await self.wp.upload_media(poster_path, os.path.basename(poster_path))
        return [poster_url]

    async def compose_poster(self, title, summary, event_details, speaker_photos, credentials, landmark_url, overlay_url):
        width, height = 1200, 1600
        img = self.imgsvc.open_image(landmark_url)
        img = self.imgsvc.resize_and_center(img, (width, height))
        overlay = self.imgsvc.open_image(overlay_url)
        overlay = self.imgsvc.resize_and_center(overlay, (width, height))
        img.alpha_composite(overlay)
        draw = ImageDraw.Draw(img)
        font_bold = ImageFont.truetype(settings.FONT_BOLD_PATH, 80)
        font_regular = ImageFont.truetype(settings.FONT_REGULAR_PATH, 48)
        # Title
        draw.text((width//2, 80), title, font=font_bold, fill="white", anchor="ma")
        # Summary
        draw.text((width//2, 200), summary, font=font_regular, fill="white", anchor="ma")
        # Speaker grid
        n = len(speaker_photos)
        if n:
            circle_size = 320 if n == 1 else 220 if n == 2 else 160
            start_x = width//2 - ((n-1)*circle_size)//2
            y = 400
            for i, (photo_url, cred) in enumerate(zip(speaker_photos, credentials)):
                if not photo_url:
                    continue
                photo = self.imgsvc.open_image(photo_url)
                photo = self.imgsvc.resize_and_center(photo, (circle_size, circle_size))
                mask = Image.new("L", (circle_size, circle_size), 0)
                ImageDraw.Draw(mask).ellipse((0,0,circle_size,circle_size), fill=255)
                img.paste(photo, (start_x + i*circle_size, y), mask)
                draw.text((start_x + i*circle_size + circle_size//2, y+circle_size+10), cred, font=font_regular, fill="white", anchor="ma")
        # Event details
        draw.text((width//2, height-220), event_details, font=font_regular, fill="white", anchor="ma")
        # Register line
        draw.text((width//2, height-100), "Register online at cmtassociation.org", font=font_regular, fill="white", anchor="ma")
        # Save
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            img.save(tmp.name, format="PNG")
            return tmp.name
