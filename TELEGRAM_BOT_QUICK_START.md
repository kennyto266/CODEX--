# Telegram Bot 快速启动指南

**最后更新**: 2025-10-18 11:38:04

---

## ⚡ 5分钟快速启动

### 第1步: 检查配置 (1分钟)

```bash
# 查看当前配置
cat config/bot.env

# 期望输出:
# TELEGRAM_BOT_TOKEN=7180490983:AAFbkKnDP...
# TELEGRAM_ADMIN_CHAT_ID=<需要配置>
```

### 第2步: 获取您的 Chat ID (2分钟)

如果 `TELEGRAM_ADMIN_CHAT_ID` 还没有配置:

```bash
# 方式1: 使用现有 Bot 获取 ID
# 1. 在 Telegram 中打开任何 Bot
# 2. 发送: /id
# 3. Bot 会返回您的数字 ID

# 方式2: 查看文件中的示例
cat telegram_bot.env.example
```

然后更新配置:
```bash
# 编辑 config/bot.env，添加您的 Chat ID
echo "TELEGRAM_ADMIN_CHAT_ID=<YOUR_ID>" >> config/bot.env
```

### 第3步: 验证设置 (1分钟)

```bash
# 运行连接测试
python test_bot_connection.py

# 预期输出:
# ✅ Bot 连接成功
# ✅ 命令列表加载成功
# ✅ 所有测试通过
```

### 第4步: 启动 Bot (1分钟)

```bash
# 方式1: 直接启动
python telegram_quant_bot.py

# 方式2: 使用启动脚本
python start_telegram_bot.py

# 方式3: 使用 PowerShell (Windows)
.\scripts\start_telegram_bot.ps1

# 方式4: 后台运行
python telegram_quant_bot.py &
```

---

## 🎯 常用命令速查表

### 基础命令

| 命令 | 用途 | 示例 |
|------|------|------|
| `/start` | Bot 介绍 | `/start` |
| `/help` | 查看帮助 | `/help` |
| `/id` | 获取 ID | `/id` |
| `/status` | 系统状态 | `/status` |

### 量化交易命令

| 命令 | 用途 | 示例 |
|------|------|------|
| `/analyze` | 技术分析 | `/analyze 0700.HK` |
| `/risk` | 风险评估 | `/risk 0700.HK` |
| `/optimize` | 策略优化 | `/optimize 0700.HK` |
| `/sentiment` | 情绪分析 | `/sentiment 0700.HK` |

### 工具命令

| 命令 | 用途 | 示例 |
|------|------|------|
| `/echo` | 文本回声 | `/echo hello` |
| `/history` | 消息历史 | `/history 10` |
| `/summary` | AI 总结 | `/summary` |
| `/cursor` | Cursor AI | `/cursor 分析这个` |

---

## 🔧 故障排除

### 问题1: 连接失败

```bash
# 检查 Token
echo $TELEGRAM_BOT_TOKEN

# 如果为空，重新加载环境变量:
source config/bot.env  # Linux/Mac
set-content -Encoding UTF8 (Get-Item config/bot.env)  # PowerShell

# 或重新启动终端
```

### 问题2: 命令无响应

```bash
# 检查白名单配置
echo $TG_ALLOWED_USER_IDS

# 获取您的 User ID
# 在 Bot 中发送: /id

# 更新白名单
echo "TG_ALLOWED_USER_IDS=<YOUR_USER_ID>" >> config/bot.env
```

### 问题3: 依赖错误

```bash
# 重新安装依赖
pip install -r telegram_requirements.txt

# 或单独安装:
pip install python-telegram-bot==21.6
pip install python-dotenv==1.0.1
```

### 问题4: 端口被占用

```bash
# Windows: 查找占用端口 39217 的进程
netstat -ano | findstr :39217

# 杀死进程 (替换 PID)
taskkill /PID <PID> /F

# 或使用不同的端口
export BOT_SINGLETON_PORT=39218
python telegram_quant_bot.py
```

---

## 📊 测试工作流

### 完整测试流程

```bash
# 1. 运行综合测试
python comprehensive_telegram_bot_test.py

# 2. 查看测试报告
cat telegram_bot_test_report_*.txt

# 3. 测试 Bot 连接
python test_bot_connection.py

# 4. 启动 Bot
python telegram_quant_bot.py

# 5. 在 Telegram 中测试命令
# - 发送: /help
# - 发送: /analyze 0700.HK
# - 发送: /status
```

---

## 🚀 生产部署建议

### 环境变量配置

创建安全的 `.env` 文件:

```bash
# 必需配置
TELEGRAM_BOT_TOKEN=<your_token_here>
TELEGRAM_ADMIN_CHAT_ID=<your_chat_id_here>

# 推荐配置
TG_ALLOWED_USER_IDS=<your_user_id>
CURSOR_API_KEY=<your_cursor_key>

# 可选配置
BOT_SINGLETON_PORT=39217
TG_ALLOWED_CHAT_IDS=<group_chat_ids>
```

