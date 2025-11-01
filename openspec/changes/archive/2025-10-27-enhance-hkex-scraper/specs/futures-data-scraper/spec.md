# HKEX 期货数据爬虫规范

## 规范信息

**规范名称:** HKEX 期货数据爬虫

**版本:** 1.0.0

**创建日期:** 2025-10-27

**变更 ID:** enhance-hkex-scraper

**相关规范:** chrome-mcp-integration

---

## 概述

本规范定义了 HKEX 期货数据爬虫的功能要求，包括恒生指数期货(HSI)、迷你恒生指数期货(MHI)、小恒生指数期货(HHI)等合约的数据提取、处理和存储。

---

## ADDED Requirements

### 1. 期货合约支持

#### 需求: 支持主要期货合约

**描述:** 系统必须支持提取 HKEX 主要期货合约数据

**支持合约:**
- HSI (恒生指数期货)
- MHI (迷你恒生指数期货)
- HHI (小恒生指数期货)
- HSI Options (恒生指数期权)
- HSTECH (恒生科技指数期货)

**实现要求:**
- 每个合约有独立的提取器
- 支持合约代码映射
- 支持合约元数据获取
- 支持合约状态查询

**验收标准:**
- [ ] 支持至少 5 种期货合约
- [ ] 合约识别准确率 100%
- [ ] 元数据提取完整率 > 95%
- [ ] 合约切换响应时间 < 1 秒

**场景:**

```python
# 场景 1: 列出支持合约
contracts = scraper.list_supported_contracts()
# 返回: ["HSI", "MHI", "HHI", "HSI_Options", "HSTECH"]

# 场景 2: 获取合约元数据
metadata = scraper.get_contract_metadata("HSI")
# 返回: {"code": "HSI", "name": "恒生指数期货", "multiplier": 10, ...}

# 场景 3: 查询合约状态
status = scraper.get_contract_status("HSI")
# 返回: {"trading": True, "last_update": "2025-10-27 16:00", ...}
```

---

### 2. 期货基础数据提取

#### 需求: 提取期货 OHLCV 数据

**描述:** 系统必须能够提取期货的开盘价、最高价、最低价、收盘价、成交量数据

**数据字段:**
- 日期 (trade_date)
- 开盘价 (open_price)
- 最高价 (high_price)
- 最低价 (low_price)
- 收盘价 (close_price)
- 成交量 (volume)
- 成交额 (turnover)
- 结算价 (settlement_price)
- 昨结算价 (prev_settlement_price)

**实现要求:**
- 支持日线数据提取
- 支持分钟线数据提取
- 支持实时数据更新
- 数据格式标准化
- 时间戳标准化

**验收标准:**
- [ ] OHLCV 数据提取准确率 > 99%
- [ ] 支持历史数据回溯至少 1 年
- [ ] 数据完整性检查通过率 > 98%
- [ ] 单次提取时间 < 10 秒

**场景:**

```python
# 场景 1: 获取日线数据
data = await scraper.get_ohlcv_data(
    contract="HSI",
    start_date=date(2024, 1, 1),
    end_date=date(2024, 12, 31)
)

# 场景 2: 获取分钟线数据
minute_data = await scraper.get_ohlcv_data(
    contract="HSI",
    start_date=date(2025, 10, 27),
    granularity="1min"
)

# 场景 3: 获取实时数据
realtime_data = await scraper.get_realtime_quote("HSI")
# 返回: {"last_price": 25000, "change": 150, "volume": 1200, ...}
```

---

#### 需求: 提取未平仓量数据

**描述:** 系统必须提取期货合约的未平仓量(OI)数据

**数据字段:**
- 日期 (trade_date)
- 总未平仓量 (total_oi)
- 买入未平仓量 (long_oi)
- 卖出未平仓量 (short_oi)
- 未平仓量变化 (oi_change)
- 净未平仓量 (net_oi)

