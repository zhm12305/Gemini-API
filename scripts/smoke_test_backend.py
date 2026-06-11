import asyncio
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi.testclient import TestClient

import app.api.user_auth as user_auth_module
import app.config.settings as settings
import app.services.user_database as user_database_module
from app.main import app
from app.models.schemas import ChatCompletionRequest
from app.services.gemini import GeminiClient, GeminiResponseWrapper
from app.services.tool_manager import ToolManager
from app.services.tool_orchestrator import ToolOrchestrator
from app.services.user_database import UserDatabase
from app.tools.code_executor import CodeExecutorTool
from app.utils.auth import custom_verify_password, get_current_client_key_id
from app.utils.api_key import APIKeyManager
from app.utils.key_health import key_health_manager
from app.utils.logging import format_log_message
from app.utils.response import map_openai_finish_reason, openAI_from_Gemini
from app.utils.tracing import set_request_id


class FakeGeminiClient:
    async def complete_chat(self, request, contents, safety_settings, system_instruction):
        assert request.tool_choice == "auto"
        assert any(
            part.get("functionResponse")
            for item in contents
            for part in item.get("parts", [])
        )
        return GeminiResponseWrapper(
            {
                "candidates": [
                    {
                        "content": {
                            "parts": [{"text": "工具结果已整合"}],
                            "role": "model",
                        },
                        "finishReason": "STOP",
                    }
                ],
                "usageMetadata": {
                    "promptTokenCount": 1,
                    "candidatesTokenCount": 1,
                    "totalTokenCount": 2,
                },
            }
        )


async def test_code_executor():
    tool = CodeExecutorTool({"code_execution_enabled": True, "code_execution_timeout": 10})
    result = await tool.safe_execute(code="print(1+2)", language="python")
    assert result["success"], result
    assert result["result"]["success"], result
    assert result["result"]["output"].strip() == "3", result


async def test_tool_orchestrator():
    settings.TOOLS_ENABLED = True
    settings.AUTO_TOOL_CALLING = True
    settings.CODE_EXECUTION_ENABLED = True
    request = ChatCompletionRequest(
        model="gemini-2.5-flash",
        messages=[{"role": "user", "content": "计算 1+2"}],
        tool_choice={"type": "function", "function": {"name": "code_executor"}},
    )
    first = GeminiResponseWrapper(
        {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "functionCall": {
                                    "name": "code_executor",
                                    "args": {"code": "print(1+2)", "language": "python"},
                                }
                            }
                        ],
                        "role": "model",
                    },
                    "finishReason": "STOP",
                }
            ],
            "usageMetadata": {
                "promptTokenCount": 1,
                "candidatesTokenCount": 1,
                "totalTokenCount": 2,
            },
        }
    )
    result = await ToolOrchestrator().complete_with_tools(
        FakeGeminiClient(),
        request,
        [{"role": "user", "parts": [{"text": "计算 1+2"}]}],
        [],
        None,
        first,
    )
    assert result.text == "工具结果已整合"


def test_tool_manager():
    manager = ToolManager()
    tools = manager.get_openai_tools()
    names = [tool["function"]["name"] for tool in tools]
    assert {"web_search", "web_fetch", "code_executor", "data_analyzer", "document_manager"}.issubset(names)
    assert manager.should_use_tools([{"role": "user", "content": "搜索 Gemini API 最新消息"}])


def test_key_health():
    key = "AIzaSyTestKeyxxxxxxxxxxxxxxxxxxxxxxxx"
    assert key_health_manager.is_available(key)
    key_health_manager.record_failure(key, "quota exceeded", 429)
    assert not key_health_manager.is_available(key)
    assert key_health_manager.get_stats([key])[0]["status"] == "quota_exceeded"
    key_health_manager.record_success(key)
    assert key_health_manager.is_available(key)


def test_trace_logging():
    set_request_id("req_smoke")
    assert "[req_smoke]" in format_log_message("INFO", "smoke", {})


def test_base_url_builder():
    old_urls = settings.GEMINI_API_BASE_URLS
    try:
        settings.GEMINI_API_BASE_URLS = [
            "https://gemini.astrbot.uk",
            "https://generativelanguage.googleapis.com/v1beta",
        ]
        assert settings.build_gemini_url("v1beta", "models?key=x") == "https://gemini.astrbot.uk/v1beta/models?key=x"
        assert settings.build_gemini_url("v1beta", "models?key=x") == "https://generativelanguage.googleapis.com/v1beta/models?key=x"
    finally:
        settings.GEMINI_API_BASE_URLS = old_urls


