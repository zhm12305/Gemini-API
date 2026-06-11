import os
import pathlib
import logging
import asyncio
from threading import Lock


def _load_dotenv_file() -> None:
    """Load project .env values for local uvicorn runs without overriding real env vars."""
    env_path = pathlib.Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv_file()

# ---------- 以下是基础配置信息 ----------

# 调用本项目时使用的密码
PASSWORD = os.environ.get("PASSWORD", "123").strip('"')

# 网页配置密码，设置后，在网页修改配置时使用 WEB_PASSWORD 而不是上面的 PASSWORD
WEB_PASSWORD = os.environ.get("WEB_PASSWORD", PASSWORD).strip('"')

# User account and user-issued API key support.
USER_DB_PATH = os.environ.get("USER_DB_PATH", "./hajimi/users.db")
USER_REGISTRATION_ENABLED = os.environ.get("USER_REGISTRATION_ENABLED", "true").lower() in ["true", "1", "yes"]
USER_API_KEYS_ENABLED = os.environ.get("USER_API_KEYS_ENABLED", "true").lower() in ["true", "1", "yes"]
USER_API_KEY_DEFAULT_DAILY_QUOTA = int(os.environ.get("USER_API_KEY_DEFAULT_DAILY_QUOTA", "1000"))
USER_SESSION_TTL_SECONDS = int(os.environ.get("USER_SESSION_TTL_SECONDS", str(7 * 24 * 3600)))
USER_ADMIN_USERNAME = os.environ.get("USER_ADMIN_USERNAME", "").strip()
USER_ADMIN_PASSWORD = os.environ.get("USER_ADMIN_PASSWORD", "").strip()

# API密钥
GEMINI_API_KEYS = os.environ.get("GEMINI_API_KEYS", "")

# Gemini API基础地址，可填写:
# - https://gemini.astrbot.uk
# - https://generativelanguage.googleapis.com
# 也兼容 https://gemini.astrbot.uk/v1beta/ 这种已带版本号的地址
GEMINI_API_BASE_URL = os.environ.get(
    "GEMINI_API_BASE_URL",
    "https://gemini.astrbot.uk",
).strip().rstrip("/")

GEMINI_API_BASE_URLS = [
    item.strip().rstrip("/")
    for item in os.environ.get("GEMINI_API_BASE_URLS", "").split(",")
    if item.strip()
]
if not GEMINI_API_BASE_URLS:
    GEMINI_API_BASE_URLS = [GEMINI_API_BASE_URL]

_gemini_base_url_index = 0
_gemini_base_url_lock = Lock()


def get_gemini_base_urls() -> list[str]:
    return list(GEMINI_API_BASE_URLS)


def get_next_gemini_base_url() -> str:
    global _gemini_base_url_index
    with _gemini_base_url_lock:
        if not GEMINI_API_BASE_URLS:
            return GEMINI_API_BASE_URL.rstrip("/")
        base_url = GEMINI_API_BASE_URLS[_gemini_base_url_index % len(GEMINI_API_BASE_URLS)]
        _gemini_base_url_index += 1
        return base_url.rstrip("/")


def build_gemini_url(api_version: str, path: str) -> str:
    """Build Gemini API URL from a base URL that may already include a version segment."""
    base_url = get_next_gemini_base_url()
    clean_path = path.lstrip("/")
    version_segments = {"v1", "v1alpha", "v1beta"}
    last_segment = base_url.rsplit("/", 1)[-1]

    if last_segment in version_segments:
        if last_segment == api_version:
            return f"{base_url}/{clean_path}"
        versionless_base = base_url.rsplit("/", 1)[0]
        return f"{versionless_base}/{api_version}/{clean_path}"

    return f"{base_url}/{api_version}/{clean_path}"

# 假流式是否开启
FAKE_STREAMING = os.environ.get("FAKE_STREAMING", "true").lower() in [
    "true",
    "1",
    "yes",
]

# 配置持久化存储目录
STORAGE_DIR = os.environ.get("STORAGE_DIR", "/hajimi/settings/")
ENABLE_STORAGE = os.environ.get("ENABLE_STORAGE", "false").lower() in [
    "true",
    "1",
    "yes",
]

