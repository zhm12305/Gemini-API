# Gemini API Balance 技术实现文档：一个 Gemini 2API 网关项目的完整工程化设计

> 项目访问地址：<https://gemini.inter-trade.top>
> 项目仓库地址：<https://github.com/zhm12305/Gemini-API>

这篇文章记录的是我围绕 Gemini API 做的一个 2API 网关项目：`Gemini API Balance`。

它不是一个简单的反向代理脚本，也不是把请求原样转发到上游就结束。这个项目的目标是把多个 Gemini API Key、Gemini 原生接口、OpenAI 兼容接口、Vertex AI、Web 管理后台、请求统计、缓存去重、限流、安全配置和 Docker 部署整合成一个可以长期运行的 API 网关。

从使用者视角看，它提供的是一个标准 API 服务：

```http
POST /v1/chat/completions
Authorization: Bearer <PASSWORD>
Content-Type: application/json
```

调用方可以按 OpenAI 的请求格式传入 `model`、`messages`、`stream`、`tools`、`temperature`、`max_tokens` 等参数，项目会在后端完成协议转换、API Key 轮询、上游请求、响应格式转换和统计记录。对于直接使用 Gemini 原生格式的客户端，也可以通过 Gemini 兼容路径访问：

```http
POST /gemini/v1beta/models/{model}:generateContent
```

这个项目最核心的价值在于：它把分散的 Gemini API Key 和不同协议格式，封装成一个统一、可观测、可管理、可部署的 AI API 网关。

---

## 1. 项目的本质：什么是 Gemini 2API

我理解的 2API，不只是“转发请求”。真正有价值的 2API 项目，需要完成这些事情：

| 阶段 | 技术目标 |
| --- | --- |
| 协议入口 | 接收 OpenAI 兼容请求和 Gemini 原生请求 |
| 协议转换 | 把 OpenAI messages 转成 Gemini contents |
| Key 管理 | 管理多个 Gemini API Key，并在请求时选择可用 Key |
| 失败切换 | 某个 Key 失败、限额、空响应时自动换 Key |
| 响应转换 | 把 Gemini 响应包装成 OpenAI `chat.completion` 或 SSE |
| 缓存去重 | 相同请求复用结果，减少重复消耗 |
| 可观测性 | 记录日志、状态、Token、调用次数和错误 |
| 管理后台 | 在 Web 页面中修改配置、检测 Key、查看状态 |
| 工程部署 | 使用 Docker、Nginx、1Panel 固化线上运行环境 |

所以这个项目的核心不是“代理 Gemini”，而是“把 Gemini 能力产品化成一个可运行的 API 服务”。

---

## 2. 项目实现了什么

当前项目主要实现了这些能力：

| 能力 | 实现说明 |
| --- | --- |
| OpenAI 兼容接口 | 提供 `/v1/chat/completions`、`/chat/completions`、`/v1/models` |
| Gemini 原生兼容接口 | 支持 `/gemini/{api_version}/models/{model}:generateContent` |
| 非流式响应 | 使用 Gemini 非流式接口，返回完整 JSON 响应 |
| 真流式响应 | 使用 Gemini `streamGenerateContent`，按 SSE chunk 转发 |
| 假流式响应 | 非流式拿到完整结果后，模拟 OpenAI SSE 输出 |
| 多 API Key 轮询 | 请求时从 Key 池选择可用 Key，失败后继续尝试 |
| 并发请求控制 | 支持配置初始并发数、失败后增加并发数、最大并发数 |
| 空响应重试 | 对空响应进行计数，达到阈值后停止轮询 |
| 请求缓存 | 基于请求内容生成缓存 key，相同请求可复用响应 |
| 活跃请求合并 | 相同请求正在处理中时，后续请求等待已有任务完成 |
| 限流保护 | 按 IP 做每分钟和每日请求限制 |
| API Key 统计 | 记录每个 Key 的调用次数、模型和 token 消耗 |
| Web 仪表盘 | 查看状态、日志、Key、配置、统计图表 |
| 配置持久化 | 将后台配置保存到 JSON 文件 |
| Vertex AI 扩展 | 支持 Service Account JSON 和 Vertex Express Key |
| Docker 部署 | 使用 `docker-compose.yaml` 管理 app、nginx、watchtower |
| Nginx 反代 | 使用容器内 Nginx + 1Panel OpenResty 处理公网入口 |

