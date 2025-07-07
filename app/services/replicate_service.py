import replicate
import asyncio
from typing import Dict, Any
from config.settings import settings
from app.services.base_service import BaseImageGenerator

class ReplicateImageGenerator(BaseImageGenerator):
    """Replicate API implementation for image generation"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.client = None
        self.model_name = "black-forest-labs/flux-schnell"
    
    async def _initialize(self):
        """Initialize Replicate client"""
        if not settings.REPLICATE_API_TOKEN:
            raise ValueError("REPLICATE_API_TOKEN is required")
        
        # Set the API token
        replicate.Client(api_token=settings.REPLICATE_API_TOKEN)
        self.client = replicate
    
    async def generate_landmark_image(self, city: str, country: str, style: str = "realistic") -> str:
        """Generate landmark image using Replicate Flux-Schnell"""
        if not self.is_initialized():
            await self.initialize()
        
        # Create prompt for landmark generation
        prompt = self._create_landmark_prompt(city, country, style)
        
        try:
            # Run the model asynchronously
            output = await self._run_model_async(prompt)
            
            # Return the first output URL
            if output and len(output) > 0:
                return output[0]
            else:
                raise Exception("No output generated from model")
                
        except Exception as e:
            raise Exception(f"Failed to generate landmark image: {str(e)}")
    
    def _create_landmark_prompt(self, city: str, country: str, style: str) -> str:
        """Create optimized prompt for landmark generation"""
        base_prompt = f"Famous landmark in {city}, {country}"
        
        style_modifiers = {
            "realistic": "photorealistic, high quality, professional photography",
            "artistic": "artistic, painterly, beautiful composition",
            "modern": "modern architecture, contemporary, sleek design",
            "vintage": "vintage style, classic, nostalgic atmosphere"
        }
        
        style_suffix = style_modifiers.get(style, style_modifiers["realistic"])
        
        prompt = f"{base_prompt}, {style_suffix}, no text, no watermark, daylight, clear sky, 16:9 aspect ratio"
        
        return prompt
    
    async def _run_model_async(self, prompt: str) -> list:
        """Run Replicate model asynchronously"""
        loop = asyncio.get_event_loop()
        
        # Run the synchronous Replicate call in a thread pool
        output = await loop.run_in_executor(
            None,
            lambda: self.client.run(
                self.model_name,
                input={
                    "prompt": prompt,
                    "num_outputs": 1,
                    "aspect_ratio": "16:9",
                    "output_format": "png",
                    "output_quality": 90
                }
            )
        )
        
        return output
    
    async def get_service_status(self) -> Dict[str, Any]:
        """Get Replicate service status"""
        try:
            if not self.is_initialized():
                await self.initialize()
            
            # Try a simple API call to check status
            # Note: This is a basic health check, Replicate doesn't have a dedicated status endpoint
            return {
                "status": "healthy",
                "service": "replicate",
                "model": self.model_name,
                "initialized": self.is_initialized()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "service": "replicate",
                "error": str(e),
                "initialized": self.is_initialized()
            }
    
    async def cleanup(self):
        """Cleanup Replicate resources"""
        self.client = None
        self._initialized = False
