# 部署文档（1Panel + Docker）

## 1. 当前端口与容器映射

按 `docker-compose.yaml`：

- `hajimi-app`: `7860:7860`
- `hajimi-nginx`: `20220:80`
- `hajimi-watchtower`: 自动拉取更新

按你 1Panel 配置：

- `gemini.inter-trade.top` -> `127.0.0.1:20220`

## 2. 目录结构建议

```text
gemini-app/
  app/
  nginx/
  page/
  settings/
  docker-compose.yaml
  .env
```

## 3. 首次部署步骤

1. 配置环境变量：

```bash
cp .env.example .env
```

2. 修改 `.env`（最少需要 `PASSWORD`、`GEMINI_API_KEYS`）。
3. 启动：

```bash
docker compose up -d
```

4. 检查：

```bash
docker compose ps
docker compose logs -f hajimi-app
docker compose logs -f nginx
```

## 4. 1Panel/OpenResty 层配置

将仓库中的 `1Panel-gemini.conf` 内容同步到 1Panel 对应站点配置（例如 `/opt/1panel/www/conf.d/gemini.conf`），并确保：

- `server_name` 与你的域名一致
- `proxy_pass` 指向 `http://127.0.0.1:20220`
- 已配置真实 IP（Cloudflare 场景）
- 已配置 WebSocket 升级头

## 5. Docker 内 Nginx 配置

需要确认：

- `nginx/nginx.conf` 中 upstream 指向 `hajimi-app:7860`
- `nginx/conf.d/gemini.conf` 的反代与超时设置生效

## 6. 前端构建与更新

如果修改了 `page/src`：

```bash
cd page
npm install
npm run build:app
cd ..
docker compose restart hajimi-app
```

## 7. 健康检查

- 应用健康：`GET /health`（按你的 Nginx 配置已透传）
- 模型测试：`GET /v1/models`（携带 `Authorization: Bearer <PASSWORD>`）

## 8. 常见问题

- 502/504：检查容器网络与 `hajimi-app` 是否正常启动
- 鉴权失败：确认请求携带的是 `PASSWORD`，不是 Gemini API Key
- 仪表盘空白：前端构建产物缺失，执行 `npm run build:app`
