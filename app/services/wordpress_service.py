import httpx
import base64
from typing import Optional, Dict, Any
from config.settings import settings
from app.services.base_service import BaseService

class WordPressService(BaseService):
    """WordPress integration for fetching speaker photos and data"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.client = None
        self.base_url = None
        self.auth_header = None
    
    async def _initialize(self):
        """Initialize WordPress client"""
        if not settings.WORDPRESS_URL:
            raise ValueError("WORDPRESS_URL is required for WordPress integration")
        
        self.base_url = settings.WORDPRESS_URL.rstrip('/')
        
        # Setup authentication if credentials provided
        if settings.WORDPRESS_USERNAME and settings.WORDPRESS_PASSWORD:
            credentials = f"{settings.WORDPRESS_USERNAME}:{settings.WORDPRESS_PASSWORD}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            self.auth_header = f"Basic {encoded_credentials}"
        
        # Create HTTP client
        headers = {"Content-Type": "application/json"}
        if self.auth_header:
            headers["Authorization"] = self.auth_header
            
        self.client = httpx.AsyncClient(
            headers=headers,
            timeout=30.0
        )
    
    async def get_speaker_photo(self, speaker_name: str, linkedin_url: Optional[str] = None) -> Optional[str]:
        """Get speaker photo URL from WordPress"""
        if not self.is_initialized():
            await self.initialize()
        
        try:
            # First try to find by name in posts/pages
            photo_url = await self._search_speaker_by_name(speaker_name)
            
            if not photo_url and linkedin_url:
                # Try to find by LinkedIn URL
                photo_url = await self._search_speaker_by_linkedin(linkedin_url)
            
            return photo_url
            
        except Exception as e:
            print(f"WordPress speaker search failed: {e}")
            return None
    
    async def _search_speaker_by_name(self, speaker_name: str) -> Optional[str]:
        """Search for speaker by name in WordPress"""
        try:
            # Search in posts
            response = await self.client.get(
                f"{self.base_url}/wp-json/wp/v2/posts",
                params={
                    "search": speaker_name,
                    "per_page": 5,
                    "_embed": True
                }
            )
            response.raise_for_status()
            posts = response.json()
            
            # Look for featured image in posts
            for post in posts:
                photo_url = self._extract_featured_image(post)
                if photo_url:
                    return photo_url
            
            # Search in pages if not found in posts
            response = await self.client.get(
                f"{self.base_url}/wp-json/wp/v2/pages",
                params={
                    "search": speaker_name,
                    "per_page": 5,
                    "_embed": True
                }
            )
            response.raise_for_status()
            pages = response.json()
            
            for page in pages:
                photo_url = self._extract_featured_image(page)
                if photo_url:
                    return photo_url
            
            return None
            
        except Exception as e:
            print(f"Error searching WordPress by name: {e}")
            return None
    
    async def _search_speaker_by_linkedin(self, linkedin_url: str) -> Optional[str]:
        """Search for speaker by LinkedIn URL"""
        try:
            # Extract LinkedIn username from URL
            linkedin_username = linkedin_url.split("/in/")[-1].strip("/")
            
            # Search posts/pages for LinkedIn username
            response = await self.client.get(
                f"{self.base_url}/wp-json/wp/v2/posts",
                params={
                    "search": linkedin_username,
                    "per_page": 10,
                    "_embed": True
                }
            )
            response.raise_for_status()
            posts = response.json()
            
            for post in posts:
                # Check if LinkedIn URL is mentioned in content or meta
                if linkedin_username.lower() in post.get("content", {}).get("rendered", "").lower():
                    photo_url = self._extract_featured_image(post)
                    if photo_url:
                        return photo_url
            
            return None
            
        except Exception as e:
            print(f"Error searching WordPress by LinkedIn: {e}")
            return None
    
    def _extract_featured_image(self, post_data: Dict) -> Optional[str]:
        """Extract featured image URL from WordPress post/page data"""
        try:
            # Try to get from _embedded data first
            if "_embedded" in post_data and "wp:featuredmedia" in post_data["_embedded"]:
                media = post_data["_embedded"]["wp:featuredmedia"][0]
                if "source_url" in media:
                    return media["source_url"]
                elif "media_details" in media and "sizes" in media["media_details"]:
                    sizes = media["media_details"]["sizes"]
                    # Prefer medium or full size
                    if "medium" in sizes:
                        return sizes["medium"]["source_url"]
                    elif "full" in sizes:
                        return sizes["full"]["source_url"]
            
            # Fallback: try to get featured media ID and fetch separately
            if "featured_media" in post_data and post_data["featured_media"]:
                media_id = post_data["featured_media"]
                return asyncio.create_task(self._get_media_url(media_id))
            
            return None
            
        except Exception as e:
            print(f"Error extracting featured image: {e}")
            return None
    
    async def _get_media_url(self, media_id: int) -> Optional[str]:
        """Get media URL by media ID"""
        try:
            response = await self.client.get(
                f"{self.base_url}/wp-json/wp/v2/media/{media_id}"
            )
            response.raise_for_status()
            media_data = response.json()
            
            return media_data.get("source_url")
            
        except Exception as e:
            print(f"Error fetching media by ID: {e}")
            return None
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test WordPress connection"""
        if not self.is_initialized():
            await self.initialize()
        
        try:
            response = await self.client.get(f"{self.base_url}/wp-json/wp/v2")
            response.raise_for_status()
            
            return {
                "status": "connected",
                "wordpress_url": self.base_url,
                "authenticated": self.auth_header is not None
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "wordpress_url": self.base_url
            }
    
    async def cleanup(self):
        """Cleanup WordPress client"""
        if self.client:
            await self.client.aclose()
        self.client = None
        self._initialized = False
