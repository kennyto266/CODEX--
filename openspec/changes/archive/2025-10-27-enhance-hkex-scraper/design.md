# HKEX 爬虫增强 - 技术设计文档

## 设计概要

**变更 ID:** enhance-hkex-scraper

**版本:** 1.0

**创建日期:** 2025-10-27

**设计者:** Claude Code

---

## 架构设计

### 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    HKEX Multi-Source Scraping System           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Chrome MCP    │  │  Web Scraper    │  │  File Download  │ │
│  │   Controller    │  │     Engine      │  │     Manager     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│           │                   │                   │            │
│           └───────────────────┼───────────────────┘            │
│                               │                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │            Data Extraction Layer                        │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │   │
│  │  │ Futures  │ │ Options  │ │  Stocks  │ │ Indices  │   │   │
│  │  │Scraper   │ │Scraper   │ │Scraper   │ │Scraper   │   │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │   │
│  │  ┌──────────┐                                         │   │
│  │  │  Market  │                                         │   │
│  │  │Scraper   │                                         │   │
│  │  └──────────┘                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                               │                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │            Data Processing Pipeline                     │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │   │
│  │  │Validation│ │Cleaning  │ │Formatting│ │Quality   │   │   │
│  │  │   &      │ │   &      │ │   &      │ │Assessment│   │   │
│  │  │Schema    │ │Transform │ │Standard  │ │ & Scoring│   │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                               │                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │           Cache & Storage Layer                         │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │   │
│  │  │  Memory  │ │   File   │ │ SQLite   │ │ Export   │   │   │
│  │  │  Cache   │ │  Cache   │ │ Database │ │ Manager  │   │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                               │                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │             API & Integration Layer                     │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │   │
│  │  │ FastAPI  │ │ Task     │ │ WebSocket│ │ Monitoring│   │   │
│  │  │ Endpoints│ │ Scheduler│ │   Push   │ │ & Logging│   │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 核心组件设计

### 1. Chrome DevTools MCP 控制器

**职责:** 浏览器自动化和页面分析

```python
class HKEXChromeController:
    """Chrome DevTools MCP 集成控制器"""

    def __init__(self):
        self.browser_session = None
        self.page_id = None

    async def create_page(self) -> str:
        """创建新的浏览器页面"""

    async def navigate(self, url: str) -> bool:
        """导航到指定页面"""

    async def take_snapshot(self) -> bytes:
        """获取页面快照"""

    async def evaluate_script(self, script: str) -> Any:
        """执行 JavaScript"""

    async def discover_selectors(self, pattern: str) -> Dict[str, str]:
        """智能发现页面选择器"""

    async def monitor_changes(self, selector: str, callback: Callable):
        """监控页面变化"""
```

**关键特性:**
- 异步操作支持
- 自动重试机制
- 页面变化监控
- 选择器自动发现
- JavaScript 执行环境

---

### 2. 数据提取层

#### 2.1 期货数据爬虫

```python
class FuturesDataScraper:
    """期货数据提取器"""

    SUPPORTED_CONTRACTS = {
        "HSI": {
            "name": "恒生指数期货",
            "url": "https://www.hkex.com.hk/Products/Market-Data/Futures",
            "data_fields": ["date", "open", "high", "low", "close", "volume", "oi", "turnover"]
        },
        "MHI": {
            "name": "迷你恒生指数期货",
            "url": "https://www.hkex.com.hk/Products/Market-Data/Futures",
            "data_fields": ["date", "open", "high", "low", "close", "volume", "oi", "turnover"]
        },
        "HHI": {
            "name": "小恒生指数期货",
            "url": "https://www.hkex.com.hk/Products/Market-Data/Futures",
            "data_fields": ["date", "open", "high", "low", "close", "volume", "oi", "turnover"]
        }
    }

    async def scrape_contract(self, contract: str, start_date: date, end_date: date) -> pd.DataFrame:
        """爬取指定合约数据"""

    async def scrape_all_contracts(self, date: date) -> Dict[str, pd.DataFrame]:
        """爬取所有合约在指定日期的数据"""
```

**设计要点:**
- 支持多种期货合约
- 批量数据提取
- 增量更新机制
- 数据格式标准化

#### 2.2 股票数据爬虫

