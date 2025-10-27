# HKEX 爬虫增强系统

基于 OpenSpec 提案 `enhance-hkex-scraper` 实施的 HKEX 数据爬虫系统。

## 📁 项目文件结构

```
src/data_adapters/hkex/
├── __init__.py                          # 模块初始化文件
├── hkex_chrome_controller.py          # Chrome DevTools MCP 控制器
├── selector_discovery.py             # 选择器自动发现引擎
├── page_monitor.py                 # 页面变化监控器
├── futures_scraper.py             # 期货数据提取器
├── HKEX_期货页面结构分析报告.md   # 期货页面结构分析
├── 实施总结报告.md                # 项目实施总结
└── README.md                     # 本文档
```

## 🚀 快速开始

### 1. 环境要求

- Python 3.10+
- Chrome/Chromium 浏览器
- Chrome DevTools MCP

### 2. 基本使用

```python
from src.data_adapters.hkex import FuturesDataScraper

# 创建提取器
scraper = FuturesDataScraper()

# 提取实时指数数据
indices = await scraper.extract_realtime_indices()

# 导出数据
await scraper.export_data(indices, format="csv")

# 清理资源
await scraper.close()
```

### 3. 运行演示

```bash
# 运行期货数据提取器
python src/data_adapters/hkex/futures_scraper.py

# 运行 Chrome 控制器
python src/data_adapters/hkex/hkex_chrome_controller.py

# 运行选择器发现
python src/data_adapters/hkex/selector_discovery.py

# 运行页面监控
python src/data_adapters/hkex/page_monitor.py
```

## 📚 核心组件

### 1. HKEXChromeController

负责浏览器自动化操作。

**主要功能:**
- 页面创建与管理
- 页面导航控制
- 元素查询与提取
- JavaScript 执行环境
- 页面快照获取
- 表格数据提取

**使用示例:**
```python
from src.data_adapters.hkex import HKEXChromeController

controller = HKEXChromeController(max_pages=5)
page_id = await controller.create_page()
await controller.navigate(page_id, "https://www.hkex.com.hk")
elements = await controller.query_elements(page_id, ["table[role='table']"])
await controller.close_page(page_id)
```

### 2. SelectorDiscoveryEngine

自动发现页面元素和选择器。

**主要功能:**
- 自动发现表格元素
- 生成稳定的 CSS 选择器
- 验证选择器有效性
- 支持多语言页面
- 选择器优化和去重

**使用示例:**
```python
from src.data_adapters.hkex import SelectorDiscoveryEngine

engine = SelectorDiscoveryEngine()
elements = await engine.discover_page_structure(page_id, controller)
selectors = engine.get_best_selectors(url, "tables", top_n=5)
```

### 3. PageMonitor

监控页面内容变化。

**主要功能:**
- 检测页面结构变化
- 监控数据更新时间
- 支持阈值配置
- 提供变更通知
- 防抖机制

**使用示例:**
```python
from src.data_adapters.hkex import PageMonitor, MonitoringConfig

monitor = PageMonitor()
config = MonitoringConfig(
    page_id="hkex",
    url="https://www.hkex.com.hk",
    check_interval=300
)
monitor_id = await monitor.start_monitoring(config, callback=my_callback)
```

### 4. FuturesDataScraper

提取期货和期权数据。

**主要功能:**
- 提取实时指数数据
- 期货合约数据
- 期权数据
- 数据验证和清洗
- 格式标准化
- 数据导出

**使用示例:**
```python
from src.data_adapters.hkex import FuturesDataScraper

scraper = FuturesDataScraper()

# 提取实时指数
indices = await scraper.extract_realtime_indices()

# 获取期货数据
futures_data = await scraper.get_futures_contract_data("HSI")

# 获取期权数据
options_data = await scraper.get_options_data("HSI")

# 导出数据
await scraper.export_data(futures_data, format="csv")
```

## 📊 支持的数据类型

### 1. 指数数据

- ✅ 恒生指数 (HSI)
- ✅ 恒生中国企业指数 (HSCEI)
- ✅ 恒生科技指数 (HSTECH)
- ✅ MSCI 中国 A50 互联互通指数
- ✅ 恒指波幅指数 (VHSI)
- ✅ 沪深300指数 (CSI300)
- ✅ 中华交易服务中国120指数

