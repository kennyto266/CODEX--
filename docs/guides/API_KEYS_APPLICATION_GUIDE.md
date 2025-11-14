# API密钥申请完整指南

## 🎯 目标

将真实数据覆盖率从22.2%提升到30%+

---

## 📊 当前状态

| 数据源 | 状态 | 数据点 |
|--------|------|--------|
| ExchangeRate-API | ✅ 已集成 | 10个外汇汇率 |
| Alpha Vantage | ✅ 已集成 | 5+个美股 |
| CoinGecko API | ✅ 已集成 | 10个加密货币 |
| OpenSpec API | ✅ 已集成 | 3个港股 |
| FRED API | ❌ 需要密钥 | 15+个宏观经济指标 |
| IEX Cloud | ❌ 需要密钥 | 10+个美股 |
| Finnhub | ❌ 需要密钥 | 10+个股票 |
| Polygon.io | ❌ 需要密钥 | 10+个股票 |

---

## 🚀 API申请清单

### 1. FRED API (联邦储备银行) - 最高优先级 ⭐⭐⭐⭐⭐

**数据价值**: 宏观经济数据
- GDP增长率
- 通胀率
- 失业率
- 利率
- 贸易数据
- 工业生产
- 消费者信心

**申请步骤**:
1. 访问: https://fred.stlouisfed.org/docs/api/api_key.html
2. 点击 "Request API Key"
3. 输入邮箱地址
4. 验证邮箱
5. 接收API密钥

**免费额度**:
- 120请求/分钟
- 无需信用卡

**预计数据点数**: +15个真实指标
**覆盖率提升**: +9.3% (15/162)

---

### 2. IEX Cloud API - 高优先级 ⭐⭐⭐⭐⭐

**数据价值**: 高质量美股数据
- 实时股价
- 公司基本面
- 财务数据
- 新闻情绪
- 技术指标

**申请步骤**:
1. 访问: https://iexcloud.io/cloud-login#/register
2. 注册账户 (使用邮箱)
3. 验证邮箱
4. 获取API密钥

**免费额度**:
- 500,000请求/月
- 无需信用卡

**预计数据点数**: +10个真实指标
**覆盖率提升**: +6.2% (10/162)

---

### 3. Finnhub API - 高优先级 ⭐⭐⭐⭐

**数据价值**: 全球股票市场
- 美股、港股、A股
- 外汇数据
- 加密货币
- 商品数据
- 公司新闻

**申请步骤**:
1. 访问: https://finnhub.io/register
2. 注册账户
3. 获取API密钥 (立即可用)

**免费额度**:
- 60请求/分钟
- 无需信用卡

**预计数据点数**: +8个真实指标
**覆盖率提升**: +4.9% (8/162)

---

### 4. Alpha Vantage Premium (可选) ⭐⭐⭐

**当前状态**: 已申请免费版
**升级好处**:
- 更快的请求速度
- 更多功能
- 实时数据

**费用**: $49.99/月

**预计数据点数**: +5个真实指标
**覆盖率提升**: +3.1% (5/162)

---

### 5. Polygon.io API - 中优先级 ⭐⭐⭐

**数据价值**: 高频交易数据
- 实时报价
- 历史tick数据
- 期权数据
- 期货数据

**申请步骤**:
1. 访问: https://polygon.io/signup
2. 注册账户
3. 获取API密钥

**免费额度**:
- 基本的股票和加密货币数据
- 需要信用卡验证

**预计数据点数**: +5个真实指标
**覆盖率提升**: +3.1% (5/162)

---

## 📝 申请流程模板

### 邮件内容模板

```
主题: API Key Application for Research Project

Dear API Provider,

I am a researcher working on a quantitative trading system project.
I would like to apply for a free API key to access your financial data for:
- Stock market data
- Economic indicators
- Market analysis

This is for academic research purposes only, non-commercial use.
I will respect your rate limits and terms of service.

My email: [YOUR_EMAIL]
Use case: Quantitative trading research
Data types needed: [SPECIFY]

Thank you for your service.

Best regards,
[YOUR_NAME]
```

---

## ⚙️ 环境变量配置

### Windows (PowerShell)
```powershell
# 设置环境变量
$env:FRED_API_KEY = "your_fred_key"
$env:IEX_CLOUD_API_KEY = "your_iex_key"
$env:FINNHUB_API_KEY = "your_finnhub_key"
$env:POLYGON_API_KEY = "your_polygon_key"

# 验证设置
echo $env:FRED_API_KEY
echo $env:IEX_CLOUD_API_KEY
```

### Linux/Mac (Bash)
```bash
# 添加到 ~/.bashrc 或 ~/.zshrc
export FRED_API_KEY="your_fred_key"
export IEX_CLOUD_API_KEY="your_iex_key"
export FINNHUB_API_KEY="your_finnhub_key"
export POLYGON_API_KEY="your_polygon_key"

# 应用更改
source ~/.bashrc
# 或
source ~/.zshrc

# 验证
echo $FRED_API_KEY
echo $IEX_CLOUD_API_KEY
```

---

## 📋 检查清单

### 申请阶段
- [ ] 申请FRED API密钥
- [ ] 申请IEX Cloud API密钥
- [ ] 申请Finnhub API密钥
- [ ] (可选) 申请Polygon.io API密钥

### 配置阶段
- [ ] 设置FRED_API_KEY环境变量
- [ ] 设置IEX_CLOUD_API_KEY环境变量
- [ ] 设置FINNHUB_API_KEY环境变量
- [ ] 测试API连接

### 集成阶段
- [ ] 创建FRED适配器
- [ ] 创建IEX Cloud适配器
- [ ] 创建Finnhub适配器
- [ ] 更新统一数据管理系统
- [ ] 测试所有数据源

### 验证阶段
- [ ] 运行覆盖率测试
- [ ] 验证数据质量
- [ ] 检查错误日志
- [ ] 确认覆盖率提升

---

## 🎯 预计覆盖率提升

| API | 数据点 | 覆盖率提升 |
|-----|--------|-----------|
| FRED | +15 | +9.3% |
| IEX Cloud | +10 | +6.2% |
| Finnhub | +8 | +4.9% |
| Polygon.io | +5 | +3.1% |
| **总计** | **+38** | **+23.5%** |

**当前**: 22.2%
**预计新总计**: 22.2% + 23.5% = **45.7%**

**实际考虑**:
- 不是所有申请都能立即获得
- 可能需要时间集成
- **保守估计**: +15% (达到37%+)

**最终目标**: 30%+ (保守) 或 45%+ (乐观)

---

## ⏱️ 时间估算

| 任务 | 预计时间 |
|------|----------|
| 申请所有API | 30分钟 |
| 配置环境变量 | 10分钟 |
| 创建适配器 | 2小时 |
| 测试集成 | 1小时 |
| **总计** | **3.5小时** |

---

## 🔗 有用链接

1. **FRED API**: https://fred.stlouisfed.org/docs/api/api_key.html
2. **IEX Cloud**: https://iexcloud.io/cloud-login#/register
3. **Finnhub**: https://finnhub.io/register
4. **Polygon.io**: https://polygon.io/signup
5. **Alpha Vantage**: https://www.alphavantage.co/support/#api-key (已有)

---

## 💡 小贴士

1. **立即行动**: 很多API都是自动审批的
2. **检查邮箱**: API密钥通常通过邮件发送
3. **记录密钥**: 建议保存在密码管理器中
4. **遵守限制**: 不要超过免费额度
5. **备份方案**: 如果某个API失败，有其他替代方案

---

**开始申请吧！预计3-4小时内完成所有API申请和集成！** 🚀
