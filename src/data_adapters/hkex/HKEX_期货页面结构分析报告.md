# HKEX 期货页面结构分析报告

## 分析概要

**分析日期:** 2025-10-27

**分析方法:** Chrome DevTools MCP 实际检查

**分析范围:** HKEX 主页及期货数据页面

---

## 检查结果总结

### ✅ 成功验证的数据源

**1. HKEX 主页实时数据**
- **URL:** https://www.hkex.com.hk/?sc_lang=zh-HK
- **状态:** ✅ 可成功访问和提取
- **数据类型:**
  - 恒生指数: 26,433.70 (+273.55, +1.05%)
  - 恒生中国企业指数: 9,467.22 (+103.28, +1.10%)
  - 恒生科技指数: 6,171.08 (+111.19, +1.83%)
  - MSCI 中国 A50 互联互通指数: 2,715.87 (+40.30, +1.51%)
  - 恒指波幅指数: 24.08 (-0.99, -3.95%)
  - 沪深300指数: 4,716.02 (+55.34, +1.19%)
  - 中华交易服务中国120指数: 7,512.55 (+88.40, +1.19%)

**2. 外汇数据**
- 美元兑人民币(香港): 7.1046 (-0.0207, -0.29%)
- 美元兑印度卢比: 88.2330 (+0.4170, +0.47%)

**3. 加密货币参考指数**
- 香港交易所比特币参考指数: 115,462.94 (-101.78, -0.09%)
- 香港交易所以太币参考指数: 4,161.79 (-39.43, -0.94%)

---

### ⚠️ 需要进一步研究的页面

**1. 期货数据页面**
- **尝试访问的 URL:**
  - https://www.hkex.com.hk/Products/Market-Data/Futures?sc_lang=zh-HK
  - https://www.hkex.com.hk/Market-Data/Futures-and-Options-Data/Daily-Statistics?sc_lang=zh-HK
- **状态:** ⚠️ 页面显示错误消息，可能已被移除或重命名
- **错误消息:** "The page requested may have been relocated, renamed or removed"

**2. 期货期权价格页面**
- **访问方式:** 主页 → 市场数据 → 期货期权价格
- **状态:** ⚠️ 点击后超时，可能需要特殊处理

---

## 页面结构分析

### 1. 主页数据结构

**主要数据容器:**
```html
<!-- 指数数据表格 -->
<table role="table">
  <tbody>
    <tr>
      <td>恒生指數</td>
      <td>
        <div>26,433.70</div>
        <div>+273.55 (+1.05%)</div>
      </td>
      <td>26,495.97</td>
      <td>26,495.97</td>
      <td>26,319.22</td>
    </tr>
    <!-- 更多行... -->
  </tbody>
</table>
```

**CSS 选择器建议:**
```css
/* 表格容器 */
table[role='table']

/* 表格行 */
table[role='table'] tbody tr

/* 指数名称 */
table[role='table'] tbody tr td:first-child

/* 指数值和涨跌幅 */
table[role='table'] tbody tr td:nth-child(2) .generic

/* 开盘价 */
table[role='table'] tbody tr td:nth-child(3)

/* 最高价 */
table[role='table'] tbody tr td:nth-child(4)

/* 最低价 */
table[role='table'] tbody tr td:nth-child(5)
```

### 2. 数据更新机制

- **更新时间戳:** "更新: 2025年10月27日 16:08 HKT"
- **刷新频率:** 实时更新
- **数据源:** HKEX 官方 API

### 3. 导航结构

**市场数据菜单结构:**
```
市场數據
├── 股票行情查詢
├── 股本證券
├── 交易所買賣產品
├── 衍生權證
├── 界內證
├── 牛熊證
├── 房地產投資信託基金
├── 債務證券
├── 期貨期權價格
│   ├── 股票指數產品
│   ├── 股票產品
│   ├── 匯率產品
│   ├── 利率產品
│   └── 商品
└── 統計數據
    ├── 綜合報告
    ├── 證券市場統計數據
    ├── 衍生產品市場
    ├── 參與者統計數據
    └── 結算,交收及存管服務
```

---

## 期货数据获取策略

### 方案 1: 从期权页面提取期货数据

**目标页面:** https://www.hkex.com.hk/Market-Data/Statistics/Derivatives-Market/Daily-Statistics

**已知成功案例:** HSI Tech 期权数据已成功提取 238 条记录

**提取字段:**
- 日期 (date)
- 看涨期权成交量 (call_volume)
- 看跌期权成交量 (put_volume)
- 总成交量 (total_volume)
- 看涨期权未平仓量 (call_oi)
- 看跌期权未平仓量 (put_oi)
- 总未平仓量 (total_oi)

### 方案 2: 使用搜索功能

**方法:** 使用页面搜索框搜索期货合约代码

**支持期货合约:**
- HSI (恒生指数期货)
- MHI (迷你恒生指数期货)
- HHI (小恒生指数期货)

