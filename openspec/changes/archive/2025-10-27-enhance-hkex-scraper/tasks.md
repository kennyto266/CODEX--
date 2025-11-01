# HKEX 爬虫增强 - 任务清单

## 项目信息

**变更 ID:** enhance-hkex-scraper

**开始日期:** 2025-10-27

**负责人:** Claude Code

**优先级:** 高

---

## 任务列表

### Phase 1: Chrome MCP 控制器开发 (2天)

#### [ ] 任务 1.1: 创建 Chrome DevTools MCP 控制器
- **描述:** 实现 Chrome DevTools MCP 集成，提供网页自动化能力
- **文件:** `src/data_adapters/hkex/hkex_chrome_controller.py`
- **依赖:** 无
- **验收标准:**
  - [ ] 支持页面导航和加载
  - [ ] 支持元素查询和选择器生成
  - [ ] 支持页面快照获取
  - [ ] 支持 JavaScript 执行
- **工作量:** 1天
- **测试:** `test/test_hkex_chrome_controller.py`

#### [ ] 任务 1.2: 实现选择器自动发现
- **描述:** 智能识别网页中的数据表格和结构
- **文件:** `src/data_adapters/hkex/selector_discovery.py`
- **依赖:** 任务 1.1
- **验收标准:**
  - [ ] 自动发现表格元素
  - [ ] 生成稳定的 CSS 选择器
  - [ ] 验证选择器有效性
  - [ ] 支持多语言页面（中文/英文）
- **工作量:** 0.5天
- **测试:** `test/test_selector_discovery.py`

#### [ ] 任务 1.3: 创建页面变化监控
- **描述:** 监控网页内容变化，触发数据更新
- **文件:** `src/data_adapters/hkex/page_monitor.py`
- **依赖:** 任务 1.1
- **验收标准:**
  - [ ] 检测页面结构变化
  - [ ] 监控数据更新时间
  - [ ] 支持阈值配置
  - [ ] 提供变更通知
- **工作量:** 0.5天
- **测试:** `test/test_page_monitor.py`

---

### Phase 2: 期货数据爬虫 (2天)

#### [ ] 任务 2.1: 分析 HKEX 期货页面结构
- **描述:** 使用 Chrome MCP 检查 HKEX 期货页面，识别数据元素
- **目标页面:**
  - 恒生指数期货 (HSI Futures): https://www.hkex.com.hk/Products/Market-Data/Futures?sc_lang=zh-HK
  - 迷你恒生指数期货 (MHI Futures): 同上
  - 小恒生指数期货 (HHI Futures): 同上
- **依赖:** Phase 1
- **验收标准:**
  - [ ] 获取页面快照和分析报告
  - [ ] 识别所有期货数据表格
  - [ ] 提取选择器和数据字段映射
  - [ ] 生成结构文档

#### [ ] 任务 2.2: 实现期货数据提取器
- **描述:** 实现期货数据爬取逻辑
- **文件:** `src/data_adapters/hkex/futures_scraper.py`
- **依赖:** 任务 2.1
- **验收标准:**
  - [ ] 支持 HSI 期货数据（价格、成交量、未平仓量）
  - [ ] 支持 MHI 期货数据
  - [ ] 支持 HHI 期货数据
  - [ ] 支持历史数据下载
  - [ ] 数据格式标准化
- **数据字段:**
  - 日期 (date)
  - 开盘价 (open)
  - 最高价 (high)
  - 最低价 (low)
  - 收盘价 (close)
  - 成交量 (volume)
  - 未平仓量 (open_interest)
  - 成交额 (turnover)
- **工作量:** 1.5天
- **测试:** `test/test_futures_scraper.py`

#### [ ] 任务 2.3: 期货数据验证与清洗
- **描述:** 实现数据质量检查和清洗逻辑
- **文件:** `src/data_adapters/hkex/data_processor.py`
- **依赖:** 任务 2.2
- **验收标准:**
  - [ ] 验证数据完整性
  - [ ] 检测异常值
  - [ ] 数据类型转换
  - [ ] 空值处理
- **工作量:** 0.5天
- **测试:** `test/test_data_processor.py`

---

### Phase 3: 股票数据爬虫 (2天)

#### [ ] 任务 3.1: 分析 HKEX 股票页面结构
- **描述:** 检查 HKEX 股票数据页面
- **目标页面:**
  - 主板股票: https://www.hkex.com.hk/eng/market/sec_tradinfo/mdata/Pages/default.aspx
  - 创业板股票: 同上
