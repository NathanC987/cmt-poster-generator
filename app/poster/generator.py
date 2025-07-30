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
        # Margins
        margin_x = 80
        margin_y = 80
        content_width = width - 2 * margin_x
        content_height = height - 2 * margin_y

        img = self.imgsvc.open_image(landmark_url)
        img = self.imgsvc.crop_to_aspect(img, (width, height))
        overlay = self.imgsvc.open_image(overlay_url)
        overlay = self.imgsvc.crop_to_aspect(overlay, (width, height))
        img.alpha_composite(overlay)
        draw = ImageDraw.Draw(img)
        font_bold = ImageFont.truetype(settings.FONT_BOLD_PATH, 80)
        font_regular = ImageFont.truetype(settings.FONT_REGULAR_PATH, 48)
        font_small = ImageFont.truetype(settings.FONT_REGULAR_PATH, 38)
        font_small_bold = ImageFont.truetype(settings.FONT_BOLD_PATH, 38)
        # Text wrapping utility
        def draw_wrapped_text(draw, text, font, x, y, max_width, line_spacing=1.2, anchor="la"):
            words = text.split()
            lines = []
            current = ""
            for word in words:
                test = current + (" " if current else "") + word
                bbox = font.getbbox(test)
                w = bbox[2] - bbox[0]
                if w > max_width and current:
                    lines.append(current)
                    current = word
                else:
                    current = test
            if current:
                lines.append(current)
            for i, line in enumerate(lines):
                draw.text((x, y + i * int(font.size * line_spacing)), line, font=font, fill="white", anchor=anchor)
            return y + len(lines) * int(font.size * line_spacing)

        # Title (wrapped)
        y_cursor = margin_y
        y_cursor = draw_wrapped_text(draw, title, font_bold, margin_x, y_cursor, content_width)
        # Summary (wrapped)
        y_cursor += 20
        y_cursor = draw_wrapped_text(draw, summary, font_regular, margin_x, y_cursor, content_width)
        # Speaker grid
        n = len(speaker_photos)
        speaker_grid_bottom = y_cursor
        if n:
            circle_size = 320 if n == 1 else 220 if n == 2 else 160
            grid_width = n * circle_size
            start_x = width//2 - grid_width//2
            y = y_cursor + 40
            for i, (photo_url, cred) in enumerate(zip(speaker_photos, credentials)):
                if not photo_url:
                    continue
                photo = self.imgsvc.open_image(photo_url)
                photo = self.imgsvc.crop_to_aspect(photo, (circle_size, circle_size))
                mask = Image.new("L", (circle_size, circle_size), 0)
                ImageDraw.Draw(mask).ellipse((0,0,circle_size,circle_size), fill=255)
                img.paste(photo, (start_x + i*circle_size, y), mask)
                # Speaker credentials (centered, name bold)
                cred_y = y + circle_size + 10
                # Split name and rest
                cred_parts = cred.split(",", 1)
                name = cred_parts[0].strip() if cred_parts else cred.strip()
                rest = cred_parts[1].strip() if len(cred_parts) > 1 else ""
                # Centered below circle
                center_x = start_x + i*circle_size + circle_size//2
                # Draw name bold, centered
                name_bbox = font_small_bold.getbbox(name)
                name_w = name_bbox[2] - name_bbox[0]
                draw.text((center_x - name_w//2, cred_y), name, font=font_small_bold, fill="white")
                # Draw rest (designation/org), regular, centered below name
                if rest:
                    rest_bbox = font_small.getbbox(rest)
                    rest_w = rest_bbox[2] - rest_bbox[0]
                    draw.text((center_x - rest_w//2, cred_y + int(font_small.size * 1.2)), rest, font=font_small, fill="white")
            speaker_grid_bottom = y + circle_size + 10 + int(font_small.size * 2)
        else:
            speaker_grid_bottom = y_cursor + 40

        # Event details (date, time, venue on separate lines, left aligned below speaker grid, with icons)
        # Fetch icons from WordPress
        icon_size = int(font_regular.size * 1.1)
        date_icon_url = await self.wp.search_media("date")
        time_icon_url = await self.wp.search_media("time")
        venue_icon_url = await self.wp.search_media("venue")
        icons = []
        for url in [date_icon_url, time_icon_url, venue_icon_url]:
            if url:
                icon = self.imgsvc.open_image(url).resize((icon_size, icon_size))
                icons.append(icon)
            else:
                icons.append(None)
        # Parse event_details for values (remove label)
        details_lines = [line.strip() for line in event_details.split(",") if line.strip()]
        details_y = speaker_grid_bottom + 30
        for i, line in enumerate(details_lines):
            # Remove label if present (e.g., 'Date: July 8, 2025' -> 'July 8, 2025')
            if ":" in line:
                value = line.split(":", 1)[1].strip()
            else:
                value = line
            icon = icons[i] if i < len(icons) else None
            x = margin_x
            y = details_y + i*54
            if icon:
                img.paste(icon, (x, y), icon)
                x += icon_size + 12
            draw.text((x, y + (icon_size - font_regular.size)//2), value, font=font_regular, fill="white", anchor="la")

        # Register line (higher, with icon)
        register_icon_url = await self.wp.search_media("register")
        register_icon = self.imgsvc.open_image(register_icon_url).resize((60, 60)) if register_icon_url else None
        reg_y = height - margin_y - 60
        reg_x = width//2
        reg_text = "Register online at cmtassociation.org"
        if register_icon:
            reg_icon_w = register_icon.width
            reg_text_bbox = font_regular.getbbox(reg_text)
            reg_text_w = reg_text_bbox[2] - reg_text_bbox[0]
            total_w = reg_icon_w + 16 + reg_text_w
            reg_icon_x = reg_x - total_w//2
            img.paste(register_icon, (reg_icon_x, reg_y), register_icon)
            draw.text((reg_icon_x + reg_icon_w + 16, reg_y + (register_icon.height - font_regular.size)//2), reg_text, font=font_regular, fill="white", anchor="la")
        else:
            draw.text((reg_x, reg_y), reg_text, font=font_regular, fill="white", anchor="ma")
        # Save
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            img.save(tmp.name, format="PNG")
            return tmp.name
