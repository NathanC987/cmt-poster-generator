import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API Configuration
    API_TITLE: str = "CMT Poster Generator"
    API_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Image Generation
    IMAGE_PROVIDER: str = "replicate"
    REPLICATE_API_TOKEN: Optional[str] = None
    
    # Text Processing
    TEXT_PROVIDER: str = "azure_openai"
    AZURE_OPENAI_ENDPOINT: Optional[str] = None
    AZURE_OPENAI_API_KEY: Optional[str] = None
    AZURE_OPENAI_DEPLOYMENT: str = "gpt-4"
    
    # Rate Limiting
    RATE_LIMITER: str = "upstash"
    UPSTASH_REDIS_URL: Optional[str] = None
    UPSTASH_REDIS_TOKEN: Optional[str] = None
    
    # Storage
    STORAGE_PROVIDER: str = "wordpress"
    
    # WordPress Integration (for speaker photos)
    WORDPRESS_URL: Optional[str] = None
    WORDPRESS_USERNAME: Optional[str] = None
    WORDPRESS_PASSWORD: Optional[str] = None
    
    # Poster Configuration
    POSTER_WIDTH: int = 1200
    POSTER_HEIGHT: int = 1600
    POSTER_FORMAT: str = "PNG"
    POSTER_QUALITY: int = 95
    
    # Font Configuration
    POSTER_FONT_FAMILY: str = "Glacial Indifference"
    
    # Rate Limiting Settings
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600  # 1 hour
    
    # AI Model Configuration
    AZURE_OPENAI_TEMPERATURE: float = 0.7
    AZURE_OPENAI_MAX_TOKENS: int = 150
    
    # Image Processing
    SPEAKER_PHOTO_CACHE_DURATION: int = 86400  # 24 hours
    LANDMARK_SEARCH_TIMEOUT: int = 30  # seconds
    
    # WordPress Media
    WORDPRESS_MEDIA_TIMEOUT: int = 60  # seconds for uploads
    WORDPRESS_SEARCH_LIMIT: int = 50  # max items to search
    
    # Performance Settings
    REQUEST_TIMEOUT: int = 25  # seconds
    IMAGE_DOWNLOAD_TIMEOUT: int = 10  # seconds
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Global settings instance
settings = Settings()
