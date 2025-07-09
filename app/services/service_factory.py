from typing import Dict, Any
from config.settings import settings
from app.services.base_service import BaseImageGenerator, BaseTextProcessor, BaseRateLimiter, BaseStorage

# Service imports
from app.services.replicate_service import ReplicateImageGenerator
from app.services.azure_openai_service import AzureOpenAITextProcessor
from app.services.upstash_service import UpstashRateLimiter, MemoryRateLimiter
from app.services.wordpress_storage_service import WordPressStorage
from app.services.local_storage_service import LocalStorage

class ServiceFactory:
    """Factory class to create service instances based on configuration"""
    
    @staticmethod
    def create_image_generator(config: Dict[str, Any] = None) -> BaseImageGenerator:
        """Create image generator service based on configuration"""
        provider = settings.IMAGE_PROVIDER.lower()
        
        if provider == "replicate":
            return ReplicateImageGenerator(config)
        else:
            raise ValueError(f"Unsupported image provider: {provider}")
    
    @staticmethod
    def create_text_processor(config: Dict[str, Any] = None) -> BaseTextProcessor:
        """Create text processor service based on configuration"""
        provider = settings.TEXT_PROVIDER.lower()
        
        if provider == "azure_openai":
            return AzureOpenAITextProcessor(config)
        else:
            raise ValueError(f"Unsupported text provider: {provider}")
    
    @staticmethod
    def create_rate_limiter(config: Dict[str, Any] = None) -> BaseRateLimiter:
        """Create rate limiter service based on configuration"""
        provider = settings.RATE_LIMITER.lower()
        
        if provider == "upstash":
            return UpstashRateLimiter(config)
        elif provider == "memory":
            return MemoryRateLimiter(config)
        else:
            # Default to memory limiter for development
            return MemoryRateLimiter(config)
    
    @staticmethod
    def create_storage(config: Dict[str, Any] = None) -> BaseStorage:
        """Create storage service based on configuration"""
        provider = settings.STORAGE_PROVIDER.lower()
        
        if provider == "wordpress":
            return WordPressStorage(config)
        elif provider == "local":
            return LocalStorage(config)
        else:
            # Default to local storage for development
            return LocalStorage(config)

# Global service instances
_image_generator = None
_text_processor = None
_rate_limiter = None
_storage = None

def get_image_generator() -> BaseImageGenerator:
    """Get global image generator instance"""
    global _image_generator
    if _image_generator is None:
        _image_generator = ServiceFactory.create_image_generator()
    return _image_generator

def get_text_processor() -> BaseTextProcessor:
    """Get global text processor instance"""
    global _text_processor
    if _text_processor is None:
        _text_processor = ServiceFactory.create_text_processor()
    return _text_processor

def get_rate_limiter() -> BaseRateLimiter:
    """Get global rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = ServiceFactory.create_rate_limiter()
    return _rate_limiter

def get_storage() -> BaseStorage:
    """Get global storage instance"""
    global _storage
    if _storage is None:
        _storage = ServiceFactory.create_storage()
    return _storage

async def initialize_services():
    """Initialize all services"""
    await get_image_generator().initialize()
    await get_text_processor().initialize()
    await get_rate_limiter().initialize()
    await get_storage().initialize()

async def cleanup_services():
    """Cleanup all services"""
    global _image_generator, _text_processor, _rate_limiter, _storage
    
    if _image_generator:
        await _image_generator.cleanup()
        _image_generator = None
    
    if _text_processor:
        await _text_processor.cleanup()
        _text_processor = None
    
    if _rate_limiter:
        await _rate_limiter.cleanup()
        _rate_limiter = None
    
    if _storage:
        await _storage.cleanup()
        _storage = None

async def get_services_status() -> Dict[str, Any]:
    """Get status of all services"""
    status = {}
    
    try:
        image_gen = get_image_generator()
        status["image_generator"] = await image_gen.get_service_status()
    except Exception as e:
        status["image_generator"] = {"status": "error", "error": str(e)}
    
    try:
        text_proc = get_text_processor()
        status["text_processor"] = await text_proc.get_service_status()
    except Exception as e:
        status["text_processor"] = {"status": "error", "error": str(e)}
    
    try:
        rate_limiter = get_rate_limiter()
        status["rate_limiter"] = {
            "status": "healthy" if rate_limiter.is_initialized() else "not_initialized",
            "service": settings.RATE_LIMITER
        }
    except Exception as e:
        status["rate_limiter"] = {"status": "error", "error": str(e)}
    
    try:
        storage = get_storage()
        status["storage"] = {
            "status": "healthy" if storage.is_initialized() else "not_initialized",
            "service": settings.STORAGE_PROVIDER
        }
    except Exception as e:
        status["storage"] = {"status": "error", "error": str(e)}
    
    return status
