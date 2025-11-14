# FRED API 快速参考卡

## 🚀 立即申请 (30秒完成)

### 步骤1: 打开申请页面
```
https://fred.stlouisfed.org/docs/api/api_key.html
```

### 步骤2: 填写表单
```
Email: [输入您的邮箱]
Reason: Academic research on quantitative trading and economic indicators
```

### 步骤3: 点击提交
```
点击 "Request API Key" 按钮
```

### 步骤4: 检查邮箱获取密钥
```
发件人: api@federalreserve.gov 或 fred@stlouisfed.org
主题: Your FRED API Key
```

---

## 🔑 获取密钥后立即测试

### 设置环境变量 (PowerShell)
```powershell
$env:FRED_API_KEY = "您的API密钥"
```

### 运行测试脚本
```bash
python test_fred_api.py
```

### 预期输出
```
[1/6] 测试 实际GDP (季度) (GDPC1)
✅ 成功!
   指标: 实际GDP (季度)
   最新日期: 2024-01-01
   最新值: 26948.8

[2/6] 测试 消费者价格指数 (CPIAUCSL)
✅ 成功!
   指标: 消费者价格指数
   最新日期: 2024-01-01
   最新值: 308.417

... (6个指标全部成功)

✅ FRED API密钥工作正常!
已成功获取 6 个宏观经济指标
覆盖率提升: +3.70%
从22.2% → 25.9%
```

---

## 📊 将获取的数据

| 指标 | 代码 | 说明 | 价值 |
|------|------|------|------|
| GDP | GDPC1 | 实际GDP季度数据 | 经济基本面 |
| CPI | CPIAUCSL | 消费者价格指数 | 通胀分析 |
| 失业率 | UNRATE | 失业率月度数据 | 劳动力市场 |
| 利率 | FEDFUNDS | 联邦基金利率 | 货币政策 |
| 就业 | PAYEMS | 非农就业人数 | 就业趋势 |
| 工业 | INDPRO | 工业生产指数 | 工业景气 |

---

## 🎯 覆盖率提升路径

### 当前状态: 22.2%
```
✅ ExchangeRate-API: 10个外汇
✅ Alpha Vantage: 5个美股
✅ CoinGecko: 10个加密货币
✅ OpenSpec: 3个港股 (部分)
```

### 申请FRED后: 25.9% (+3.7%)
```
✅ +6个宏观经济指标
```

### 申请IEX Cloud后: 32.1% (+6.2%)
```
✅ +10个高质量美股
```

### 申请Finnhub后: 37.0% (+4.9%)
```
✅ +8个全球股票数据
```

### 申请Quandl后: 39.9% (+2.9%)
```
✅ +5个金融数据
```

**最终目标**: 40%+ 覆盖率 ✅

---

## ⚠️ 常见问题

**Q: API密钥多久能收到?**
A: 通常1-5分钟内发送到邮箱

**Q: 需要信用卡吗?**
A: 完全免费，无需信用卡

**Q: 有请求限制吗?**
A: 120请求/分钟，足够使用

**Q: 密钥不工作怎么办?**
A: 检查邮箱垃圾邮件文件夹，确认密钥复制正确

---

## 📞 下一步

1. **申请并测试FRED API** (当前任务)
2. **创建FRED适配器** (`fred_adapter.py`)
3. **申请IEX Cloud API**
4. **申请Finnhub API**
5. **测试所有API集成**
6. **验证30%+覆盖率**

---

**状态**: 🚀 准备申请FRED API密钥
**预计完成**: 10分钟
**覆盖率提升**: +3.7% (22.2% → 25.9%)
