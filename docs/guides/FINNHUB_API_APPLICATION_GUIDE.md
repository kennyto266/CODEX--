# Finnhub API密钥申请指南

## 🎯 目标

申请Finnhub API密钥，将真实数据覆盖率从32.1%提升到**37.0%**

---

## 📊 Finnhub数据价值

**全球金融市场数据** - 一站式市场数据平台

### 可获取的核心数据 (8+个)

| 数据类别 | 具体数据 | 数据价值 | 预计覆盖提升 |
|----------|----------|----------|--------------|
| **美股数据** | AAPL, MSFT, GOOGL, AMZN, TSLA | 补充Alpha Vantage数据 | +3.1% |
| **港股数据** | 0700.HK, 0939.HK, 0388.HK | 改善港股数据获取 | +1.2% |
| **外汇数据** | USD/CNY, EUR/USD | 外汇市场补充 | +0.4% |
| **加密货币** | BTC, ETH, USDT | 补充CoinGecko数据 | +0.2% |

**总预计提升**: +4.9% (8/162)

---

## 🚀 申请步骤

### 步骤1: 访问注册页面

打开浏览器，访问：
```
https://finnhub.io/register
```

### 步骤2: 注册账户

1. **填写注册表单**
   ```
   Full Name: [输入您的姓名]
   Email: [输入您的邮箱]
   Password: [设置密码]
   Company: [输入公司/机构名称]
   Intended Use: [选择用途]
     - 选择: Academic Research
     或选择: Quant Research
   ```

2. **同意条款**
   - ☑️ 勾选 "I agree to Terms of Service"
   - ☑️ 勾选 "I agree to Privacy Policy"

3. **点击注册**
   ```
   点击 "Create Free Account" 按钮
   ```

### 步骤3: 验证邮箱

1. **检查邮箱** (立即)
   - 发件人: `noreply@finnhub.io`
   - 主题: `Verify your email - Finnhub`

2. **点击验证链接**
   - 在邮件中点击 "Verify Email" 按钮

3. **登录账户**
   ```
   访问: https://finnhub.io/login
   Email: [您的邮箱]
   Password: [设置的密码]
   ```

### 步骤4: 获取API密钥

1. **进入控制台**
   ```
   登录后自动进入: https://finnhub.io/dashboard
   ```

2. **查看API密钥**
   ```
   菜单 → API Key 或 Profile → API Key
   ```

3. **复制密钥**
   ```
   格式: cxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

4. **设置环境变量**

**Windows (PowerShell)**:
```powershell
# 设置环境变量
$env:FINNHUB_API_KEY = "cxxxxxxxxxxxxxxxxxxxxxxxxxx"

# 验证设置
echo $env:FINNHUB_API_KEY
```

**Linux/Mac (Bash)**:
```bash
# 添加到 ~/.bashrc 或 ~/.zshrc
export FINNHUB_API_KEY="cxxxxxxxxxxxxxxxxxxxxxxxxxx"

# 应用更改
source ~/.bashrc

# 验证
echo $FINNHUB_API_KEY
```

---

## 📋 免费额度

| 项目 | 限制 | 备注 |
|------|------|------|
| **请求频率** | 60请求/分钟 | 较宽松限制 |
| **实时数据** | ✅ 包含 | 免费版也提供实时数据 |
| **数据延迟** | 15分钟延迟 | 实时数据15分钟延迟 |
| **信用卡要求** | ❌ 不需要 | 完全免费 |
| **历史数据** | ✅ 可访问 | 1年历史数据 |

---

## 🧪 测试API密钥

### 方法1: 使用curl

```bash
# 测试获取AAPL股票价格
curl "https://finnhub.io/api/v1/quote?symbol=AAPL&token=YOUR_API_KEY"

# 预期响应格式
{
  "c": 270.04,  // Current price
  "d": -2.15,   // Change
  "dp": -0.79,  // Percent change
  "h": 272.50,  // High price of the day
  "l": 269.00,  // Low price of the day
  "o": 271.00,  // Open price of the day
  "pc": 272.19, // Previous close price
  "t": 1234567890  // Timestamp
}
```

### 方法2: 使用Python测试脚本

创建 `test_finnhub.py`:

```python
#!/usr/bin/env python3
import requests
import os
import json
import time

# 设置API密钥
FINNHUB_KEY = os.environ.get('FINNHUB_API_KEY')
if not FINNHUB_KEY:
    print("请先设置FINNHUB_API_KEY环境变量")
    exit(1)

# 测试获取多支股票数据
symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
base_url = "https://finnhub.io/api/v1"

