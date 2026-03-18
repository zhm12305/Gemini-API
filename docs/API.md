# API 文档（核心）

## 鉴权说明

网关密码默认使用 `PASSWORD`，可通过以下方式传递：

- Header: `Authorization: Bearer <PASSWORD>`
- Header: `x-goog-api-key: <PASSWORD>`
- Query: `?key=<PASSWORD>`

## 1. OpenAI 兼容接口

### 获取模型

`GET /v1/models` 或 `GET /models`

### 对话补全

`POST /v1/chat/completions` 或 `POST /chat/completions`

示例：

```bash
curl -X POST "https://your-domain/v1/chat/completions" \
  -H "Authorization: Bearer your_gateway_password" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemini-2.0-flash",
    "messages": [{"role":"user","content":"你好"}],
    "stream": false
  }'
```

## 2. Gemini 原生兼容接口

`POST /gemini/{api_version}/models/{model}:generateContent`  
`POST /gemini/{api_version}/models/{model}:streamGenerateContent`

网关会做兼容转换后复用后端逻辑。

## 3. Dashboard 管理接口

前缀：`/api`

- `GET /dashboard-data`
- `POST /reset-stats`
- `POST /update-config`
- `POST /test-api-keys`
- `GET /test-api-keys/progress`
- `POST /clear-invalid-api-keys`
- `POST /export-valid-api-keys`

说明：

- 管理接口密码校验字段在请求体中：`password`
- 管理密码是 `WEB_PASSWORD`

## 4. Vertex 路由（可选）

- `GET /vertex/models`
- `POST /vertex/chat/completions`

仅在启用 `ENABLE_VERTEX=true` 后参与主要路由逻辑。