```python
class StocksDataScraper:
    """股票数据提取器"""

    async def scrape_stock_list(self, board: str = "main") -> pd.DataFrame:
        """爬取股票列表"""

    async def scrape_stock_details(self, stock_codes: List[str]) -> pd.DataFrame:
        """批量获取股票详情"""

    async def scrape_realtime_quotes(self, stock_codes: List[str]) -> pd.DataFrame:
        """获取实时报价"""

    async def scrape_historical_data(self, stock_code: str, start_date: date, end_date: date) -> pd.DataFrame:
        """获取历史数据"""
```

**设计要点:**
- 分板支持（主板、创业板）
- 批量处理优化
- 实时数据获取
- 股票代码映射

#### 2.3 指数数据爬虫

```python
class IndicesDataScraper:
    """指数数据提取器"""

    SUPPORTED_INDICES = [
        "HSI",        # 恒生指数
        "HSCEI",      # 恒生中国企业指数
        "HSTECH",     # 恒生科技指数
        "HSCI",       # 恒生综合指数
        "HSCCI",      # 恒生综合消费品指数
        "HSCIF",      # 恒生综合金融指数
    ]

    async def scrape_index_value(self, index_code: str, date: date) -> Dict[str, float]:
        """获取指数点位"""

    async def scrape_index_components(self, index_code: str, date: date) -> pd.DataFrame:
        """获取指数成分股"""

    async def scrape_historical_index(self, index_code: str, start_date: date, end_date: date) -> pd.DataFrame:
        """获取指数历史数据"""
```

**设计要点:**
- 支持多指数类型
- 成分股提取
- 历史数据回溯
- 权重信息获取

#### 2.4 市场统计爬虫

```python
class MarketStatsScraper:
    """市场统计数据提取器"""

    STATISTICS_TYPES = {
        "market_overview": "市场概览",
        "turnover_stats": "成交统计",
        "sector_performance": "行业表现",
        "ipo_data": "IPO 数据",
        "new_listings": "新股上市"
    }

    async def scrape_market_overview(self, date: date) -> Dict[str, Any]:
        """获取市场概览"""

    async def scrape_turnover_stats(self, date: date) -> pd.DataFrame:
        """获取成交统计"""

    async def scrape_sector_performance(self, date: date) -> pd.DataFrame:
        """获取行业表现"""

    async def scrape_ipo_data(self, start_year: int, end_year: int) -> pd.DataFrame:
        """获取 IPO 数据"""
```

**设计要点:**
- 多类型统计数据
- 历史数据查询
- 行业分类统计
- IPO 追踪

---

### 3. 数据处理管道

```python
class DataProcessingPipeline:
    """统一数据处理管道"""

    async def process_raw_data(self, data: pd.DataFrame, data_type: str) -> pd.DataFrame:
        """处理原始数据"""

    async def validate_data(self, data: pd.DataFrame, schema: Dict) -> Tuple[bool, List[str]]:
        """验证数据质量"""

    async def clean_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """清洗数据"""

    async def format_data(self, data: pd.DataFrame, format_type: str) -> pd.DataFrame:
        """格式化数据"""

    async def assess_quality(self, data: pd.DataFrame) -> Dict[str, float]:
        """评估数据质量"""
```

**处理阶段:**

1. **验证阶段 (Validation)**
   - 数据完整性检查
   - 类型验证
   - 范围检查
   - 必填字段验证

2. **清洗阶段 (Cleaning)**
   - 空值处理
   - 重复数据删除
   - 异常值处理
   - 格式统一

3. **格式化阶段 (Formatting)**
   - 时间戳标准化
   - 数值类型转换
   - 枚举值映射
   - 单位标准化

4. **质量评估阶段 (Quality Assessment)**
   - 完整性得分
   - 一致性得分
   - 准确性得分
   - 及时性得分

---

### 4. 缓存与存储层

#### 4.1 多层缓存架构

```python
class CacheManager:
    """多层缓存管理器"""

    def __init__(self):
        self.memory_cache = {}  # LRU 内存缓存
        self.file_cache = FileCache()  # 文件缓存
        self.db_cache = SQLiteCache()  # 数据库缓存

    async def get(self, key: str, ttl: int = 3600) -> Optional[Any]:
        """获取缓存数据 (多级查找)"""

    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """设置缓存数据 (多级存储)"""

    async def invalidate(self, pattern: str) -> int:
        """失效缓存"""

    async def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
```

**缓存策略:**

- **内存缓存 (L1)**
  - 容量: 100 MB
  - 算法: LRU
  - TTL: 5-30 分钟
  - 用途: 热点数据

