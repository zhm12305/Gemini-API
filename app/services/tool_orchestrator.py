import json
from copy import deepcopy
from typing import Any, Dict, List

import app.config.settings as settings
from app.models.tool_models import ToolCall, ToolConfig
from app.services.tool_manager import get_tool_manager
from app.utils.logging import log, log_model_json


class ToolOrchestrator:
    def __init__(self):
        config = ToolConfig(
            google_search_api_key=settings.GOOGLE_SEARCH_API_KEY,
            google_search_cx=settings.GOOGLE_SEARCH_CX,
            code_execution_enabled=settings.CODE_EXECUTION_ENABLED,
            code_execution_timeout=settings.CODE_EXECUTION_TIMEOUT,
            web_fetch_timeout=settings.WEB_FETCH_TIMEOUT,
            max_search_results=settings.MAX_SEARCH_RESULTS,
            documents_directory=settings.TOOL_DOCUMENTS_DIR,
        )
        self.tool_manager = get_tool_manager(config)

    def maybe_inject_tools(self, chat_request) -> bool:
        if not settings.TOOLS_ENABLED:
            return False
        if getattr(chat_request, "format_type", None) == "gemini":
            return False
        if getattr(chat_request, "tool_choice", "auto") == "none":
            return False
        if chat_request.tools:
            return False
        if not self.tool_manager.should_use_tools(chat_request.messages):
            return False

        chat_request.tools = self.tool_manager.get_openai_tools()
        log("info", f"自动注入本地工具定义: {len(chat_request.tools)} 个", extra={"request_type": "tool", "model": chat_request.model})
        return True

    async def complete_with_tools(
        self,
        gemini_client,
        chat_request,
        contents: List[Dict[str, Any]],
        safety_settings,
        system_instruction,
        first_response,
    ):
        if not settings.TOOLS_ENABLED or not settings.AUTO_TOOL_CALLING:
            return first_response
        if getattr(chat_request, "format_type", None) == "gemini":
            return first_response

        response = first_response
        followup_request = deepcopy(chat_request)
        if isinstance(getattr(followup_request, "tool_choice", None), dict):
            followup_request.tool_choice = "auto"
        working_contents = deepcopy(contents or [])
        for round_index in range(max(settings.TOOL_MAX_ROUNDS, 0)):
            function_calls = response.function_call or []
            if not function_calls:
                return response

            local_tool_names = set(self.tool_manager.tools.keys())
            unknown_tool_names = [
                item.get("name")
                for item in function_calls
                if item.get("name") not in local_tool_names
            ]
            if unknown_tool_names:
                log(
                    "info",
                    f"检测到非本地工具调用，交还客户端处理: {unknown_tool_names}",
                    extra={"request_type": "tool", "model": chat_request.model},
                )
                return response

            tool_calls = [self._gemini_function_call_to_tool_call(item) for item in function_calls]
            log("info", f"检测到模型工具调用: {len(tool_calls)} 个, round={round_index + 1}", extra={"request_type": "tool", "model": chat_request.model})
            tool_results = await self.tool_manager.execute_multiple_tool_calls(tool_calls)

            working_contents.append(
                {
                    "role": "model",
                    "parts": [{"functionCall": item} for item in function_calls],
                }
            )
            for result in tool_results:
                working_contents.append(
                    {
                        "role": "function",
                        "parts": [
                            {
                                "functionResponse": {
                                    "name": result.name,
                                    "response": {"content": result.content},
                                }
                            }
                        ],
                    }
                )

            log_model_json(
                "INFO",
                "工具执行结果回填 Gemini contents",
                {"round": round_index + 1, "tool_results": [result.model_dump() for result in tool_results]},
                extra={"request_type": "tool", "model": chat_request.model},
            )

            response = await gemini_client.complete_chat(
                followup_request,
                working_contents,
                safety_settings,
                system_instruction,
            )
            response.set_model(chat_request.model)

        return response

    def _gemini_function_call_to_tool_call(self, function_call: Dict[str, Any]) -> ToolCall:
        name = function_call.get("name") or "unknown"
        args = function_call.get("args") or {}
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                args = {}
        return ToolCall(
            id=f"call_{name}",
            type="function",
            function={"name": name, "arguments": args},
        )