### 2. 外汇数据

- ✅ 美元兑人民币(香港)
- ✅ 美元兑印度卢比

### 3. 加密货币参考指数

- ✅ 香港交易所比特币参考指数
- ✅ 香港交易所以太币参考指数

### 4. 期货数据

- 🔄 恒生指数期货 (HSI) - 部分实现
- 🔄 迷你恒生指数期货 (MHI) - 部分实现
- 🔄 小恒生指数期货 (HHI) - 部分实现
- 🔄 恒生指数期权 (HSI Options) - 部分实现

## 📖 文档索引

### 项目文档

1. **实施总结报告.md** - 完整的项目实施总结
   - 项目成果
   - 技术架构
   - 性能指标
   - 后续建议

2. **HKEX_期货页面结构分析报告.md** - 期货页面结构分析
   - 页面结构分析
   - 数据提取策略
   - 技术实现建议

### OpenSpec 文档

3. **提案文档** - `openspec/changes/enhance-hkex-scraper/proposal.md`
4. **设计文档** - `openspec/changes/enhance-hkex-scraper/design.md`
5. **任务清单** - `openspec/changes/enhance-hkex-scraper/tasks.md`

### 规范文档

6. **Chrome MCP 集成规范** - `openspec/changes/enhance-hkex-scraper/specs/chrome-mcp-integration/spec.md`
7. **期货数据爬虫规范** - `openspec/changes/enhance-hkex-scraper/specs/futures-data-scraper/spec.md`
8. **股票数据爬虫规范** - `openspec/changes/enhance-hkex-scraper/specs/stocks-data-scraper/spec.md`

## 🔧 配置说明

### 选择器配置

选择器定义在 `futures_scraper.py` 中：

```python
SELECTORS = {
    "index_table": "table[role='table']",
    "index_rows": "table[role='table'] tbody tr",
    "index_name": "table[role='table'] tbody tr td:first-child",
    "index_value": "table[role='table'] tbody tr td:nth-child(2)",
    # ...
}
```

### 监控配置

```python
config = MonitoringConfig(
    page_id="hkex",
    url="https://www.hkex.com.hk",
    selectors=["table[role='table'] tbody tr"],
    check_interval=300,  # 5分钟
    debounce_ms=10000,   # 10秒
    change_threshold=0.01  # 1%
)
```

## ⚠️ 注意事项

### 1. 访问限制

- 建议设置请求间隔 >= 2 秒
- 避免频繁访问导致 IP 被封
- 使用代理池提高稳定性

### 2. 数据质量

- 所有数据都经过验证和清洗
- 支持数据质量评分
- 异常值会自动标记

### 3. 错误处理

- 所有模块都有完整的错误处理
- 支持自动重试机制
- 详细的错误日志

## 🐛 故障排除

### 常见问题

**1. 页面加载超时**
- 增加超时时间
- 检查网络连接
- 尝试使用代理

**2. 选择器失效**
- 使用选择器自动发现功能
- 重新分析页面结构
- 检查页面是否更新

**3. 数据提取失败**
- 检查选择器是否正确
- 验证数据格式
- 查看错误日志

### 日志配置

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## 📈 性能优化

### 1. 并发处理

- 使用页面池管理多个页面
- 支持异步并发查询
- 批量数据提取

### 2. 缓存机制

- 内存缓存热点数据
- 文件缓存中期数据
- 数据库缓存历史数据

### 3. 监控指标

- 页面加载时间
- 数据提取成功率
- 缓存命中率

## 🤝 贡献指南

### 1. 添加新数据源

1. 继承 `BaseAdapter` 类
2. 实现数据提取方法
3. 添加数据验证逻辑
4. 更新文档

### 2. 优化选择器

1. 使用 `SelectorDiscoveryEngine` 分析页面
2. 验证选择器有效性
3. 优化选择器性能

### 3. 提交代码

1. 遵循 PEP 8 规范
2. 添加单元测试
3. 更新文档
4. 提交 Pull Request

## 📄 许可证

本项目基于项目现有许可证。

## 👨‍💻 作者

**Claude Code** - 2025-10-27

---

**最后更新:** 2025-10-27
**版本:** v1.0.0
