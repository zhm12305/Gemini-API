# Gemini API Balance (1Panel + Docker)

当前部署在 Linux 服务器（1Panel + Docker）上的网关项目仓库化版本。  
项目本质是一个 `FastAPI` 网关，提供：

- OpenAI 兼容接口
- Gemini 原生接口兼容转发
- Vertex AI 可选接入
- Web 仪表盘（配置、统计、日志、Key 管理）

## 1. 当前线上部署架构（与你现网一致）

```text
Client
  -> Cloudflare (可选)
    -> 1Panel OpenResty (1Panel-gemini.conf)
      -> Docker Nginx (20220 -> 80)
        -> FastAPI App (hajimi-app:7860)
```

核心配置映射：

- 外层 1Panel 反代配置: `1Panel-gemini.conf`
- Docker 编排: `docker-compose.yaml`
- Docker 内 Nginx 主配置: `nginx/nginx.conf`
- Docker 内站点配置: `nginx/conf.d/gemini.conf`
- 后端入口: `app/main.py`
- 前端源码: `page/`
- 前端构建输出: `app/templates/` 与 `app/templates/assets/`

## 2. 功能总览

- API 网关
  - `GET /v1/models`
  - `POST /v1/chat/completions`
  - `POST /gemini/{api_version}/models/{model}:generateContent|streamGenerateContent`
- 仪表盘管理 API（`/api/*`）
  - 实时统计、配置更新、重置统计、API Key 测试与导出
- 缓存与请求去重
  - 基于请求内容哈希缓存
  - 相同请求并发合并，降低重复消耗
- 限流
  - 每分钟 + 每日按 IP 限制
- Vertex 扩展
  - 支持 Service Account JSON / Vertex Express Key

## 3. 技术栈

- 后端: `Python`, `FastAPI`, `Pydantic`, `httpx`, `APScheduler`
- 前端: `Vue3`, `Pinia`, `Vue Router`, `Vite`, `ECharts`
- 网关/代理: `Nginx`, `OpenResty (1Panel)`
- 部署: `Docker Compose`, `Watchtower`
- 持久化: JSON 文件 + 浏览器 `localStorage`（不是传统数据库）

## 4. 数据库说明（重点）

本项目代码本身**不依赖 MySQL/PostgreSQL/Redis** 作为业务数据存储。  
持久化方式是：

- 后端配置落盘: `settings/settings.json`（容器内 `/hajimi/settings/settings.json`）
- 凭据文件目录: `settings/credentials/`
- 前端实例配置: 浏览器 `localStorage`

你在 1Panel 中看到的 MySQL 容器，不是该项目必需组件（可能服务于其他应用）。

详见: [docs/DATABASE.md](docs/DATABASE.md)

## 5. 快速运行

1. 复制环境变量模板：

```bash
cp .env.example .env
```

2. 编辑 `.env` 填写密码和密钥。
3. 启动：

```bash
docker compose up -d
```

4. 访问：
- API: `http://<server-ip>:7860`（容器直接映射）
- Nginx 网关: `http://<server-ip>:20220`

## 6. 前端构建说明

`page/` 是源码；构建输出到后端模板目录：

```bash
cd page
npm install
npm run build:app
```

该命令会把静态资源写入 `app/templates/assets/`，并生成 `app/templates/index.html`。

## 7. 文档导航

- 架构: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- 部署: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- 配置: [docs/CONFIGURATION.md](docs/CONFIGURATION.md)
- API: [docs/API.md](docs/API.md)
- 数据存储: [docs/DATABASE.md](docs/DATABASE.md)
- GitHub 发布清单: [docs/GITHUB_PUBLISH_CHECKLIST.md](docs/GITHUB_PUBLISH_CHECKLIST.md)
- 安全策略: [SECURITY.md](SECURITY.md)

## 8. 上传 GitHub 前必做

1. 不要提交 `.env`（已在 `.gitignore` 忽略）。  
2. 轮换所有已暴露 API Key。  
3. 检查仓库内是否仍有硬编码密钥。  
4. 仅提交源码与文档，不提交 `page/node_modules` 与运行日志。

## 9. 许可证

本仓库默认采用 MIT，见 [LICENSE](LICENSE)。
