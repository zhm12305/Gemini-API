import json
import os
from datetime import datetime
from pathlib import Path

from app.tools.base import BaseTool, ToolError


class DocumentManagerTool(BaseTool):
    def __init__(self, config=None):
        super().__init__(config)
        self.docs_dir = Path(self.config.get("documents_directory") or "/hajimi/settings/documents")
        try:
            self.docs_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            self.docs_dir = Path(os.getcwd()) / "settings" / "documents"
            self.docs_dir.mkdir(parents=True, exist_ok=True)

    @property
    def name(self) -> str:
        return "document_manager"

    @property
    def description(self) -> str:
        return "Create, read, list, update, and delete markdown documents."

    @property
    def parameters_schema(self):
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["create", "read", "list", "update", "delete"],
                    "description": "Document action",
                },
                "document_id": {"type": "string", "description": "Document id"},
                "title": {"type": "string", "description": "Document title"},
                "content": {"type": "string", "description": "Markdown content"},
            },
            "required": ["action"],
        }

    async def execute(self, **kwargs):
        action = kwargs.get("action")
        if action == "create":
            return self._create(kwargs)
        if action == "read":
            return self._read(kwargs)
        if action == "list":
            return self._list()
        if action == "update":
            return self._update(kwargs)
        if action == "delete":
            return self._delete(kwargs)
        raise ToolError(f"unknown action: {action}")

    def _safe_id(self, title: str) -> str:
        cleaned = "".join(char if char.isalnum() or char in ("-", "_") else "_" for char in title)
        cleaned = cleaned.strip("_")[:60] or "document"
        return f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{cleaned}"

    def _paths(self, document_id: str):
        if not document_id or "/" in document_id or "\\" in document_id:
            raise ToolError("invalid document_id")
        return self.docs_dir / f"{document_id}.md", self.docs_dir / f"{document_id}.json"

    def _create(self, kwargs):
        title = kwargs.get("title") or "Untitled"
        content = kwargs.get("content") or ""
        document_id = self._safe_id(title)
        doc_path, meta_path = self._paths(document_id)
        doc_path.write_text(f"# {title}\n\n{content}", encoding="utf-8")
        meta = {
            "id": document_id,
            "title": title,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        return meta

    def _read(self, kwargs):
        doc_path, meta_path = self._paths(kwargs.get("document_id"))
        if not doc_path.exists():
            raise ToolError("document not found")
        meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
        return {**meta, "content": doc_path.read_text(encoding="utf-8")}

    def _list(self):
        docs = []
        for meta_path in self.docs_dir.glob("*.json"):
            try:
                docs.append(json.loads(meta_path.read_text(encoding="utf-8")))
            except Exception:
                continue
        docs.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
        return {"total": len(docs), "documents": docs[:50]}

    def _update(self, kwargs):
        document_id = kwargs.get("document_id")
        content = kwargs.get("content")
        if not content:
            raise ToolError("content is required")
        doc_path, meta_path = self._paths(document_id)
        if not doc_path.exists():
            raise ToolError("document not found")
        meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {"id": document_id}
        title = kwargs.get("title") or meta.get("title") or document_id
        doc_path.write_text(f"# {title}\n\n{content}", encoding="utf-8")
        meta.update({"title": title, "updated_at": datetime.now().isoformat()})
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        return meta

    def _delete(self, kwargs):
        doc_path, meta_path = self._paths(kwargs.get("document_id"))
        if not doc_path.exists():
            raise ToolError("document not found")
        doc_path.unlink()
        if meta_path.exists():
            meta_path.unlink()
        return {"deleted": True, "document_id": kwargs.get("document_id")}

    def format_result_for_ai(self, result):
        if not result.get("success"):
            return f"Document operation failed: {result.get('error')}"
        return json.dumps(result.get("result"), ensure_ascii=False, indent=2)