- **文件缓存 (L2)**
  - 容量: 1 GB
  - 格式: JSON/Parquet
  - TTL: 1-24 小时
  - 用途: 中期数据

- **数据库缓存 (L3)**
  - 容量: 磁盘限制
  - 引擎: SQLite
  - TTL: 7-30 天
  - 用途: 历史数据

#### 4.2 数据存储设计

```python
class DatabaseManager:
    """SQLite 数据库管理器"""

    def __init__(self, db_path: str):
        self.db_path = db_path

    async def create_tables(self):
        """创建表结构"""

    async def insert_data(self, table: str, data: pd.DataFrame, batch_size: int = 1000):
        """批量插入数据"""

    async def query_data(self, table: str, conditions: Dict[str, Any]) -> pd.DataFrame:
        """查询数据"""

    async def create_indexes(self):
        """创建索引"""

    async def backup_database(self, backup_path: str):
        """备份数据库"""
```

**数据库表设计:**

```sql
-- 期货数据表
CREATE TABLE futures_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_code TEXT NOT NULL,
    trade_date DATE NOT NULL,
    open_price REAL,
    high_price REAL,
    low_price REAL,
    close_price REAL,
    volume INTEGER,
    open_interest INTEGER,
    turnover REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(contract_code, trade_date)
);

-- 股票数据表
CREATE TABLE stocks_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_code TEXT NOT NULL,
    trade_date DATE NOT NULL,
    current_price REAL,
    change_amount REAL,
    change_percent REAL,
    volume INTEGER,
    turnover REAL,
    market_cap REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stock_code, trade_date)
);

-- 指数数据表
CREATE TABLE indices_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    index_code TEXT NOT NULL,
    trade_date DATE NOT NULL,
    index_value REAL,
    change_amount REAL,
    change_percent REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(index_code, trade_date)
);

-- 市场统计数据表
CREATE TABLE market_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stat_date DATE NOT NULL,
    stat_type TEXT NOT NULL,
    total_turnover REAL,
    total_volume INTEGER,
    gainers_count INTEGER,
    losers_count INTEGER,
    unchanged_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stat_date, stat_type)
);

-- 索引
CREATE INDEX idx_futures_contract_date ON futures_data(contract_code, trade_date);
CREATE INDEX idx_stocks_code_date ON stocks_data(stock_code, trade_date);
CREATE INDEX idx_indices_code_date ON indices_data(index_code, trade_date);
CREATE INDEX idx_market_stats_date_type ON market_stats(stat_date, stat_type);
```

---

### 5. API 接口设计

```python
from fastapi import FastAPI, BackgroundTasks, Query
from typing import Optional, List

app = FastAPI(title="HKEX Scraper API", version="1.0")

@app.get("/api/hkex/data/{data_type}")
async def get_data(
    data_type: str,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    stock_codes: Optional[List[str]] = Query(None),
    limit: int = Query(100, le=10000)
):
    """获取指定类型的数据"""

@app.post("/api/hkex/scrape/start")
async def start_scrape(
    data_types: List[str],
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    background_tasks: BackgroundTasks
):
    """启动数据爬取任务"""

@app.get("/api/hkex/scrape/status/{task_id}")
async def get_scrape_status(task_id: str):
    """获取爬取任务状态"""

@app.get("/api/hkex/metrics")
async def get_metrics():
    """获取系统指标"""

@app.get("/api/hkex/export")
async def export_data(
    data_type: str,
    format: str = "csv",
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
):
    """导出数据"""
```

**API 端点详细设计:**

| 方法 | 路径 | 描述 | 参数 |
|------|------|------|------|
| GET | `/api/hkex/data/futures` | 获取期货数据 | start_date, end_date, contract |
| GET | `/api/hkex/data/stocks` | 获取股票数据 | start_date, end_date, stock_codes |
| GET | `/api/hkex/data/indices` | 获取指数数据 | start_date, end_date, index_codes |
| GET | `/api/hkex/data/market` | 获取市场统计 | start_date, end_date |
| POST | `/api/hkex/scrape/start` | 启动爬取 | data_types, start_date, end_date |
| GET | `/api/hkex/scrape/status/{id}` | 任务状态 | task_id |
| GET | `/api/hkex/metrics` | 系统指标 | - |
| GET | `/api/hkex/export` | 数据导出 | data_type, format, start_date, end_date |

---

### 6. 任务调度系统

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

