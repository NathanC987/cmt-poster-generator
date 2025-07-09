import io
import hashlib
import httpx
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
from app.services.service_factory import get_storage, get_image_generator, get_text_processor
from app.services.font_service import get_font_service
from app.services.wordpress_service import WordPressService
from app.models.request_models import PosterGenerationRequest, SpeakerInfo, EventDetails

class PosterComposer:
    """Main poster composition engine"""
    
    def __init__(self):
        self.storage = get_storage()
        self.image_generator = get_image_generator()
        self.text_processor = get_text_processor()
        
        # Default poster dimensions
        self.poster_width = 1200
        self.poster_height = 1600
        
        # Color scheme
        self.colors = {
            "primary": "#2C3E50",      # Dark blue
            "secondary": "#3498DB",     # Light blue
            "accent": "#E74C3C",       # Red
            "text_primary": "#2C3E50", # Dark blue
            "text_secondary": "#7F8C8D", # Gray
            "background": "#FFFFFF",    # White
            "overlay": "#00000080"      # Semi-transparent black
        }
    
    async def generate_posters(self, request: PosterGenerationRequest) -> List[Dict[str, Any]]:
        """Generate all requested poster types"""
        posters = []
        event_id = self._generate_event_id(request.event_details)
        
        # Get or generate landmark background
        landmark_url = await self._get_landmark_image(
            request.event_details.city,
            request.event_details.country
        )
        
        # Generate different poster types
        for poster_type in request.poster_types:
            if poster_type == "general":
                poster_info = await self._generate_general_poster(
                    request, event_id, landmark_url
                )
            elif poster_type == "speaker":
                # Generate one poster per speaker
                for speaker in request.speakers:
                    poster_info = await self._generate_speaker_poster(
                        request, speaker, event_id, landmark_url
                    )
                    posters.append(poster_info)
                continue
            elif poster_type == "theme":
                poster_info = await self._generate_theme_poster(
                    request, event_id, landmark_url
                )
            else:
                continue
            
            posters.append(poster_info)
        
        return posters
    
    async def _generate_general_poster(self, request: PosterGenerationRequest, event_id: str, landmark_url: str) -> Dict[str, Any]:
        """Generate general overview poster"""
        # Create base poster
        poster = await self._create_base_poster(landmark_url)
        
        # Add event information
        poster = await self._add_event_info(poster, request.event_details, "general")
        
        # Add speakers grid
        poster = await self._add_speakers_grid(poster, request.speakers)
        
        # Add call-to-action
        poster = await self._add_cta(poster, request.event_details)
        
        # Save poster
        poster_url = await self._save_poster(poster, event_id, "general")
        
        return {
            "poster_type": "general",
            "url": poster_url,
            "dimensions": {"width": self.poster_width, "height": self.poster_height},
            "file_size": self._estimate_file_size(poster),
            "format": "PNG"
        }
    
    async def _generate_speaker_poster(self, request: PosterGenerationRequest, speaker: SpeakerInfo, event_id: str, landmark_url: str) -> Dict[str, Any]:
        """Generate speaker-focused poster"""
        # Create base poster
        poster = await self._create_base_poster(landmark_url)
        
        # Add event information (minimal)
        poster = await self._add_event_info(poster, request.event_details, "speaker")
        
        # Add speaker focus
        poster = await self._add_speaker_focus(poster, speaker, request.event_details)
        
        # Save poster
        poster_url = await self._save_poster(poster, event_id, "speaker", speaker.name)
        
        return {
            "poster_type": "speaker",
            "speaker_name": speaker.name,
            "url": poster_url,
            "dimensions": {"width": self.poster_width, "height": self.poster_height},
            "file_size": self._estimate_file_size(poster),
            "format": "PNG"
        }
    
    async def _generate_theme_poster(self, request: PosterGenerationRequest, event_id: str, landmark_url: str) -> Dict[str, Any]:
        """Generate theme-focused poster"""
        # Create base poster (may skip landmark for theme focus)
        use_landmark = request.event_details.theme is not None
        poster = await self._create_base_poster(landmark_url if use_landmark else None)
        
        # Add theme focus
        poster = await self._add_theme_focus(poster, request.event_details)
        
        # Add minimal event info
        poster = await self._add_event_info(poster, request.event_details, "theme")
        
        # Save poster
        poster_url = await self._save_poster(poster, event_id, "theme")
        
        return {
            "poster_type": "theme",
            "url": poster_url,
            "dimensions": {"width": self.poster_width, "height": self.poster_height},
            "file_size": self._estimate_file_size(poster),
            "format": "PNG"
        }
    
    async def _create_base_poster(self, landmark_url: Optional[str] = None) -> Image.Image:
        """Create base poster with 3-layer structure: background → overlay.png → content"""
        # Layer 1: Background/Landmark image
        poster = Image.new('RGB', (self.poster_width, self.poster_height), self.colors["background"])
        
        if landmark_url:
            # Download and add landmark background
            landmark_img = await self._download_image(landmark_url)
            landmark_img = self._resize_and_crop(landmark_img, self.poster_width, self.poster_height)
            poster.paste(landmark_img, (0, 0))
        
        # Convert to RGBA for overlay blending
        poster = poster.convert('RGBA')
        
        # Layer 2: Branding overlay (overlay.png from WordPress)
        poster = await self._add_branding_overlay(poster)
        
        # Layer 3: Content will be added by other methods (_add_event_info, etc.)
        
        return poster
    
    async def _add_branding_overlay(self, poster: Image.Image) -> Image.Image:
        """Add branding overlay from WordPress media"""
        try:
            # Search for branding overlay in WordPress media
            overlay_url = await self._search_wordpress_media("overlay")
            
            if overlay_url:
                print(f"Found branding overlay: {overlay_url}")
                
                # Download the overlay image
                overlay_img = await self._download_image(overlay_url)
                
                # Convert poster to RGBA for overlay blending
                poster_rgba = poster.convert('RGBA')
                
                # Resize overlay to match poster dimensions if needed
                if overlay_img.size != (self.poster_width, self.poster_height):
                    overlay_img = overlay_img.resize((self.poster_width, self.poster_height), Image.Resampling.LANCZOS)
                
                # Ensure overlay has alpha channel
                if overlay_img.mode != 'RGBA':
                    overlay_img = overlay_img.convert('RGBA')
                
                # Blend the overlay with the poster
                poster_rgba = Image.alpha_composite(poster_rgba, overlay_img)
                
                print("Branding overlay applied successfully")
                return poster_rgba
            else:
                print("No branding overlay found - continuing without overlay")
                return poster
                
        except Exception as e:
            print(f"Error applying branding overlay: {e}")
            return poster
    
    async def _add_event_info(self, poster: Image.Image, event_details: EventDetails, poster_type: str) -> Image.Image:
        """Add event information to poster"""
        draw = ImageDraw.Draw(poster)
        
        # Load fonts using font service
        font_service = await get_font_service()
        title_font = font_service.get_title_font(48)
        subtitle_font = font_service.get_subtitle_font(28)
        body_font = font_service.get_body_font(24)
        
        # Position calculations
        margin = 60
        y_position = margin
        
        # Title
        title_text = event_details.title
        if poster_type == "speaker":
            title_text = f"Speaker Session: {title_text}"
        elif poster_type == "theme" and event_details.theme:
            title_text = f"Theme: {event_details.theme}"
        
        title_lines = self._wrap_text(title_text, title_font, self.poster_width - 2 * margin)
        for line in title_lines:
            draw.text((margin, y_position), line, fill="white", font=title_font)
            y_position += 60
        
        y_position += 20
        
        # Date and venue
        date_str = event_details.date.strftime("%B %d, %Y at %I:%M %p")
        venue_text = f"📍 {event_details.venue}, {event_details.city}"
        
        draw.text((margin, y_position), date_str, fill="white", font=subtitle_font)
        y_position += 35
        draw.text((margin, y_position), venue_text, fill="white", font=subtitle_font)
        y_position += 50
        
        # Description (if space allows)
        if poster_type == "general" or poster_type == "theme":
            desc_text = await self._summarize_description(event_details.description, 150)
            desc_lines = self._wrap_text(desc_text, body_font, self.poster_width - 2 * margin)
            for line in desc_lines[:4]:  # Limit to 4 lines
                draw.text((margin, y_position), line, fill="white", font=body_font)
                y_position += 30
        
        return poster
    
    async def _add_speakers_grid(self, poster: Image.Image, speakers: List[SpeakerInfo]) -> Image.Image:
        """Add speakers grid to poster"""
        if not speakers:
            return poster
        
        # Calculate grid layout
        speaker_count = len(speakers)
        layout = self._calculate_speaker_layout(speaker_count)
        
        # Starting position for speakers section
        start_y = 600
        grid_width = self.poster_width - 120  # 60px margin on each side
        
        # Calculate cell dimensions
        cell_width = grid_width // layout["cols"]
        cell_height = 200
        
        for i, speaker in enumerate(speakers):
            row = i // layout["cols"]
            col = i % layout["cols"]
            
            x = 60 + col * cell_width
            y = start_y + row * cell_height
            
            # Add speaker photo and info
            await self._add_speaker_cell(poster, speaker, x, y, cell_width, cell_height)
        
        return poster
    
    async def _add_speaker_focus(self, poster: Image.Image, speaker: SpeakerInfo, event_details: EventDetails) -> Image.Image:
        """Add speaker focus to poster"""
        draw = ImageDraw.Draw(poster)
        
        # Load fonts using font service
        font_service = await get_font_service()
        name_font = font_service.get_title_font(36)
        title_font = font_service.get_subtitle_font(28)
        bio_font = font_service.get_body_font(24)
        
        # Speaker photo (large, centered)
        center_x = self.poster_width // 2
        photo_y = 400
        photo_size = 200
        
        if speaker.photo_url:
            try:
                photo = await self._download_image(speaker.photo_url)
                photo = self._resize_to_circle(photo, photo_size)
                poster.paste(photo, (center_x - photo_size // 2, photo_y), photo)
            except:
                # Draw placeholder circle
                draw.ellipse([center_x - photo_size // 2, photo_y, center_x + photo_size // 2, photo_y + photo_size], 
                           fill=self.colors["secondary"])
        
        # Speaker name
        y_pos = photo_y + photo_size + 30
        name_text = speaker.name
        name_bbox = draw.textbbox((0, 0), name_text, font=name_font)
        name_width = name_bbox[2] - name_bbox[0]
        draw.text((center_x - name_width // 2, y_pos), name_text, fill="white", font=name_font)
        
        # Speaker title and organization
        if speaker.title and speaker.organization:
            y_pos += 50
            title_text = f"{speaker.title} at {speaker.organization}"
            title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            draw.text((center_x - title_width // 2, y_pos), title_text, fill="white", font=title_font)
        
        # Speaker bio (summarized)
        if speaker.bio:
            y_pos += 60
            bio_text = await self._summarize_description(speaker.bio, 200)
            bio_lines = self._wrap_text(bio_text, bio_font, self.poster_width - 120)
            for line in bio_lines[:5]:  # Limit to 5 lines
                line_bbox = draw.textbbox((0, 0), line, font=bio_font)
                line_width = line_bbox[2] - line_bbox[0]
                draw.text((center_x - line_width // 2, y_pos), line, fill="white", font=bio_font)
                y_pos += 30
        
        return poster
    
    async def _add_theme_focus(self, poster: Image.Image, event_details: EventDetails) -> Image.Image:
        """Add theme focus to poster"""
        if not event_details.theme:
            return poster
        
        draw = ImageDraw.Draw(poster)
        
        # Load fonts using font service
        font_service = await get_font_service()
        theme_font = font_service.get_title_font(64)
        desc_font = font_service.get_subtitle_font(28)
        
        # Center the theme
        center_x = self.poster_width // 2
        center_y = self.poster_height // 2
        
        # Theme title
        theme_text = event_details.theme
        theme_bbox = draw.textbbox((0, 0), theme_text, font=theme_font)
        theme_width = theme_bbox[2] - theme_bbox[0]
        draw.text((center_x - theme_width // 2, center_y - 50), theme_text, fill="white", font=theme_font)
        
        # Theme description
        if event_details.description:
            desc_text = await self._summarize_description(event_details.description, 180)
            desc_lines = self._wrap_text(desc_text, desc_font, self.poster_width - 120)
            y_pos = center_y + 50
            for line in desc_lines[:3]:  # Limit to 3 lines
                line_bbox = draw.textbbox((0, 0), line, font=desc_font)
                line_width = line_bbox[2] - line_bbox[0]
                draw.text((center_x - line_width // 2, y_pos), line, fill="white", font=desc_font)
                y_pos += 35
        
        return poster
    
    async def _add_cta(self, poster: Image.Image, event_details: EventDetails) -> Image.Image:
        """Add call-to-action to poster"""
        draw = ImageDraw.Draw(poster)
        
        # Load font using font service
        font_service = await get_font_service()
        cta_font = font_service.get_title_font(32)
        
        # CTA text
        cta_text = "Register Now!"
        if event_details.registration_url:
            cta_text = "Visit our website to register"
        
        # Position at bottom
        cta_bbox = draw.textbbox((0, 0), cta_text, font=cta_font)
        cta_width = cta_bbox[2] - cta_bbox[0]
        center_x = self.poster_width // 2
        y_pos = self.poster_height - 100
        
        # Draw CTA background
        padding = 20
        draw.rectangle([center_x - cta_width // 2 - padding, y_pos - padding,
                       center_x + cta_width // 2 + padding, y_pos + 40 + padding],
                      fill=self.colors["accent"])
        
        # Draw CTA text
        draw.text((center_x - cta_width // 2, y_pos), cta_text, fill="white", font=cta_font)
        
        return poster
    
    def _calculate_speaker_layout(self, count: int) -> Dict[str, int]:
        """Calculate optimal grid layout for speakers"""
        if count <= 2:
            return {"rows": 1, "cols": count}
        elif count <= 4:
            return {"rows": 2, "cols": 2}
        elif count <= 6:
            return {"rows": 2, "cols": 3}
        elif count <= 9:
            return {"rows": 3, "cols": 3}
        else:
            return {"rows": 4, "cols": 3}  # Max 12 speakers
    
    async def _add_speaker_cell(self, poster: Image.Image, speaker: SpeakerInfo, x: int, y: int, width: int, height: int):
        """Add individual speaker cell to poster"""
        draw = ImageDraw.Draw(poster)
        
        # Load fonts using font service
        font_service = await get_font_service()
        name_font = font_service.get_font("title", 20)
        title_font = font_service.get_font("subtitle", 16)
        
        # Speaker photo
        photo_size = 60
        photo_x = x + width // 2 - photo_size // 2
        photo_y = y + 10
        
        # Try to get speaker photo from multiple sources
        photo_url = await self._get_speaker_photo(speaker)
        
        if photo_url:
            try:
                photo = await self._download_image(photo_url)
                photo = self._resize_to_circle(photo, photo_size)
                poster.paste(photo, (photo_x, photo_y), photo)
            except:
                # Draw placeholder circle
                draw.ellipse([photo_x, photo_y, photo_x + photo_size, photo_y + photo_size], 
                           fill=self.colors["secondary"])
        else:
            # Draw placeholder circle
            draw.ellipse([photo_x, photo_y, photo_x + photo_size, photo_y + photo_size], 
                       fill=self.colors["secondary"])
        
        # Speaker name
        name_lines = self._wrap_text(speaker.name, name_font, width - 10)
        text_y = photo_y + photo_size + 10
        for line in name_lines[:2]:  # Max 2 lines
            line_bbox = draw.textbbox((0, 0), line, font=name_font)
            line_width = line_bbox[2] - line_bbox[0]
            draw.text((x + width // 2 - line_width // 2, text_y), line, fill="white", font=name_font)
            text_y += 22
        
        # Speaker title (if space allows)
        if speaker.title and text_y < y + height - 20:
            title_lines = self._wrap_text(speaker.title, title_font, width - 10)
            for line in title_lines[:1]:  # Max 1 line
                line_bbox = draw.textbbox((0, 0), line, font=title_font)
                line_width = line_bbox[2] - line_bbox[0]
                draw.text((x + width // 2 - line_width // 2, text_y), line, fill="white", font=title_font)
                break
    
    async def _get_speaker_photo(self, speaker: SpeakerInfo) -> Optional[str]:
        """Get speaker photo from multiple sources"""
        # First priority: provided photo URL
        if speaker.photo_url:
            return speaker.photo_url
        
        # Second priority: try WordPress lookup
        try:
            wordpress_service = WordPressService()
            await wordpress_service.initialize()
            
            photo_url = await wordpress_service.get_speaker_photo(
                speaker.name, 
                speaker.linkedin_url
            )
            
            if photo_url:
                return photo_url
                
        except Exception as e:
            print(f"WordPress photo lookup failed for {speaker.name}: {e}")
        
        # No photo found
        return None
    
    async def _get_landmark_image(self, city: str, country: str) -> Optional[str]:
        """Get landmark image from WordPress media library"""
        try:
            # Search for landmark images using WordPress REST API
            # WordPress automatically organizes by date: /wp-content/uploads/YYYY/MM/filename.jpg
            
            # Search patterns for manually uploaded images
            search_terms = [
                f"{city.lower()}-{country.lower()}",
                f"{city.lower()}-{country.lower().replace(' ', '-')}",
                f"{city.lower()}",
                f"{city.replace(' ', '-').lower()}-{country.lower()}",
                f"{city.replace(' ', '').lower()}-{country.lower()}",
            ]
            
            # Use WordPress storage service to search for images
            for search_term in search_terms:
                try:
                    # Search in WordPress media using REST API
                    landmark_url = await self._search_wordpress_media(search_term)
                    if landmark_url:
                        print(f"Found landmark image for {city}, {country}: {landmark_url}")
                        return landmark_url
                except Exception as e:
                    print(f"Error searching for {search_term}: {e}")
                    continue
            
            print(f"No landmark image found for {city}, {country}")
            return None
            
        except Exception as e:
            print(f"Error getting landmark image: {e}")
            return None
    
    async def _search_wordpress_media(self, search_term: str) -> Optional[str]:
        """Search WordPress media library for images by filename"""
        try:
            import httpx
            
            # Use WordPress REST API to search media
            search_url = f"https://cmtpl.org/wp-json/wp/v2/media"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    search_url,
                    params={
                        "search": search_term,
                        "media_type": "image",
                        "per_page": 10
                    }
                )
                
                if response.status_code == 200:
                    media_items = response.json()
                    
                    for item in media_items:
                        source_url = item.get("source_url", "")
                        filename = item.get("title", {}).get("rendered", "").lower()
                        alt_text = item.get("alt_text", "").lower()
                        
                        # Check if this image matches our search criteria
                        if (search_term in source_url.lower() or 
                            search_term in filename or 
                            search_term in alt_text):
                            return source_url
                
                return None
                
        except Exception as e:
            print(f"Error searching WordPress media: {e}")
            return None
    
    async def _download_image(self, url: str) -> Image.Image:
        """Download image from URL"""
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            return Image.open(io.BytesIO(response.content))
    
    async def _download_image_data(self, url: str) -> bytes:
        """Download image data from URL"""
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content
    
    def _resize_and_crop(self, image: Image.Image, target_width: int, target_height: int) -> Image.Image:
        """Resize and crop image to fit target dimensions"""
        # Calculate aspect ratios
        img_ratio = image.width / image.height
        target_ratio = target_width / target_height
        
        if img_ratio > target_ratio:
            # Image is wider, fit to height
            new_height = target_height
            new_width = int(new_height * img_ratio)
        else:
            # Image is taller, fit to width
            new_width = target_width
            new_height = int(new_width / img_ratio)
        
        # Resize image
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Crop to target size
        left = (new_width - target_width) // 2
        top = (new_height - target_height) // 2
        right = left + target_width
        bottom = top + target_height
        
        return image.crop((left, top, right, bottom))
    
    def _resize_to_circle(self, image: Image.Image, size: int) -> Image.Image:
        """Resize image to circular format"""
        # Resize to square
        image = image.resize((size, size), Image.Resampling.LANCZOS)
        
        # Create circular mask
        mask = Image.new('L', (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse([0, 0, size, size], fill=255)
        
        # Apply mask
        output = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        output.paste(image, (0, 0))
        output.putalpha(mask)
        
        return output
    
    def _wrap_text(self, text: str, font: ImageFont.ImageFont, max_width: int) -> List[str]:
        """Wrap text to fit within max width"""
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            bbox = font.getbbox(test_line)
            if bbox[2] - bbox[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines
    
    async def _summarize_description(self, text: str, target_length: int) -> str:
        """Summarize description using AI"""
        try:
            return await self.text_processor.summarize_text(text, target_length)
        except Exception as e:
            print(f"Failed to summarize text: {e}")
            # Fallback to simple truncation
            return text[:target_length] + "..." if len(text) > target_length else text
    
    async def _save_poster(self, poster: Image.Image, event_id: str, poster_type: str, speaker_name: str = None) -> str:
        """Save poster to storage and return URL"""
        # Convert to bytes
        buffer = io.BytesIO()
        poster.save(buffer, format='PNG', optimize=True)
        buffer.seek(0)
        
        # Generate storage key
        storage_key = self.storage.generate_poster_key(event_id, poster_type, speaker_name)
        
        # Upload to storage
        return await self.storage.upload_file(storage_key, buffer.getvalue(), "image/png")
    
    def _generate_event_id(self, event_details: EventDetails) -> str:
        """Generate unique event ID"""
        event_string = f"{event_details.title}_{event_details.date}_{event_details.venue}"
        return hashlib.md5(event_string.encode()).hexdigest()[:12]
    
    def _estimate_file_size(self, poster: Image.Image) -> int:
        """Estimate file size in bytes"""
        # Rough estimation based on image dimensions and format
        return self.poster_width * self.poster_height * 3  # RGB bytes