# 并发请求配置
CONCURRENT_REQUESTS = int(os.environ.get("CONCURRENT_REQUESTS", "1"))  # 默认并发请求数
INCREASE_CONCURRENT_ON_FAILURE = int(
    os.environ.get("INCREASE_CONCURRENT_ON_FAILURE", "0")
)  # 失败时增加的并发数
MAX_CONCURRENT_REQUESTS = int(
    os.environ.get("MAX_CONCURRENT_REQUESTS", "3")
)  # 最大并发请求数

# 缓存配置
CACHE_EXPIRY_TIME = int(
    os.environ.get("CACHE_EXPIRY_TIME", "21600")
)  # 默认缓存 6 小时 (21600 秒)
MAX_CACHE_ENTRIES = int(
    os.environ.get("MAX_CACHE_ENTRIES", "500")
)  # 默认最多缓存500条响应
CALCULATE_CACHE_ENTRIES = int(
    os.environ.get("CALCULATE_CACHE_ENTRIES", "6")
)  # 默认取最后 6 条消息算缓存键
PRECISE_CACHE = os.environ.get("PRECISE_CACHE", "false").lower() in [
    "true",
    "1",
    "yes",
]  # 是否取所有消息来算缓存键

# 是否启用 Vertex AI
ENABLE_VERTEX = os.environ.get("ENABLE_VERTEX", "false").lower() in ["true", "1", "yes"]
GOOGLE_CREDENTIALS_JSON = os.environ.get("GOOGLE_CREDENTIALS_JSON", "")

# 是否启用快速模式 Vertex
ENABLE_VERTEX_EXPRESS = os.environ.get("ENABLE_VERTEX_EXPRESS", "false").lower() in [
    "true",
    "1",
    "yes",
]
VERTEX_EXPRESS_API_KEY = os.environ.get("VERTEX_EXPRESS_API_KEY", "")

# 联网搜索配置
search = {
    "search_mode": os.environ.get("SEARCH_MODE", "false").lower()
    in ["true", "1", "yes"],
    "search_prompt": os.environ.get(
        "SEARCH_PROMPT", "（使用搜索工具联网搜索，需要在content中结合搜索内容）"
    ).strip('"'),
}

# Local tool calling. This is separate from Gemini native Google Search.
TOOLS_ENABLED = os.environ.get("TOOLS_ENABLED", "false").lower() in ["true", "1", "yes"]
AUTO_TOOL_CALLING = os.environ.get("AUTO_TOOL_CALLING", "true").lower() in ["true", "1", "yes"]
TOOL_MAX_ROUNDS = int(os.environ.get("TOOL_MAX_ROUNDS", "2"))
GOOGLE_SEARCH_API_KEY = os.environ.get("GOOGLE_SEARCH_API_KEY", "")
GOOGLE_SEARCH_CX = os.environ.get("GOOGLE_SEARCH_CX", "")
CODE_EXECUTION_ENABLED = os.environ.get("CODE_EXECUTION_ENABLED", "false").lower() in ["true", "1", "yes"]
CODE_EXECUTION_TIMEOUT = int(os.environ.get("CODE_EXECUTION_TIMEOUT", "20"))
WEB_FETCH_TIMEOUT = int(os.environ.get("WEB_FETCH_TIMEOUT", "10"))
MAX_SEARCH_RESULTS = int(os.environ.get("MAX_SEARCH_RESULTS", "5"))
TOOL_DOCUMENTS_DIR = os.environ.get("TOOL_DOCUMENTS_DIR", "/hajimi/settings/documents")

# API key health and cooldown.
KEY_FAILURE_COOLDOWN_SECONDS = int(os.environ.get("KEY_FAILURE_COOLDOWN_SECONDS", "60"))
KEY_QUOTA_COOLDOWN_SECONDS = int(os.environ.get("KEY_QUOTA_COOLDOWN_SECONDS", "3600"))

# 随机字符串
RANDOM_STRING = os.environ.get("RANDOM_STRING", "false").lower() in ["true", "1", "yes"]
RANDOM_STRING_LENGTH = int(os.environ.get("RANDOM_STRING_LENGTH", "5"))