### 后台运行 (Linux/Mac)

```bash
# 使用 nohup
nohup python telegram_quant_bot.py > bot.log 2>&1 &

# 使用 screen
screen -S tg_bot python telegram_quant_bot.py

# 查看日志
tail -f bot.log
```

### 后台运行 (Windows)

```powershell
# 使用 Task Scheduler
$action = New-ScheduledTaskAction -Execute "python" -Argument "telegram_quant_bot.py"
$trigger = New-ScheduledTaskTrigger -AtStartup
Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "TelegramBot"

# 或使用 NSSM (Non-Sucking Service Manager)
nssm install TelegramBot python telegram_quant_bot.py
nssm start TelegramBot
```

### Docker 部署

```dockerfile
FROM python:3.10

WORKDIR /app

COPY telegram_requirements.txt .
RUN pip install -r telegram_requirements.txt

COPY . .

CMD ["python", "telegram_quant_bot.py"]
```

运行:
```bash
docker build -t tg-bot .
docker run -d -e TELEGRAM_BOT_TOKEN=$TOKEN TG-BOT
```

---

## 📈 性能监控

### 查看 Bot 日志

```bash
# 实时监控日志
tail -f quant_system.log | grep "TELEGRAM\|Bot"

# 搜索错误
grep "ERROR\|CRITICAL" quant_system.log

# 统计命令使用
grep "CommandHandler\|command" quant_system.log | wc -l
```

### 监控 Bot 状态

```bash
# 检查进程是否运行
ps aux | grep telegram_quant_bot

# 检查端口占用
netstat -an | grep 39217
```

---

## 🔐 安全检查清单

- [ ] TELEGRAM_BOT_TOKEN 已配置且不在代码中
- [ ] TELEGRAM_ADMIN_CHAT_ID 已设置
- [ ] TG_ALLOWED_USER_IDS 已配置白名单
- [ ] Bot 代码已审查，无明显漏洞
- [ ] 日志不包含敏感信息
- [ ] 使用 HTTPS 连接到 Telegram API
- [ ] 错误处理完善，无信息泄露

---

## 📞 常见问题 (FAQ)

### Q1: 如何重新启动 Bot？
```bash
# 杀死当前进程
pkill -f telegram_quant_bot

# 或
taskkill /F /IM python.exe

# 重新启动
python telegram_quant_bot.py
```

### Q2: 如何查看所有命令？
在 Telegram 中发送:
```
/help
```

### Q3: 如何添加新的量化指标？
编辑 `telegram_quant_bot.py` 中的分析命令处理器。

### Q4: 如何启用 Playwright 截图功能？
```bash
pip install playwright
playwright install
```

### Q5: 如何限制某些用户访问？
编辑 `config/bot.env`:
```
TG_ALLOWED_USER_IDS=123456789,987654321
```

### Q6: 批量发送消息会被限流吗？
是的，Telegram 有速率限制。Bot 已实现 `AIORateLimiter` 处理此问题。

### Q7: Bot 支持群组吗？
支持，配置 `TG_ALLOWED_CHAT_IDS` 后可加入群组。

### Q8: 如何查看历史消息？
在 Telegram 中发送:
```
/history 20
```

---

## 🎓 学习资源

- 📖 [Telegram Bot API 文档](https://core.telegram.org/bots/api)
- 📚 [python-telegram-bot 文档](https://python-telegram-bot.readthedocs.io/)
- 🤖 [Cursor AI API 文档](https://cursor.sh/docs)
- 📊 [量化系统文档](./README.md)

---

## ✅ 快速检查清单

启动前确保:

- [ ] `config/bot.env` 文件存在
- [ ] `TELEGRAM_BOT_TOKEN` 已配置
- [ ] `TELEGRAM_ADMIN_CHAT_ID` 已配置
- [ ] Python 依赖已安装 (`pip install -r telegram_requirements.txt`)
- [ ] 网络连接正常
- [ ] 没有其他 Bot 实例运行

---

## 📊 快速参考

### 环境要求
```
Python: 3.10+
依赖: telegram, python-dotenv, pandas, numpy, requests, httpx
可选: playwright (用于截图)
```

### 推荐系统
```
OS: Windows 10+, Linux, macOS
CPU: 2+ 核心
内存: 2GB+ RAM
网络: 需要 Telegram API 访问
```

### 典型启动时间
```
初始化: ~2 秒
连接: ~1 秒
就绪: ~3 秒
总计: ~3-5 秒
```

---

**更新**: 2025-10-18 11:38:04
**版本**: 1.0
**作者**: Telegram Bot 测试系统