**实现要求:**
- 支持日度 OI 数据
- 支持 OI 分布分析
- 支持 OI 历史趋势
- 支持 OI 变化率计算

**验收标准:**
- [ ] OI 数据提取准确率 > 99%
- [ ] OI 变化计算正确性 100%
- [ ] 支持 OI 分布图表数据
- [ ] OI 数据延迟 < 15 分钟

**场景:**

```python
# 场景 1: 获取 OI 历史数据
oi_data = await scraper.get_open_interest_data(
    contract="HSI",
    start_date=date(2024, 1, 1),
    end_date=date(2024, 12, 31)
)

# 场景 2: 获取当前 OI 分布
oi_distribution = await scraper.get_oi_distribution("HSI")
# 返回: {"long_oi": 50000, "short_oi": 48000, "net_oi": 2000}

# 场景 3: 计算 OI 变化率
oi_change = await scraper.calculate_oi_change_rate(
    contract="HSI",
    days=30
)
```

---

### 3. 期货高级数据

#### 需求: 提取期货持仓报告

**描述:** 系统必须提取期货持仓报告数据

**数据字段:**
- 日期 (trade_date)
- 多头持仓 (long_positions)
- 空头持仓 (short_positions)
- 净持仓 (net_positions)
- 持仓变化 (position_change)
- 会员代码 (member_code)
- 会员名称 (member_name)

**实现要求:**
- 支持大额持仓报告
- 支持所有会员持仓
- 支持持仓排名
- 支持历史持仓分析

**验收标准:**
- [ ] 持仓数据提取完整率 > 95%
- [ ] 支持至少前 20 名会员持仓
- [ ] 持仓数据更新延迟 < 1 天
- [ ] 排名数据准确率 100%

**场景:**

```python
# 场景 1: 获取持仓报告
positions = await scraper.get_positions_report(
    contract="HSI",
    date=date(2025, 10, 26),
    limit=20
)

# 场景 2: 获取会员持仓历史
member_positions = await scraper.get_member_position_history(
    contract="HSI",
    member_code="ABC123",
    start_date=date(2024, 1, 1),
    end_date=date(2024, 12, 31)
)

# 场景 3: 分析持仓集中度
concentration = await scraper.analyze_position_concentration(
    contract="HSI",
    date=date(2025, 10, 26)
)
```

---

#### 需求: 提取期货交易统计

**描述:** 系统必须提取期货交易统计数据

**数据字段:**
- 交易日期 (trade_date)
- 总成交量 (total_volume)
- 总成交额 (total_turnover)
- 总持仓量 (total_positions)
- 合约数量 (contracts_traded)
- 交易笔数 (trades_count)
- 平均成交价 (avg_price)
- 价格波动率 (volatility)

**实现要求:**
- 支持日度统计
- 支持周度统计
- 支持月度统计
- 支持同比环比分析

**验收标准:**
- [ ] 统计数据准确率 > 99%
- [ ] 统计数据覆盖所有交易日
- [ ] 波动率计算正确性验证
- [ ] 统计数据计算延迟 < 1 分钟

**场景:**

```python
# 场景 1: 获取日度交易统计
daily_stats = await scraper.get_daily_trading_stats(
    contract="HSI",
    date=date(2025, 10, 27)
)

# 场景 2: 获取月度统计汇总
monthly_stats = await scraper.get_monthly_trading_stats(
    contract="HSI",
    year=2025,
    month=10
)

# 场景 3: 计算交易活跃度
activity = await scraper.calculate_trading_activity(
    contract="HSI",
    period="weekly"
)
```

---

### 4. 数据处理与验证

#### 需求: 数据质量验证

**描述:** 系统必须对提取的期货数据进行质量验证

**验证规则:**
- 价格数据范围检查
- 成交量非负性检查
- 未平仓量逻辑检查
- 数据完整性检查
- 时间序列连续性检查

**实现要求:**
- 自动数据清洗
- 异常值检测
- 数据一致性验证
- 质量评分系统
- 错误报告生成