# 空响应重试次数限制
MAX_EMPTY_RESPONSES = int(
    os.environ.get("MAX_EMPTY_RESPONSES", "5")
)  # 默认最多允许5次空响应

# ---------- 以下是其他配置信息 ----------

# 访问限制
MAX_RETRY_NUM = int(os.environ.get("MAX_RETRY_NUM", "15"))  # 请求时的最大总轮询 key 数
MAX_REQUESTS_PER_MINUTE = int(os.environ.get("MAX_REQUESTS_PER_MINUTE", "30"))
MAX_REQUESTS_PER_DAY_PER_IP = int(os.environ.get("MAX_REQUESTS_PER_DAY_PER_IP", "600"))

# API密钥使用限制
API_KEY_DAILY_LIMIT = int(
    os.environ.get("API_KEY_DAILY_LIMIT", "100")
)  # 默认每个API密钥每24小时可使用100次

# 模型屏蔽黑名单，格式应为逗号分隔的模型名称集合
BLOCKED_MODELS = {
    model.strip()
    for model in os.environ.get("BLOCKED_MODELS", "").split(",")
    if model.strip()
}

# 公益站模式
PUBLIC_MODE = os.environ.get("PUBLIC_MODE", "false").lower() in ["true", "1", "yes"]
# 前端地址
DASHBOARD_URL = os.environ.get("DASHBOARD_URL", "")

# 模型屏蔽白名单
WHITELIST_MODELS = {
    x.strip() for x in os.environ.get("WHITELIST_MODELS", "").split(",") if x.strip()
}
# 白名单User-Agent
WHITELIST_USER_AGENT = {
    x.strip().lower()
    for x in os.environ.get("WHITELIST_USER_AGENT", "").split(",")
    if x.strip()
}

# 跨域配置
# 允许的源列表，逗号分隔，例如 "http://localhost:3000,https://example.com"
ALLOWED_ORIGINS_STR = os.environ.get("ALLOWED_ORIGINS", "")
ALLOWED_ORIGINS = [
    origin.strip() for origin in ALLOWED_ORIGINS_STR.split(",") if origin.strip()
]

# ---------- 运行时全局信息，无需修改 ----------

# 基础目录设置
BASE_DIR = pathlib.Path(__file__).parent.parent

# 失效的API密钥
INVALID_API_KEYS = os.environ.get("INVALID_API_KEYS", "")

version = {"local_version": "0.0.0", "remote_version": "0.0.0", "has_update": False}

# API调用统计
# 这个对象保留为空结构以保持向后兼容性
# 实际统计数据已迁移到 app/utils/stats.py 中的 ApiStatsManager 类
api_call_stats = {
    "calls": []  # 兼容旧版代码结构
}

# 用于保护 api_call_stats 并发访问的锁
stats_lock = asyncio.Lock()

# 日志配置
logging.getLogger("uvicorn").disabled = True
logging.getLogger("uvicorn.access").disabled = True


# ---------- 以下配置信息已废弃 ----------

# 假流式请求的空内容返回间隔（秒）
FAKE_STREAMING_INTERVAL = float(os.environ.get("FAKE_STREAMING_INTERVAL", "1"))
# 假流式响应的每个块大小
FAKE_STREAMING_CHUNK_SIZE = int(os.environ.get("FAKE_STREAMING_CHUNK_SIZE", "10"))
# 假流式响应的每个块之间的延迟（秒）
FAKE_STREAMING_DELAY_PER_CHUNK = float(
    os.environ.get("FAKE_STREAMING_DELAY_PER_CHUNK", "0.1")
)

# 非流式请求TCP保活配置
NONSTREAM_KEEPALIVE_ENABLED = os.environ.get(
    "NONSTREAM_KEEPALIVE_ENABLED", "true"
).lower() in ["true", "1", "yes"]
NONSTREAM_KEEPALIVE_INTERVAL = float(
    os.environ.get("NONSTREAM_KEEPALIVE_INTERVAL", "5.0")
)