这些功能组合起来，项目就不只是单个 API，而是一个完整的 Gemini API 网关系统。

---

## 3. 技术栈选择

项目技术栈偏实用，重点是稳定、易部署、可维护。

| 层级 | 技术 |
| --- | --- |
| 后端框架 | Python、FastAPI |
| 数据模型 | Pydantic |
| 异步请求 | httpx、asyncio |
| 定时任务 | APScheduler |
| 前端框架 | Vue 3 |
| 状态管理 | Pinia |
| 前端构建 | Vite |
| 图表展示 | ECharts |
| 代理层 | Nginx、1Panel OpenResty |
| 部署方式 | Docker Compose |
| 自动更新 | Watchtower |
| 持久化 | JSON 文件、浏览器 localStorage |
| 上游模型 | Gemini API、Vertex AI |

为什么选择 FastAPI？

FastAPI 适合这类 API 网关项目。它天然支持异步处理、依赖注入、Pydantic 校验和路由拆分。项目中大量请求都要等待上游 Gemini 响应，如果使用同步框架，很容易在并发下阻塞。FastAPI 配合 `asyncio` 和 `httpx.AsyncClient`，可以更自然地实现并发请求、流式响应和后台任务。

为什么没有引入数据库？

这个项目主要维护的是配置、Key、统计和临时缓存，数据关系并不复杂。使用 JSON 文件和内存结构可以降低部署成本，不需要额外维护 MySQL、PostgreSQL 或 Redis。对于个人服务器和轻量网关来说，这种设计更直接。

---

## 4. 代码结构

项目主要目录如下：

```text
gemini-app/
  app/
    main.py
    api/
      routes.py
      dashboard.py
      stream_handlers.py
      nonstream_handlers.py
    services/
      gemini.py
      OpenAI.py
    utils/
      api_key.py
      auth.py
      cache.py
      error_handling.py
      logging.py
      rate_limiting.py
      response.py
      stats.py
      request.py
      model_limits.py
    config/
      settings.py
      safety.py
      persistence.py
    vertex/
      api_helpers.py
      credentials_manager.py
      message_processing.py
      model_loader.py
      routes/
        chat_api.py
        models_api.py
    models/
      schemas.py
    templates/
      index.html
      assets/
  page/
    src/
      views/
      stores/
      components/
  nginx/
    nginx.conf
    conf.d/
      gemini.conf
  docs/
  docker-compose.yaml
  1Panel-gemini.conf
```

几个核心文件的职责如下：

| 文件 | 职责 |
| --- | --- |
| `app/main.py` | FastAPI 应用入口，初始化路由、缓存、Key 管理、后台任务 |
| `app/api/routes.py` | API 主路由，区分 OpenAI、Gemini、Vertex 请求入口 |
| `app/services/gemini.py` | Gemini REST 调用、OpenAI 请求到 Gemini 请求的转换 |
| `app/api/nonstream_handlers.py` | 非流式请求轮询、并发、缓存和失败处理 |
| `app/api/stream_handlers.py` | 真流式和假流式响应处理 |
| `app/utils/response.py` | Gemini 响应到 OpenAI 响应的格式转换 |
| `app/utils/api_key.py` | Gemini API Key 池管理 |
| `app/utils/cache.py` | 请求缓存 key 生成和响应缓存 |
| `app/utils/stats.py` | API 调用统计 |
| `app/api/dashboard.py` | Web 仪表盘后端接口 |
| `app/vertex/*` | Vertex AI 兼容层 |
| `page/src` | Vue 仪表盘源码 |
| `nginx/*` | 容器内 Nginx 配置 |

---

## 5. 整体架构

线上访问链路可以拆成七层：

```text
客户端
  -> Cloudflare
  -> 1Panel OpenResty
  -> Docker Nginx
  -> FastAPI App
  -> 协议转换与调度层
  -> Gemini API / Vertex AI
```

每层职责如下：

