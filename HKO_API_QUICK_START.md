# 香港天文台API - 5分钟快速配置

## 🚀 快速开始

### 第1步: 注册 (2分钟)
```
🔗 访问: https://data.weather.gov.hk/
📝 点击: 注册 / Register
✉️ 邮箱验证
```

### 第2步: 申请API Key (2分钟)
```
✅ 登录控制台
➕ 创建新应用
📝 填写信息:
   名称: Telegram港股Bot
   描述: 获取天气数据的机器人
⏳ 等待审核 (1-2工作日)
```

### 第3步: 配置机器人 (1分钟)
```bash
# 编辑 .env 文件
WEATHER_API_KEY=你的API密钥

# 重启机器人
python src/telegram_bot/run_bot_clean.py
```

### 第4步: 测试
```
在Telegram中发送: /weather
应该看到: "香港天文台 HKO (官方)"
```

---

## 📱 测试命令

```bash
/weather        # 获取天气 (现在支持HKO官方数据)
/mark6          # 查看Mark6 (智能推测)
/score          # 体育比分 (正常)
/stock 0700.HK  # 股票查询 (正常)
/help           # 帮助信息
```

---

## 🔍 故障排除

### API Key未配置
- 状态: 使用wttr.in备用数据
- 解决: 配置WEATHER_API_KEY后重启

### API认证失败 (401)
- 检查API Key是否正确
- 确认账户已通过审核

### 请求频率过高 (429)
- 减少调用频率
- 15分钟缓存自动生效

### 所有API失败
- 自动降级到模拟数据
- 查看日志: `tail -f quant_system.log | grep weather`

---

## 📊 当前状态

```
🟢 机器人运行中: PID a1b7d0
⏰ 启动时间: 19:54:20
🔑 HKO API: 已集成 (等待配置密钥)
📡 备用API: wttr.in, OpenWeatherMap
💾 缓存: 15分钟TTL
```

---

## 📚 完整文档

- **完整指南**: `HKO_WEATHER_API_GUIDE.md`
- **集成报告**: `HKO_API_INTEGRATION_SUMMARY.md`
- **优化报告**: `TELEGRAM_BOT_OPTIMIZATION_COMPLETE_REPORT.md`
- **快速指南**: `TELEGRAM_BOT_QUICK_GUIDE.md`

---

## ✅ 配置检查清单

- [ ] 已注册HKO账户
- [ ] 已申请API Key
- [ ] 已在.env配置WEATHER_API_KEY
- [ ] 已重启机器人
- [ ] 已测试/weather命令

---

**最后更新**: 2025-10-28 19:55
