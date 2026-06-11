from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class ToolFunction(BaseModel):
    name: str = Field(description="Function name")
    description: str = Field(description="Function description")
    parameters: Dict[str, Any] = Field(description="JSON schema for function parameters")


class ToolDefinition(BaseModel):
    type: Literal["function"] = Field(default="function")
    function: ToolFunction


class ToolCall(BaseModel):
    id: str
    type: Literal["function"] = Field(default="function")
    function: Dict[str, Any]


class ToolCallResult(BaseModel):
    tool_call_id: str
    role: Literal["tool"] = Field(default="tool")
    name: str
    content: str


class ToolConfig(BaseModel):
    google_search_api_key: Optional[str] = None
    google_search_cx: Optional[str] = None
    code_execution_enabled: bool = True
    code_execution_timeout: int = 30
    web_fetch_timeout: int = 10
    max_search_results: int = 5
    documents_directory: str = "/hajimi/settings/documents"