- **依赖:** Phase 1
- **验收标准:**
  - [ ] 获取页面快照
  - [ ] 识别股票列表表格
  - [ ] 提取股票基本信息字段
  - [ ] 生成选择器映射

#### [ ] 任务 3.2: 实现股票数据提取器
- **描述:** 实现股票数据爬取
- **文件:** `src/data_adapters/hkex/stocks_scraper.py`
- **依赖:** 任务 3.1
- **验收标准:**
  - [ ] 支持主板所有股票列表
  - [ ] 支持创业板股票列表
  - [ ] 提取股票代码、名称、行业
  - [ ] 获取实时报价数据
  - [ ] 支持批量处理
- **数据字段:**
  - 股票代码 (stock_code)
  - 股票名称 (stock_name)
  - 行业分类 (sector)
  - 现价 (current_price)
  - 涨跌额 (change)
  - 涨跌幅 (change_percent)
  - 成交量 (volume)
  - 成交额 (turnover)
  - 市值 (market_cap)
- **工作量:** 1.5天
- **测试:** `test/test_stocks_scraper.py`

#### [ ] 任务 3.3: 股票代码映射系统
- **描述:** 实现股票代码到完整信息的映射
- **文件:** `src/data_adapters/hkex/stock_registry.py`
- **依赖:** 任务 3.2
- **验收标准:**
  - [ ] 创建股票代码索引
  - [ ] 支持模糊搜索
  - [ ] 缓存股票信息
  - [ ] API 查询接口
- **工作量:** 0.5天
- **测试:** `test/test_stock_registry.py`

---

### Phase 4: 指数数据爬虫 (2天)

#### [ ] 任务 4.1: 分析 HKEX 指数页面
- **描述:** 检查指数数据页面
- **目标页面:**
  - 恒生指数: https://www.hkex.com.hk/eng/market/sec_tradinfo/mdata/Pages/HSI.aspx
  - 恒生中国企业指数: 同上
  - 恒生科技指数: 同上
  - 恒生综合指数: 同上
- **依赖:** Phase 1
- **验收标准:**
  - [ ] 获取各指数页面快照
  - [ ] 识别指数成分股列表
  - [ ] 提取指数历史数据
  - [ ] 生成选择器文档

#### [ ] 任务 4.2: 实现指数数据提取器
- **描述:** 实现指数数据爬取
- **文件:** `src/data_adapters/hkex/indices_scraper.py`
- **依赖:** 任务 4.1
- **验收标准:**
  - [ ] 支持恒生指数系列
  - [ ] 获取指数成分股
  - [ ] 提取指数历史数据
  - [ ] 计算指数统计指标
- **数据字段:**
  - 指数代码 (index_code)
  - 指数名称 (index_name)
  - 当前点数 (current_value)
  - 涨跌点数 (change)
  - 涨跌比例 (change_percent)
  - 成分股数量 (components_count)
- **工作量:** 1.5天
- **测试:** `test/test_indices_scraper.py`

#### [ ] 任务 4.3: 指数成分股提取
- **描述:** 提取指数成分股详情
- **文件:** `src/data_adapters/hkex/index_components.py`
- **依赖:** 任务 4.2
- **验收标准:**
  - [ ] 提取成分股列表
  - [ ] 获取权重信息
  - [ ] 支持定期更新
  - [ ] 缓存成分股数据
- **工作量:** 0.5天
- **测试:** `test/test_index_components.py`

---

### Phase 5: 市场统计爬虫 (2天)

#### [ ] 任务 5.1: 分析市场统计页面
- **描述:** 检查 HKEX 市场统计页面
- **目标页面:**
  - 市场统计: https://www.hkex.com.hk/eng/market/sec_tradinfo/sec_tradinfo.aspx
  - 成交数据: 同上
  - IPO 数据: 同上
- **依赖:** Phase 1
- **验收标准:**
  - [ ] 获取市场统计页面结构
  - [ ] 识别所有统计指标
  - [ ] 提取历史数据链接
  - [ ] 生成数据字典

#### [ ] 任务 5.2: 实现市场统计提取器
- **描述:** 实现市场统计数据爬取
- **文件:** `src/data_adapters/hkex/market_stats_scraper.py`
- **依赖:** 任务 5.1
- **验收标准:**
  - [ ] 支持市场概览数据
  - [ ] 支持成交统计
  - [ ] 支持 IPO 数据
  - [ ] 支持行业分类统计
