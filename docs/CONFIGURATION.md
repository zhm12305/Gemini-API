# 配置说明

## 1. 鉴权与安全

- `PASSWORD`
  - 网关 API 访问密码
  - 支持 `Authorization: Bearer <PASSWORD>`、`x-goog-api-key`、`?key=`
- `WEB_PASSWORD`
  - 仪表盘管理密码（`/api/update-config` 等）
  - 不配置时默认使用 `PASSWORD`

## 2. 上游模型

- `GEMINI_API_KEYS`
  - 逗号分隔的 Gemini Key 列表
- `GEMINI_API_BASE_URL`
  - Gemini 上游地址，默认可设为代理地址
- `SEARCH_MODE`
  - `true/false`，开启后可使用 `-search` 模型后缀逻辑
- `SEARCH_PROMPT`
  - 搜索模式下插入提示词

## 3. 请求控制

- `MAX_REQUESTS_PER_MINUTE`
- `MAX_REQUESTS_PER_DAY_PER_IP`
- `CONCURRENT_REQUESTS`
- `INCREASE_CONCURRENT_ON_FAILURE`
- `MAX_CONCURRENT_REQUESTS`
- `MAX_RETRY_NUM`
- `MAX_EMPTY_RESPONSES`

## 4. 缓存/伪装

- `CACHE_EXPIRY_TIME`
- `MAX_CACHE_ENTRIES`
- `CALCULATE_CACHE_ENTRIES`
- `PRECISE_CACHE`
- `RANDOM_STRING`
- `RANDOM_STRING_LENGTH`

## 5. 持久化

- `ENABLE_STORAGE=true` 时会把可持久化配置写入：
  - `${STORAGE_DIR}/settings.json`
- 推荐：
  - `STORAGE_DIR=/hajimi/settings/`
  - 并挂载到宿主机 `./settings:/hajimi/settings`

## 6. Vertex 可选配置

- `ENABLE_VERTEX`
- `GOOGLE_CREDENTIALS_JSON`
- `ENABLE_VERTEX_EXPRESS`
- `VERTEX_EXPRESS_API_KEY`
- `VERTEX_PROJECT_ID`
- `VERTEX_LOCATION`
- `VERTEX_MODELS_CONFIG_URL`

## 7. 示例模板

见仓库根目录：`.env.example`