| 层级 | 职责 |
| --- | --- |
| 客户端 | OpenAI SDK、Gemini SDK、聊天客户端、自动化脚本 |
| Cloudflare | DNS、HTTPS、防护、真实 IP 转发 |
| 1Panel OpenResty | 域名入口、证书、外层反向代理 |
| Docker Nginx | 容器内反代、超时、CORS、SSE 连接保持 |
| FastAPI App | 鉴权、限流、缓存、Key 轮询、协议转换 |
| 调度层 | 选择 API Key、并发请求、失败切换、统计记录 |
| 上游模型 | Gemini API 或 Vertex AI |

项目部署后的实际访问地址是：

```text
https://gemini.inter-trade.top
```

容器内部服务默认监听：

```text
hajimi-app:7860
```

Docker Nginx 对外暴露：

```text
20220:80
```

1Panel 再把公网域名反向代理到：

```text
127.0.0.1:20220
```

这种设计把公网入口、容器网络、后端业务逻辑分开，后期排查问题时也更清晰。

---

## 6. OpenAI 兼容接口的实现思路

OpenAI 兼容入口主要在：

```text
app/api/routes.py
```

核心路由包括：

```http
POST /v1/chat/completions
POST /chat/completions
GET /v1/models
GET /models
```

一次 OpenAI 兼容请求进入系统后，大致流程如下：

```text
客户端请求 /v1/chat/completions
  -> 校验 Authorization Bearer
  -> 检查 User-Agent 白名单
  -> 按 IP 限流
  -> 判断是否启用 Vertex
  -> 生成请求缓存 key
  -> 检查响应缓存
  -> 检查相同请求是否已有活跃任务
  -> 根据 stream 参数进入流式或非流式处理
  -> 选择 Gemini API Key
  -> OpenAI messages 转 Gemini contents
  -> 请求 Gemini 上游
  -> Gemini 响应转 OpenAI choices
  -> 写入统计和日志
  -> 返回客户端
```

OpenAI 请求示例：

```json
{
  "model": "gemini-3-flash-preview",
  "messages": [
    {
      "role": "user",
      "content": "请总结这篇技术文章"
    }
  ],
  "temperature": 0.7,
  "stream": false
}
```

项目会把它转换成 Gemini 的请求结构：

```json
{
  "contents": [
    {
      "role": "user",
      "parts": [
        {
          "text": "请总结这篇技术文章"
        }
      ]
    }
  ],
  "generationConfig": {
    "temperature": 0.7,
    "candidateCount": 1
  },
  "safetySettings": []
}
```

转换逻辑集中在：

```text
app/services/gemini.py
```

其中 `convert_messages()` 负责将 OpenAI 的 `messages` 转成 Gemini 的 `contents`。它处理了几类情况：

| OpenAI 角色 | Gemini 角色 |
| --- | --- |
| `user` | `user` |
| `system` | `user` 或 `system_instruction` |
| `assistant` | `model` |
| `tool` | `function` |

同时它也处理了多模态输入：

```json
{
  "type": "image_url",
  "image_url": {
    "url": "data:image/png;base64,..."
  }
}
```

这类内容会被转换成 Gemini 支持的 `inline_data` 结构。

---

## 7. Gemini 原生接口兼容

除了 OpenAI 格式，项目也支持 Gemini 原生风格路径：

```http
POST /gemini/{api_version}/models/{model}:generateContent
POST /gemini/{api_version}/models/{model}:streamGenerateContent
```

对应代码在：

```text
app/api/routes.py
```

路由会解析路径中的模型名和动作类型，然后包装成内部统一的 `AIRequest`：

```text
ChatRequestGemini
  -> AIRequest
  -> aistudio_chat_completions()
  -> process_request() 或 process_stream_request()
```

这样 OpenAI 格式和 Gemini 原生格式最终可以复用同一套 Key 轮询、缓存、限流和统计逻辑。这个设计避免了两套路由各自实现一遍调度逻辑。

---

## 8. API Key 轮询与失败切换

项目的核心能力之一是多 Gemini API Key 轮询。

Key 管理逻辑主要在：

```text
app/utils/api_key.py
```

非流式请求处理主要在：