**验收标准:**
- [ ] 异常值检测准确率 > 95%
- [ ] 数据清洗正确率 100%
- [ ] 质量评分覆盖所有数据
- [ ] 错误报告详细准确

**场景:**

```python
# 场景 1: 验证单日数据
quality_report = await scraper.validate_data_quality(
    contract="HSI",
    date=date(2025, 10, 27)
)
# 返回: {"score": 95, "issues": [], "warnings": []}

# 场景 2: 批量验证
batch_report = await scraper.batch_validate_data_quality(
    contract="HSI",
    start_date=date(2025, 1, 1),
    end_date=date(2025, 10, 27)
)

# 场景 3: 数据修复
repaired_data = await scraper.repair_data_quality(
    contract="HSI",
    date=date(2025, 10, 27),
    repair_mode="auto"
)
```

---

#### 需求: 数据标准化

**描述:** 系统必须将提取的数据标准化为统一格式

**标准化规则:**
- 时间戳统一格式 (ISO 8601)
- 数值精度统一 (小数点后 2 位)
- 枚举值统一映射
- 缺失值处理规则
- 货币单位统一 (HKD)

**实现要求:**
- 自动格式转换
- 类型安全转换
- 单位换算支持
- 本地化处理
- 国际化支持

**验收标准:**
- [ ] 格式转换正确率 100%
- [ ] 类型转换成功率 > 99%
- [ ] 单位换算准确率 100%
- [ ] 转换性能 > 1000 记录/秒

**场景:**

```python
# 场景 1: 标准化数据格式
standard_data = await scraper.standardize_data(
    data=raw_data,
    format="iso8601",
    precision=2,
    currency="HKD"
)

# 场景 2: 处理缺失值
complete_data = await scraper.handle_missing_values(
    data=raw_data,
    strategy="forward_fill"
)

# 场景 3: 单位换算
converted_data = await scraper.convert_units(
    data=raw_data,
    from_unit="HKD",
    to_unit="USD",
    exchange_rate=0.128
)
```

---

### 5. 批量数据处理

#### 需求: 批量数据提取

**描述:** 系统必须支持批量提取多个期货合约的数据

**实现要求:**
- 并发提取多个合约
- 异步批量处理
- 进度跟踪
- 错误隔离
- 部分失败恢复

**验收标准:**
- [ ] 并发支持至少 5 个合约
- [ ] 批量处理吞吐量 > 10 合约/分钟
- [ ] 错误隔离率 100%
- [ ] 部分失败不影响成功任务

**场景:**

```python
# 场景 1: 并发提取多个合约
batch_data = await scraper.batch_extract_data(
    contracts=["HSI", "MHI", "HHI"],
    start_date=date(2025, 10, 1),
    end_date=date(2025, 10, 27),
    max_concurrency=5
)

# 场景 2: 带进度跟踪
async def on_progress(progress):
    print(f"进度: {progress.completed}/{progress.total}")

task = await scraper.batch_extract_data_async(
    contracts=all_contracts,
    callback=on_progress
)

# 场景 3: 部分失败恢复
partial_results = await scraper.batch_extract_with_recovery(
    contracts=all_contracts,
    retry_failed=True,
    max_retries=3
)
```

---

#### 需求: 增量数据更新

**描述:** 系统必须支持增量数据更新，避免重复提取

**实现要求:**
- 识别最新数据时间戳
- 智能跳过已提取数据
- 合并新数据与历史数据
- 冲突检测与解决
- 更新日志记录

**验收标准:**
- [ ] 增量更新覆盖率 100%
- [ ] 重复数据率 < 1%
- [ ] 冲突解决正确率 > 95%
- [ ] 更新性能提升 > 50%

**场景:**

