# 香港天文台天气API配置指南

## 📖 概述

香港天文台（HKO）提供开放数据API，是获取香港地区最权威天气数据的官方渠道。本指南将帮助您配置并使用HKO API来优化Telegram机器人的天气功能。

---

## 🔑 API注册流程

### 步骤1: 访问HKO开放数据平台
- **官方网站**: https://www.weather.gov.hk/en/wservices/HKO_WebAPI.html
- **开放数据平台**: https://data.weather.gov.hk/

### 步骤2: 创建账户
1. 点击"注册"或"Register"
2. 填写基本信息：
   - 邮箱地址
   - 用户名
   - 密码
   - 验证码
3. 验证邮箱

### 步骤3: 申请API Key
1. 登录后进入"API管理"或"My Account"
2. 点击"创建新应用"或"Create New Application"
3. 填写应用信息：
   - 应用名称: "Telegram港股量化Bot"
   - 应用描述: "用于获取香港天气数据的Telegram机器人"
   - 使用条款: 勾选同意
4. 提交申请
5. 等待审核（通常1-2个工作日）

### 步骤4: 获取API Key
- 审核通过后，您将收到包含API Key的邮件
- 或在控制台中查看您的API Key
- **格式示例**: `hko_api_key_1234567890abcdef`

---

## 🔧 配置方法

### 方法1: 环境变量配置
编辑 `.env` 文件：

```bash
# 香港天文台 HKO 开放数据 API Key
WEATHER_API_KEY=你的真实API密钥

# 示例:
WEATHER_API_KEY=hko_api_key_1234567890abcdef
```

### 方法2: 系统环境变量
```bash
# Windows
set WEATHER_API_KEY=hko_api_key_1234567890abcdef

# Linux/Mac
export WEATHER_API_KEY=hko_api_key_1234567890abcdef
```

### 方法3: 直接代码配置 (不推荐)
```python
# 在 weather_service.py 中直接设置 (仅用于测试)
self.hko_api_key = "hko_api_key_1234567890abcdef"
```

---

## 🌐 可用的API端点

### 实时天气数据
```
https://data.weather.gov.hk/weatherAPI/env/FN_000.json?key=YOUR_API_KEY
```

### 九日天气预报
```
https://data.weather.gov.hk/weatherAPI/flw/fnwpd/FNWP.json?key=YOUR_API_KEY
```

### 当前天气警告
```
https://data.weather.gov.hk/weatherAPI/wrn/chooseregion/FNRN.json?key=YOUR_API_KEY
```

### 自动站数据
```
https://data.weather.gov.hk/weatherAPI/opendata/aws.json?key=YOUR_API_KEY
```

---

## 📊 API响应格式示例

### 实时天气数据
```json
{
  "Temperature": {
    "value": 26.5,
    "unit": "C",
    "latestTime": "2025-10-28T19:00:00+08:00",
    "updateTime": "2025-10-28T19:05:00+08:00"
  },
  "Humidity": {
    "value": 75,
    "unit": "%",
    "latestTime": "2025-10-28T19:00:00+08:00",
    "updateTime": "2025-10-28T19:05:00+08:00"
  },
  "Wind": {
    "Speed": {
      "value": 12.5,
      "unit": "km/h"
    },
    "Direction": {
      "value": "NE",
      "unit": "16方位"
    },
    "LatestTime": "2025-10-28T19:00:00+08:00"
  },
  "Weather": {
    "value": "天晴",
    "LatestTime": "2025-10-28T19:00:00+08:00"
  },
  "UVIndex": {
    "value": 6,
    "desc": "甚高",
    "time": "2025-10-28T18:00:00+08:00"
  }
}
```

---

## 🎯 在Telegram机器人中的使用

### 配置完成后
1. 重启Telegram机器人：
```bash
python src/telegram_bot/run_bot_clean.py
```

2. 在Telegram中测试：
```
/weather
```

### 预期输出
```
🌤️ 香港实时天气 (香港天文台)

📍 温度: 26°C
💧 湿度: 75%
💨 风速: 13 km/h
🌬️ 风向: 东北风
☀️ 天气: 天晴
☀️ UV指数: 6 (甚高)

⏰ 更新时间: 2025-10-28 19:05
📡 数据源: 香港天文台 HKO
```

