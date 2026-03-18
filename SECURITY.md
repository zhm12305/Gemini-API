# Security Policy

## Supported Versions

当前仓库默认仅维护 `main` 分支最新版本。

## Reporting a Vulnerability

如果发现安全问题（密钥泄露、认证绕过、敏感信息暴露等），请不要公开提 Issue。  
请私下联系维护者并附带：

- 漏洞类型
- 复现步骤
- 影响范围
- 修复建议（可选）

## Secret Management

请遵循以下规则：

1. 绝不提交 `.env` 到仓库  
2. 绝不在脚本中硬编码真实 API Key  
3. 公开前执行敏感信息扫描  
4. 发现泄露立即轮换密钥  

## Pre-Publish Mandatory Checklist

1. 轮换所有曾经出现在仓库历史或截图中的密钥  
2. 确认 `.gitignore` 生效  
3. 重新检查 `docker-compose.yaml`、脚本、示例配置  
4. 使用最小权限原则管理外部服务凭据
