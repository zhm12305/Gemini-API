#!/bin/bash

# Hajimi 容器诊断脚本
# 用于检查容器内的配置和文件状态

echo "🔍 Hajimi 容器诊断脚本"
echo "================================"

# 检查容器是否运行
CONTAINER_NAME="hajimi-app"
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo "❌ 容器 $CONTAINER_NAME 未运行"
    echo "尝试查看所有容器："
    docker ps -a | grep hajimi
    exit 1
fi

echo "✅ 容器 $CONTAINER_NAME 正在运行"
echo ""

# 1. 检查环境变量
echo "📋 1. 检查环境变量"
echo "================================"
echo "GEMINI_API_BASE_URL:"
docker exec $CONTAINER_NAME printenv GEMINI_API_BASE_URL || echo "❌ 未设置"

echo ""
echo "GEMINI_API_KEYS (前20字符):"
API_KEYS=$(docker exec $CONTAINER_NAME printenv GEMINI_API_KEYS)
if [ -n "$API_KEYS" ]; then
    echo "${API_KEYS:0:20}..."
    # 计算API密钥数量
    KEY_COUNT=$(echo "$API_KEYS" | tr ',' '\n' | wc -l)
    echo "API密钥数量: $KEY_COUNT"
else
    echo "❌ 未设置"
fi

echo ""
echo "其他重要环境变量:"
docker exec $CONTAINER_NAME printenv | grep -E "(PASSWORD|ENABLE_STORAGE|TZ)" || echo "❌ 未找到"

echo ""

# 2. 检查配置文件内容
echo "📄 2. 检查配置文件"
echo "================================"

echo "检查 settings.py 中的 GEMINI_API_BASE_URL 配置:"
if docker exec $CONTAINER_NAME test -f /app/app/config/settings.py; then
    echo "✅ settings.py 文件存在"
    docker exec $CONTAINER_NAME grep -n "GEMINI_API_BASE_URL" /app/app/config/settings.py || echo "❌ 未找到 GEMINI_API_BASE_URL 配置"
else
    echo "❌ settings.py 文件不存在"
fi

echo ""

# 3. 检查关键服务文件
echo "🔧 3. 检查服务文件"
echo "================================"

FILES=(
    "/app/app/config/settings.py"
    "/app/app/utils/api_key.py"
    "/app/app/services/gemini.py"
    "/app/app/services/OpenAI.py"
)

for file in "${FILES[@]}"; do
    echo "检查文件: $file"
    if docker exec $CONTAINER_NAME test -f "$file"; then
        echo "✅ 文件存在"
        # 检查是否包含硬编码的官方地址
        if docker exec $CONTAINER_NAME grep -q "generativelanguage.googleapis.com" "$file"; then
            echo "❌ 仍包含硬编码的官方地址"
            docker exec $CONTAINER_NAME grep -n "generativelanguage.googleapis.com" "$file"
        else
            echo "✅ 未发现硬编码的官方地址"
        fi
        
        # 检查是否使用了settings.GEMINI_API_BASE_URL
        if docker exec $CONTAINER_NAME grep -q "settings.GEMINI_API_BASE_URL" "$file"; then
            echo "✅ 使用了配置变量"
        else
            echo "⚠️  未使用配置变量"
        fi
    else
        echo "❌ 文件不存在"
    fi
    echo ""
done

# 4. 检查API密钥测试函数
echo "🔑 4. 检查API密钥测试函数"
echo "================================"
echo "api_key.py 中的 test_api_key 函数:"
if docker exec $CONTAINER_NAME test -f /app/app/utils/api_key.py; then
    docker exec $CONTAINER_NAME grep -A 10 "async def test_api_key" /app/app/utils/api_key.py
else
    echo "❌ api_key.py 文件不存在"
fi

echo ""

# 5. 检查实际运行时配置
echo "⚙️  5. 检查运行时配置"
echo "================================"
echo "尝试从容器内部获取实际配置:"

# 创建临时Python脚本来检查配置
docker exec $CONTAINER_NAME python3 -c "
try:
    import sys
    sys.path.append('/app')
    from app.config import settings
    print('✅ 成功导入 settings')
    print(f'GEMINI_API_BASE_URL: {getattr(settings, \"GEMINI_API_BASE_URL\", \"未定义\")}')
    print(f'GEMINI_API_KEYS 数量: {len(getattr(settings, \"GEMINI_API_KEYS\", \"\").split(\",\")) if getattr(settings, \"GEMINI_API_KEYS\", \"\") else 0}')
    print(f'ENABLE_STORAGE: {getattr(settings, \"ENABLE_STORAGE\", \"未定义\")}')
except Exception as e:
    print(f'❌ 导入失败: {e}')
"

echo ""

# 6. 检查容器日志中的错误
echo "📝 6. 检查最近的容器日志"
echo "================================"
echo "最近的错误日志:"
docker logs --tail 20 $CONTAINER_NAME 2>&1 | grep -i "error\|exception\|failed" || echo "未发现明显错误"

echo ""

# 7. 检查文件挂载情况
echo "💾 7. 检查文件挂载情况"
echo "================================"
echo "Docker inspect 挂载信息:"
docker inspect $CONTAINER_NAME | grep -A 20 '"Mounts"' | grep -E "(Source|Destination)" || echo "❌ 获取挂载信息失败"

echo ""

# 8. 测试API调用
echo "🧪 8. 测试API调用"
echo "================================"
echo "从容器内部测试API调用:"

# 在容器内执行API测试
docker exec $CONTAINER_NAME python3 -c "
import os
import asyncio
import sys
sys.path.append('/app')

async def test_api():
    try:
        from app.utils.api_key import test_api_key
        api_key = os.environ.get('DIAGNOSE_TEST_API_KEY', '')
        if not api_key:
            print('跳过 API 测试：未设置 DIAGNOSE_TEST_API_KEY')
            return
        result = await test_api_key(api_key)
        print(f'API测试结果: {result}')
    except Exception as e:
        print(f'API测试失败: {e}')
        import traceback
        traceback.print_exc()

asyncio.run(test_api())
"

echo ""
echo "🎯 诊断完成"
echo "================================"
echo "如果发现问题，请根据上述信息进行修复："
echo "1. 检查文件是否正确挂载"
echo "2. 确认环境变量是否正确设置"
echo "3. 验证配置文件是否包含正确的修复"
echo "4. 重启容器应用更改: docker-compose restart hajimi-app"
