from fastapi import HTTPException, Request, status
import time
import redis.asyncio as aioredis
from src.core.config import settings

redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)

async def rate_limiter(request : Request):
    """
    Fixed Window Rate Limiting using Redis.
    Limit: 5 requests per 60 seconds per IP.
    """
    # client_ip = request.client.host
    # # have to use below line for testing
    client_ip = request.client.host if request.client else "testclient"
    current_minute = int(time.time() // 60)

    key = f"rate_limit:{client_ip}:{current_minute}"

    request_count = await redis_client.incr(key)

    if request_count == 1:
        await redis_client.expire(key, 60)

    if request_count > 5 :
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            detail="Rate limit exceeded. Maximum 5 tasks per minute.")
