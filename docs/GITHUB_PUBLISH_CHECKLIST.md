# GitHub 发布检查清单

## 发布前（必须）

1. 轮换所有已暴露密钥  
2. 确认 `.env` 不进入 Git  
3. 运行敏感信息扫描  
4. 检查 `settings/`、日志、`node_modules`、构建产物是否被忽略  
5. 完成 README 与部署文档更新  

## 建议命令

```bash
# 初始化仓库（若尚未初始化）
git init

# 查看待提交文件
git status

# 简单密钥扫描（按需扩展）
rg -n "AIzaSy|sk-|PRIVATE KEY|PASSWORD=" -g "!page/node_modules/*" .
```

## 首次提交建议

```bash
git add .
git commit -m "chore: initial open-source docs and deployment notes"
git branch -M main
git remote add origin <your-repo-url>
git push -u origin main
```

## 公开仓库额外建议

1. 在 GitHub 开启 Secret Scanning 与 Dependabot  
2. 使用最小权限 API Key  
3. 为生产和测试环境分离不同密钥  
4. 使用 `SECURITY.md` 作为安全响应入口
