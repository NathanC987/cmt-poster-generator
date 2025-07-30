import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        self.endpoint = settings.AZURE_OPENAI_ENDPOINT
        self.api_key = settings.AZURE_OPENAI_API_KEY

    async def ask(self, prompt, system=None):
        headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key
        }
        data = {
            "messages": [
                {"role": "system", "content": system or "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        }
        logger.info(f"Calling OpenAI API with prompt: {prompt[:100]}...")
        async with httpx.AsyncClient() as client:
            resp = await client.post(self.endpoint, json=data, headers=headers)
            resp.raise_for_status()
            result = resp.json()["choices"][0]["message"]["content"]
            logger.info(f"OpenAI API response: {result[:100]}...")
            return result

    async def get_landmark_slug(self, venue):
        prompt = f"Given the venue '{venue}', return the city and country in the format 'city-country' (lowercase, hyphens, no spaces) for image lookup. Only output the slug."
        return (await self.ask(prompt)).strip()

    async def format_event_details(self, date, time, venue):
        prompt = f"Format the following date, time, and venue for a poster. Output as: Date: ..., Time: ..., Venue: ...\nDate: {date}\nTime: {time}\nVenue: {venue}"
        return (await self.ask(prompt)).strip()

    async def summarize_description(self, description):
        prompt = (
            "Summarize the following event description for a poster. "
            "Exclude date, time, venue, and links. Focus on what the meeting/event is and why it is important. "
            "The summary must be concise, not more than 35 words, and should fit in 3 to 4 lines.\n\n"
            f"{description}"
        )
        return (await self.ask(prompt)).strip()

    async def extract_speakers_and_credentials(self, speakers_text):
        prompt = (
            "From the following text, extract the list of speakers and generate a short credential for each, suitable for a poster. "
            "For each speaker, only output their name and their main designation/role and organization, nothing else. "
            "Do not add numbering or bullet points. Output as: Name, Designation, Organization.\n\n"
            f"{speakers_text}"
        )
        return (await self.ask(prompt)).strip()