- **数据字段:**
  - 日期 (date)
  - 总成交额 (total_turnover)
  - 总成交量 (total_volume)
  - 上涨家数 (gainers)
  - 下跌家数 (losers)
  - 平盘家数 (unchanged)
  - IPO 数量 (ipo_count)
  - IPO 募资 (ipo_funds)
- **工作量:** 1.5天
- **测试:** `test/test_market_stats_scraper.py`

#### [ ] 任务 5.3: 历史数据下载器
- **描述:** 下载历史市场统计文件
- **文件:** `src/data_adapters/hkex/historical_downloader.py`
- **依赖:** 任务 5.2
- **验收标准:**
  - [ ] 支持 CSV/Excel 文件下载
  - [ ] 自动解析文件格式
  - [ ] 增量数据更新
  - [ ] 错误重试机制
- **工作量:** 0.5天
- **测试:** `test/test_historical_downloader.py`

---

### Phase 6: 数据处理管道 (2天)

#### [ ] 任务 6.1: 创建统一数据处理器
- **描述:** 整合所有数据源，建立统一处理管道
- **文件:** `src/data_adapters/hkex/data_processor.py`
- **依赖:** Phase 2-5
- **验收标准:**
  - [ ] 统一数据格式
  - [ ] 数据清洗流程
  - [ ] 质量评估
  - [ ] 异常检测
- **工作量:** 1天
- **测试:** `test/test_data_processor_integration.py`

#### [ ] 任务 6.2: 实现数据验证系统
- **描述:** 数据质量和一致性验证
- **文件:** `src/data_adapters/hkex/data_validator.py`
- **依赖:** 任务 6.1
- **验收标准:**
  - [ ] 完整性检查
  - [ ] 一致性验证
  - [ ] 异常值标记
  - [ ] 质量报告生成
- **工作量:** 0.5天
- **测试:** `test/test_data_validator.py`

#### [ ] 任务 6.3: 数据格式标准化
- **描述:** 统一所有数据源的格式
- **文件:** `src/data_adapters/hkex/data_formatter.py`
- **依赖:** 任务 6.1
- **验收标准:**
  - [ ] 时间戳标准化
  - [ ] 数值类型转换
  - [ ] 枚举值映射
  - [ ] 缺失值处理
- **工作量:** 0.5天
- **测试:** `test/test_data_formatter.py`

---

### Phase 7: 缓存与存储 (1天)

#### [ ] 任务 7.1: 实现缓存管理器
- **描述:** 多层缓存系统实现
- **文件:** `src/data_adapters/hkex/cache_manager.py`
- **依赖:** Phase 6
- **验收标准:**
  - [ ] 内存缓存 (LRU)
  - [ ] 文件缓存
  - [ ] 数据库缓存 (SQLite)
  - [ ] 缓存策略配置
- **缓存策略:**
  - 实时数据: 5分钟 TTL
  - 历史数据: 24小时 TTL
  - 元数据: 7天 TTL
- **工作量:** 0.5天
- **测试:** `test/test_cache_manager.py`

#### [ ] 任务 7.2: SQLite 数据库集成
- **描述:** 使用 SQLite 存储结构化数据
- **文件:** `src/data_adapters/hkex/database.py`
- **依赖:** 任务 7.1
- **验收标准:**
  - [ ] 自动创建表结构
  - [ ] 批量插入优化
  - [ ] 查询索引优化
  - [ ] 数据备份机制
- **工作量:** 0.5天
- **测试:** `test/test_database.py`

---

### Phase 8: API 接口开发 (1天)

#### [ ] 任务 8.1: 创建 FastAPI 路由
- **描述:** 实现 REST API 接口
- **文件:** `src/data_adapters/hkex/api_routes.py`
- **依赖:** Phase 7
- **验收标准:**
  - [ ] `GET /api/hkex/data/{data_type}` - 获取数据
  - [ ] `POST /api/hkex/scrape/start` - 启动爬取
  - [ ] `GET /api/hkex/scrape/status/{task_id}` - 任务状态
  - [ ] `GET /api/hkex/metrics` - 系统指标
  - [ ] `GET /api/hkex/export` - 数据导出
- **工作量:** 0.5天
- **测试:** `test/test_api_routes.py`

#### [ ] 任务 8.2: 实现任务调度
- **描述:** 使用 APScheduler 实现定时任务
- **文件:** `src/data_adapters/hkex/scheduler.py`
- **依赖:** 任务 8.1
- **验收标准:**
  - [ ] 定时数据更新
  - [ ] 任务状态监控
  - [ ] 错误处理
  - [ ] Webhook 通知
- **工作量:** 0.5天
- **测试:** `test/test_scheduler.py`

