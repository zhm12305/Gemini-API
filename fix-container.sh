#!/bin/bash

# 容器修复脚本 - 强制修复容器内的硬编码问题

echo "🔧 Hajimi 容器修复脚本"
echo "========================"

CONTAINER_NAME="hajimi-app"

# 检查容器状态
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo "❌ 容器未运行，请先启动容器"
    exit 1
fi

echo "✅ 容器正在运行，开始修复..."

# 1. 直接在容器内修复 api_key.py
echo ""
echo "🔧 修复 api_key.py..."
docker exec $CONTAINER_NAME bash -c '
if grep -q "generativelanguage.googleapis.com" /app/app/utils/api_key.py; then
    echo "发现硬编码，正在修复..."
    sed -i "s|https://generativelanguage.googleapis.com|{settings.GEMINI_API_BASE_URL}|g" /app/app/utils/api_key.py
    sed -i "s|url = \"{settings.GEMINI_API_BASE_URL}/v1beta/models?key={}\".format(api_key)|url = f\"{settings.GEMINI_API_BASE_URL}/v1beta/models?key={api_key}\"|g" /app/app/utils/api_key.py
    
    # 确保导入了settings
    if ! grep -q "from app.config import settings" /app/app/utils/api_key.py; then
        sed -i "/import httpx/a\\        from app.config import settings" /app/app/utils/api_key.py
    fi
    echo "✅ api_key.py 修复完成"
else
    echo "✅ api_key.py 无需修复"
fi
'

# 2. 修复 gemini.py
echo ""
echo "🔧 修复 gemini.py..."
docker exec $CONTAINER_NAME bash -c '
if grep -q "https://generativelanguage.googleapis.com" /app/app/services/gemini.py; then
    echo "发现硬编码，正在修复..."
    sed -i "s|https://generativelanguage.googleapis.com|{settings.GEMINI_API_BASE_URL}|g" /app/app/services/gemini.py
    echo "✅ gemini.py 修复完成"
else
    echo "✅ gemini.py 无需修复"
fi
'

# 3. 修复 OpenAI.py
echo ""
echo "🔧 修复 OpenAI.py..."
docker exec $CONTAINER_NAME bash -c '
if grep -q "https://generativelanguage.googleapis.com" /app/app/services/OpenAI.py; then
    echo "发现硬编码，正在修复..."
    sed -i "s|https://generativelanguage.googleapis.com|{settings.GEMINI_API_BASE_URL}|g" /app/app/services/OpenAI.py
    echo "✅ OpenAI.py 修复完成"
else
    echo "✅ OpenAI.py 无需修复"
fi
'

# 4. 确保 settings.py 有正确的配置
echo ""
echo "🔧 检查 settings.py 配置..."
docker exec $CONTAINER_NAME bash -c '
if ! grep -q "GEMINI_API_BASE_URL.*os.environ.get" /app/app/config/settings.py; then
    echo "添加 GEMINI_API_BASE_URL 配置..."
    sed -i "/GEMINI_API_KEYS.*os.environ.get/a\\\\n# Gemini API基础地址\\nGEMINI_API_BASE_URL = os.environ.get(\"GEMINI_API_BASE_URL\", \"https://gemini.my996.top\")" /app/app/config/settings.py
    echo "✅ settings.py 配置添加完成"
else
    echo "检查默认值是否为反代地址..."
    if grep -q "https://generativelanguage.googleapis.com" /app/app/config/settings.py; then
        echo "修复默认值为反代地址..."
        sed -i "s|https://generativelanguage.googleapis.com|https://gemini.my996.top|g" /app/app/config/settings.py
        echo "✅ 默认值已修复"
    else
        echo "✅ settings.py 配置正确"
    fi
fi
'

# 5. 重启应用进程（如果可能）
echo ""
echo "🔄 尝试重启应用..."
docker exec $CONTAINER_NAME bash -c '
# 查找主进程
PID=$(ps aux | grep "python.*app" | grep -v grep | awk "{print \$2}" | head -1)
if [ -n "$PID" ]; then
    echo "发现应用进程 PID: $PID"
    echo "发送 SIGHUP 信号重新加载..."
    kill -HUP $PID 2>/dev/null || echo "无法发送信号，可能需要重启容器"
else
    echo "未找到应用进程"
fi
'

# 6. 验证修复结果
echo ""
echo "✅ 验证修复结果..."
docker exec $CONTAINER_NAME python3 -c "
import sys
sys.path.append('/app')
try:
    from app.config import settings
    print(f'GEMINI_API_BASE_URL: {getattr(settings, \"GEMINI_API_BASE_URL\", \"未定义\")}')
    
    # 测试URL构建
    test_key = 'test_key'
    url = f'{settings.GEMINI_API_BASE_URL}/v1beta/models?key={test_key}'
    print(f'测试URL: {url}')
    
    if 'generativelanguage.googleapis.com' in url:
        print('❌ 仍在使用官方地址')
    elif 'gemini.my996.top' in url:
        print('✅ 成功使用反代地址')
    else:
        print(f'⚠️  使用了其他地址: {url}')
        
except Exception as e:
    print(f'❌ 验证失败: {e}')
    import traceback
    traceback.print_exc()
"

echo ""
echo "🎯 修复完成！"
echo "========================"
echo "建议操作："
echo "1. 如果修复成功，测试API调用功能"
echo "2. 如果仍有问题，重启容器: docker-compose restart hajimi-app"
echo "3. 查看应用日志: docker logs hajimi-app"

# 显示最近的日志
echo ""
echo "📝 最近的应用日志："
docker logs --tail 10 $CONTAINER_NAME