```python
# 场景 1: 检查最新数据时间戳
last_update = await scraper.get_last_update_time("HSI")

# 场景 2: 增量更新
incremental_data = await scraper.incremental_update(
    contract="HSI",
    since_date=last_update
)

# 场景 3: 冲突检测与解决
merged_data = await scraper.merge_with_conflict_resolution(
    old_data=existing_data,
    new_data=new_data,
    resolution_strategy="newest_timestamp"
)
```

---

### 6. 缓存与存储

#### 需求: 多层缓存系统

**描述:** 系统必须实现多层缓存以提高数据访问性能

**缓存层级:**
- 内存缓存 (5 分钟)
- 文件缓存 (1 小时)
- 数据库缓存 (24 小时)

**实现要求:**
- LRU 内存缓存
- 文件序列化存储
- SQLite 数据库存储
- 缓存失效策略
- 缓存预热机制

**验收标准:**
- [ ] 缓存命中率 > 80%
- [ ] 内存使用 < 500MB
- [ ] 缓存读取延迟 < 10ms
- [ ] 缓存更新一致性 100%

**场景:**

```python
# 场景 1: 读取缓存
cached_data = await scraper.get_cached_data(
    contract="HSI",
    date=date(2025, 10, 27)
)

# 场景 2: 更新缓存
await scraper.update_cache(
    contract="HSI",
    data=processed_data,
    ttl=3600
)

# 场景 3: 缓存预热
await scraper.warmup_cache(
    contracts=["HSI", "MHI", "HHI"],
    recent_days=7
)
```

---

#### 需求: 数据持久化

**描述:** 系统必须将数据持久化到数据库

**存储要求:**
- SQLite 数据库
- 表结构设计优化
- 索引优化
- 批量写入优化
- 数据备份机制

**验收标准:**
- [ ] 写入性能 > 1000 记录/秒
- [ ] 查询性能 < 100ms
- [ ] 数据一致性 100%
- [ ] 备份恢复成功率 100%

**场景:**

```python
# 场景 1: 存储期货数据
await scraper.store_futures_data(
    contract="HSI",
    data=df
)

# 场景 2: 查询历史数据
historical_data = await scraper.query_historical_data(
    contract="HSI",
    start_date=date(2024, 1, 1),
    end_date=date(2024, 12, 31)
)

# 场景 3: 数据库备份
backup_path = await scraper.backup_database(
    backup_dir="./backups"
)
```

---

### 7. 实时数据监控

#### 需求: 实时数据流

**描述:** 系统必须支持实时期货数据流

**实现要求:**
- WebSocket 连接
- 实时数据推送
- 数据过滤
- 连接重试机制
- 断线重连

**验收标准:**
- [ ] 实时延迟 < 1 秒
- [ ] 连接稳定性 > 99%
- [ ] 数据丢失率 < 0.1%
- [ ] 重连恢复时间 < 5 秒

**场景:**

```python
# 场景 1: 订阅实时数据
async def on_realtime_data(data):
    print(f"实时数据: {data}")

await scraper.subscribe_realtime_data(
    contracts=["HSI", "MHI"],
    callback=on_realtime_data
)

# 场景 2: 过滤实时数据
await scraper.subscribe_realtime_data(
    contracts=["HSI"],
    filters={
        "min_volume": 1000,
        "price_change_threshold": 0.5
    },
    callback=on_filtered_data
)

# 场景 3: 断开连接
await scraper.unsubscribe_realtime_data(subscription_id)
```

---

### 8. API 接口

#### 需求: RESTful API

**描述:** 系统必须提供 RESTful API 接口

**API 端点:**
- GET /api/futures/contracts - 获取合约列表
- GET /api/futures/data/{contract} - 获取合约数据
- GET /api/futures/realtime/{contract} - 获取实时数据
- GET /api/futures/oi/{contract} - 获取 OI 数据
- GET /api/futures/stats/{contract} - 获取交易统计

**验收标准:**
- [ ] API 响应时间 < 200ms
- [ ] API 可用性 > 99.9%
- [ ] 支持并发请求 > 100
- [ ] API 文档完整

