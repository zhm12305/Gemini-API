from contextvars import ContextVar
from typing import Optional

from fastapi import Header, HTTPException, Query

import app.config.settings as settings


current_client_key_id: ContextVar[Optional[int]] = ContextVar("current_client_key_id", default=None)
current_client_key_prefix: ContextVar[str] = ContextVar("current_client_key_prefix", default="")


async def custom_verify_password(
    authorization: Optional[str] = Header(None, description="OpenAI 格式请求 Key, 格式: Bearer sk-xxxx"),
    x_goog_api_key: Optional[str] = Header(None, description="Gemini 格式请求 Key, 从请求头 x-goog-api-key 获取"),
    key: Optional[str] = Query(None, description="Gemini 格式请求 Key, 从查询参数 key 获取"),
    alt: Optional[str] = None,
):
    client_provided_api_key: Optional[str] = None

    if x_goog_api_key:
        client_provided_api_key = x_goog_api_key
    elif key:
        client_provided_api_key = key
    elif authorization and authorization.startswith("Bearer "):
        client_provided_api_key = authorization.split(" ", 1)[1]

    current_client_key_id.set(None)
    current_client_key_prefix.set("")

    if not client_provided_api_key:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid token")

    if client_provided_api_key == settings.PASSWORD:
        return {"type": "master"}

    if settings.USER_API_KEYS_ENABLED:
        from app.services.user_database import user_db

        api_key_record = user_db.validate_api_key(client_provided_api_key)
        if api_key_record:
            current_client_key_id.set(api_key_record["id"])
            current_client_key_prefix.set(api_key_record["key_prefix"])
            return {"type": "user_api_key", "api_key": api_key_record}

    raise HTTPException(status_code=401, detail="Unauthorized: Invalid token")


def verify_web_password(password: str):
    return password == settings.WEB_PASSWORD


def get_current_client_key_id() -> Optional[int]:
    return current_client_key_id.get()

