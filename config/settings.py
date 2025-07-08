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
    STORAGE_PROVIDER: str = "cloudflare_r2"
    R2_BUCKET: Optional[str] = None
    R2_ACCESS_KEY_ID: Optional[str] = None
    R2_SECRET_ACCESS_KEY: Optional[str] = None
    R2_ENDPOINT: Optional[str] = None
    
    # WordPress Integration (for speaker photos)
    WORDPRESS_URL: Optional[str] = None
    WORDPRESS_USERNAME: Optional[str] = None
    WORDPRESS_PASSWORD: Optional[str] = None
    
    # Poster Configuration
    POSTER_WIDTH: int = 1200
    POSTER_HEIGHT: int = 1600
    POSTER_FORMAT: str = "PNG"
    POSTER_QUALITY: int = 95
    
    # Caching
    CACHE_EXPIRY_HOURS: int = 24
    LANDMARK_CACHE_EXPIRY_DAYS: int = 30
    
    # Rate Limiting Settings
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600  # 1 hour
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Global settings instance
settings = Settings()
