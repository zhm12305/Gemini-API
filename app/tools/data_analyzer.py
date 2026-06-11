import csv
import io
import json
from statistics import mean, median

from app.tools.base import BaseTool, ToolError


class DataAnalyzerTool(BaseTool):
    @property
    def name(self) -> str:
        return "data_analyzer"

    @property
    def description(self) -> str:
        return "Analyze CSV or JSON array data and return basic statistics."

    @property
    def parameters_schema(self):
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["analyze", "statistics"],
                    "default": "analyze",
                    "description": "Analysis action",
                },
                "data": {
                    "type": "string",
                    "description": "CSV text or JSON array",
                },
            },
            "required": ["data"],
        }

    async def execute(self, **kwargs):
        data = kwargs.get("data")
        if not data:
            raise ToolError("data is required")
        rows = self._parse_rows(str(data))
        if not rows:
            raise ToolError("no rows parsed")

        columns = sorted({key for row in rows for key in row.keys()})
        numeric = {}
        for column in columns:
            values = []
            for row in rows:
                try:
                    value = row.get(column)
                    if value not in (None, ""):
                        values.append(float(value))
                except (TypeError, ValueError):
                    continue
            if values:
                numeric[column] = {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "mean": mean(values),
                    "median": median(values),
                }

        return {
            "row_count": len(rows),
            "columns": columns,
            "numeric_summary": numeric,
            "sample": rows[:5],
        }

    def _parse_rows(self, data: str):
        try:
            parsed = json.loads(data)
            if isinstance(parsed, list):
                if all(isinstance(item, dict) for item in parsed):
                    return parsed
                return [{"value": item} for item in parsed]
        except json.JSONDecodeError:
            pass

        reader = csv.DictReader(io.StringIO(data))
        return [dict(row) for row in reader]

    def format_result_for_ai(self, result):
        if not result.get("success"):
            return f"Data analysis failed: {result.get('error')}"
        return json.dumps(result.get("result"), ensure_ascii=False, indent=2)
