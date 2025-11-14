# C&SD数据适配器 (Phase 8b - T345-T349)

## 概述

Phase 8b实现了5个香港统计处(C&SD)经济数据适配器，支持从C&SD官网自动获取和解析各种经济指标数据。所有适配器均基于统一的架构设计，支持异步操作、缓存机制和错误恢复。

## 适配器列表

| 任务ID | 适配器名称 | 文件路径 | 功能描述 |
|--------|------------|----------|----------|
| T345 | CSDDataCrawler | `src/data_adapters/cs_d_crawler.py` | C&SD经济数据爬虫 |
| T346 | GDPParser | `src/data_adapters/gdp_parser.py` | GDP和经济指标解析器 |
| T347 | RetailDataProcessor | `src/data_adapters/retail_parser.py` | 零售销售数据处理器 |
| T348 | VisitorDataProcessor | `src/data_adapters/visitor_parser.py` | 访港旅客数据处理器 |
| T349 | TradeDataIntegrator | `src/data_adapters/trade_parser.py` | 贸易数据集成器 |

## 架构设计

### 统一基类

所有适配器继承自 `UnifiedBaseAdapter`，提供以下统一功能：

- **缓存管理** (`CacheManager`): 内存缓存减少重复请求
- **错误处理** (`ErrorHandler`): 统一的错误处理和重试机制
- **异步支持**: 完全支持异步操作
- **数据验证**: 自动数据格式验证和质量检查

### 核心特性

1. **多格式支持**: CSV、Excel、XML、JSON
2. **自动格式检测**: 智能识别数据格式
3. **增长率计算**: 自动计算同比/环比增长率
4. **数据转换**: 转换为pandas DataFrame
5. **类型系统**: 使用Pydantic模型确保数据安全

## 快速开始

### 1. CSDDataCrawler - 数据爬虫

```python
from src.data_adapters import CSDDataCrawler, CSDCrawlerConfig, CSDDataType

# 创建配置
config = CSDCrawlerConfig(
    base_url="https://www.censtatd.gov.hk",
    download_dir="data/csd_downloads",
    rate_limit=1.0
)

# 初始化爬虫
crawler = CSDDataCrawler(config)

# 发现数据表
tables = await crawler.discover_tables(CSDDataType.GDP)

# 获取数据
result = await crawler.fetch_data(CSDDataType.GDP)

# 关闭资源
await crawler.close()
```

### 2. GDPParser - GDP解析

```python
from src.data_adapters import GDPParser, GDPIndicator

# 初始化解析器
parser = GDPParser()

# 解析GDP文件
datasets = await parser.parse_gdp_data('data/gdp.xlsx')

# 获取特定指标
gdp_data = await parser.get_gdp_data(GDPIndicator.NOMINAL_GDP)

# 计算增长率
growth_rates = await parser.calculate_gdp_growth(GDPIndicator.NOMINAL_GDP)

# 导出为DataFrame
df = await parser.export_to_dataframe(GDPIndicator.NOMINAL_GDP)
print(df.head())
```

### 3. RetailDataProcessor - 零售数据处理

```python
from src.data_adapters import RetailDataProcessor, RetailCategory

# 初始化处理器
processor = RetailDataProcessor()

# 解析零售文件
datasets = await processor.parse_retail_data('data/retail.xlsx')

# 获取特定类别
retail_data = await processor.get_retail_data(RetailCategory.TOTAL_SALES)

# 计算市场份额
market_share = await processor.calculate_market_share(RetailCategory.CLOTHING, date(2023, 12, 1))

# 导出为DataFrame
df = await processor.export_to_dataframe(RetailCategory.TOTAL_SALES)
```

### 4. VisitorDataProcessor - 访客数据处理