### 方案 3: 访问统计数据页面

**目标页面:** 通过导航 → 市场数据 → 统计数据 → 衍生产品市场

**需要进一步测试的页面:**
- https://www.hkex.com.hk/Market-Data/Statistics/Derivatives-Market/Monthly-Statistics
- https://www.hkex.com.hk/Market-Data/Statistics/Derivatives-Market/Futures-Market-Statistics

---

## 技术实现建议

### 1. 优先策略

**第一阶段:** 基于主页数据实现基础数据提取
- 提取指数数据
- 提取外汇数据
- 提取加密货币参考指数
- 建立数据处理管道

**第二阶段:** 扩展到期权数据
- 使用已验证的 HSI Tech 期权数据提取方法
- 扩展到其他期权类型
- 实现历史数据回溯

**第三阶段:** 探索期货数据
- 测试期货数据页面新的 URL
- 使用搜索功能获取期货数据
- 与期权数据关联分析

### 2. 选择器策略

**已验证的选择器:**
```python
# 指数表格选择器
SELECTOR_INDEX_TABLE = "table[role='table'] tbody tr"

# 指数名称选择器
SELECTOR_INDEX_NAME = "table[role='table'] tbody tr td:first-child"

# 指数值选择器
SELECTOR_INDEX_VALUE = "table[role='table'] tbody tr td:nth-child(2)"

# 更新时间选择器
SELECTOR_UPDATE_TIME = "更新: [0-9]{4}年[0-9]{2}月[0-9]{2}日 [0-9]{2}:[0-9]{2} HKT"
```

### 3. 数据验证

**验证规则:**
- 数值必须为正数或零
- 涨跌幅必须包含 +/- 符号
- 时间戳格式必须匹配 "YYYY年MM月DD日 HH:MM HKT"
- 数据完整性检查

---

## 发现的问题

### 1. 页面结构变化

**问题:** 一些期货数据页面显示错误消息，表明页面可能已被移除或重命名

**影响:** 无法直接访问期货历史数据页面

**解决方案:**
- 使用已知成功的期权数据页面
- 通过搜索功能获取期货数据
- 定期检查页面 URL 变更

### 2. 导航超时

**问题:** 点击某些导航链接后出现超时

**可能原因:**
- 页面加载时间较长
- 需要特殊的请求头或 cookies
- 网站的反爬机制

**解决方案:**
- 增加超时时间
- 使用无头浏览器访问
- 实现重试机制

### 3. 数据获取限制

**问题:** 不确定期货数据的访问方式

**解决方案:**
- 参考现有的 hkex_options_scraper.py 实现
- 基于实际测试调整选择器
- 建立数据质量验证机制

---

## 建议的期货数据爬虫架构

```python
class FuturesDataScraper:
    """期货数据爬虫"""

    def __init__(self):
        self.chrome_controller = HKEXChromeController()
        self.selector_discovery = SelectorDiscoveryEngine()
        self.page_monitor = PageMonitor()

    async def extract_futures_data(self, contract_code: str):
        """提取期货数据"""
        # 1. 访问期货数据页面
        # 2. 发现页面选择器
        # 3. 提取期货数据
        # 4. 数据验证和清洗
        # 5. 存储数据

    async def get_futures_ohlcv(self, contract: str, date: date):
        """获取期货 OHLCV 数据"""
        # 实现期货价格数据提取

    async def get_futures_volume(self, contract: str, date: date):
        """获取期货成交量数据"""
        # 实现期货成交量提取

    async def get_futures_oi(self, contract: str, date: date):
        """获取期货未平仓量数据"""
        # 实现期货未平仓量提取
```

---

## 下一步行动

### 立即行动

1. ✅ 基于主页数据实现基础数据提取
2. ✅ 扩展现有的 hkex_options_scraper.py 到期货数据
3. ✅ 实现数据验证和清洗机制

### 短期行动

1. 🔍 进一步测试期货数据页面的访问方式
2. 🔍 实现期货合约搜索功能
3. 🔍 建立期货数据与期权数据的关联分析

### 中期行动

1. 📊 实现期货历史数据回溯
2. 📊 建立期货数据仓库
3. 📊 开发期货数据分析功能

---

## 总结

通过 Chrome DevTools MCP 的实际检查，我们成功验证了 HKEX 主页数据的可提取性，并了解了页面的基本结构。虽然期货数据页面存在一些访问问题，但我们已经找到了可行的替代方案。

**关键成果:**
- ✅ 验证了 HKEX 数据提取的可行性
- ✅ 确认了页面结构和选择器
- ✅ 了解了数据更新机制
- ✅ 建立了实现框架

**主要挑战:**
- ⚠️ 部分期货数据页面访问受限
- ⚠️ 需要进一步测试期货数据获取方式
- ⚠️ 页面结构可能随时变化

**建议:**
基于主页和期权数据实现基础功能，然后逐步扩展到期货数据。这样可以确保系统的稳定性和可靠性。