def test_api_key_parser_accepts_proxy_tokens():
    manager = APIKeyManager()
    keys = manager._parse_api_keys("AIxxx")
    assert keys == [
        "AIzaSyC6rlbZRZ9mzF2dlmNr_UcAdzQ-ovqOWEQ",
        "AQ.Ab8RNabcdefghi0123456789abcdefghijklmnopqrstuvw",
    ]


def test_finish_reason_mapping():
    assert map_openai_finish_reason("STOP") == "stop"
    assert map_openai_finish_reason("MAX_TOKENS") == "length"
    assert map_openai_finish_reason("SAFETY") == "content_filter"
    response = GeminiResponseWrapper(
        {
            "candidates": [
                {
                    "content": {"parts": [{"text": "OK"}], "role": "model"},
                    "finishReason": "MAX_TOKENS",
                }
            ],
            "usageMetadata": {"totalTokenCount": 1},
        }
    )
    assert openAI_from_Gemini(response, stream=False)["choices"][0]["finish_reason"] == "length"


def test_short_output_disables_default_thinking():
    request = ChatCompletionRequest(
        model="gemini-2.5-flash",
        messages=[{"role": "user", "content": "请只回答 OK"}],
        max_tokens=30,
    )
    contents, system_instruction = GeminiClient.convert_messages(GeminiClient, request.messages, model=request.model)
    _, data = GeminiClient("test-key")._convert_openAI_request(request, contents, [], system_instruction)
    assert data["generationConfig"]["thinkingConfig"]["thinkingBudget"] == 0


def test_tool_schema_sanitized_for_gemini():
    request = ChatCompletionRequest(
        model="gemini-2.5-flash",
        messages=[{"role": "user", "content": "分析数据"}],
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "demo",
                    "description": "demo",
                    "parameters": {
                        "type": "object",
                        "$schema": "http://json-schema.org/draft-07/schema#",
                        "properties": {
                            "count": {"type": "integer", "default": 5, "minimum": 1, "maximum": 10}
                        },
                    },
                },
            }
        ],
    )
    contents, system_instruction = GeminiClient.convert_messages(GeminiClient, request.messages, model=request.model)
    _, data = GeminiClient("test-key")._convert_openAI_request(request, contents, [], system_instruction)
    params = data["tools"][0]["functionDeclarations"][0]["parameters"]
    assert "$schema" not in params
    assert "default" not in params["properties"]["count"]
    assert "minimum" not in params["properties"]["count"]
    assert "maximum" not in params["properties"]["count"]


def test_user_database_flow():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        db = UserDatabase(str(Path(tmpdir) / "users.db"))

        user = db.create_user("SmokeUser", "password-123")
        assert user["username"] == "smokeuser"
        assert not user["is_admin"]

        try:
            db.create_user("smokeuser", "password-123")
        except ValueError as exc:
            assert "already exists" in str(exc)
        else:
            raise AssertionError("duplicate username should fail")

        assert db.authenticate_user("smokeuser", "wrong-password") is None
        logged_in = db.authenticate_user("smokeuser", "password-123")
        assert logged_in and logged_in["id"] == user["id"]

        session_token = db.create_session_token(logged_in)
        assert db.verify_session_token(session_token)["id"] == user["id"]
        assert db.verify_session_token(session_token + "x") is None
        old_ttl = settings.USER_SESSION_TTL_SECONDS
        try:
            settings.USER_SESSION_TTL_SECONDS = 60
            assert db._session_is_fresh(datetime.now(timezone.utc).isoformat())
            assert not db._session_is_fresh((datetime.now(timezone.utc) - timedelta(seconds=61)).isoformat())
            settings.USER_SESSION_TTL_SECONDS = 0
            assert db._session_is_fresh((datetime.now(timezone.utc) - timedelta(days=365)).isoformat())
        finally:
            settings.USER_SESSION_TTL_SECONDS = old_ttl

        key_data = db.create_api_key(user["id"], "smoke", quota_daily=2)
        raw_key = key_data["api_key"]
        record = db.validate_api_key(raw_key)
        assert record and record["username"] == "smokeuser"

        db.record_api_key_usage(record["id"], tokens=11)
        db.record_api_key_usage(record["id"], tokens=7)
        assert db.get_api_key_usage_today(record["id"]) == 2
        assert db.validate_api_key(raw_key) is None

        keys = db.list_api_keys(user["id"])
        assert keys[0]["total_requests"] == 2
        assert keys[0]["total_tokens"] == 18

        assert db.revoke_api_key(user["id"], keys[0]["id"])
        assert db.validate_api_key(raw_key) is None

        summary = db.get_summary()
        assert summary["users"] == 1
        assert summary["active_api_keys"] == 0


