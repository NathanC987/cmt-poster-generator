from fastapi import Request, HTTPException
from app.core.config import settings
import httpx
import hashlib
import time

# Simple Upstash Redis rate limiter (per IP, per minute)
async def rate_limiter(request: Request):
    if settings.RATE_LIMITER != "upstash":
        return
    ip = request.client.host
    key = f"ratelimit:{ip}"
    url = f"{settings.UPSTASH_REDIS_URL}/set/{key}/1/EX/60/NX"
    headers = {"Authorization": f"Bearer {settings.UPSTASH_REDIS_TOKEN}"}
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code == 409:
            raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again in 1 minute.")