```python
from src.data_adapters import VisitorDataProcessor, VisitorType

# 初始化处理器
processor = VisitorDataProcessor()

# 解析访客文件
datasets = await processor.parse_visitor_data('data/visitors.xlsx')

# 获取特定访客类型
visitor_data = await processor.get_visitor_data(VisitorType.TOTAL_VISITORS)

# 计算访客占比
share = await processor.calculate_visitor_share(VisitorType.MAINLAND_CHINA, date(2023, 12, 1))

# 获取季节性模式
patterns = await processor.get_seasonal_patterns(VisitorType.TOTAL_VISITORS)
print(patterns)
```

### 5. TradeDataIntegrator - 贸易数据集成

```python
from src.data_adapters import TradeDataIntegrator, TradeType, TradeCategory

# 初始化集成器
integrator = TradeDataIntegrator()

# 解析贸易文件
datasets = await integrator.parse_trade_data('data/trade.xlsx')

# 获取贸易数据
trade_data = await integrator.get_trade_data(TradeType.EXPORTS, TradeCategory.TOTAL_TRADE)

# 计算贸易差额
balance = await integrator.calculate_trade_balance(TradeCategory.TOTAL_TRADE, date(2023, 12, 1))

# 获取主要贸易伙伴
top_partners = await integrator.get_top_trade_partners(TradeType.EXPORTS, TradeCategory.TOTAL_TRADE)
print(top_partners)
```

## 便捷函数

每个适配器都提供了便捷函数，简化使用：

```python
# GDP解析
from src.data_adapters import parse_gdp_file, get_gdp_indicator

datasets = await parse_gdp_file('data/gdp.xlsx')
gdp_data = await get_gdp_indicator('data/gdp.xlsx', GDPIndicator.NOMINAL_GDP)

# 零售数据处理
from src.data_adapters import parse_retail_file, get_retail_category

datasets = await parse_retail_file('data/retail.xlsx')
retail_data = await get_retail_category('data/retail.xlsx', RetailCategory.TOTAL_SALES)

# 访客数据处理
from src.data_adapters import parse_visitor_file, get_visitor_type

datasets = await parse_visitor_file('data/visitors.xlsx')
visitor_data = await get_visitor_type('data/visitors.xlsx', VisitorType.TOTAL_VISITORS)

# 贸易数据集成
from src.data_adapters import parse_trade_file, get_trade_data

datasets = await parse_trade_file('data/trade.xlsx')
trade_data = await get_trade_data('data/trade.xlsx', TradeType.EXPORTS, TradeCategory.TOTAL_TRADE)
```

## 数据模型

### GDP数据模型

```python
from src.data_adapters import GDPIndicator, GDPFrequency

class GDPDataPoint(BaseModel):
    indicator: GDPIndicator
    frequency: GDPFrequency
    date: date
    value: Decimal
    unit: str
    growth_rate: Optional[Decimal]
    source: str
```

### 零售数据模型

```python
from src.data_adapters import RetailCategory, RetailFrequency

class RetailDataPoint(BaseModel):
    category: RetailCategory
    frequency: RetailFrequency
    date: date
    value: Decimal
    unit: str
    growth_rate: Optional[Decimal]
    source: str
```

### 访客数据模型

```python
from src.data_adapters import VisitorType, VisitorFrequency

class VisitorDataPoint(BaseModel):
    visitor_type: VisitorType
    frequency: VisitorFrequency
    date: date
    value: Decimal
    unit: str
    growth_rate: Optional[Decimal]
    source: str
```

### 贸易数据模型

```python
from src.data_adapters import TradeType, TradeCategory, TradePartner

class TradeDataPoint(BaseModel):
    trade_type: TradeType
    category: TradeCategory
    trade_partner: Optional[TradePartner]
    frequency: TradeFrequency
    date: date
    value: Decimal
    unit: str
    growth_rate: Optional[Decimal]
    source: str
```

## 配置选项

### CSDCrawlerConfig

```python
CSDCrawlerConfig(
    base_url="https://www.censtatd.gov.hk",
    data_center_url="https://www.censtatd.gov.hk/en/data",
    request_timeout=30,          # 请求超时
    max_retries=3,               # 最大重试次数
    retry_delay=1.0,             # 重试延迟
    rate_limit=1.0,              # 请求频率限制
    download_dir="data/csd_downloads",
    cache_ttl=3600               # 缓存生存时间
)
```

