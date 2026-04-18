import json
import os
from app.models.schemas import ChatCompletionRequest
from dataclasses import dataclass
from typing import Optional
import httpx
import secrets
import string
import app.config.settings as settings

from app.utils.logging import log, log_model_json
from app.utils.model_limits import apply_gemini_3_flash_openai_params


def generate_secure_random_string(length):
    all_characters = string.ascii_letters + string.digits
    secure_random_string = "".join(
        secrets.choice(all_characters) for _ in range(length)
    )
    return secure_random_string


@dataclass
class GeneratedText:
    text: str
    finish_reason: Optional[str] = None


class OpenAIClient:
    AVAILABLE_MODELS = []
    EXTRA_MODELS = os.environ.get("EXTRA_MODELS", "").split(",")

    def __init__(self, api_key: str):
        self.api_key = api_key

    @staticmethod
    def filter_data_by_whitelist(data, allowed_keys):
        """
        根据白名单过滤字典。
        Args:
            data (dict): 原始的 Python 字典 (代表 JSON 对象)。
            allowed_keys (list or set): 包含允许保留的键名的列表或集合。
                                        使用集合 (set) 进行查找通常更快。
        Returns:
            dict: 只包含白名单中键的新字典。
        """
        if hasattr(data, "model_dump"):
            source_data = data.model_dump(exclude_none=True)
        elif hasattr(data, "dict"):
            source_data = data.dict(exclude_none=True)
        else:
            source_data = data

        # 使用集合(set)可以提高查找效率，特别是当白名单很大时
        allowed_keys_set = set(allowed_keys)
        # 使用字典推导式创建过滤后的新字典
        filtered_data = {
            key: value for key, value in source_data.items() if key in allowed_keys_set
        }
        return filtered_data

    # 真流式处理
    async def stream_chat(self, request: ChatCompletionRequest):
        whitelist = [
            "model",
            "messages",
            "temperature",
            "max_tokens",
            "stream",
            "tools",
            "reasoning_effort",
            "top_k",
            "presence_penalty",
        ]

        data = self.filter_data_by_whitelist(request, whitelist)
        data_model = data.get("model") if isinstance(data, dict) else data.model

        if settings.search["search_mode"] and data_model.endswith("-search"):
            log(
                "INFO",
                "开启联网搜索模式",
                extra={"key": self.api_key[:8], "model": request.model},
            )
            data.setdefault("tools", []).append({"google_search": {}})

        data_model = data_model.removesuffix("-search")
        if isinstance(data, dict):
            data["model"] = data_model
        else:
            data.model = data_model
        apply_gemini_3_flash_openai_params(data_model, data)

        # 真流式请求处理逻辑
        extra_log = {
            "key": self.api_key[:8],
            "request_type": "stream",
            "model": request.model,
        }
        log("INFO", "流式请求开始", extra=extra_log)
        log_model_json(
            "INFO",
            "模型请求 JSON 详细内容",
            {
                "api_version": "v1beta",
                "model": data_model,
                "action": "openai.chat.completions.stream",
                "payload": data,
            },
            extra=extra_log,
        )

        url = f"{settings.GEMINI_API_BASE_URL}/v1beta/openai/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST", url, headers=headers, json=data, timeout=600
            ) as response:
                buffer = b""  # 用于累积可能不完整的 JSON 数据
                try:
                    async for line in response.aiter_lines():
                        if not line.strip():  # 跳过空行 (SSE 消息分隔符)
                            continue
                        if line.startswith("data: "):
                            line = line[len("data: ") :].strip()  # 去除 "data: " 前缀

                        # 检查是否是结束标志，如果是，结束循环
                        if line == "[DONE]":
                            break

                        buffer += line.encode("utf-8")
                        try:
                            # 尝试解析整个缓冲区
                            parsed_chunk = json.loads(buffer.decode("utf-8"))
                            # 解析成功，清空缓冲区
                            buffer = b""
                            log_model_json(
                                "INFO",
                                "模型流式回答片段 JSON 详细内容",
                                parsed_chunk,
                                extra=extra_log,
                            )
                            yield parsed_chunk

                        except json.JSONDecodeError:
                            # JSON 不完整，继续累积到 buffer
                            continue
                        except Exception as e:
                            log(
                                "ERROR",
                                "流式处理期间发生错误",
                                extra={
                                    "key": self.api_key[:8],
                                    "request_type": "stream",
                                    "model": request.model,
                                },
                            )
                            raise e
                except Exception as e:
                    raise e
                finally:
                    log("info", "流式请求结束")
