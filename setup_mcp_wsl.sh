#!/bin/bash
# MCP 持久終端設置腳本 (WSL)

echo "================================================"
echo "MCP 持久終端設置 (WSL)"
echo "================================================"

# 檢查 Node.js
echo -e "\n1. 檢查 Node.js..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安裝！"
    echo "請先安裝: sudo apt update && sudo apt install nodejs npm -y"
    exit 1
fi
echo "✅ Node.js $(node --version)"
echo "✅ npm $(npm --version)"

# 安裝 node-pty
echo -e "\n2. 安裝 node-pty..."
if npm list -g node-pty &> /dev/null; then
    echo "✅ node-pty 已安裝"
else
    echo "正在安裝 node-pty..."
    sudo npm install -g node-pty
    if [ $? -eq 0 ]; then
        echo "✅ node-pty 安裝成功"
    else
        echo "❌ 安裝失敗！請手動運行: sudo npm install -g node-pty"
        exit 1
    fi
fi

# 查找 node-pty 路徑
echo -e "\n3. 查找 node-pty 路徑..."
NPM_ROOT=$(npm root -g)
NODE_PTY_PATH="$NPM_ROOT/node-pty/lib/index.js"

if [ -f "$NODE_PTY_PATH" ]; then
    echo "✅ 找到 node-pty: $NODE_PTY_PATH"
else
    # 嘗試其他可能的路徑
    NODE_PTY_PATH="$NPM_ROOT/node-pty/dist/index.js"
    if [ -f "$NODE_PTY_PATH" ]; then
        echo "✅ 找到 node-pty: $NODE_PTY_PATH"
    else
        echo "❌ 找不到 node-pty 入口文件"
        echo "已安裝的全局包："
        npm list -g --depth=0
        exit 1
    fi
fi

# 生成 MCP 配置命令
echo -e "\n4. 生成 MCP 配置命令..."
echo "================================================"
echo "請在 Windows PowerShell 或 CMD 中運行以下命令："
echo "================================================"
echo ""
echo "claude mcp add persistent-terminal \\"
echo "  --env MAX_BUFFER_SIZE=10000 \\"
echo "  --env SESSION_TIMEOUT=86400000 \\"
echo "  --env COMPACT_ANIMATIONS=true \\"
echo "  --env ANIMATION_THROTTLE_MS=100 \\"
echo "  -- wsl node $NODE_PTY_PATH"
echo ""
echo "================================================"

# 保存到文件
CONFIG_FILE="/mnt/c/Users/Penguin8n/CODEX--/CODEX--/mcp_config_command.txt"
cat > "$CONFIG_FILE" << EOF
MCP 持久終端配置命令 (在 Windows 終端中運行):

claude mcp add persistent-terminal \\
  --env MAX_BUFFER_SIZE=10000 \\
  --env SESSION_TIMEOUT=86400000 \\
  --env COMPACT_ANIMATIONS=true \\
  --env ANIMATION_THROTTLE_MS=100 \\
  -- wsl node $NODE_PTY_PATH

或者單行版本（PowerShell）:

claude mcp add persistent-terminal --env MAX_BUFFER_SIZE=10000 --env SESSION_TIMEOUT=86400000 --env COMPACT_ANIMATIONS=true --env ANIMATION_THROTTLE_MS=100 -- wsl node $NODE_PTY_PATH
EOF

echo "✅ 配置命令已保存到: $CONFIG_FILE"
echo ""
echo "================================================"
echo "安裝完成！"
echo "================================================"
echo ""
echo "下一步："
echo "1. 複製上述命令"
echo "2. 在 Windows PowerShell 或 CMD 中運行"
echo "3. 運行 'claude mcp list' 驗證配置"
echo ""