```text
app/api/nonstream_handlers.py
```

流式请求处理主要在：

```text
app/api/stream_handlers.py
```

非流式请求的轮询逻辑可以概括为：

```text
读取当前配置的并发数
  -> 从 Key 池取出一批可用 Key
  -> 检查 Key 是否达到每日调用限制
  -> 并发请求 Gemini
  -> 任意一个请求成功且非空，立即使用该响应
  -> 失败或空响应则计数
  -> 必要时增加并发数继续尝试
  -> 超过最大重试次数后返回错误响应
```

核心参数包括：

| 配置 | 说明 |
| --- | --- |
| `CONCURRENT_REQUESTS` | 初始并发请求数 |
| `INCREASE_CONCURRENT_ON_FAILURE` | 失败后增加的并发数量 |
| `MAX_CONCURRENT_REQUESTS` | 最大并发请求数 |
| `MAX_RETRY_NUM` | 单次请求最多尝试多少个 Key |
| `MAX_EMPTY_RESPONSES` | 空响应最大容忍次数 |
| `API_KEY_DAILY_LIMIT` | 单个 Key 每日调用上限 |

这个设计解决了几个实际问题：

| 问题 | 处理方式 |
| --- | --- |
| 某个 Key 失效 | 捕获错误后继续换 Key |
| 某个 Key 限额 | 根据统计跳过该 Key |
| Gemini 返回空响应 | 记录空响应次数，继续尝试 |
| 上游偶发 500/503 | 错误处理后继续轮询 |
| 多 Key 可用性不稳定 | 使用并发和重试提升成功率 |

它的本质不是负载均衡，而是“可用性优先”的请求调度。

---

## 9. 流式响应与假流式响应

项目支持两类流式体验。

第一类是真流式：

```text
客户端 stream=true
  -> FastAPI StreamingResponse
  -> Gemini streamGenerateContent
  -> 逐个解析 SSE data
  -> 转换为 OpenAI SSE chunk
  -> 返回客户端
```

真流式的优点是首 token 更快，体验更接近原生模型输出。实现代码主要在：

```text
app/services/gemini.py
app/api/stream_handlers.py
```

第二类是假流式：

```text
客户端 stream=true
  -> 后端先使用非流式请求 Gemini
  -> 拿到完整模型回答
  -> 按片段切分文本
  -> 模拟 OpenAI SSE 输出
```

假流式的优点是更容易结合多 Key 并发轮询和缓存逻辑，缺点是首包不如真流式自然，因为它需要先等完整响应回来。

项目通过配置控制：

```env
FAKE_STREAMING=true
FAKE_STREAMING_INTERVAL=1
FAKE_STREAMING_CHUNK_SIZE=10
FAKE_STREAMING_DELAY_PER_CHUNK=0.1
```

这使得使用者可以在稳定性和实时体验之间做取舍。

---

## 10. 响应格式转换

Gemini 的响应格式和 OpenAI 的响应格式并不一致。

Gemini 非流式响应一般类似：

```json
{
  "candidates": [
    {
      "content": {
        "parts": [
          {
            "text": "模型回答"
          }
        ],
        "role": "model"
      },
      "finishReason": "STOP"
    }
  ],
  "usageMetadata": {
    "promptTokenCount": 100,
    "candidatesTokenCount": 20,
    "totalTokenCount": 120
  }
}
```

OpenAI 兼容响应需要是：

```json
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion",
  "created": 1710000000,
  "model": "gemini-3-flash-preview",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "模型回答"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 100,
    "completion_tokens": 20,
    "total_tokens": 120
  }
}
```

转换逻辑主要在：

```text
app/utils/response.py
```

其中 `openAI_from_Gemini()` 负责把 GeminiResponseWrapper 转成 OpenAI 格式。它还处理了函数调用：

```text
Gemini functionCall
  -> OpenAI tool_calls
```

这一步是 2API 项目的关键。代理不只是转发 HTTP，而是要理解两个协议的数据结构，并做语义层面的兼容。

---

## 11. 请求缓存与活跃请求合并

项目中有两层避免重复消耗的设计。

第一层是响应缓存：