**场景:**

```python
# 场景 1: 获取合约列表
contracts = requests.get("http://localhost:8001/api/futures/contracts")

# 场景 2: 获取合约数据
data = requests.get(
    "http://localhost:8001/api/futures/data/HSI",
    params={
        "start_date": "2025-10-01",
        "end_date": "2025-10-27"
    }
)

# 场景 3: 获取实时数据
realtime = requests.get("http://localhost:8001/api/futures/realtime/HSI")
```

---

## 数据格式规范

### 期货数据 JSON 格式

```json
{
  "contract": "HSI",
  "trade_date": "2025-10-27",
  "ohlcv": {
    "open": 24850.0,
    "high": 25200.0,
    "low": 24750.0,
    "close": 25100.0,
    "volume": 150000
  },
  "open_interest": {
    "total": 120000,
    "long": 65000,
    "short": 55000,
    "change": 2000
  },
  "turnover": {
    "amount": 3750000000.0,
    "avg_price": 25000.0
  },
  "metadata": {
    "currency": "HKD",
    "multiplier": 10,
    "source": "HKEX",
    "timestamp": "2025-10-27T16:10:00"
  }
}
```

### 错误响应格式

```json
{
  "error": {
    "code": "DATA_NOT_FOUND",
    "message": "未找到指定日期的期货数据",
    "details": {
      "contract": "HSI",
      "date": "2025-10-28"
    }
  }
}
```

---

## 性能要求

### 提取性能
- 单合约日数据提取: < 5 秒
- 多合约并发提取: 5 合约/分钟
- 实时数据延迟: < 1 秒
- 历史数据查询: < 100ms

### 处理性能
- 数据验证: < 1 秒/1000 条
- 数据清洗: < 1 秒/1000 条
- 数据存储: < 1 秒/1000 条
- 缓存读取: < 10ms

### 并发性能
- 支持并发提取: 10 合约
- API 并发请求: 100
- 实时连接数: 50
- 数据库连接池: 20

---

## 错误处理

### 错误分类
1. **网络错误** - 连接超时、HTTP 错误
2. **数据错误** - 格式错误、缺失数据
3. **系统错误** - 内存不足、磁盘空间不足
4. **业务错误** - 无效合约、数据过期

### 错误恢复策略
- 指数退避重试
- 降级到缓存数据
- 切换备用数据源
- 告警通知

---

## 监控指标

### 关键指标
- 数据提取成功率
- 数据质量评分
- API 响应时间
- 缓存命中率
- 错误率分布

### 告警阈值
- 数据提取成功率 < 95%
- API 响应时间 > 500ms
- 缓存命中率 < 70%
- 错误率 > 5%

---

## 测试要求

### 单元测试
- 数据提取测试覆盖率 > 90%
- 数据验证测试覆盖率 > 90%
- 缓存功能测试覆盖率 > 90%
- API 接口测试覆盖率 > 90%

### 集成测试
- 端到端数据流测试
- 并发提取测试
- 缓存一致性测试
- 错误恢复测试

### 性能测试
- 负载测试 (100 并发)
- 压力测试 (极限负载)
- 稳定性测试 (72 小时)
- 数据一致性测试

---

## 文档要求

### 用户文档
- API 参考文档
- 数据格式说明
- 使用示例
- 最佳实践

### 开发文档
- 架构设计文档
- 模块接口文档
- 扩展开发指南
- 维护手册

---

## 版本历史

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|----------|------|
| 1.0.0 | 2025-10-27 | 初始版本创建 | Claude Code |

---

## 批准状态

- [ ] 技术架构师审批
- [ ] 开发负责人审批
- [ ] 最终批准

---

## 相关文档

- 提案文档: `../../proposal.md`
- 任务文档: `../../tasks.md`
- 设计文档: `../../design.md`
- Chrome MCP 集成: `../chrome-mcp-integration/spec.md`
