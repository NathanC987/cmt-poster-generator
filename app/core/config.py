import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API Configuration
    API_TITLE: str = os.getenv("API_TITLE", "CMT Poster Generator")
    API_VERSION: str = os.getenv("API_VERSION", "1.0.0")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Rate Limiting
    RATE_LIMITER: str = os.getenv("RATE_LIMITER", "upstash")
    UPSTASH_REDIS_URL: str = os.getenv("UPSTASH_REDIS_URL")
    UPSTASH_REDIS_TOKEN: str = os.getenv("UPSTASH_REDIS_TOKEN")
    
    # OpenAI Configuration
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY")
    
    # WordPress Configuration
    WORDPRESS_URL: str = os.getenv("WORDPRESS_URL")
    WORDPRESS_USERNAME: str = os.getenv("WORDPRESS_USERNAME")
    WORDPRESS_PASSWORD: str = os.getenv("WORDPRESS_PASSWORD")
    
    # Font Paths
    FONT_BOLD_PATH: str = os.path.join(os.path.dirname(__file__), "..", "fonts", "GlacialIndifference-Bold.ttf")
    FONT_REGULAR_PATH: str = os.path.join(os.path.dirname(__file__), "..", "fonts", "GlacialIndifference-Regular.ttf")

settings = Settings()