```text
请求内容
  -> generate_cache_key()
  -> 查询 response_cache_manager
  -> 命中则直接返回
```

配置项包括：

```env
CACHE_EXPIRY_TIME=21600
MAX_CACHE_ENTRIES=500
PRECISE_CACHE=false
CALCULATE_CACHE_ENTRIES=6
```

第二层是活跃请求合并：

```text
相同 cache_key 的请求正在进行中
  -> 后续请求等待已有任务
  -> 已有任务成功后复用结果
```

这解决了一个很常见的问题：多个客户端在短时间内提交相同 prompt，如果全部打到上游，会浪费 Key 额度，也会增加失败概率。通过缓存和活跃任务池，可以降低重复请求。

相关代码：

```text
app/utils/cache.py
app/utils/request.py
app/api/routes.py
```

---

## 12. 模型参数与 Gemini 3 适配

项目对 Gemini 3 Flash Preview 做了专门适配。

根据官方文档，`gemini-3-flash-preview` 的关键限制是：

| 项目 | 数值 |
| --- | --- |
| 输入上限 | 1,048,576 tokens |
| 输出上限 | 65,536 tokens |
| Thinking | 支持 |
| 默认 thinking level | high |

项目中新增了统一规则文件：

```text
app/utils/model_limits.py
```

对于 Gemini REST 请求，会自动修正为：

```json
{
  "maxOutputTokens": 65536,
  "thinkingConfig": {
    "thinkingLevel": "high"
  }
}
```

对于 OpenAI 兼容请求，会自动修正为：

```json
{
  "max_tokens": 65536,
  "reasoning_effort": "high"
}
```

这样做的原因是 Gemini 3 的 thinking token 也会占用输出预算。如果上游只给很小的输出上限，例如 `300`，模型可能把大部分预算用于思考，最终可见回答被截断，出现 `MAX_TOKENS`。把输出上限对齐官方能力后，可以减少非预期截断。

---

## 13. 日志与可观测性

项目的日志系统在：

```text
app/utils/logging.py
```

普通日志包含：

| 字段 | 说明 |
| --- | --- |
| timestamp | 时间 |
| level | 日志级别 |
| key | API Key 前缀 |
| request_type | stream、non-stream、fake-stream |
| model | 请求模型 |
| status_code | 状态码 |
| message | 日志内容 |

为了排查上游模型行为，项目还增加了模型请求和响应的 JSON 详情日志：

```text
模型请求 JSON 详细内容
模型回答 JSON 详细内容
模型流式回答片段 JSON 详细内容
```

这样可以直接看到后端最终发给 Gemini 的 payload，以及 Gemini 实际返回的原始结构。排查问题时非常有用，比如：

| 现象 | 可通过日志定位 |
| --- | --- |
| 模型回答被截断 | 查看 `finishReason` 是否为 `MAX_TOKENS` |
| 中文任务输出英文 | 查看 prompt 是否被额外消息干扰 |
| 空响应 | 查看 `candidates` 是否为空 |
| thinking 占用过高 | 查看 `thoughtsTokenCount` |
| 参数未生效 | 查看最终请求 JSON |

这类可观测性是 API 网关项目很重要的一部分。没有完整日志，很多问题只能靠猜。

---

## 14. Web 仪表盘

前端管理后台在：

```text
page/src
```

后端管理接口在：

```text
app/api/dashboard.py
```

仪表盘主要提供这些功能：

| 模块 | 功能 |
| --- | --- |
| 状态总览 | 当前 Key 数量、模型数量、缓存数量、活跃请求 |
| API Key 管理 | 添加、检测、清理失效 Key、导出有效 Key |
| 配置管理 | 修改并发、重试、限流、缓存、搜索、随机字符串 |
| Vertex 配置 | 设置 Google Credentials JSON 和 Vertex Express Key |
| 日志面板 | 查看普通日志和 Vertex 日志 |
| 调用统计 | 查看调用次数、模型使用、Token 统计 |

前端技术栈：

```text
Vue 3
Pinia
Vue Router
Vite
ECharts
```

构建命令：

```bash
cd page
npm install
npm run build:app
```

构建结果会写入：

```text
app/templates/index.html
app/templates/assets/
```

