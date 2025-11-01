# Chrome DevTools 爬虫开发加速指南

使用 `chrome-devtools-mcp` + `scraper_development_kit.py` 快速开发替代数据爬虫

## 快速开始 (5分钟)

### 步骤 1: 启动开发工具包

```bash
cd src/data_adapters/scrapers
python scraper_development_kit.py
```

输出: 工作流指南 + 生成的爬虫代码框架

### 步骤 2: 使用Chrome DevTools分析网站

#### 打开目标网站
```bash
# 在Chrome中打开HKEX网站
https://www.hkex.com.hk/

# 或政府数据网站
https://data.gov.hk/
```

#### 查找数据容器
1. 按 `F12` 打开DevTools
2. 按 `Ctrl+Shift+C` 使用选择器工具
3. 点击页面上的数据元素 (例如: 期货成交量)
4. 在 Elements 标签查看 HTML 代码
5. **记录 CSS 选择器** (例如: `.futures-volume`, `[data-value="volume"]`)

#### 验证选择器
在 DevTools 的 Console 标签运行:

```javascript
// 验证选择器是否有效
document.querySelectorAll('.futures-volume').length  // 应该 > 0

// 获取数据值
document.querySelector('.futures-volume').textContent

// 获取属性值
document.querySelector('[data-volume]').getAttribute('data-volume')
```

### 步骤 3: 更新爬虫代码

编辑 `scraper_development_kit.py`，更新选择器:

```python
def create_hkex_scraper_target() -> ScraperTarget:
    return ScraperTarget(
        name="HKEX Futures",
        url="https://www.hkex.com.hk/",
        data_selectors={
            "hsi_volume": ".actual-selector-found",  # 👈 更新为找到的选择器
            "hsi_price": ".price-selector-here",     # 👈 更新
            # ...
        },
        extraction_rules={
            "hsi_volume": "text",      # text, data-attr, attr:href等
            "hsi_price": "text",
        }
    )
```

### 步骤 4: 测试爬虫

```python
import asyncio
from scraper_development_kit import create_hkex_scraper_target, ScraperDevKit

kit = ScraperDevKit()
kit.register_target(create_hkex_scraper_target())

# 生成爬虫代码
code = kit.generate_scraper_code(kit.targets["HKEX Futures"])

# 保存并测试
with open("hkex_scraper_test.py", "w", encoding="utf-8") as f:
    f.write(code)

# 运行测试
# python hkex_scraper_test.py
```

## Chrome DevTools 常用技巧

### 选择器查找技巧

| 任务 | 方法 |
|------|------|
| 找ID元素 | 点击元素 → Elements → 查看 `id="..."`  |
| 找Class | 点击元素 → Elements → 查看 `class="..."`  |
| 找属性值 | 点击元素 → Elements → 查看 `data-*` 属性 |
| 验证XPath | Console: `$x('//div[@class="target"]').length` |
| 获取文本 | Console: `document.querySelector('.target').textContent` |

### 常见选择器模式

```css
/* 按Class找 */
.futures-volume
.market-data

/* 按ID找 */
#hsi-volume
#market-time

/* 按属性找 */
[data-value="volume"]
[data-currency="HKD"]

/* 按标签+Class找 */
div.price-container
span.value

/* 嵌套选择 */
.market-data .futures-volume .value
```

### 提取规则

| 规则 | 说明 | 示例 |
|------|------|------|
| `text` | 获取元素文本 | 期货成交量数字 |
| `data-attr` | 获取 data-* 属性 | `data-volume`, `data-price` |
| `attr:href` | 获取其他属性 | `href`, `src`, `title` |
| `html` | 获取HTML内容 | 复杂的HTML结构 |

## 目标网站分析示例

### HKEX (hkex.com.hk)

```
期货数据位置分析:
├─ 页面: https://www.hkex.com.hk/
├─ 数据容器: .market-data 或 #futures-container
├─ 选择器示例:
│  ├─ HSI期货: .futures-hsi .last-price
│  ├─ MHI期货: .futures-mhi .volume
│  └─ 时间戳: .market-timestamp
└─ 更新频率: 实时 (每几秒)
```

### 政府数据 (data.gov.hk)

```
经济指标位置分析:
├─ 页面: https://data.gov.hk/
├─ 数据容器: 通常是API或结构化表格
├─ 选择器示例:
│  ├─ HIBOR: .hibor-indicator .value
│  ├─ 访客: .visitor-stats .number
│  └─ 更新: .last-update-time
└─ 更新频率: 每天 (通常18:00后)
```

## 高级用法

### 动态内容处理

如果网站使用JavaScript渲染内容:

```python
# 使用Selenium而不是httpx
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

driver = webdriver.Chrome()
driver.get("https://www.hkex.com.hk/")
time.sleep(3)  # 等待JS加载

# 现在DOM已准备好
volume_element = driver.find_element(By.CSS_SELECTOR, ".futures-volume")
volume = volume_element.text
```

### 错误处理和重试

```python
async def fetch_with_retry(self, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await self.fetch_data()
        except Exception as e:
            wait_time = 2 ** attempt  # 指数退避
            logger.warning(f"重试 {attempt+1}/{max_retries}, 等待{wait_time}秒...")
            await asyncio.sleep(wait_time)
    raise Exception("所有重试均失败")
```

### 性能优化

```python
# 缓存优化
self.cache_ttl = 3600  # 1小时

# 并发抓取多个页面
async def fetch_multiple(self, urls):
    tasks = [self.fetch_url(url) for url in urls]
    return await asyncio.gather(*tasks)
```

## 工作流检查清单

- [ ] 打开DevTools (F12)
- [ ] 使用选择器工具找到数据容器
- [ ] 记录CSS选择器和提取规则
- [ ] 在Console验证选择器
- [ ] 更新 `scraper_development_kit.py`
- [ ] 生成爬虫代码
- [ ] 本地测试爬虫
- [ ] 集成到适配器
- [ ] 添加单元测试
- [ ] 性能测试 (缓存, 并发)

## 常见问题

### Q: 选择器经常变化怎么办?
A: 使用更稳定的选择器 (ID > data-attr > Class)，添加备用选择器

### Q: 网站反爬虫怎么办?
A: 添加User-Agent, 随机延迟, 使用代理

### Q: 如何处理登录页面?
A: 使用Selenium处理Cookie, 或通过API直接获取数据

### Q: 如何测试爬虫可靠性?
A: 运行多天的数据采集，验证数据一致性和缺失率

## 快速参考命令

```bash
# 生成爬虫代码
python scraper_development_kit.py

# 测试爬虫
python hkex_scraper.py

# 集成到适配器
# 1. 复制生成的爬虫类到 hkex_data_collector.py
# 2. 在 AlternativeDataAdapter 中实现 fetch_data()

# 运行单元测试
pytest tests/test_hkex_scraper.py -v

# 性能分析
python -m cProfile -s cumulative hkex_scraper.py
```

## 预期时间表

| 步骤 | 时间 | 说明 |
|------|------|------|
| 网站分析 | 5-10分钟 | 使用DevTools找选择器 |
| 代码生成 | 1分钟 | 运行工具包生成框架 |
| 本地测试 | 5分钟 | 测试爬虫逻辑 |
| 集成 | 10分钟 | 集成到适配器 |
| 单元测试 | 10分钟 | 编写测试用例 |
| 性能优化 | 15分钟 | 缓存, 并发, 重试 |
| **总计** | **45分钟** | **完整爬虫就绪** |

---

**下一步**: 选择一个目标网站，使用chrome-devtools分析，然后运行工具包生成爬虫代码！