---

## 🔒 安全注意事项

### ✅ 正确的做法
- 将API Key保存在 `.env` 文件中（已添加到 `.gitignore`）
- 使用环境变量传递密钥
- 定期更换API Key
- 监控API使用量

### ❌ 错误的做法
- 不要将API Key硬编码在代码中
- 不要提交 `.env` 文件到Git
- 不要在公共聊天中分享API Key
- 不要使用他人的API Key

---

## 📈 使用限制

### HKO API限制
- **请求频率**: 每秒最多5次
- **每日限额**: 1000次请求/天
- **数据更新**: 10分钟更新一次
- **缓存建议**: 15分钟TTL

### 费用
- **基础版**: 免费
- **商业版**: 需要联系HKO商务部门

---

## 🔍 故障排除

### 问题1: API认证失败
```
错误: 401 Unauthorized
解决:
1. 检查API Key是否正确
2. 确认账户已通过审核
3. 检查API Key是否已激活
```

### 问题2: 请求频率过高
```
错误: 429 Too Many Requests
解决:
1. 减少API调用频率
2. 增加缓存时间 (15分钟 → 30分钟)
3. 升级API套餐
```

### 问题3: 数据解析错误
```
错误: JSON解析失败
解决:
1. 检查API Key权限
2. 查看响应数据格式
3. 启用备用解析模式
```

---

## 🧪 测试API连接

### 方法1: 使用curl
```bash
curl "https://data.weather.gov.hk/weatherAPI/env/FN_000.json?key=YOUR_API_KEY"
```

### 方法2: 使用Python
```python
import requests

api_key = "YOUR_API_KEY"
url = f"https://data.weather.gov.hk/weatherAPI/env/FN_000.json?key={api_key}"

response = requests.get(url)
if response.status_code == 200:
    data = response.json()
    print("✅ API连接成功")
    print(f"温度: {data['Temperature']['value']}°C")
else:
    print(f"❌ API连接失败: {response.status_code}")
```

### 方法3: 查看机器人日志
```bash
tail -f quant_system.log | grep -i weather
```

---

## 📚 其他资源

### 官方文档
- [HKO WebAPI 文档](https://www.weather.gov.hk/en/wservices/HKO_WebAPI.html)
- [开放数据平台](https://data.weather.gov.hk/)
- [API使用条款](https://www.weather.gov.hk/en/wservices/TnC.html)

### 社区支持
- [HKO开发者论坛](https://www.weather.gov.hk/en/forum)
- [GitHub示例代码](https://github.com/hko-data)

---

## 🚀 高级功能

### 自定义数据源
您可以修改 `weather_service.py` 来使用其他HKO API：

```python
# 九日天气预报
self.weather_apis.append({
    "name": "HKO 预报",
    "url": f"{self.hko_base_url}/flw/fnwpd/FNWP.json?key={self.hko_api_key}",
    "parser": self._parse_hko_forecast,
    "enabled": True,
    "priority": 1
})
```

### 数据缓存优化
```python
# 在天气服务中调整缓存时间
self.cache_ttl = 600  # 10分钟
```

### 错误监控
```python
# 记录API使用统计
self.api_call_count = 0
self.api_last_reset = datetime.now()

if self.api_call_count > 900:  # 接近每日限额
    logger.warning("API使用量接近上限")
```

---

## ✅ 配置检查清单

- [ ] 已注册HKO开放数据账户
- [ ] 已通过API Key审核
- [ ] 已在.env文件中配置WEATHER_API_KEY
- [ ] 已重启Telegram机器人
- [ ] 已在Telegram中测试 /weather 命令
- [ ] 日志显示成功连接HKO API
- [ ] 天气数据正确显示

---

## 📞 技术支持

如遇到问题，请：

1. **查看日志**: `tail -f quant_system.log | grep weather`
2. **检查配置**: 确认 `.env` 文件中的API Key正确
3. **测试连接**: 使用curl或Python测试API访问
4. **查看文档**: 参考HKO官方API文档
5. **联系支持**: 访问HKO开发者论坛

---

**创建日期**: 2025-10-28
**作者**: Claude Code
**版本**: v1.0
**状态**: ✅ 配置完成