FastAPI 再通过模板和静态文件对外提供页面。

---

## 15. Vertex AI 扩展

项目不仅支持普通 Gemini API Key，也支持 Vertex AI。

相关目录：

```text
app/vertex/
```

主要能力包括：

| 能力 | 说明 |
| --- | --- |
| Service Account JSON | 通过 Google 凭据访问 Vertex AI |
| Vertex Express Key | 支持 Express API Key 模式 |
| OpenAI Direct Path | 使用 Vertex OpenAI endpoint |
| 模型加载 | 从远程模型配置加载 Vertex 模型列表 |
| 消息转换 | OpenAI messages 转 Vertex Gemini Content |
| fake stream | Vertex 非流式响应模拟流式输出 |

Vertex 路由入口：

```text
app/vertex/routes/chat_api.py
app/vertex/routes/models_api.py
```

Vertex 消息转换：

```text
app/vertex/message_processing.py
```

Vertex 调用辅助逻辑：

```text
app/vertex/api_helpers.py
```

这个扩展层让项目不是单纯绑定一种 Gemini 调用方式，而是可以根据部署环境选择普通 Gemini API 或 Vertex AI。

---

## 16. 安全与鉴权设计

项目的外部调用鉴权不是直接暴露 Gemini API Key，而是使用网关自己的密码：

```http
Authorization: Bearer <PASSWORD>
```

Gemini API Key 保存在服务端环境变量或后台配置中，不直接交给客户端。

鉴权逻辑在：

```text
app/utils/auth.py
```

支持的传参方式包括：

| 方式 | 说明 |
| --- | --- |
| `Authorization: Bearer <PASSWORD>` | OpenAI 兼容接口常用 |
| `x-goog-api-key` | Gemini 风格客户端兼容 |
| `?key=` | Gemini 原生 URL 参数兼容 |

另外还有 User-Agent 白名单：

```env
WHITELIST_USER_AGENT=
```

以及 IP 限流：

```env
MAX_REQUESTS_PER_MINUTE=30
MAX_REQUESTS_PER_DAY_PER_IP=600
```

这样做的目标是让上游 Gemini Key 不暴露，同时对外部调用做最基本的访问控制。

---

## 17. 配置管理与持久化

项目配置集中在：

```text
app/config/settings.py
```

配置来源主要是环境变量：

```env
PASSWORD=123
GEMINI_API_KEYS=
GEMINI_API_BASE_URL=https://generativelanguage.googleapis.com
FAKE_STREAMING=true
CONCURRENT_REQUESTS=1
MAX_RETRY_NUM=15
API_KEY_DAILY_LIMIT=100
ENABLE_VERTEX=false
```

后台修改配置后，持久化逻辑在：

```text
app/config/persistence.py
```

默认持久化目录：

```text
/hajimi/settings/
```

Docker 映射到宿主机：

```yaml
volumes:
  - ./settings:/hajimi/settings
```

这让配置可以在容器重启后保留，不会因为重新部署丢失。

---

## 18. 运维部署

项目使用 Docker Compose 部署，核心服务包括：

```yaml
services:
  hajimi-app:
    image: beijixingxing/hajimi:latest
    container_name: hajimi-app
    ports:
      - "7860:7860"

  hajimi-nginx:
    container_name: hajimi-nginx
    ports:
      - "20220:80"

  hajimi-watchtower:
    container_name: hajimi-watchtower
```

部署步骤：

```bash
cp .env.example .env
vim .env
docker compose up -d
```

查看状态：

```bash
docker compose ps
docker compose logs -f hajimi-app
docker compose logs -f hajimi-nginx
```

1Panel 层负责把公网域名转发到容器 Nginx：

```text
gemini.inter-trade.top
  -> 127.0.0.1:20220
```

容器 Nginx 再转发到 FastAPI：

```text
hajimi-nginx
  -> hajimi-app:7860
```

这里有几个关键运维点：

| 运维点 | 说明 |
| --- | --- |
| SSE 超时 | Nginx 需要配置较长超时，避免流式响应中断 |
| 请求体大小 | 多模态和长上下文需要调整 body size |
| CORS | 兼容浏览器客户端调用 |
| WebSocket/Upgrade | 保留代理升级头，兼容扩展场景 |
| 日志排查 | 使用 `docker logs -f hajimi-app` 观察后端行为 |
| 配置持久化 | 挂载 `settings` 目录 |

