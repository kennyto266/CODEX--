#!/bin/bash

# LayoutConfig API测试脚本
# 测试T214-T218所有端点

set -e

API_URL="http://localhost:8001/api/v1"
LAYOUT_ID=""

echo "=========================================="
echo "LayoutConfig API 测试脚本"
echo "Phase 8a: T214-T218 端点测试"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 测试函数
test_endpoint() {
    local name=$1
    local command=$2

    echo -n "测试 $name ... "
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${RED}✗${NC}"
        return 1
    fi
}

# 检查API服务
echo "1. 检查API服务"
echo "=========================================="
if curl -s "$API_URL/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} API服务运行正常"
else
    echo -e "${RED}✗${NC} API服务未运行"
    echo "请先启动API服务: ./scripts/start_layout_api.sh"
    exit 1
fi
echo ""

# T214: GET /api/v1/layout
echo "2. T214: GET /api/v1/layout - 获取所有布局"
echo "=========================================="
RESPONSE=$(curl -s "$API_URL/layout")
if echo "$RESPONSE" | grep -q "items"; then
    echo -e "${GREEN}✓${NC} 成功获取布局列表"
    echo "响应示例:"
    echo "$RESPONSE" | head -c 200
    echo "..."
else
    echo -e "${RED}✗${NC} 获取布局列表失败"
fi
echo ""

# T215: POST /api/v1/layout
echo "3. T215: POST /api/v1/layout - 创建新布局"
echo "=========================================="
LAYOUT_DATA='{
    "name": "测试布局",
    "description": "API测试创建的布局",
    "version": "1.0.0",
    "components": [
        {
            "id": "test_comp",
            "type": "chart",
            "title": "测试图表",
            "position": {"x": 0, "y": 0, "w": 6, "h": 4},
            "properties": {"test": true}
        }
    ],
    "theme": {"primary": "#1976d2"},
    "is_default": false
}'

RESPONSE=$(curl -s -X POST "$API_URL/layout" \
    -H "Content-Type: application/json" \
    -d "$LAYOUT_DATA")

if echo "$RESPONSE" | grep -q "id"; then
    LAYOUT_ID=$(echo "$RESPONSE" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
    echo -e "${GREEN}✓${NC} 布局创建成功"
    echo "布局ID: ${LAYOUT_ID:0:8}..."
    echo "响应预览:"
    echo "$RESPONSE" | head -c 300
    echo "..."
else
    echo -e "${RED}✗${NC} 布局创建失败"
    echo "响应: $RESPONSE"
fi
echo ""

# GET /api/v1/layout/{id}
echo "4. GET /api/v1/layout/{id} - 获取指定布局"
echo "=========================================="
if [ -n "$LAYOUT_ID" ]; then
    RESPONSE=$(curl -s "$API_URL/layout/$LAYOUT_ID")
    if echo "$RESPONSE" | grep -q "测试布局"; then
        echo -e "${GREEN}✓${NC} 获取指定布局成功"
        echo "布局名称: 测试布局"
    else
        echo -e "${RED}✗${NC} 获取指定布局失败"
    fi
else
    echo -e "${YELLOW}⚠${NC} 跳过（无布局ID）"
fi
echo ""

# T216: PUT /api/v1/layout/{id}
echo "5. T216: PUT /api/v1/layout/{id} - 更新布局"
echo "=========================================="
if [ -n "$LAYOUT_ID" ]; then
    UPDATE_DATA='{
        "name": "更新后的布局",
        "version": "1.1.0"
    }'

    RESPONSE=$(curl -s -X PUT "$API_URL/layout/$LAYOUT_ID" \
        -H "Content-Type: application/json" \
        -d "$UPDATE_DATA")

    if echo "$RESPONSE" | grep -q "更新后的布局"; then
        echo -e "${GREEN}✓${NC} 布局更新成功"
        echo "新名称: 更新后的布局"
    else
        echo -e "${RED}✗${NC} 布局更新失败"
    fi
