from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

import app.config.settings as settings
from app.services.user_database import user_db


user_router = APIRouter(prefix="/api", tags=["users"])


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class CreateApiKeyRequest(BaseModel):
    name: str = "default"
    quota_daily: Optional[int] = None


class AdminUpdateUserRequest(BaseModel):
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None


class AdminUpdateApiKeyRequest(BaseModel):
    is_active: Optional[bool] = None
    quota_daily: Optional[int] = None


def _public_user(user: dict):
    return {
        "id": user["id"],
        "username": user["username"],
        "is_admin": bool(user["is_admin"]),
        "is_active": bool(user["is_active"]),
        "created_at": user["created_at"],
        "last_login_at": user.get("last_login_at"),
    }


async def require_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing user token")
    token = authorization.split(" ", 1)[1]
    user = user_db.verify_session_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid user token")
    return user


async def require_admin(user=Depends(require_user)):
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin permission required")
    return user


@user_router.post("/auth/register")
async def register_user(request: RegisterRequest):
    if not settings.USER_REGISTRATION_ENABLED:
        raise HTTPException(status_code=403, detail="Registration is disabled")
    try:
        user = user_db.create_user(request.username, request.password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    token = user_db.create_session_token(user)
    return {"user": _public_user(user), "access_token": token, "token_type": "bearer"}


@user_router.post("/auth/login")
async def login_user(request: LoginRequest):
    user = user_db.authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = user_db.create_session_token(user)
    return {"user": _public_user(user), "access_token": token, "token_type": "bearer"}


@user_router.get("/user/me")
async def get_user_me(user=Depends(require_user)):
    return {"user": _public_user(user)}


@user_router.get("/user/api-keys")
async def list_user_api_keys(user=Depends(require_user)):
    return {"api_keys": user_db.list_api_keys(user["id"])}


@user_router.post("/user/api-keys")
async def create_user_api_key(request: CreateApiKeyRequest, user=Depends(require_user)):
    try:
        key_data = user_db.create_api_key(user["id"], request.name, request.quota_daily)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return key_data


@user_router.delete("/user/api-keys/{key_id}")
async def revoke_user_api_key(key_id: int, user=Depends(require_user)):
    if not user_db.revoke_api_key(user["id"], key_id):
        raise HTTPException(status_code=404, detail="API key not found")
    return {"status": "success"}


@user_router.get("/user/audit-logs")
async def list_user_audit_logs(limit: int = 50, user=Depends(require_user)):
    return {"logs": user_db.list_audit_logs(user["id"], limit)}


@user_router.get("/admin/summary")
async def get_admin_summary(admin=Depends(require_admin)):
    return {"summary": user_db.get_summary(), "admin": _public_user(admin)}


@user_router.get("/admin/users")
async def list_admin_users(limit: int = 100, offset: int = 0, admin=Depends(require_admin)):
    return {"users": user_db.list_users(limit=limit, offset=offset)}


@user_router.patch("/admin/users/{user_id}")
async def update_admin_user(user_id: int, request: AdminUpdateUserRequest, admin=Depends(require_admin)):
    if user_id == admin["id"] and request.is_active is False:
        raise HTTPException(status_code=400, detail="Cannot disable current admin account")
    user = user_db.update_user(user_id, is_active=request.is_active, is_admin=request.is_admin)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user": _public_user(user)}


@user_router.get("/admin/api-keys")
async def list_admin_api_keys(limit: int = 100, offset: int = 0, admin=Depends(require_admin)):
    return {"api_keys": user_db.list_all_api_keys(limit=limit, offset=offset)}


@user_router.patch("/admin/api-keys/{key_id}")
async def update_admin_api_key(key_id: int, request: AdminUpdateApiKeyRequest, admin=Depends(require_admin)):
    key = user_db.update_api_key(key_id, is_active=request.is_active, quota_daily=request.quota_daily)
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    return {"api_key": key}


@user_router.get("/admin/audit-logs")
async def list_admin_audit_logs(limit: int = 100, admin=Depends(require_admin)):
    return {"logs": user_db.list_all_audit_logs(limit)}
