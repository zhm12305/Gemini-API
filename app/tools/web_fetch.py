import re
from html.parser import HTMLParser
from urllib.parse import urlparse

import httpx

from app.tools.base import BaseTool, ToolError


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.skip_stack = []
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "nav", "footer", "header", "aside"}:
            self.skip_stack.append(tag)
        if tag in {"p", "br", "div", "section", "article", "li", "h1", "h2", "h3"}:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if self.skip_stack and self.skip_stack[-1] == tag:
            self.skip_stack.pop()
        if tag in {"p", "div", "section", "article", "li", "h1", "h2", "h3"}:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip_stack:
            text = data.strip()
            if text:
                self.parts.append(text + " ")

    def text(self):
        content = "".join(self.parts)
        content = re.sub(r"[ \t]+", " ", content)
        content = re.sub(r"\n\s*\n\s*\n+", "\n\n", content)
        return content.strip()


class WebFetchTool(BaseTool):
    @property
    def name(self) -> str:
        return "web_fetch"

    @property
    def description(self) -> str:
        return "Fetch an HTML page and return readable text content."

    @property
    def parameters_schema(self):
        return {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to fetch"},
            },
            "required": ["url"],
        }

    async def execute(self, **kwargs):
        url = kwargs.get("url")
        if not url:
            raise ToolError("url is required")
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ToolError("invalid url")

        headers = {"User-Agent": "Mozilla/5.0 Gemini-API-Balance/1.0"}
        timeout = float(self.config.get("web_fetch_timeout", 10))
        async with httpx.AsyncClient(timeout=timeout, headers=headers, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()

        content_type = response.headers.get("content-type", "")
        if "html" not in content_type.lower() and "text" not in content_type.lower():
            raise ToolError(f"unsupported content type: {content_type}")

        title_match = re.search(r"<title[^>]*>(.*?)</title>", response.text, flags=re.I | re.S)
        title = re.sub(r"\s+", " ", title_match.group(1)).strip() if title_match else url
        extractor = _TextExtractor()
        extractor.feed(response.text)
        text = extractor.text()
        if len(text) > 12000:
            text = text[:12000] + "\n\n[Content truncated]"
        return {
            "url": url,
            "title": title,
            "content": text,
            "status_code": response.status_code,
        }

    def format_result_for_ai(self, result):
        if not result.get("success"):
            return f"Web fetch failed: {result.get('error')}"
        data = result.get("result") or {}
        return f"Title: {data.get('title')}\nURL: {data.get('url')}\nStatus: {data.get('status_code')}\n\n{data.get('content', '')}"