### 其他配置

所有解析器都有类似的配置选项，支持：
- 下载目录设置
- 缓存TTL配置
- 并发工作线程数
- 解析格式优先级

## 错误处理

所有适配器都实现了统一的错误处理机制：

1. **网络错误**: 自动重试机制
2. **数据格式错误**: 智能格式检测和转换
3. **数据质量验证**: 自动数据验证和警告
4. **缓存失效**: 自动清理过期缓存

```python
result = await parser.parse_gdp_data('data/gdp.xlsx')
if result['success']:
    data = result['data']
else:
    error = result['error']
    print(f"处理失败: {error['error_message']}")
```

## 数据缓存

适配器实现了智能缓存机制：

1. **内存缓存**: 减少重复请求
2. **TTL控制**: 自动过期清理
3. **缓存键生成**: 基于参数生成唯一键
4. **缓存命中率**: 优化性能

```python
# 启用缓存 (默认开启)
config = GDPParserConfig(cache_ttl=3600)  # 1小时TTL

# 手动清理缓存
parser.clear_cache()

# 检查缓存状态
summary = await parser.get_summary()
print(f"缓存大小: {summary.get('cache_size', 0)}")
```

## 性能优化

1. **异步操作**: 所有I/O操作均为异步
2. **连接池**: 使用aiohttp连接池
3. **数据流处理**: 大文件分块处理
4. **缓存预热**: 频繁访问数据预加载
5. **并发控制**: 可配置并发数

## 测试

运行综合测试：

```bash
# 运行所有C&SD适配器测试
pytest tests/data_adapters/test_csd_adapters_comprehensive.py -v

# 运行特定适配器测试
pytest tests/data_adapters/test_csd_adapters_comprehensive.py::TestGDPParser -v

# 生成覆盖率报告
pytest tests/data_adapters/test_csd_adapters_comprehensive.py --cov=src/data_adapters --cov-report=html
```

## 示例程序

查看完整示例：

```bash
python examples/csd_data_adapters_demo.py
```

示例程序包含：
- 5个适配器的完整使用演示
- 数据创建和解析流程
- 增长率计算
- 市场份额分析
- 季节性模式分析
- 综合报告生成

## 数据源

所有数据均来自香港统计处(C&SD)官网：

- **官网**: https://www.censtatd.gov.hk/
- **数据中心**: https://www.censtatd.gov.hk/en/data/
- **开放数据**: 提供多种格式的下载

支持的指标类型：

1. **GDP**: 名义GDP、实际GDP、增长率、人均GDP、分行业GDP
2. **零售销售**: 总额、各类别销售、分行业数据
3. **访港旅客**: 总访客、各地区访客、增长率
4. **对外贸易**: 出口、进口、贸易差额、主要伙伴

## 依赖库

```txt
aiohttp>=3.8.0
pandas>=1.5.0
numpy>=1.21.0
pydantic>=1.10.0
beautifulsoup4>=4.11.0
openpyxl>=3.0.0
lxml>=4.9.0
```

## 注意事项

1. **网络连接**: 需要稳定的网络连接访问C&SD官网
2. **数据格式**: 支持多种格式，但实际数据格式可能因源而异
3. **更新频率**: 数据更新频率因指标而异，月度/季度/年度
4. **历史数据**: 支持获取历史数据，但受限于C&SD的发布范围
5. **错误处理**: 网络或数据错误会自动重试，但仍需处理异常情况

## 贡献指南

1. Fork项目
2. 创建特性分支
3. 提交代码
4. 创建Pull Request

## 许可证

本项目采用MIT许可证。详情见LICENSE文件。

## 更新日志

### Version 1.0.0 (2025-11-09)
- 初始版本发布
- 实现5个C&SD数据适配器
- 完整的测试套件
- 详细文档和示例

## 联系方式

如有问题或建议，请提交Issue或联系开发团队。

---

**最后更新**: 2025-11-09
**作者**: Claude Code
**版本**: 1.0.0
