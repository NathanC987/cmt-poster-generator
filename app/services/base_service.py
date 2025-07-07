from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class BaseService(ABC):
    """Base class for all services with common functionality"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._initialized = False
    
    async def initialize(self):
        """Initialize the service"""
        if not self._initialized:
            await self._initialize()
            self._initialized = True
    
    @abstractmethod
    async def _initialize(self):
        """Service-specific initialization logic"""
        pass
    
    def is_initialized(self) -> bool:
        """Check if service is initialized"""
        return self._initialized
    
    async def cleanup(self):
        """Cleanup service resources"""
        pass

class BaseImageGenerator(BaseService):
    """Base class for image generation services"""
    
    @abstractmethod
    async def generate_landmark_image(self, city: str, country: str, style: str = "realistic") -> str:
        """Generate landmark image and return URL"""
        pass
    
    @abstractmethod
    async def get_service_status(self) -> Dict[str, Any]:
        """Get service health status"""
        pass

class BaseTextProcessor(BaseService):
    """Base class for text processing services"""
    
    @abstractmethod
    async def summarize_text(self, text: str, target_length: int, style: str = "professional") -> str:
        """Summarize text to target length"""
        pass
    
    @abstractmethod
    async def generate_poster_caption(self, event_details: Dict[str, Any], poster_type: str) -> str:
        """Generate caption for poster based on event details"""
        pass
    
    @abstractmethod
    async def get_service_status(self) -> Dict[str, Any]:
        """Get service health status"""
        pass

class BaseRateLimiter(BaseService):
    """Base class for rate limiting services"""
    
    @abstractmethod
    async def check_rate_limit(self, key: str, limit: int, window: int) -> bool:
        """Check if request is within rate limit"""
        pass
    
    @abstractmethod
    async def increment_counter(self, key: str, window: int) -> int:
        """Increment counter and return current count"""
        pass
    
    @abstractmethod
    async def get_remaining_requests(self, key: str, limit: int, window: int) -> int:
        """Get remaining requests for the key"""
        pass

class BaseStorage(BaseService):
    """Base class for storage services"""
    
    @abstractmethod
    async def upload_file(self, file_path: str, content: bytes, content_type: str) -> str:
        """Upload file and return URL"""
        pass
    
    @abstractmethod
    async def download_file(self, file_path: str) -> bytes:
        """Download file content"""
        pass
    
    @abstractmethod
    async def file_exists(self, file_path: str) -> bool:
        """Check if file exists"""
        pass
    
    @abstractmethod
    async def delete_file(self, file_path: str) -> bool:
        """Delete file"""
        pass
    
    @abstractmethod
    async def get_file_url(self, file_path: str) -> str:
        """Get public URL for file"""
        pass
