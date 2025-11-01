# 🤖 Telegram Bot 使用指南

## 🎯 快速开始

### 方法一：一键启动 (推荐)

**Windows用户:**
```bash
double-click quick_start_bot.bat
```

**Linux/Mac用户:**
```bash
./quick_start_bot.sh
```

### 方法二：命令行启动

**启动独立模式Bot (包含基础功能):**
```bash
python start_bot_standalone.py
```

**启动完整模式Bot (包含所有功能):**
```bash
python src/telegram_bot/telegram_quant_bot.py
```

### 方法三：测试模式

**仅测试连接:**
```bash
python test_bot_simple.py
```

---

## 📱 Bot访问

在Telegram中搜索以下任一用户名：
- `@penguinai_bot`
- `@penguin8n_bot`

或点击链接：[https://t.me/penguinai_bot](https://t.me/penguinai_bot)

---

## 🚀 核心功能

### 1. 基础功能 (立即可用)

| 命令 | 功能 | 示例 |
|------|------|------|
| `/start` | 启动和问候 | `/start` |
| `/help` | 显示帮助信息 | `/help` |
| `/ai` | AI问答助手 | `/ai 什么是量化交易？` |
| `/weather` | 香港天气查询 | `/weather` |
| `/id` | 显示用户和群组ID | `/id` |
| `/echo` | 回声测试 | `/echo hello` |

### 2. 体育比分功能 ✅

| 命令 | 功能 | 示例 |
|------|------|------|
| `/score` | 查看所有体育比分 | `/score` |
| `/score nba` | 查看NBA比分 | `/score nba` |
| `/score soccer` | 查看足球比分 | `/score soccer` |
| `/schedule` | 查看体育赛程 | `/schedule` |
| `/favorite` | 收藏球队 | `/favorite` |

### 3. 量化交易功能 (需配置)

| 命令 | 功能 | 需求 |
|------|------|------|
| `/analyze <代码>` | 股票技术分析 | 数据源API |
| `/optimize <代码>` | 策略参数优化 | 完整依赖 |
| `/risk <代码>` | 风险评估 | 数据源API |
| `/sentiment <代码>` | 市场情绪分析 | 数据源API |
| `/portfolio` | 投资组合管理 | 完整依赖 |
| `/alert` | 价格警报管理 | 完整依赖 |
| `/heatmap` | 股票热力图 | 完整依赖 |
| `/mark6` | 六合彩资讯 | 数据源API |

### 4. 高级功能 (可选)

| 命令 | 功能 | 需求 |
|------|------|------|
| `/summary <文本>` | 总结消息 | API密钥 |
| `/cursor` | 调用Cursor | 白名单 |
| `/wsl` | WSL执行 | 白名单 |
| `/tftcap` | 浏览器截图 | Playwright |

---

## 💡 使用示例

### 1. 开始使用
```
用户: /start
Bot: 👋 嗨！欢迎使用量化交易系统Bot！

🤖 主要功能:
• 投资组合管理
• 价格警报
• AI助手
• 天气查询
• 股票热力图

输入 /help 查看所有可用指令
```

### 2. AI问答
```
用户: /ai 什么是量化交易？
Bot: 🤖 AI思考中...
Bot: 量化交易是一种使用数学模型和计算机算法进行交易的方法...
```

### 3. 体育比分
```
用户: /score
Bot: ⚽ 体育比分

📊 来源: 足智彩
测试队A 1-0 测试队B (进行中)

📊 来源: 备用数据源
曼联 2-1 利物浦 (已结束)
```

### 4. 股票分析
```
用户: /analyze 0700.HK
Bot: 🔍 正在分析 0700.HK...
Bot: 📈 腾讯 (0700.HK)

现价: ¥380.50
RSI(14): 65.2 🟡 中性
MACD: 0.245 (Signal: 0.198)
SMA20: 375.20
```

---

## ⚙️ 配置说明

### 环境变量 (可选)

创建 `.env` 文件或设置环境变量:

```bash
# Telegram Bot Token (必需)
TELEGRAM_BOT_TOKEN=7180490983:AAFbkKnDPC1MHAaOGzQA1fOs9FBwSGGonzI

# AI API (可选，用于 /ai 命令)
AI_API_KEY=your_openai_api_key
AI_API_BASE=https://api.openai.com

# 数据源API (可选，用于股票功能)
DATA_API_KEY=your_data_api_key
DATA_SOURCE_URL=http://18.180.162.113:9191
```

### 完整依赖安装 (可选)

如需使用量化交易功能:

```bash
pip install -r requirements.txt
```

---

## 🔧 故障排除

### 1. Bot无响应

**检查是否启动:**
```bash
# Windows
tasklist | findstr python

# Linux/Mac
ps aux | grep python
```

**重启Bot:**
```bash
# 终止所有Python进程
pkill -f python

# 重新启动
python start_bot_standalone.py
```

### 2. 连接冲突

如看到 "Telegram connection conflict" 错误:

```bash
# 清理Webhooks
curl "https://api.telegram.org/bot7180490983:AAFbkKnDPC1MHAaOGzQA1fOs9FBwSGGonzI/deleteWebhook?drop_pending_updates=true"

# 等待10秒后重新启动
```

### 3. 模块导入错误

```bash
# 安装基础依赖
pip install python-telegram-bot pandas numpy requests

# 安装可选依赖 (用于截图功能)
pip install playwright
playwright install chromium
```

### 4. 编码错误 (Windows)

如果遇到编码问题，设置环境变量:
```bash
set PYTHONIOENCODING=utf-8
python start_bot_standalone.py
```

---

## 📊 性能特性

### 缓存系统
- ✅ LRU缓存管理 (最近最少使用)
- ✅ TTL过期控制 (股票5分钟，天气15分钟)
- ✅ 内存优化
- ✅ 命中率统计

### 异步处理
- ✅ 并发请求管理 (最多100个连接)
- ✅ 连接池复用
- ✅ 指数退避重试机制
- ✅ 错误自动恢复

### 监控告警
- ✅ 响应时间追踪
- ✅ 错误率统计
- ✅ 性能指标收集 (P95, P99)
- ✅ 自动警报系统

---

## 🎯 最佳实践

### 1. 立即可用功能
无需配置，直接使用:
- `/start` - 开始
- `/help` - 帮助
- `/score` - 体育比分
- `/weather` - 天气
- `/ai` - AI对话

### 2. 高级功能配置
按需配置:
1. 编辑 `.env` 文件
2. 设置 API 密钥
3. 重启Bot

### 3. 生产环境部署
推荐使用:
```bash
python secure_complete_system.py
```

---

## 📞 技术支持

### 问题反馈
- GitHub Issues: [项目地址]
- 邮箱: [your-email@example.com]

### 文档链接
- 项目README: `README.md`
- API文档: [API文档地址]
- 测试报告: `FINAL_BOT_TEST_SUMMARY.md`

---

## 🏆 致谢

感谢使用 Telegram 量化交易系统 Bot！

**开发团队**: Claude Code
**版本**: v2.0
**更新时间**: 2025-10-28

**🎊 祝您交易愉快！**
