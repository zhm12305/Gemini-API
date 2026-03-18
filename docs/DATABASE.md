# 数据库与存储说明

## 结论

该项目不是传统“前后端 + MySQL”架构。  
它的状态存储主要是文件与浏览器本地存储，不依赖关系型数据库。

## 1. 后端持久化

启用 `ENABLE_STORAGE=true` 后：

- 配置持久化文件：`${STORAGE_DIR}/settings.json`
- 凭据目录：`${STORAGE_DIR}/credentials/`

默认 `STORAGE_DIR=/hajimi/settings/`，通过 volume 映射到宿主机 `./settings`。

## 2. 前端持久化

前端多后端实例配置写入浏览器 `localStorage`：

- key: `hajimi_backends`

## 3. 日志与运行态数据

- Nginx 日志：`nginx/logs/`
- API 调用统计、缓存、活跃请求：以内存为主（重启后重建）

## 4. 与 1Panel MySQL 容器的关系

你服务器里出现的 MySQL 容器不是该仓库核心依赖。  
从当前代码与配置看，本项目功能可在无 MySQL 情况下正常运行。
