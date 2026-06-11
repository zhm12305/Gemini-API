import time
from contextvars import ContextVar
from uuid import uuid4


_request_id: ContextVar[str] = ContextVar("request_id", default="")


def new_request_id() -> str:
    return f"req_{uuid4().hex[:16]}"


def set_request_id(request_id: str) -> None:
    _request_id.set(request_id)


def get_request_id() -> str:
    return _request_id.get()


def request_trace_payload(request_id: str, model: str = "", stream: bool = False) -> dict:
    return {
        "request_id": request_id,
        "model": model,
        "stream": stream,
        "created_at": time.time(),
    }
