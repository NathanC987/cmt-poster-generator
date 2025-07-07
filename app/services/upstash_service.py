import httpx
import time
import hashlib
from typing import Dict, Any
from config.settings import settings
from app.services.base_service import BaseRateLimiter

class UpstashRateLimiter(BaseRateLimiter):
    """Upstash Redis implementation for rate limiting"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.client = None
        self.redis_url = None
        self.redis_token = None
    
    async def _initialize(self):
        """Initialize Upstash Redis client"""
        if not all([settings.UPSTASH_REDIS_URL, settings.UPSTASH_REDIS_TOKEN]):
            raise ValueError("UPSTASH_REDIS_URL and UPSTASH_REDIS_TOKEN are required")
        
        self.redis_url = settings.UPSTASH_REDIS_URL
        self.redis_token = settings.UPSTASH_REDIS_TOKEN
        
        # Create HTTP client for Upstash REST API
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {self.redis_token}",
                "Content-Type": "application/json"
            },
            timeout=30.0
        )
    
    async def check_rate_limit(self, key: str, limit: int, window: int) -> bool:
        """Check if request is within rate limit"""
        if not self.is_initialized():
            await self.initialize()
        
        try:
            current_count = await self.get_current_count(key, window)
            return current_count < limit
        except Exception as e:
            # If rate limiter fails, allow the request (fail-open)
            print(f"Rate limiter error: {e}")
            return True
    
    async def increment_counter(self, key: str, window: int) -> int:
        """Increment counter and return current count"""
        if not self.is_initialized():
            await self.initialize()
        
        try:
            # Use sliding window algorithm
            current_time = int(time.time())
            redis_key = self._generate_redis_key(key, window)
            
            # Pipeline multiple operations
            pipeline = [
                ["ZREMRANGEBYSCORE", redis_key, 0, current_time - window],
                ["ZADD", redis_key, current_time, f"{current_time}_{hash(key)}"],
                ["ZCARD", redis_key],
                ["EXPIRE", redis_key, window]
            ]
            
            # Execute pipeline
            response = await self._execute_pipeline(pipeline)
            
            # Return the count (third operation result)
            return response[2] if len(response) > 2 else 1
            
        except Exception as e:
            print(f"Error incrementing counter: {e}")
            return 1
    
    async def get_remaining_requests(self, key: str, limit: int, window: int) -> int:
        """Get remaining requests for the key"""
        if not self.is_initialized():
            await self.initialize()
        
        try:
            current_count = await self.get_current_count(key, window)
            return max(0, limit - current_count)
        except Exception as e:
            print(f"Error getting remaining requests: {e}")
            return limit
    
    async def get_current_count(self, key: str, window: int) -> int:
        """Get current count for the key"""
        try:
            current_time = int(time.time())
            redis_key = self._generate_redis_key(key, window)
            
            # Clean old entries and get count
            pipeline = [
                ["ZREMRANGEBYSCORE", redis_key, 0, current_time - window],
                ["ZCARD", redis_key]
            ]
            
            response = await self._execute_pipeline(pipeline)
            return response[1] if len(response) > 1 else 0
            
        except Exception as e:
            print(f"Error getting current count: {e}")
            return 0
    
    def _generate_redis_key(self, key: str, window: int) -> str:
        """Generate Redis key for rate limiting"""
        # Hash the key to ensure consistent length and valid characters
        key_hash = hashlib.sha256(key.encode()).hexdigest()[:12]
        return f"rate_limit:{key_hash}:{window}"
    
    async def _execute_pipeline(self, commands: list) -> list:
        """Execute multiple Redis commands as a pipeline"""
        try:
            response = await self.client.post(
                f"{self.redis_url}/pipeline",
                json=commands
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"Redis pipeline execution failed: {e}")
    
    async def _execute_command(self, command: list) -> Any:
        """Execute a single Redis command"""
        try:
            # Format command for Upstash REST API
            cmd_parts = command[0].split()
            cmd_name = cmd_parts[0]
            
            # Build URL path
            url_path = f"{self.redis_url}/{cmd_name.lower()}"
            
            # Add parameters
            if len(command) > 1:
                url_path += "/" + "/".join(str(arg) for arg in command[1:])
            
            response = await self.client.post(url_path)
            response.raise_for_status()
            
            result = response.json()
            return result.get("result") if isinstance(result, dict) else result
            
        except Exception as e:
            raise Exception(f"Redis command execution failed: {e}")
    
    async def cleanup(self):
        """Cleanup Upstash client resources"""
        if self.client:
            await self.client.aclose()
        self.client = None
        self._initialized = False

# Memory-based fallback rate limiter for development
class MemoryRateLimiter(BaseRateLimiter):
    """In-memory rate limiter for development/testing"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.counters = {}
    
    async def _initialize(self):
        """Initialize memory rate limiter"""
        self.counters = {}
    
    async def check_rate_limit(self, key: str, limit: int, window: int) -> bool:
        """Check if request is within rate limit"""
        current_count = await self.get_current_count(key, window)
        return current_count < limit
    
    async def increment_counter(self, key: str, window: int) -> int:
        """Increment counter and return current count"""
        current_time = int(time.time())
        
        if key not in self.counters:
            self.counters[key] = []
        
        # Clean old entries
        self.counters[key] = [
            timestamp for timestamp in self.counters[key]
            if timestamp > current_time - window
        ]
        
        # Add new entry
        self.counters[key].append(current_time)
        
        return len(self.counters[key])
    
    async def get_remaining_requests(self, key: str, limit: int, window: int) -> int:
        """Get remaining requests for the key"""
        current_count = await self.get_current_count(key, window)
        return max(0, limit - current_count)
    
    async def get_current_count(self, key: str, window: int) -> int:
        """Get current count for the key"""
        if key not in self.counters:
            return 0
        
        current_time = int(time.time())
        
        # Clean old entries
        self.counters[key] = [
            timestamp for timestamp in self.counters[key]
            if timestamp > current_time - window
        ]
        
        return len(self.counters[key])
    
    async def cleanup(self):
        """Cleanup memory counters"""
        self.counters = {}
        self._initialized = False
