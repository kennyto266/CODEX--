# CODEX 项目数据存储位置总览

**生成日期**: 2025-10-27
**项目路径**: /Users/Penguin8n/CODEX--/CODEX--

---

## 主要数据目录结构

### 1. 核心数据目录 ./data/

| 文件/目录 | 类型 | 大小 | 描述 |
|-----------|------|------|------|
| quant_system.db | SQLite | 84KB | 主要系统数据库 |
| portfolio_12345.json | JSON | 139B | 投资组合数据 |
| price_alerts.json | JSON | 307B | 价格告警配置 |
| sentiment_demo_report.json | JSON | 288B | 情感分析报告 |
| cache/ | 目录 | - | 缓存文件 |
| monitoring/ | 目录 | - | 监控数据 |
| raw/ | 目录 | 228KB | 原始数据 |
| registry/ | 目录 | 1.48MB | 数据注册表 |
| registry/registry.json | JSON | 1.44MB | 数据源注册信息 |

### 2. 数据适配器 ./src/data_adapters/

核心适配器文件:
- base_adapter.py (9.6KB) - 基础适配器类
- data_service.py (18.6KB) - 数据服务
- config_manager.py (11.5KB) - 配置管理
- realtime_hkex_adapter.py (8.3KB) - HKEX实时数据适配器

数据源适配器:
- hkex_adapter.py (17.8KB) - HKEX数据适配器
- yahoo_finance_adapter.py (15.7KB) - Yahoo Finance适配器
- alpha_vantage_adapter.py (18KB) - Alpha Vantage适配器

### 3. 实时数据源

HKEX 真实数据:
- 适配器: ./src/data_adapters/realtime_hkex_adapter.py
- API端点: http://18.180.162.113:9191/inst/getInst
- 缓存位置: ./data/cache/
- 格式: JSON, SQLite

### 4. 政府数据爬虫 ./gov_crawler/

主要数据文件:
- data/all_alternative_data_20251023_210419.json (100KB) - 所有替代数据
- data/hibor_data_*.csv (26KB each) - HIBOR利率数据
- data/alternative_data_*.json (74KB each) - 替代数据

### 5. LiHKG 情感爬虫 ./lihkg_scraper/

| 文件 | 大小 | 描述 |
|------|------|------|
| data/lihkg.db | 12KB | LiHKG主数据库 |
| data/demo_run.db | 12KB | 演示运行数据库 |
| data/test.db | 12KB | 测试数据库 |

---

## 数据库类型统计

### SQLite 数据库 (6个)
1. ./data/quant_system.db (84KB) - 主系统数据库
2. ./lihkg_scraper/data/lihkg.db (12KB) - LiHKG数据
3. ./lihkg_scraper/data/demo_run.db (12KB) - 演示数据
4. ./lihkg_scraper/data/test.db (12KB) - 测试数据
5. ./lihkg_scraper/data/e2e_test.db (12KB) - E2E测试
6. ./lihkg_scraper/data/integration_test.db (12KB) - 集成测试

### JSON 数据文件
1. ./data/portfolio_12345.json - 投资组合
2. ./data/price_alerts.json - 价格告警
3. ./data/registry/registry.json (1.44MB) - 数据注册表
4. ./data/raw/finance_20251023_215953.json (225KB) - 原始财务数据
5. ./gov_crawler/data/all_alternative_data_*.json (100KB) - 替代数据

---

## 数据类型分类

### 1. 实时市场数据
- 位置: ./src/data_adapters/realtime_hkex_adapter.py
- 数据源: http://18.180.162.113:9191/inst/getInst
- 缓存: ./data/cache/
- 格式: JSON, SQLite

### 2. 历史数据
- 位置: ./data/raw/
- 格式: JSON, CSV
- 来源: HKEX, Yahoo Finance, Alpha Vantage

### 3. 替代数据 (Alternative Data)
- 位置: ./gov_crawler/data/
- 类型: HIBOR、房地产、零售销售、GDP、游客、贸易、交通、MTR、边境
- 格式: JSON, CSV

### 4. 情感数据
- 位置: ./lihkg_scraper/data/
- 来源: LiHKG论坛
- 格式: SQLite

---

## 数据流架构

数据源 -> 数据适配器 -> 数据服务 -> 存储层
   ↓         ↓          ↓         ↓
HKEX API -> realtime_ -> data_ -> SQLite/JSON
Yahoo   -> adapter    service  CSV
AlphaV  -> adapter           cache

---

## 数据管理

### 1. 数据适配器框架
- 基类: ./src/data_adapters/base_adapter.py
- 接口: 统一的数据获取接口
- 支持: 多种数据源适配

### 2. 数据服务
- 服务层: ./src/data_adapters/data_service.py
- 功能: 数据聚合、清洗、验证

### 3. 配置管理
- 管理器: ./src/data_adapters/config_manager.py

---

## 快速访问

### 查看数据文件
```bash
# 查看主要数据目录
ls -la ./data/

# 查看数据库
sqlite3 ./data/quant_system.db ".schema"

# 查看替代数据
ls -la ./gov_crawler/data/

# 查看LiHKG数据
ls -la ./lihkg_scraper/data/
```

### 测试数据源
```bash
# 测试HKEX API
curl 'http://18.180.162.113:9191/inst/getInst?symbol=0700.hk&duration=30'
```

---

**最后更新**: 2025-10-27 20:41
**维护者**: Claude Code
