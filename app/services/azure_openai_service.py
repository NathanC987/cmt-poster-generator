import openai
import asyncio
from typing import Dict, Any
from config.settings import settings
from app.services.base_service import BaseTextProcessor

class AzureOpenAITextProcessor(BaseTextProcessor):
    """Azure OpenAI implementation for text processing"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.client = None
    
    async def _initialize(self):
        """Initialize Azure OpenAI client"""
        if not all([settings.AZURE_OPENAI_ENDPOINT, settings.AZURE_OPENAI_API_KEY]):
            raise ValueError("AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY are required")
        
        self.client = openai.AsyncAzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version="2024-02-01",
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
        )
    
    async def summarize_text(self, text: str, target_length: int, style: str = "professional") -> str:
        """Summarize text to target length using Azure OpenAI"""
        if not self.is_initialized():
            await self.initialize()
        
        prompt = self._create_summary_prompt(text, target_length, style)
        
        try:
            response = await self.client.chat.completions.create(
                model=settings.AZURE_OPENAI_DEPLOYMENT,
                messages=[
                    {"role": "system", "content": "You are a professional content editor specializing in event marketing copy."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=target_length + 50,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            raise Exception(f"Failed to summarize text: {str(e)}")
    
    async def extract_speaker_credentials(self, speaker_bio: str, prompt_override: str = None) -> (str, str, str):
        """Extract speaker credentials (name, designation/title, organization) using Azure OpenAI"""
        if not self.is_initialized():
            await self.initialize()
        
        prompt = prompt_override or (
            "From the following speaker bio, extract only the speaker's full name, designation/title, and organization in this format (each on a new line):\n\n"
            "[Speaker Name]\n[Designation/Title]\n[Organization]\n\n"
            f"Bio:\n{speaker_bio}\n\nOutput:"
        )
        
        try:
            response = await self.client.chat.completions.create(
                model=settings.AZURE_OPENAI_DEPLOYMENT,
                messages=[
                    {"role": "system", "content": "You are a professional assistant for event marketing posters."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.1
            )
            lines = response.choices[0].message.content.strip().splitlines()
            name = lines[0].strip() if len(lines) > 0 else ""
            title = lines[1].strip() if len(lines) > 1 else ""
            org = lines[2].strip() if len(lines) > 2 else ""
            return name, title, org
        except Exception as e:
            raise Exception(f"Failed to extract speaker credentials: {str(e)}")
    
    def _create_summary_prompt(self, text: str, target_length: int, style: str) -> str:
        """Create improved prompt for event description summarization"""
        prompt = (
            f"Summarize the following event description for a poster. "
            f"Focus on what the event is about and why it is being held. "
            f"Do NOT include the date, time, venue, speaker names, or LinkedIn links. "
            f"The summary should be concise, engaging, and suitable for a poster. "
            f"Target length: {target_length} characters.\n\n"
            f"Description:\n{text}\n\nSummary:"
        )
        return prompt
    
    def _create_caption_prompt(self, event_details: Dict[str, Any], poster_type: str) -> str:
        """Create prompt for poster caption generation"""
        caption_styles = {
            "general": "comprehensive overview emphasizing all speakers and key event details",
            "speaker": "focused on individual speaker expertise and what attendees will learn",
            "theme": "emphasizing the event theme and overall value proposition"
        }
        
        style_instruction = caption_styles.get(poster_type, caption_styles["general"])
        
        prompt = f"""
        Create a compelling poster caption for a {poster_type} poster with the following event details:
        
        Event: {event_details.get('title', 'N/A')}
        Date: {event_details.get('date', 'N/A')}
        Venue: {event_details.get('venue', 'N/A')}
        City: {event_details.get('city', 'N/A')}
        Theme: {event_details.get('theme', 'N/A')}
        Description: {event_details.get('description', 'N/A')}
        
        Requirements:
        - Focus on {style_instruction}
        - Keep it concise and engaging (50-100 words)
        - Include a call-to-action
        - Use professional, enthusiastic tone
        - Highlight key value propositions
        
        Caption:
        """
        
        return prompt
    
    async def get_service_status(self) -> Dict[str, Any]:
        """Get Azure OpenAI service status"""
        try:
            if not self.is_initialized():
                await self.initialize()
            
            # Test with a simple completion
            response = await self.client.chat.completions.create(
                model=settings.AZURE_OPENAI_DEPLOYMENT,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            
            return {
                "status": "healthy",
                "service": "azure_openai",
                "model": settings.AZURE_OPENAI_DEPLOYMENT,
                "initialized": self.is_initialized()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "service": "azure_openai",
                "error": str(e),
                "initialized": self.is_initialized()
            }
    
    async def cleanup(self):
        """Cleanup Azure OpenAI resources"""
        if self.client:
            await self.client.close()
        self.client = None
        self._initialized = False
