import httpx
import base64
import asyncio
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
        self.session_cookies = None
        self.is_authenticated = False
    
    async def _initialize(self):
        """Initialize WordPress client"""
        if not settings.WORDPRESS_URL:
            raise ValueError("WORDPRESS_URL is required for WordPress integration")
        
        self.base_url = settings.WORDPRESS_URL.rstrip('/')
        
        # Create HTTP client with persistent cookies
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True
        )
        
        # Attempt authentication if credentials are provided
        if settings.WORDPRESS_USERNAME and settings.WORDPRESS_PASSWORD:
            await self._authenticate_session()
    
    async def _authenticate_session(self) -> bool:
        """Authenticate with WordPress using session login"""
        try:
            # Step 1: Get login page to obtain nonce and cookies
            login_url = f"{self.base_url}/wp-login.php"
            response = await self.client.get(login_url)
            response.raise_for_status()
            
            # Extract nonce from login form (if present)
            nonce = None
            if 'name="_wpnonce"' in response.text:
                import re
                nonce_match = re.search(r'name="_wpnonce"[^>]*value="([^"]*)"', response.text)
                if nonce_match:
                    nonce = nonce_match.group(1)
            
            # Step 2: Submit login credentials
            login_data = {
                "log": settings.WORDPRESS_USERNAME,
                "pwd": settings.WORDPRESS_PASSWORD,
                "wp-submit": "Log In",
                "redirect_to": f"{self.base_url}/wp-admin/",
                "testcookie": "1"
            }
            
            if nonce:
                login_data["_wpnonce"] = nonce
            
            response = await self.client.post(
                login_url,
                data=login_data,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Referer": login_url
                }
            )
            
            # Check if login was successful
            if response.status_code == 200 and "wp-admin" in str(response.url):
                self.is_authenticated = True
                print("WordPress authentication successful")
                return True
            else:
                print(f"WordPress authentication failed: Status {response.status_code}")
                return False
                
        except Exception as e:
            print(f"WordPress authentication error: {e}")
            return False
    
    async def get_authenticated_photo_url(self, photo_path: str) -> Optional[str]:
        """Get photo URL for protected content that requires authentication"""
        if not self.is_authenticated:
            print("Not authenticated - cannot access protected content")
            return None
        
        try:
            # Construct full URL for the photo
            if photo_path.startswith('http'):
                photo_url = photo_path
            else:
                photo_url = f"{self.base_url}/{photo_path.lstrip('/')}"
            
            # Test if the photo is accessible
            response = await self.client.head(photo_url)
            
            if response.status_code == 200:
                return photo_url
            else:
                print(f"Photo not accessible: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error accessing authenticated photo: {e}")
            return None
    
    async def get_speaker_photo(self, speaker_name: str, linkedin_url: Optional[str] = None) -> Optional[str]:
        """Get speaker photo URL from WordPress"""
        if not self.is_initialized():
            await self.initialize()
        
        try:
            # Method 1: Try direct URL pattern if known
            photo_url = await self._try_direct_photo_url(speaker_name)
            if photo_url:
                return photo_url
            
            # Method 2: Search by name in posts/pages
            photo_url = await self._search_speaker_by_name(speaker_name)
            if photo_url:
                return photo_url
            
            # Method 3: Try LinkedIn URL search
            if linkedin_url:
                photo_url = await self._search_speaker_by_linkedin(linkedin_url)
                if photo_url:
                    return photo_url
            
            # Method 4: Try authenticated access if available
            if self.is_authenticated:
                photo_url = await self._try_authenticated_speaker_search(speaker_name)
                if photo_url:
                    return photo_url
            
            return None
            
        except Exception as e:
            print(f"WordPress speaker search failed: {e}")
            return None
    
    async def _try_direct_photo_url(self, speaker_name: str) -> Optional[str]:
        """Try direct photo URL patterns (customize for CMT site structure)"""
        try:
            # Common WordPress photo URL patterns
            name_slug = speaker_name.lower().replace(' ', '-').replace('.', '')
            
            potential_urls = [
                f"{self.base_url}/wp-content/uploads/speakers/{name_slug}.jpg",
                f"{self.base_url}/wp-content/uploads/speakers/{name_slug}.png",
                f"{self.base_url}/wp-content/uploads/{name_slug}.jpg",
                f"{self.base_url}/wp-content/uploads/{name_slug}.png",
                f"{self.base_url}/wp-content/uploads/speaker-photos/{name_slug}.jpg",
                f"{self.base_url}/wp-content/uploads/speaker-photos/{name_slug}.png",
            ]
            
            # Test each potential URL
            for url in potential_urls:
                try:
                    response = await self.client.head(url)
                    if response.status_code == 200:
                        print(f"Found direct speaker photo: {url}")
                        return url
                except:
                    continue
            
            return None
            
        except Exception as e:
            print(f"Error trying direct photo URLs: {e}")
            return None
    
    async def _try_authenticated_speaker_search(self, speaker_name: str) -> Optional[str]:
        """Try authenticated search for speaker photos in admin area"""
        if not self.is_authenticated:
            return None
        
        try:
            # Search in media library for speaker photos
            media_search_url = f"{self.base_url}/wp-admin/upload.php"
            response = await self.client.get(
                media_search_url,
                params={"s": speaker_name}
            )
            
            if response.status_code == 200:
                # Parse response for image URLs (basic implementation)
                import re
                img_pattern = r'<img[^>]+src="([^"]*)"[^>]*>'
                matches = re.findall(img_pattern, response.text)
                
                # Look for images that might be speaker photos
                for img_url in matches:
                    if any(keyword in img_url.lower() for keyword in ['speaker', 'photo', 'portrait']):
                        return img_url
            
            return None
            
        except Exception as e:
            print(f"Error in authenticated speaker search: {e}")
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