print("Finnhub API测试")
print("=" * 70)

for symbol in symbols:
    url = f"{base_url}/quote"
    params = {
        'symbol': symbol,
        'token': FINNHUB_KEY
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        print(f"\n[{symbol}]")
        print(f"  当前价格: ${data.get('c', 0):.2f}")
        print(f"  涨跌: {data.get('d', 0):+.2f} ({data.get('dp', 0):+.2f}%)")
        print(f"  今日开盘: ${data.get('o', 0):.2f}")
        print(f"  今日最高: ${data.get('h', 0):.2f}")
        print(f"  今日最低: ${data.get('l', 0):.2f}")

        # 避免请求过快
        time.sleep(0.1)

    except Exception as e:
        print(f"\n[{symbol}] ERROR: {str(e)[:50]}")

print("\n" + "=" * 70)
print("Finnhub API测试完成")
```

运行测试:
```bash
python test_finnhub.py
```

---

## 📈 集成到系统

### 更新适配器配置

1. **创建Finnhub适配器** `finnhub_adapter.py`
   ```python
   import os
   import requests
   from typing import Dict, Any

   class FinnhubAdapter:
       def __init__(self):
           self.api_key = os.environ.get('FINNHUB_API_KEY')
           self.base_url = "https://finnhub.io/api/v1"

       async def get_quote(self, symbol: str):
           url = f"{self.base_url}/quote"
           params = {
               'symbol': symbol,
               'token': self.api_key
           }
           # ... 实现获取报价
   ```

2. **港股数据增强**
   ```python
   async def get_hk_stock_data(self, symbol: str):
       # Finnhub港股代码格式: 0700.HK
       hk_symbol = f"{symbol}.HK"
       quote = await self.get_quote(hk_symbol)
       # ... 处理港股数据
   ```

---

## 🎯 覆盖提升计划

### 申请Finnhub后 (+4.9% → 37.0%)
- 新增: 全球股票数据 8个
  - 美股补充: 5个
  - 港股改善: 3个

### 申请Quandl后 (+2.9% → 39.9%)
- 新增: 金融数据 5个

---

## ⏱️ 时间估算

| 任务 | 预计时间 | 实际可能时间 |
|------|----------|--------------|
| 填写注册表单 | 3分钟 | 2-5分钟 |
| 验证邮箱 | 1分钟 | 1-3分钟 |
| 获取API密钥 | 2分钟 | 1-3分钟 |
| 配置环境变量 | 3分钟 | 2-5分钟 |
| 测试API | 5分钟 | 5-10分钟 |
| 集成到系统 | 30分钟 | 30-60分钟 |
| **总计** | **44分钟** | **41-86分钟** |

---

## 🔗 有用链接

- **Finnhub主页**: https://finnhub.io/
- **注册页面**: https://finnhub.io/register
- **登录页面**: https://finnhub.io/login
- **API文档**: https://finnhub.io/docs/api
- **控制台**: https://finnhub.io/dashboard

---

## 💡 小贴士

1. **自动获批**: Finnhub注册后立即可用，无需审批
2. **免费计划足够**: 60请求/分钟适合测试使用
3. **数据质量好**: 实时数据仅15分钟延迟
4. **港股支持**: 对港股数据支持较好
5. **全面覆盖**: 股票、外汇、加密货币均可获取

---

## ❗ 注意事项

1. **请求频率**: 注意60请求/分钟限制
2. **数据延迟**: 免费版数据延迟15分钟
3. **历史数据**: 仅1年历史数据可访问
4. **速率控制**: 测试时避免请求过快

---

## ✅ 检查清单

### 申请阶段
- [ ] 访问 https://finnhub.io/register
- [ ] 填写注册表单 (邮箱 + 密码 + 用途)
- [ ] 验证邮箱
- [ ] 登录控制台获取API密钥

### 配置阶段
- [ ] 设置FINNHUB_API_KEY环境变量
- [ ] 运行测试脚本验证
- [ ] 检查API响应格式

### 集成阶段
- [ ] 创建Finnhub适配器
- [ ] 测试获取美股数据
- [ ] 测试获取港股数据
- [ ] 更新终极数据融合系统
- [ ] 重新计算覆盖率

### 验证阶段
- [ ] 确认覆盖率达到37.0%+
- [ ] 验证数据质量
- [ ] 检查错误日志

---

**预计完成时间**: 44分钟
**预计覆盖率提升**: +4.9% (32.1% → 37.0%)
**状态**: 🚀 准备申请