---

## 19. 一次真实请求的完整链路

以 OpenAI 兼容非流式请求为例：

```text
1. 客户端请求 https://gemini.inter-trade.top/v1/chat/completions
2. 1Panel OpenResty 接收 HTTPS 请求
3. 1Panel 转发到 127.0.0.1:20220
4. Docker Nginx 转发到 hajimi-app:7860
5. FastAPI 进入 /v1/chat/completions 路由
6. 校验 Authorization Bearer
7. 校验 User-Agent 和 IP 限流
8. 生成 cache_key
9. 检查缓存和活跃任务池
10. 从 Key 池取出可用 Gemini API Key
11. OpenAI messages 转 Gemini contents
12. 发起 Gemini generateContent 请求
13. 解析 Gemini candidates 和 usageMetadata
14. 转换成 OpenAI chat.completion
15. 写入 API 调用统计
16. 返回客户端
```

这条链路覆盖了 API 网关的核心能力：入口兼容、鉴权、调度、协议转换、上游调用、响应封装、可观测性和部署代理。

---

## 20. 项目中的工程取舍

这个项目里有一些明显的工程取舍。

第一，优先保证可用性。

多 Key 轮询、失败切换、空响应重试、并发尝试，都是为了让客户端尽量拿到可用响应。对于个人 API 网关来说，上游 Key 的稳定性和限额比单次请求的绝对纯粹性更重要。

第二，降低部署复杂度。

项目没有引入数据库、消息队列或 Redis，而是使用内存结构和 JSON 文件。这样部署成本更低，适合个人服务器长期运行。

第三，协议兼容优先。

项目同时支持 OpenAI 兼容接口和 Gemini 原生接口，内部尽量复用统一调度逻辑。这比单独写两套路由更复杂，但后期维护更清晰。

第四，可观测性优先。

模型请求 JSON 和响应 JSON 详情日志会让日志量变大，但在排查模型行为时非常有价值。比如输出被截断、thinking token 过高、payload 被错误转换，都可以直接从日志里定位。

---

## 21. 我在这个项目中解决的关键问题

这个项目体现的技术点主要有：

| 技术点 | 具体体现 |
| --- | --- |
| API 网关设计 | 统一入口、鉴权、限流、缓存、统计 |
| 协议转换 | OpenAI messages 与 Gemini contents 双向适配 |
| 异步并发 | 使用 asyncio 并发请求多个 Key |
| 流式处理 | FastAPI StreamingResponse + SSE chunk 转换 |
| 容错调度 | Key 失效、限额、空响应、上游异常自动处理 |
| 可观测性 | 日志缓存、前端日志面板、模型 JSON 详情 |
| 前后端整合 | Vue 管理后台 + FastAPI API |
| 容器化部署 | Docker Compose + Nginx + 1Panel |
| 配置持久化 | 环境变量、JSON 配置、后台动态更新 |
| 模型适配 | Gemini 3 token 上限和 thinking 参数适配 |

这些能力不是孤立的功能点，而是围绕“把 Gemini 能力稳定地封装成 API 服务”这个目标形成的一套完整工程实现。

---

## 22. 总结

`Gemini API Balance` 的核心不是简单代理，而是一个围绕 Gemini API 构建的 2API 网关。

它解决了三个层面的问题：

第一，协议层面。

它让 OpenAI 兼容客户端和 Gemini 原生客户端都可以通过统一网关访问 Gemini 能力。

第二，调度层面。

它通过多 Key 轮询、失败切换、缓存、活跃请求合并和限流，提高了个人 API 服务的可用性。

第三，工程层面。

它通过 Web 仪表盘、日志、统计、配置持久化、Docker、Nginx 和 1Panel 部署，把一个 API 转发能力整理成了可运维的线上服务。

这个项目的技术重点在于：把模型 API 调用从“能跑”推进到“可管理、可观测、可部署、可扩展”。这也是我认为 2API 项目真正有价值的地方。
