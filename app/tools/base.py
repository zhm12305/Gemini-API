import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from app.models.tool_models import ToolDefinition, ToolFunction


class ToolError(Exception):
    pass


class BaseTool(ABC):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @property
    @abstractmethod
    def parameters_schema(self) -> Dict[str, Any]:
        pass

    def get_tool_definition(self) -> ToolDefinition:
        return ToolDefinition(
            type="function",
            function=ToolFunction(
                name=self.name,
                description=self.description,
                parameters=self.parameters_schema,
            ),
        )

    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        pass

    def validate_parameters(self, parameters: Dict[str, Any]) -> None:
        required = self.parameters_schema.get("required", [])
        for param in required:
            if param not in parameters or parameters[param] is None:
                raise ToolError(f"Missing required parameter: {param}")

    async def safe_execute(self, **kwargs) -> Dict[str, Any]:
        start_time = time.time()
        try:
            self.validate_parameters(kwargs)
            result = await self.execute(**kwargs)
            return {
                "success": True,
                "result": result,
                "execution_time": time.time() - start_time,
                "error": None,
            }
        except Exception as exc:
            return {
                "success": False,
                "result": None,
                "execution_time": time.time() - start_time,
                "error": str(exc),
            }

    def format_result_for_ai(self, result: Dict[str, Any]) -> str:
        if not result.get("success"):
            return f"Tool execution failed: {result.get('error')}"
        return str(result.get("result"))
