import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class WordPressService:
    """
    Service class for interacting with WordPress REST API.
    
    Provides methods for:
    - Searching and retrieving media files
    - Uploading new media files
    """
    
    def __init__(self):
        """Initialize the WordPress service with site credentials."""
        self.base_url = settings.WORDPRESS_URL
        self.username = settings.WORDPRESS_USERNAME
        self.password = settings.WORDPRESS_PASSWORD
        self.auth = (self.username, self.password)

    async def search_media(self, search):
        """
        Search for media files in WordPress by keyword.
        
        Args:
            search (str): Search term for media lookup
            
        Returns:
            str or None: URL of the first matching media file, or None if not found
        """
        url = f"{self.base_url}/wp-json/wp/v2/media?search={search}"
        logger.info(f"Searching WordPress media for: {search}")
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, auth=self.auth)
            resp.raise_for_status()
            results = resp.json()
            if results:
                logger.info(f"Found media: {results[0]['source_url']}")
                return results[0]["source_url"]
            logger.warning(f"No media found for: {search}")
            return None

    async def upload_media(self, file_path, filename):
        """
        Upload a media file to WordPress.
        
        Args:
            file_path (str): Local path to the file to upload
            filename (str): Desired filename for the uploaded file
            
        Returns:
            str: URL of the uploaded file
        """
        url = f"{self.base_url}/wp-json/wp/v2/media"
        headers = {"Content-Disposition": f"attachment; filename={filename}"}
        logger.info(f"Uploading poster to WordPress: {filename}")
        with open(file_path, "rb") as f:
            data = f.read()
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, content=data, auth=self.auth)
            resp.raise_for_status()
            uploaded_url = resp.json()["source_url"]
            logger.info(f"Poster uploaded to: {uploaded_url}")
            return uploaded_url
