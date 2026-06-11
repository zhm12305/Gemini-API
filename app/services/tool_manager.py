import json
import re
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.models.tool_models import ToolCall, ToolCallResult, ToolConfig, ToolDefinition
from app.tools import (
    CodeExecutorTool,
    DataAnalyzerTool,
    DocumentManagerTool,
    WebFetchTool,
    WebSearchTool,
)
from app.utils.logging import log


class ToolManager:
    def __init__(self, config: Optional[ToolConfig] = None):
        self.config = config or ToolConfig()
        tool_config = self.config.model_dump()
        self.tools = {
            "web_search": WebSearchTool(tool_config),
            "web_fetch": WebFetchTool(tool_config),
            "code_executor": CodeExecutorTool(tool_config),
            "data_analyzer": DataAnalyzerTool(tool_config),
            "document_manager": DocumentManagerTool(tool_config),
        }

    def get_available_tools(self) -> List[ToolDefinition]:
        return [tool.get_tool_definition() for tool in self.tools.values()]

    def get_openai_tools(self) -> List[Dict[str, Any]]:
        return [tool.model_dump(exclude_none=True) for tool in self.get_available_tools()]

    def create_tool_call(self, function_name: str, arguments: Dict[str, Any]) -> ToolCall:
        return ToolCall(
            id=f"call_{uuid4().hex[:8]}",
            type="function",
            function={"name": function_name, "arguments": arguments},
        )

    async def execute_tool_call(self, tool_call: ToolCall) -> ToolCallResult:
        name = tool_call.function.get("name")
        args = tool_call.function.get("arguments", {})
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                args = {}
        if not isinstance(args, dict):
            args = {}

        tool = self.tools.get(name)
        if not tool:
            return ToolCallResult(
                tool_call_id=tool_call.id,
                name=name or "unknown",
                content=f"Tool not found: {name}",
            )

        log("info", f"工具调用开始: {name}", extra={"request_type": "tool"})
        result = await tool.safe_execute(**args)
        content = tool.format_result_for_ai(result)
        log(
            "info",
            f"工具调用结束: {name}, 耗时 {result.get('execution_time', 0):.2f}s",
            extra={"request_type": "tool"},
        )
        return ToolCallResult(tool_call_id=tool_call.id, name=name, content=content)

    async def execute_multiple_tool_calls(self, tool_calls: List[ToolCall]) -> List[ToolCallResult]:
        results = []
        for tool_call in tool_calls:
            results.append(await self.execute_tool_call(tool_call))
        return results

    def should_use_tools(self, messages: List[Dict[str, Any]]) -> bool:
        content = self._last_user_text(messages).lower()
        if not content:
            return False

        skip_patterns = [
            r"<user_info>",
            r"<rules>",
            r"<project_layout>",
            r"<environment_details>",
            r"# vscode visible files",
            r"# current working directory",
        ]
        if any(re.search(pattern, content) for pattern in skip_patterns):
            return False

        tool_keywords = [
            "搜索",
            "查找",
            "联网",
            "最新",
            "访问",
            "抓取",
            "网页",
            "链接",
            "http://",
            "https://",
            "执行代码",
            "运行代码",
            "计算",
            "分析数据",
            "csv",
            "json数组",
            "创建文件",
            "保存文件",
            "search",
            "find",
            "fetch",
            "run code",
            "calculate",
            "analyze data",
        ]
        return any(keyword in content for keyword in tool_keywords)

    def create_tool_calls_from_messages(self, messages: List[Dict[str, Any]]) -> List[ToolCall]:
        text = self._last_user_text(messages)
        lower = text.lower()
        tool_calls: List[ToolCall] = []

        urls = re.findall(r"https?://[^\s<>'\"{}|\\^`\[\]]+", text)
        if urls:
            tool_calls.append(self.create_tool_call("web_fetch", {"url": urls[0]}))
            return tool_calls

        if any(word in lower for word in ["搜索", "查找", "联网", "最新", "search", "find"]):
            query = text
            for word in ["请搜索", "搜索一下", "搜索", "请查找", "查找", "联网搜索", "search", "find"]:
                query = query.replace(word, "")
            query = query.strip(" ：:\n\t")
            if query:
                tool_calls.append(self.create_tool_call("web_search", {"query": query, "num_results": self.config.max_search_results}))

        code_blocks = re.findall(r"```(?:python)?\s*(.*?)```", text, flags=re.S | re.I)
        if code_blocks:
            tool_calls.append(self.create_tool_call("code_executor", {"code": code_blocks[0].strip(), "language": "python"}))
        elif any(word in lower for word in ["计算", "calculate"]):
            expr_match = re.search(r"([0-9+\-*/().\s]{3,})", text)
            if expr_match:
                expr = expr_match.group(1).strip()
                tool_calls.append(self.create_tool_call("code_executor", {"code": f"print({expr})", "language": "python"}))

        if any(word in lower for word in ["分析数据", "csv", "json数组", "analyze data"]):
            tool_calls.append(self.create_tool_call("data_analyzer", {"data": text}))

        if any(word in lower for word in ["创建文件", "保存文件", "create file", "save file"]):
            tool_calls.append(
                self.create_tool_call(
                    "document_manager",
                    {"action": "create", "title": "tool_document", "content": text},
                )
            )

        return tool_calls[:3]

    def _last_user_text(self, messages: List[Dict[str, Any]]) -> str:
        for message in reversed(messages or []):
            if message.get("role") != "user":
                continue
            content = message.get("content", "")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                parts = []
                for item in content:
                    if isinstance(item, dict):
                        if item.get("type") == "text":
                            parts.append(item.get("text", ""))
                        elif "text" in item:
                            parts.append(item.get("text", ""))
                return " ".join(parts)
        return ""


_tool_manager: Optional[ToolManager] = None


def get_tool_manager(config: Optional[ToolConfig] = None) -> ToolManager:
    global _tool_manager
    if _tool_manager is None or config is not None:
        _tool_manager = ToolManager(config)
    return _tool_manager
