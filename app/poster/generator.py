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
            # Try several variants for best match, including first name only, ignore case, and missing middle names
            import re
            base = name.strip()
            # Remove extra spaces and punctuation
            base_clean = re.sub(r'[^a-zA-Z0-9 ]', '', base)
            parts = base_clean.split()
            first = parts[0] if parts else base_clean
            last = parts[-1] if len(parts) > 1 else ''
            variants = set()
            # Full name variants
            variants.add(base)
            variants.add(base.lower())
            variants.add(base.upper())
            variants.add(base.replace(" ", "-").lower())
            variants.add(base.replace(" ", "_").lower())
            variants.add(base.replace(" ", ""))
            # First name only
            variants.add(first)
            variants.add(first.lower())
            variants.add(first.upper())
            # First + last (skip middle)
            if first and last and first != last:
                variants.add(f"{first} {last}")
                variants.add(f"{first.lower()} {last.lower()}")
                variants.add(f"{first}{last}")
                variants.add(f"{first.lower()}{last.lower()}")
            # Try all variants
            for variant in variants:
                photo = await self.wp.search_media(variant)
                if photo:
                    return photo
            return None

        speaker_photos = [await find_speaker_photo(name) for name in speaker_names]
        # 4. Text formatting
        # Normalize date to YYYY-MM-DD for OpenAI
        import dateutil.parser
        raw_date = payload.get("date", "")
        try:
            parsed_date = dateutil.parser.parse(raw_date, dayfirst=False, yearfirst=False)
            norm_date = parsed_date.strftime("%Y-%m-%d")
        except Exception:
            norm_date = raw_date
        # Get event details from OpenAI (separator should be handled in the OpenAI prompt, not as an argument)
        event_details = await self.openai.format_event_details(norm_date, payload.get("time", ""), payload.get("venue", ""))
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
            # 1 row for up to 4 speakers, 2 rows for 5-8, etc.
            import math
            max_per_row = 4
            rows = math.ceil(n / max_per_row)
            circle_size = 320 if n == 1 else 220 if n == 2 else 160
            y = y_cursor + 40
            for row in range(rows):
                speakers_in_row = min(max_per_row, n - row * max_per_row)
                # Evenly space circles across the row
                total_space = width - 2 * margin_x
                if speakers_in_row == 1:
                    x_positions = [width // 2 - circle_size // 2]
                else:
                    gap = (total_space - speakers_in_row * circle_size) // (speakers_in_row - 1) if speakers_in_row > 1 else 0
                    x_positions = [margin_x + j * (circle_size + gap) for j in range(speakers_in_row)]
                for j in range(speakers_in_row):
                    i = row * max_per_row + j
                    if i >= n:
                        break
                    photo_url = speaker_photos[i]
                    cred = credentials[i]
                    if not photo_url:
                        continue
                    photo = self.imgsvc.open_image(photo_url)
                    photo = self.imgsvc.crop_to_aspect(photo, (circle_size, circle_size))
                    mask = Image.new("L", (circle_size, circle_size), 0)
                    ImageDraw.Draw(mask).ellipse((0,0,circle_size,circle_size), fill=255)
                    img.paste(photo, (x_positions[j], y), mask)
                    # Speaker credentials (centered, name bold)
                    cred_y = y + circle_size + 10
                    cred_parts = cred.split(",", 1)
                    name = cred_parts[0].strip() if cred_parts else cred.strip()
                    rest = cred_parts[1].strip() if len(cred_parts) > 1 else ""
                    center_x = x_positions[j] + circle_size//2
                    name_bbox = font_small_bold.getbbox(name)
                    name_w = name_bbox[2] - name_bbox[0]
                    draw.text((center_x - name_w//2, cred_y), name, font=font_small_bold, fill="white")
                    if rest:
                        rest_bbox = font_small.getbbox(rest)
                        rest_w = rest_bbox[2] - rest_bbox[0]
                        draw.text((center_x - rest_w//2, cred_y + int(font_small.size * 1.2)), rest, font=font_small, fill="white")
                y += circle_size + int(font_small.size * 2.2)
            speaker_grid_bottom = y
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
        # Robustly extract date, time, venue from OpenAI output like:
        # 'Date: ..., Time: ..., Venue: ...'
        details_lines = []
        import re as _re
        s = event_details.strip()
        # Try to match the pattern
        m = _re.match(r"Date:\s*(.*?),\s*Time:\s*(.*?),\s*Venue:\s*(.*)", s)
        if m:
            details_lines = [m.group(1).strip(), m.group(2).strip(), m.group(3).strip()]
        else:
            # Fallback: try to split by label
            for label in ["Date:", "Time:", "Venue:"]:
                idx = s.find(label)
                if idx != -1:
                    value = s[idx+len(label):].split("\n")[0].strip()
                    details_lines.append(value)
            # If not found, fallback to comma split
            if not details_lines:
                details_lines = [x.strip() for x in s.split(",") if x.strip()]
        details_y = speaker_grid_bottom + 30
        line_gap = 54
        free_gap = 30
        for i, line in enumerate(details_lines):
            # Remove label if present (e.g., 'Date: July 8, 2025' -> 'July 8, 2025')
            if ":" in line:
                value = line.split(":", 1)[1].strip()
            else:
                value = line
            icon = icons[i] if i < len(icons) else None
            x = margin_x
            y = details_y + i * (line_gap + free_gap)
            if icon:
                img.paste(icon, (x, y), icon)
                x += icon_size + 12
            draw.text((x, y + (icon_size - font_regular.size)//2), value, font=font_regular, fill="white", anchor="la")

        # Register line (move higher, with icon)
        register_icon_url = await self.wp.search_media("register")
        register_icon = self.imgsvc.open_image(register_icon_url).resize((60, 60)) if register_icon_url else None
        reg_y = height - margin_y - 160
        if n:
            # 1 row for up to 4 speakers, 2 rows for 5-8, etc.
            import math
            max_per_row = 4
            rows = math.ceil(n / max_per_row)
            circle_size = 320 if n == 1 else 220 if n == 2 else 160
            y = y_cursor + 40
            for row in range(rows):
                speakers_in_row = min(max_per_row, n - row * max_per_row)
                # Center speakers in the row, evenly spaced between left and right borders
                total_space = width - 2 * margin_x
                row_width = speakers_in_row * circle_size + (speakers_in_row - 1) * 60  # 60px gap between circles
                start_x = margin_x + (total_space - row_width) // 2 if speakers_in_row > 1 else width // 2 - circle_size // 2
                x_positions = [start_x + j * (circle_size + 60) for j in range(speakers_in_row)]
                for j in range(speakers_in_row):
                    i = row * max_per_row + j
                    if i >= n:
                        break
                    photo_url = speaker_photos[i]
                    cred = credentials[i]
                    if not photo_url:
                        continue
                    photo = self.imgsvc.open_image(photo_url)
                    photo = self.imgsvc.crop_to_aspect(photo, (circle_size, circle_size))
                    mask = Image.new("L", (circle_size, circle_size), 0)
                    ImageDraw.Draw(mask).ellipse((0,0,circle_size,circle_size), fill=255)
                    img.paste(photo, (x_positions[j], y), mask)
                    # Speaker credentials (centered, name bold)
                    cred_y = y + circle_size + 10
                    cred_parts = cred.split(",", 1)
                    name = cred_parts[0].strip() if cred_parts else cred.strip()
                    rest = cred_parts[1].strip() if len(cred_parts) > 1 else ""
                    center_x = x_positions[j] + circle_size//2
                    name_bbox = font_small_bold.getbbox(name)
                    name_w = name_bbox[2] - name_bbox[0]
                    draw.text((center_x - name_w//2, cred_y), name, font=font_small_bold, fill="white")
                    if rest:
                        rest_bbox = font_small.getbbox(rest)
                        rest_w = rest_bbox[2] - rest_bbox[0]
                        draw.text((center_x - rest_w//2, cred_y + int(font_small.size * 1.2)), rest, font=font_small, fill="white")
                y += circle_size + int(font_small.size * 2.2)
            speaker_grid_bottom = y
        else:
            speaker_grid_bottom = y_cursor + 40
