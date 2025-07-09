import os
import hashlib
from typing import Dict, Any
from app.services.base_service import BaseStorage

class LocalStorage(BaseStorage):
    """Local file storage for development/testing"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.storage_path = "storage"
        
    async def _initialize(self):
        """Initialize local storage"""
        os.makedirs(self.storage_path, exist_ok=True)
        os.makedirs(os.path.join(self.storage_path, "cmt-landmarks"), exist_ok=True)
        os.makedirs(os.path.join(self.storage_path, "cmt-posters"), exist_ok=True)
    
    async def upload_file(self, file_path: str, content: bytes, content_type: str) -> str:
        """Save file locally and return URL"""
        full_path = os.path.join(self.storage_path, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, 'wb') as f:
            f.write(content)
        
        return f"/storage/{file_path}"
    
    async def download_file(self, file_path: str) -> bytes:
        """Download file content from local storage"""
        full_path = os.path.join(self.storage_path, file_path)
        
        if not os.path.exists(full_path):
            raise Exception(f"File not found: {file_path}")
        
        with open(full_path, 'rb') as f:
            return f.read()
    
    async def file_exists(self, file_path: str) -> bool:
        """Check if file exists locally"""
        full_path = os.path.join(self.storage_path, file_path)
        return os.path.exists(full_path)
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete file from local storage"""
        full_path = os.path.join(self.storage_path, file_path)
        
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
        return False
    
    async def get_file_url(self, file_path: str) -> str:
        """Get URL for local file"""
        return f"/storage/{file_path}"
    
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
        """Cleanup local storage resources"""
        pass
