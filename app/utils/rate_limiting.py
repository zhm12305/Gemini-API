import time
import asyncio
from fastapi import HTTPException, Request

rate_limit_data = {}
rate_limit_lock = asyncio.Lock() 

async def protect_from_abuse(request: Request, max_requests_per_minute: int = 30, max_requests_per_day_per_ip: int = 600):
    now = int(time.time())
    minute = now // 60
    day = now // (60 * 60 * 24)

    minute_key = f"{request.url.path}:{minute}"
    day_key = f"{request.client.host}:{day}"

    async with rate_limit_lock:
        minute_count, minute_timestamp = rate_limit_data.get(minute_key, (0, now))
        
        if now - minute_timestamp >= 60:
            minute_count = 0
            minute_timestamp = now
        minute_count += 1
        rate_limit_data[minute_key] = (minute_count, minute_timestamp)

        day_count, day_timestamp = rate_limit_data.get(day_key, (0, now))
        if now - day_timestamp >= 86400:
            day_count = 0
            day_timestamp = now
        day_count += 1
        rate_limit_data[day_key] = (day_count, day_timestamp)

    if minute_count > max_requests_per_minute:
        raise HTTPException(status_code=429, detail={
            "message": "Too many requests per minute", "limit": max_requests_per_minute})
    if day_count > max_requests_per_day_per_ip:
        raise HTTPException(status_code=429, detail={"message": "Too many requests per day from this IP", "limit": max_requests_per_day_per_ip})