def test_user_auth_routes():
    old_route_db = user_auth_module.user_db
    old_service_db = user_database_module.user_db
    old_registration = settings.USER_REGISTRATION_ENABLED
    old_user_keys = settings.USER_API_KEYS_ENABLED

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        db = UserDatabase(str(Path(tmpdir) / "users.db"))
        user_auth_module.user_db = db
        user_database_module.user_db = db
        settings.USER_REGISTRATION_ENABLED = True
        settings.USER_API_KEYS_ENABLED = True
        try:
            client = TestClient(app)
            response = client.post(
                "/api/auth/register",
                json={"username": "RouteUser", "password": "password-123"},
            )
            assert response.status_code == 200, response.text
            token = response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            response = client.get("/api/user/me", headers=headers)
            assert response.status_code == 200, response.text
            assert response.json()["user"]["username"] == "routeuser"

            response = client.post(
                "/api/user/api-keys",
                json={"name": "route", "quota_daily": 5},
                headers=headers,
            )
            assert response.status_code == 200, response.text
            raw_key = response.json()["api_key"]
            assert raw_key.startswith("sk-user-")

            response = client.get("/api/user/api-keys", headers=headers)
            assert response.status_code == 200, response.text
            key_id = response.json()["api_keys"][0]["id"]

            response = client.delete(f"/api/user/api-keys/{key_id}", headers=headers)
            assert response.status_code == 200, response.text
            assert db.validate_api_key(raw_key) is None

            admin = db.ensure_admin_user("AdminUser", "password-123")
            admin_token = db.create_session_token(admin)
            admin_headers = {"Authorization": f"Bearer {admin_token}"}

            response = client.get("/api/admin/summary", headers=headers)
            assert response.status_code == 403, response.text

            response = client.get("/api/admin/summary", headers=admin_headers)
            assert response.status_code == 200, response.text
            assert response.json()["summary"]["admins"] == 1

            response = client.get("/api/admin/users", headers=admin_headers)
            assert response.status_code == 200, response.text
            assert len(response.json()["users"]) >= 2

            route_user = db.authenticate_user("routeuser", "password-123")
            response = client.patch(
                f"/api/admin/users/{route_user['id']}",
                json={"is_active": False},
                headers=admin_headers,
            )
            assert response.status_code == 200, response.text
            assert not response.json()["user"]["is_active"]

            response = client.get("/api/admin/api-keys", headers=admin_headers)
            assert response.status_code == 200, response.text
        finally:
            user_auth_module.user_db = old_route_db
            user_database_module.user_db = old_service_db
            settings.USER_REGISTRATION_ENABLED = old_registration
            settings.USER_API_KEYS_ENABLED = old_user_keys


async def test_user_api_key_auth_dependency():
    old_service_db = user_database_module.user_db
    old_user_keys = settings.USER_API_KEYS_ENABLED

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        db = UserDatabase(str(Path(tmpdir) / "users.db"))
        user_database_module.user_db = db
        settings.USER_API_KEYS_ENABLED = True
        try:
            user = db.create_user("AuthUser", "password-123")
            raw_key = db.create_api_key(user["id"], "auth", quota_daily=5)["api_key"]
            result = await custom_verify_password(
                authorization=f"Bearer {raw_key}",
                x_goog_api_key=None,
                key=None,
            )
            assert result["type"] == "user_api_key"
            assert get_current_client_key_id() == result["api_key"]["id"]
        finally:
            user_database_module.user_db = old_service_db
            settings.USER_API_KEYS_ENABLED = old_user_keys


async def main():
    assert app.title == "FastAPI"
    assert len(app.routes) > 0
    test_tool_manager()
    test_key_health()
    test_trace_logging()
    test_base_url_builder()
    test_api_key_parser_accepts_proxy_tokens()
    test_finish_reason_mapping()
    test_short_output_disables_default_thinking()
    test_tool_schema_sanitized_for_gemini()
    test_user_database_flow()
    test_user_auth_routes()
    await test_user_api_key_auth_dependency()
    await test_code_executor()
    await test_tool_orchestrator()
    print("backend smoke tests passed")


if __name__ == "__main__":
    asyncio.run(main())
