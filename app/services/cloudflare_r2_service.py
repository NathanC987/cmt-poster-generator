import boto3
import hashlib
from typing import Dict, Any
from botocore.exceptions import ClientError
from config.settings import settings
from app.services.base_service import BaseStorage

class CloudflareR2Storage(BaseStorage):
    """Cloudflare R2 storage implementation using S3-compatible API"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.client = None
        self.bucket_name = None
    
    async def _initialize(self):
        """Initialize Cloudflare R2 client"""
        if not all([
            settings.R2_ACCESS_KEY_ID,
            settings.R2_SECRET_ACCESS_KEY,
            settings.R2_ENDPOINT,
            settings.R2_BUCKET
        ]):
            raise ValueError("R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_ENDPOINT, and R2_BUCKET are required")
        
        self.bucket_name = settings.R2_BUCKET
        
        # Initialize S3 client for R2
        self.client = boto3.client(
            's3',
            endpoint_url=settings.R2_ENDPOINT,
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            region_name='auto'  # R2 uses 'auto' as region
        )
    
    async def upload_file(self, file_path: str, content: bytes, content_type: str) -> str:
        """Upload file to Cloudflare R2 and return URL"""
        if not self.is_initialized():
            await self.initialize()
        
        try:
            # Upload file to R2
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=file_path,
                Body=content,
                ContentType=content_type,
                ACL='public-read'  # Make file publicly accessible
            )
            
            # Return public URL
            return await self.get_file_url(file_path)
            
        except ClientError as e:
            raise Exception(f"Failed to upload file to R2: {str(e)}")
    
    async def download_file(self, file_path: str) -> bytes:
        """Download file content from Cloudflare R2"""
        if not self.is_initialized():
            await self.initialize()
        
        try:
            response = self.client.get_object(
                Bucket=self.bucket_name,
                Key=file_path
            )
            
            return response['Body'].read()
            
        except ClientError as e:
            raise Exception(f"Failed to download file from R2: {str(e)}")
    
    async def file_exists(self, file_path: str) -> bool:
        """Check if file exists in Cloudflare R2"""
        if not self.is_initialized():
            await self.initialize()
        
        try:
            self.client.head_object(
                Bucket=self.bucket_name,
                Key=file_path
            )
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            raise Exception(f"Error checking file existence: {str(e)}")
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete file from Cloudflare R2"""
        if not self.is_initialized():
            await self.initialize()
        
        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=file_path
            )
            return True
            
        except ClientError as e:
            raise Exception(f"Failed to delete file from R2: {str(e)}")
    
    async def get_file_url(self, file_path: str) -> str:
        """Get public URL for file in Cloudflare R2"""
        # For R2, construct the public URL directly
        # Format: https://bucket-name.account-id.r2.cloudflarestorage.com/file-path
        base_url = settings.R2_ENDPOINT.replace('https://', '')
        return f"https://{self.bucket_name}.{base_url}/{file_path}"
    
    def generate_cache_key(self, city: str, country: str, style: str = "realistic") -> str:
        """Generate cache key for landmark images"""
        # Create consistent hash for caching
        cache_string = f"{city.lower()}_{country.lower()}_{style.lower()}"
        hash_key = hashlib.md5(cache_string.encode()).hexdigest()
        return f"landmarks/{hash_key}.png"
    
    def generate_poster_key(self, event_id: str, poster_type: str, speaker_name: str = None) -> str:
        """Generate key for poster storage"""
        if speaker_name:
            # Speaker-specific poster
            speaker_hash = hashlib.md5(speaker_name.encode()).hexdigest()[:8]
            return f"posters/{event_id}/{poster_type}_{speaker_hash}.png"
        else:
            # General or theme poster
            return f"posters/{event_id}/{poster_type}.png"
    
    async def cleanup(self):
        """Cleanup R2 client resources"""
        # boto3 clients don't need explicit cleanup
        self.client = None
        self._initialized = False

# Local storage fallback for development
class LocalStorage(BaseStorage):
    """Local file storage for development/testing"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.storage_path = "storage"
        import os
        os.makedirs(self.storage_path, exist_ok=True)
    
    async def _initialize(self):
        """Initialize local storage"""
        import os
        os.makedirs(self.storage_path, exist_ok=True)
    
    async def upload_file(self, file_path: str, content: bytes, content_type: str) -> str:
        """Save file locally and return URL"""
        import os
        
        full_path = os.path.join(self.storage_path, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, 'wb') as f:
            f.write(content)
        
        return f"/storage/{file_path}"
    
    async def download_file(self, file_path: str) -> bytes:
        """Download file content from local storage"""
        import os
        
        full_path = os.path.join(self.storage_path, file_path)
        
        if not os.path.exists(full_path):
            raise Exception(f"File not found: {file_path}")
        
        with open(full_path, 'rb') as f:
            return f.read()
    
    async def file_exists(self, file_path: str) -> bool:
        """Check if file exists locally"""
        import os
        full_path = os.path.join(self.storage_path, file_path)
        return os.path.exists(full_path)
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete file from local storage"""
        import os
        
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
        return f"landmarks/{hash_key}.png"
    
    def generate_poster_key(self, event_id: str, poster_type: str, speaker_name: str = None) -> str:
        """Generate key for poster storage"""
        if speaker_name:
            speaker_hash = hashlib.md5(speaker_name.encode()).hexdigest()[:8]
            return f"posters/{event_id}/{poster_type}_{speaker_hash}.png"
        else:
            return f"posters/{event_id}/{poster_type}.png"
    
    async def cleanup(self):
        """Cleanup local storage resources"""
        pass