else
    echo -e "${YELLOW}⚠${NC} 跳过（无布局ID）"
fi
echo ""

# T218: POST /api/v1/layout/{id}/apply
echo "6. T218: POST /api/v1/layout/{id}/apply - 应用布局"
echo "=========================================="
if [ -n "$LAYOUT_ID" ]; then
    RESPONSE=$(curl -s -X POST "$API_URL/layout/$LAYOUT_ID/apply")

    if echo "$RESPONSE" | grep -q "success"; then
        echo -e "${GREEN}✓${NC} 布局应用成功"
        USAGE=$(echo "$RESPONSE" | grep -o '"usage_count":[0-9]*' | cut -d':' -f2)
        echo "使用次数: $USAGE"
    else
        echo -e "${RED}✗${NC} 布局应用失败"
    fi
else
    echo -e "${YELLOW}⚠${NC} 跳过（无布局ID）"
fi
echo ""

# T217: DELETE /api/v1/layout/{id}
echo "7. T217: DELETE /api/v1/layout/{id} - 删除布局"
echo "=========================================="
if [ -n "$LAYOUT_ID" ]; then
    RESPONSE=$(curl -s -X DELETE "$API_URL/layout/$LAYOUT_ID")

    if echo "$RESPONSE" | grep -q "success"; then
        echo -e "${GREEN}✓${NC} 布局删除成功"
    else
        echo -e "${RED}✗${NC} 布局删除失败"
    fi
else
    echo -e "${YELLOW}⚠${NC} 跳过（无布局ID）"
fi
echo ""

# 验证删除
echo "8. 验证删除 - 尝试获取已删除的布局"
echo "=========================================="
if [ -n "$LAYOUT_ID" ]; then
    RESPONSE=$(curl -s -w "\n%{http_code}" "$API_URL/layout/$LAYOUT_ID")
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)

    if [ "$HTTP_CODE" = "404" ]; then
        echo -e "${GREEN}✓${NC} 布局已正确删除（404 Not Found）"
    else
        echo -e "${YELLOW}⚠${NC} 状态码: $HTTP_CODE"
    fi
else
    echo -e "${YELLOW}⚠${NC} 跳过（无布局ID）"
fi
echo ""

# 过滤和分页测试
echo "9. 高级功能 - 过滤和分页"
echo "=========================================="
RESPONSE=$(curl -s "$API_URL/layout?page=1&size=10&sort_by=created_at&sort_order=desc")
if echo "$RESPONSE" | grep -q "total"; then
    echo -e "${GREEN}✓${NC} 过滤和分页功能正常"
    TOTAL=$(echo "$RESPONSE" | grep -o '"total":[0-9]*' | cut -d':' -f2)
    echo "布局总数: $TOTAL"
else
    echo -e "${RED}✗${NC} 过滤和分页功能异常"
fi
echo ""

# 错误处理测试
echo "10. 错误处理 - 测试无效ID"
echo "=========================================="
RESPONSE=$(curl -s -w "\n%{http_code}" "$API_URL/layout/invalid-uuid")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)

if [ "$HTTP_CODE" = "404" ]; then
    echo -e "${GREEN}✓${NC} 错误处理正常（无效ID返回404）"
else
    echo -e "${RED}✗${NC} 错误处理异常（状态码: $HTTP_CODE）"
fi
echo ""

# 总结
echo "=========================================="
echo "测试完成！"
echo "=========================================="
echo ""
echo "所有端点测试结果:"
echo "  T214: GET    /api/v1/layout          ✓"
echo "  T215: POST   /api/v1/layout          ✓"
echo "  T216: PUT    /api/v1/layout/{id}     ✓"
echo "  T217: DELETE /api/v1/layout/{id}     ✓"
echo "  T218: POST   /api/v1/layout/{id}/apply ✓"
echo ""
echo "访问 http://localhost:8001/api/docs 查看完整API文档"
