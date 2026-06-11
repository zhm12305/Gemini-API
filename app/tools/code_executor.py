import asyncio
import os
import subprocess
import sys
import tempfile
import time

from app.tools.base import BaseTool, ToolError


class CodeExecutorTool(BaseTool):
    @property
    def name(self) -> str:
        return "code_executor"

    @property
    def description(self) -> str:
        return "Execute short Python code for calculations and data processing."

    @property
    def parameters_schema(self):
        return {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Python code to execute"},
                "language": {
                    "type": "string",
                    "enum": ["python"],
                    "default": "python",
                    "description": "Execution language",
                },
            },
            "required": ["code"],
        }

    async def execute(self, **kwargs):
        if not self.config.get("code_execution_enabled", True):
            raise ToolError("code execution is disabled")
        code = kwargs.get("code")
        language = kwargs.get("language", "python")
        if not code:
            raise ToolError("code is required")
        if language != "python":
            raise ToolError("only python is enabled")

        timeout = int(self.config.get("code_execution_timeout", 30))
        start = time.time()
        fd, path = tempfile.mkstemp(prefix="gemini_tool_", suffix=".py")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(code)
            try:
                completed = await asyncio.to_thread(
                    subprocess.run,
                    [sys.executable, path],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    encoding="utf-8",
                    errors="replace",
                )
            except subprocess.TimeoutExpired:
                raise ToolError(f"code execution timed out after {timeout} seconds")

            return {
                "success": completed.returncode == 0,
                "output": completed.stdout,
                "error": completed.stderr or None,
                "return_code": completed.returncode,
                "execution_time": time.time() - start,
            }
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass

    def format_result_for_ai(self, result):
        if not result.get("success"):
            return f"Code tool failed: {result.get('error')}"
        data = result.get("result") or {}
        if not data.get("success"):
            return f"Code execution failed:\n{data.get('error')}\nOutput:\n{data.get('output', '')}"
        return f"Code executed in {data.get('execution_time', 0):.2f}s.\nOutput:\n{data.get('output') or '(no output)'}"