---

### Phase 9: 测试与优化 (2天)

#### [ ] 任务 9.1: 集成测试
- **描述:** 全流程集成测试
- **文件:** `tests/integration/test_hkex_complete_flow.py`
- **依赖:** Phase 1-8
- **验收标准:**
  - [ ] 端到端数据流程测试
  - [ ] 多数据源并发测试
  - [ ] 性能压力测试
  - [ ] 错误恢复测试
- **工作量:** 1天
- **测试类型:** 集成测试

#### [ ] 任务 9.2: 性能优化
- **描述:** 优化系统性能
- **依赖:** 任务 9.1
- **验收标准:**
  - [ ] 减少数据获取时间
  - [ ] 优化内存使用
  - [ ] 缓存命中率 > 80%
  - [ ] 并发处理优化
- **工作量:** 0.5天

#### [ ] 任务 9.3: 文档编写
- **描述:** 完善用户文档和 API 文档
- **文件:**
  - `docs/hkex_scraper_guide.md` - 用户指南
  - `docs/api_reference.md` - API 参考
  - `README.md` 更新
- **依赖:** Phase 1-8
- **验收标准:**
  - [ ] 用户指南完整
  - [ ] API 文档详细
  - [ ] 示例代码可用
  - [ ] 故障排除指南
- **工作量:** 0.5天

---

## 测试任务

### 单元测试要求

每个模块必须包含对应测试文件：

- `test/test_hkex_chrome_controller.py`
- `test/test_selector_discovery.py`
- `test/test_futures_scraper.py`
- `test/test_stocks_scraper.py`
- `test/test_indices_scraper.py`
- `test/test_market_stats_scraper.py`
- `test/test_data_processor.py`
- `test/test_cache_manager.py`
- `test/test_database.py`
- `test/test_api_routes.py`

### 测试覆盖率要求

- **行覆盖率:** > 80%
- **分支覆盖率:** > 70%
- **函数覆盖率:** > 90%
- **类覆盖率:** > 90%

### 集成测试

- `tests/integration/test_hkex_complete_flow.py` - 完整流程测试
- `tests/integration/test_multi_source_extraction.py` - 多数据源测试
- `tests/integration/test_performance.py` - 性能测试

---

## 部署清单

### [ ] 开发环境部署
- [ ] 安装依赖包
- [ ] 配置环境变量
- [ ] 启动测试服务

### [ ] 测试环境部署
- [ ] 部署到测试服务器
- [ ] 导入测试数据
- [ ] 运行集成测试

### [ ] 生产环境部署
- [ ] 灰度发布
- [ ] 监控系统
- [ ] 性能基线

---

## 验收检查清单

### 代码质量
- [ ] 通过 flake8 检查
- [ ] 通过 mypy 类型检查
- [ ] 单元测试覆盖率 > 80%
- [ ] 文档字符串完整
- [ ] 异常处理完善

### 功能完整性
- [ ] 所有 4 种数据源（期货、股票、指数、市场统计）实现
- [ ] Chrome MCP 集成完成
- [ ] 数据缓存系统工作
- [ ] API 接口全部可用
- [ ] 任务调度正常

### 性能要求
- [ ] 单页数据提取 < 5 秒
- [ ] 缓存命中率 > 80%
- [ ] 内存使用 < 500MB
- [ ] 并发处理 > 10 请求/秒

### 可靠性
- [ ] 数据准确率 > 99%
- [ ] 错误自动恢复
- [ ] 日志记录完整
- [ ] 监控指标正常

---

## 风险缓解

### 高优先级风险
1. **HKEX 网站结构变更**
   - 缓解：选择器自动发现机制
   - 监控：每日页面结构检查

2. **访问频率限制**
   - 缓解：请求间隔 1-2 秒
   - 监控：响应状态码 429

3. **数据不一致**
   - 缓解：数据验证系统
   - 监控：质量指标报告

### 备用方案
- 如果自动选择器失效，回退到预设选择器
- 如果频繁失败，启用代理池
- 如果数据质量差，切换到模拟数据模式

---

## 任务完成标准

每个任务完成后，必须满足以下条件：

1. **代码完成**
   - 功能代码实现
   - 单元测试通过
   - 文档更新

2. **质量检查**
   - 静态分析通过
   - 测试覆盖率达标
   - 无严重警告

3. **集成验证**
   - 与其他模块集成正常
   - 端到端流程可用
   - 性能指标达标

只有满足所有条件，任务才能标记为完成并进入下一阶段。
