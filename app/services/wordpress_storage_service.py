import httpx
import base64
import hashlib
import io
from typing import Optional, Dict, Any
from config.settings import settings
from app.services.base_service import BaseStorage

class WordPressStorage(BaseStorage):
    """WordPress media storage implementation for landmarks, branding, and posters"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.client = None
        self.base_url = None
        self.is_authenticated = False
    
    async def _initialize(self):
        """Initialize WordPress storage client (REST API only, no session login needed)"""
        if not settings.WORDPRESS_URL:
            raise ValueError("WORDPRESS_URL is required for WordPress storage")
        
        self.base_url = settings.WORDPRESS_URL.rstrip('/')
        
        # Create HTTP client for REST API usage only
        self.client = httpx.AsyncClient(
            timeout=60.0,  # Longer timeout for media uploads
            follow_redirects=True
        )
        # No session authentication needed for REST API uploads
    
    async def _authenticate_session(self) -> bool:
        """Authenticate with WordPress using session login"""
        try:
            # Get login page to obtain nonce and cookies
            login_url = f"{self.base_url}/wp-login.php"
            response = await self.client.get(login_url)
            response.raise_for_status()
            
            # Extract nonce from login form
            nonce = None
            if 'name="_wpnonce"' in response.text:
                import re
                nonce_match = re.search(r'name="_wpnonce"[^>]*value="([^"]*)"', response.text)
                if nonce_match:
                    nonce = nonce_match.group(1)
            
            # Submit login credentials
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
                print("WordPress storage authentication successful")
                return True
            else:
                print(f"WordPress storage authentication failed: Status {response.status_code}")
                return False
                
        except Exception as e:
            print(f"WordPress storage authentication error: {e}")
            return False
    
    async def upload_file(self, file_path: str, content: bytes, content_type: str) -> str:
        """
        Upload file to WordPress media library using Basic Auth and REST API.
        This matches the working curl command for WordPress.com.
        """

        # Use REST API endpoint directly, with Basic Auth and correct headers
        filename = file_path.split('/')[-1]
        upload_url = f"{self.base_url}/wp-json/wp/v2/media"

        # Prepare Basic Auth header
        user = settings.WORDPRESS_USERNAME
        password = settings.WORDPRESS_PASSWORD
        userpass = f"{user}:{password}"
        basic_auth = base64.b64encode(userpass.encode()).decode()

        headers = {
            "Authorization": f"Basic {basic_auth}",
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": content_type,
            "User-Agent": "CMTPosterBot/1.0"
        }

        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            response = await client.post(
                upload_url,
                headers=headers,
                content=content
            )
            if response.status_code in (200, 201):
                json_resp = response.json()
                media_url = json_resp.get("source_url")
                print(f"Successfully uploaded to WordPress: {media_url}")
                return media_url
            else:
                text = response.text
                print(f"WordPress upload failed: {response.status_code} {text}")
                raise Exception(f"WordPress upload failed: {response.status_code} {text}")
    
    async def _get_media_url_by_id(self, media_id: str) -> Optional[str]:
        """Get media URL by ID using REST API"""
        try:
            response = await self.client.get(f"{self.base_url}/wp-json/wp/v2/media/{media_id}")
            if response.status_code == 200:
                media_data = response.json()
                return media_data.get("source_url")
        except:
            pass
        return None
    
    async def download_file(self, file_path: str) -> bytes:
        """Download file content from WordPress media"""
        try:
            # file_path should be a full URL for WordPress media
            response = await self.client.get(file_path)
            response.raise_for_status()
            return response.content
        except Exception as e:
            raise Exception(f"Failed to download from WordPress media: {str(e)}")
    
    async def file_exists(self, file_path: str) -> bool:
        """Check if file exists in WordPress media library"""
        try:
            # Search for media by filename
            filename = file_path.split('/')[-1].split('.')[0]  # Remove extension
            response = await self.client.get(
                f"{self.base_url}/wp-json/wp/v2/media",
                params={
                    "search": filename,
                    "per_page": 10
                }
            )
            
            if response.status_code == 200:
                media_items = response.json()
                for item in media_items:
                    # Check if the file matches our expected path pattern
                    source_url = item.get("source_url", "")
                    if filename in source_url:
                        return True
            
            return False
            
        except Exception as e:
            print(f"Error checking file existence: {e}")
            return False
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete file from WordPress media library"""
        if not self.is_authenticated:
            return False
        
        try:
            # Search for media item first
            filename = file_path.split('/')[-1].split('.')[0]
            response = await self.client.get(
                f"{self.base_url}/wp-json/wp/v2/media",
                params={
                    "search": filename,
                    "per_page": 1
                }
            )
            
            if response.status_code == 200:
                media_items = response.json()
                if media_items:
                    media_id = media_items[0]["id"]
                    
                    # Delete the media item
                    delete_response = await self.client.delete(
                        f"{self.base_url}/wp-json/wp/v2/media/{media_id}",
                        params={"force": True}
                    )
                    
                    return delete_response.status_code == 200
            
            return False
            
        except Exception as e:
            print(f"Error deleting file: {e}")
            return False
    
    async def get_file_url(self, file_path: str) -> str:
        """Get public URL for file in WordPress media"""
        try:
            # Search for the media file
            filename = file_path.split('/')[-1].split('.')[0]
            response = await self.client.get(
                f"{self.base_url}/wp-json/wp/v2/media",
                params={
                    "search": filename,
                    "per_page": 1
                }
            )
            
            if response.status_code == 200:
                media_items = response.json()
                if media_items:
                    return media_items[0]["source_url"]
            
            # If not found, return constructed URL
            return f"{self.base_url}/wp-content/uploads/{file_path}"
            
        except Exception as e:
            print(f"Error getting file URL: {e}")
            return f"{self.base_url}/wp-content/uploads/{file_path}"
    
    def generate_cache_key(self, city: str, country: str, style: str = "realistic") -> str:
        """Generate cache key for landmark images"""
        cache_string = f"{city.lower()}_{country.lower()}_{style.lower()}"
        hash_key = hashlib.md5(cache_string.encode()).hexdigest()
        return f"cmt-landmarks/{hash_key}.png"
    
    def generate_poster_key(self, event_id: str, poster_type: str, speaker_name: str = None) -> str:
        """Generate key for poster storage"""
        if speaker_name:
            speaker_hash = hashlib.md5(speaker_name.encode()).hexdigest()[:8]
            return f"cmt-posters/{event_id}/{poster_type}_{speaker_hash}.png"
        else:
            return f"cmt-posters/{event_id}/{poster_type}.png"
    
    async def cleanup(self):
        """Cleanup WordPress storage client"""
        if self.client:
            await self.client.aclose()
        self.client = None
        self._initialized = False