class TaskScheduler:
    """任务调度器"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()

    def start(self):
        """启动调度器"""

    async def schedule_daily_update(self, job_func: Callable, time: str = "16:00"):
        """每日更新任务"""

    async def schedule_hourly_update(self, job_func: Callable):
        """每小时更新任务"""

    async def schedule_custom(self, job_func: Callable, cron_expr: str):
        """自定义调度"""
```

**调度策略:**

- **每日更新** (16:00 HKT)
  - 更新期货数据
  - 更新股票列表
  - 更新指数数据
  - 更新市场统计

- **每小时更新** (交易时间内)
  - 实时报价数据
  - 市场变化监控

- **每周更新**
  - 指数成分股调整
  - 数据质量报告

---

## 关键技术决策

### 决策 1: 选择器自动发现 vs 手动配置

**选项:**
1. 自动发现选择器 (推荐)
2. 手动配置选择器

**理由:**
- 自动发现降低维护成本
- 适应页面结构变化
- 提供更好的容错性

**实现:**
- 使用 Chrome DevTools 分析页面
- 机器学习识别数据表格
- 版本控制选择器历史

### 决策 2: 缓存策略

**选项:**
1. 单层缓存
2. 多层缓存 (推荐)

**理由:**
- 多层缓存提高性能
- 不同层级适配不同访问模式
- 灵活配置 TTL

**实现:**
- L1: 内存缓存 (热点数据)
- L2: 文件缓存 (中期数据)
- L3: 数据库缓存 (历史数据)

### 决策 3: 并发控制

**选项:**
1. 同步处理
2. 异步处理 (推荐)

**理由:**
- 异步提高并发能力
- 更好的资源利用
- 支持大量并发请求

**实现:**
- 使用 asyncio
- 协程池控制并发数
- 背压机制防止过载

### 决策 4: 数据存储格式

**选项:**
1. 纯文件 (CSV/JSON)
2. 关系型数据库 (推荐)
3. NoSQL 数据库

**理由:**
- 关系型数据库支持复杂查询
- SQLite 无需额外服务
- 支持事务和数据完整性

**实现:**
- SQLite 作为主存储
- Parquet 作为导出格式
- JSON 用于 API 响应

---

## 性能优化策略

### 1. 网络优化

- **请求合并:** 批量获取多个数据源
- **连接复用:** HTTP Keep-Alive
- **压缩传输:** Gzip 压缩
- **CDN 缓存:** 静态资源缓存

### 2. 数据处理优化

- **向量化操作:** 使用 Pandas/NumPy
- **分批处理:** 避免内存溢出
- **并行处理:** 多进程/多线程
- **惰性加载:** 按需加载数据

### 3. 缓存优化

- **预热策略:** 提前加载热点数据
- **智能失效:** 基于访问模式的 TTL
- **压缩存储:** 压缩缓存文件
- **缓存穿透保护:** 布隆过滤器

### 4. 数据库优化

- **索引优化:** 针对查询模式优化
- **查询优化:** 避免 N+1 查询
- **批量操作:** 减少 I/O 次数
- **分区表:** 按日期分区大表

---

## 错误处理与恢复

### 错误分类

1. **网络错误**
   - 连接超时
   - DNS 解析失败
   - HTTP 错误 (4xx/5xx)

2. **数据错误**
   - 解析失败
   - 格式错误
   - 验证失败

3. **系统错误**
   - 内存不足
   - 磁盘空间不足
   - 进程崩溃

### 恢复策略

```python
class ErrorHandler:
    """错误处理器"""

    async def handle_network_error(self, error: Exception, retry_count: int) -> bool:
        """处理网络错误"""
        if retry_count < self.max_retries:
            await asyncio.sleep(2 ** retry_count)  # 指数退避
            return True
        return False

    async def handle_data_error(self, error: Exception) -> Optional[Any]:
        """处理数据错误"""
        # 记录错误
        # 尝试降级获取
        # 返回缓存数据

    async def handle_system_error(self, error: Exception) -> bool:
        """处理系统错误"""
        # 检查资源
        # 清理缓存
        # 重启服务
```

**重试策略:**
- 指数退避: 2^retry_count 秒
- 最大重试: 3-5 次
- 熔断器: 连续失败后暂停
- 降级: 返回缓存或模拟数据

---

## 监控与日志

### 监控指标

```python
class MetricsCollector:
    """指标收集器"""

    metrics = {
        "request_count": "请求总数",
        "request_duration": "请求耗时",
        "success_rate": "成功率",
        "cache_hit_rate": "缓存命中率",
        "data_freshness": "数据新鲜度",
        "error_rate": "错误率",
        "throughput": "吞吐量"
    }

    async def record_request(self, endpoint: str, duration: float, success: bool):
        """记录请求指标"""

    async def get_metrics_summary(self) -> Dict[str, Any]:
        """获取指标摘要"""
```

### 日志结构

```python
import structlog

logger = structlog.get_logger("hkex_scraper")

# 结构化日志示例
logger.info(
    "scraping_started",
    data_type="futures",
    contract="HSI",
    url="https://www.hkex.com.hk/...",
    retry_count=0
)

logger.error(
    "scraping_failed",
    data_type="futures",
    contract="HSI",
    error=str(exception),
    retry_count=3
)
```

**日志等级:**
- DEBUG: 详细调试信息
- INFO: 一般信息记录
- WARNING: 警告信息
- ERROR: 错误信息
- CRITICAL: 严重错误

---

## 安全考虑

### 1. 访问控制

- **API 密钥认证**
- **请求频率限制**
- **IP 白名单**
- **用户角色管理**

### 2. 数据安全

- **敏感数据加密**
- **数据传输加密 (HTTPS)**
- **数据脱敏**
- **访问审计**

### 3. 系统安全

- **输入验证**
- **SQL 注入防护**
- **XSS 防护**
- **CSRF 防护**

---

## 扩展性设计

### 水平扩展

- **无状态设计:** 支持多实例部署
- **负载均衡:** Nginx/HAProxy
- **消息队列:** Celery/RQ
- **分布式缓存:** Redis Cluster

### 垂直扩展

- **资源监控:** CPU/内存/磁盘
- **自动扩缩容:** Kubernetes HPA
- **性能调优:** 缓存、索引、查询优化

### 功能扩展

- **插件架构:** 支持自定义爬虫
- **数据源抽象:** 统一数据源接口
- **配置热更新:** 无需重启服务

---

## 部署架构

### 开发环境

```
┌─────────────────────────────────────┐
│           Developer Laptop          │
│  ┌──────────┐  ┌─────────────────┐  │
│  │   IDE    │  │   Chrome MCP    │  │
│  └──────────┘  └─────────────────┘  │
│         │              │             │
│  ┌─────────────────────────────────┐ │
│  │     Docker Compose              │ │
│  │  ┌──────┐ ┌──────┐ ┌──────┐    │ │
│  │  │Scraper│ │SQLite│ │Redis │    │ │
│  │  └──────┘ └──────┘ └──────┘    │ │
│  └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

### 生产环境

```
┌──────────────────────────────────────────────────────────────┐
│                        Load Balancer                        │
└──────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼───────┐   ┌───────▼───────┐   ┌───────▼───────┐
│   Scraper 1   │   │   Scraper 2   │   │   Scraper 3   │
│  (Container)  │   │  (Container)  │   │  (Container)  │
└───────────────┘   └───────────────┘   └───────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼───────┐   ┌───────▼───────┐   ┌───────▼───────┐
│   PostgreSQL  │   │     Redis     │   │     MinIO     │
│   (Database)  │   │    (Cache)    │   │   (Storage)   │
└───────────────┘   └───────────────┘   └───────────────┘
```

---

## 成本估算

### 基础设施成本

- **计算资源:**
  - 2x CPU (4 cores)
  - 8GB RAM
  - 100GB 磁盘
  - 估算: $100/月

- **网络流量:**
  - 带宽: 100 Mbps
  - 流量: 1TB/月
  - 估算: $50/月

- **第三方服务:**
  - Chrome 实例
  - 监控服务
  - 估算: $50/月

**总计: ~$200/月**

### 人力成本

- **开发:** 16 天 × 1 人 = 16 人日
- **测试:** 5 天 × 1 人 = 5 人日
- **部署:** 2 天 × 1 人 = 2 人日
- **总计:** 23 人日

---

## 总结

本设计文档详细阐述了 HKEX 爬虫增强系统的技术架构。关键设计原则:

1. **模块化设计:** 每个组件独立，易于测试和维护
2. **高性能:** 多层缓存 + 异步处理 + 并发控制
3. **可扩展:** 支持水平扩展和功能扩展
4. **可靠性:** 错误处理 + 重试机制 + 降级策略
5. **可观测:** 完整的监控和日志系统

通过遵循本设计，系统能够高效、可靠地爬取 HKEX 的大量金融数据，为量化交易系统提供数据支持。
