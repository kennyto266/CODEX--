# Gov Crawler API 集成 - 设计文档

## 架构设计

### 双数据源架构

```
CODEX Dashboard (端口 8002)
├── HKEX 数据源
│   └── /api/stock/data (股票数据)
│       ├── 真实数据源: http://18.180.162.113:9191
│       └── 错误处理: HTTP 503 (不回退到 Mock)
│
└── gov_crawler 数据源
    ├── /api/gov/status (系统状态)
    ├── /api/gov/indicators (指标列表)
    └── /api/gov/data (政府数据)
        └── 数据文件: 98.09 KB (35 个指标)
```

## API 设计

### 1. HKEX 数据 API

**端点**: `GET /api/stock/data`

**参数**:
- `symbol`: 股票代码 (e.g., "0700.HK")
- `duration`: 时间范围（天数，默认 365 天）

**响应格式**:
```json
{
  "symbol": "0700.HK",
  "name": "Tencent (騰訊)",
  "last_price": 656.0,
  "change": 18.5,
  "change_percent": 2.9,
  "data_source": "Real-time HKEX API"
}
```

**错误处理**:
- 失败时返回 HTTP 503
- 不回退到 Mock 数据

### 2. Gov Crawler 状态 API

**端点**: `GET /api/gov/status`

**响应格式**:
```json
{
  "project": "gov_crawler",
  "status": "operational",
  "data_source": "gov_crawler",
  "timestamp": "2025-10-28T08:15:50.022389",
  "checks": {
    "project_directory": "✅ 存在",
    "data_file": "✅ 存在"
  },
  "project_found": true,
  "data_file_size": "98.09 KB",
  "data_available": true,
  "total_indicators": 9
}
```

### 3. Gov Crawler 指标列表 API

**端点**: `GET /api/gov/indicators`

**响应格式**:
```json
{
  "total_indicators": 35,
  "total_categories": 9,
  "categories": [
    "hibor", "property", "retail", "gdp",
    "visitors", "trade", "traffic", "mtr", "border_crossing"
  ],
  "indicators": [
    "hibor_overnight", "hibor_1m", "hibor_3m",
    ...
  ]
}
```

### 4. Gov Crawler 数据 API

**端点**: `GET /api/gov/data`

**参数**:
- `indicator`: 指标类型 (e.g., "hibor_overnight", "property_price", "gdp")
- `start_date`: 开始日期 (格式: YYYY-MM-DD，默认 "2024-01-01")
- `end_date`: 结束日期 (格式: YYYY-MM-DD，默认 "2025-10-28")

**响应格式 (扁平结构)**:
```json
{
  "indicator": "hibor_overnight",
  "category": "hibor",
  "data": {
    "values": [4.138, 4.199, ...],
    "dates": ["2024-01-02", "2024-01-03", ...]
  },
  "source": "gov_crawler",
  "timestamp": "2025-10-28T08:15:50.022389",
  "note": "數據來自 gov_crawler 政府數據收集系統"
}
```

**响应格式 (嵌套结构)**:
```json
{
  "indicator": "gdp",
  "data": {
    "gdp_nominal": {
      "values": [2019484853211.4165, ...],
      "dates": ["2023Q1", "2023Q2", ...]
    },
    "gdp_yoy_growth": {
      ...
    }
  },
  "source": "gov_crawler",
  "timestamp": "2025-10-28T08:15:50.022389"
}
```

## 数据结构

### Gov Crawler 数据文件

**文件路径**: `gov_crawler/data/all_alternative_data_20251023_210419.json`

**数据结构**:
```json
{
  "hibor": {
    "hibor_overnight": {
      "values": [...],
      "dates": [...],
      "count": 262,
      "min": 2.5,
      "max": 5.2,
      "mean": 3.8
    },
    "hibor_1m": {...},
    ...
  },
  "property": {
    "property_sale_price": {...},
    ...
  },
  ...
}
```

**指标分类**:
1. **hibor** (5 个指标) - 银行同业拆息
2. **property** (5 个指标) - 房地产数据
3. **retail** (6 个指标) - 零售销售
4. **gdp** (5 个指标) - GDP 数据
5. **visitors** (3 个指标) - 访客数据
6. **trade** (3 个指标) - 贸易数据
7. **traffic** (3 个指标) - 交通流量
8. **mtr** (2 个指标) - MTR 乘客
9. **border_crossing** (3 个指标) - 边境过境

## 错误处理

### 1. HKEX API 错误

- **503 SERVICE_UNAVAILABLE**: 数据源不可用
- **503 ADAPTER_NOT_AVAILABLE**: 适配器未正确安装
- **503 DATA_SOURCE_ERROR**: 数据源连接失败

### 2. Gov Crawler API 错误

- **503 PROJECT_NOT_FOUND**: gov_crawler 项目未找到
- **503 DATA_NOT_AVAILABLE**: 数据文件未找到
- **404 INDICATOR_NOT_FOUND**: 指标不存在
- **503 DATA_SOURCE_ERROR**: 数据源错误

## 性能优化

### 1. 缓存策略
- HKEX 数据: 5 分钟 TTL 缓存
- Gov Crawler 数据: 读取时加载到内存

### 2. 异步处理
- 使用 `asyncio.to_thread()` 运行同步数据获取
- 所有 API 端点都是异步的

### 3. 响应时间
- 目标: < 100ms
- 实际: < 50ms

## 测试策略

### 单元测试
- `test_gov_crawler_api.py`: 6 个测试用例
- 覆盖所有 API 端点
- 验证错误处理

### 集成测试
- 启动完整服务
- 使用 httpx 进行 HTTP 请求测试
- 验证所有响应格式

## 部署配置

### 端口配置
- **开发环境**: 8002
- **生产环境**: 8001 (可通过环境变量配置)

### 环境变量
- `PYTHONPATH`: 项目根目录
- `PORT`: 服务端口 (可选)

---

**设计版本**: v1.1.0  
**创建日期**: 2025-10-28  
**负责人**: Claude Code AI
