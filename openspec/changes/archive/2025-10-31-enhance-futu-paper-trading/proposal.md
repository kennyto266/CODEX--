# OpenSpec Proposal: 增强富途牛牛模拟账户交易系统

## 变更概要

**变更ID**: enhance-futu-paper-trading
**类型**: 功能增强 (Feature Enhancement)
**影响范围**: 交易执行系统、仪表板、API集成
**优先级**: 高

## 目标

实现完整的富途牛牛模拟账户交易系统，基于现有的 FUTU API 实现，提供安全的模拟交易环境，用于策略验证和系统测试。

## Why

### 业务价值
1. **策略验证**: 当前缺乏安全的模拟交易环境，策略开发者无法在不冒真实资金风险的情况下验证交易策略
2. **系统测试**: 新的交易功能需要在接近真实环境的条件下进行充分测试
3. **用户培训**: 新用户需要学习和熟悉交易系统，模拟环境是理想的学习场所
4. **风险评估**: 通过模拟交易可以评估策略在不同市场条件下的表现

### 技术价值
1. **架构完善**: 现有 FUTU API 集成已具备 SIMULATE 能力，但缺乏统一的模拟交易管理系统
2. **功能补全**: 虽然已有基础实现，但缺少风险控制、实时监控、性能分析等高级功能
3. **用户体验**: 需要专门的模拟交易界面和工具，提升用户体验
4. **系统可靠性**: 模拟环境有助于发现和修复潜在问题，提高真实交易环境的安全性

### 竞争优势
1. **安全性**: 100% 使用模拟环境，确保不会造成真实资金损失
2. **完整性**: 提供端到端的模拟交易解决方案
3. **可扩展性**: 基于现有架构，易于扩展和维护

## What Changes

这个变更将添加以下功能：

1. **新增核心组件**：
   - FutuPaperTradingController - 模拟交易控制器
   - PaperTradingEngine - 模拟交易执行引擎
   - SimulatedOrderManager - 模拟订单管理器
   - PaperTradingDashboard - 模拟交易仪表板

2. **增强现有功能**：
   - 扩展 FutuTradingAPI 的模拟交易能力
   - 集成风险控制机制
   - 添加实时监控功能

3. **新增API端点**：
   - GET/POST /api/paper-trading/status
   - GET/POST /api/paper-trading/orders
   - GET /api/paper-trading/positions
   - GET /api/paper-trading/performance

4. **新增前端页面**：
   - 模拟交易概览页
   - 持仓管理页
   - 交易历史页
   - 性能分析页

## 背景与现状

### 现有实现分析

当前系统已具备基础组件：

1. **FutuTradingAPI** (`src/trading/futu_trading_api.py`)
   - 已实现 SIMULATE 交易环境
   - 支持港股交易（HK市场）
   - 具备下单、查询、取消订单功能

2. **FutuLiveTradingSystem** (`src/trading/futu_live_trading_system.py`)
   - 集成实时执行引擎
   - 信号管理集成
   - 自动交易循环

3. **配置信息**
   - User ID: 2860386
   - Host: 127.0.0.1:11111
   - WebSocket: 127.0.0.1:33333

### 现有问题

1. 缺乏独立的模拟交易控制器
2. 交易工作流不够清晰
3. 缺少模拟交易专用仪表板
4. 风险控制机制不完善
5. 性能监控功能不足

## 详细方案

### 1. 核心组件设计

#### FutuPaperTradingController
- 模拟交易主控制器
- 负责交易流程管理
- 集成信号处理和执行
- 提供统一的 API 接口

#### PaperTradingEngine
- 模拟交易执行引擎
- 订单生命周期管理
- 仓位和资金跟踪
- 交易日志记录

#### SimulatedOrderManager
- 订单状态管理
- 订单匹配逻辑
- 成交确认处理
- 异常订单处理

#### PaperTradingDashboard
- 实时交易监控
- 持仓和收益展示
- 交易历史查询
- 风险指标监控

### 2. 功能需求

#### 2.1 交易执行功能
- ✅ 基于现有 FutuTradingAPI 的 SIMULATE 环境
- ✅ 支持限价单、市价单
- ✅ 订单取消和修改
- ✅ 实时订单状态更新

#### 2.2 资金管理功能
- 虚拟初始资金设置（默认 1,000,000 HKD）
- 实时资金余额计算
- 交易费用计算
- 盈亏统计

#### 2.3 风险控制功能
- 单笔交易金额限制
- 日交易次数限制
- 持仓集中度控制
- 紧急停止机制

#### 2.4 监控功能
- 实时持仓监控
- 交易性能指标
- 风险指标计算
- 交易日志记录

#### 2.5 API 集成
- RESTful API 接口
- WebSocket 实时推送
- 与现有 SignalManager 集成
- 与 RealtimeExecutionEngine 集成

### 3. 集成方案

#### 3.1 与现有系统集成
- 复用 `FutuTradingAPI` (SIMULATE 模式)
- 集成到 `RealtimeExecutionEngine`
- 通过 WebSocket 提供实时数据
- 与仪表板系统对接

#### 3.2 配置管理
- 扩展 `futu_config.py` 添加模拟交易配置
- 环境变量支持
- 配置文件热重载

#### 3.3 数据流设计
```
信号生成 → 信号验证 → 风险检查 → 下单 → 执行监控 → 成交确认 → 更新持仓
```

### 4. 安全措施

1. **环境隔离**
   - 仅使用 DEMO/SIMULATE 环境
   - 与真实交易环境物理隔离

2. **权限控制**
   - API 密钥管理
   - 交易密码保护

3. **资金保护**
   - 虚拟资金限制
   - 交易金额限制

4. **操作日志**
   - 所有交易操作日志记录
   - 异常操作告警

## 实现计划

### 阶段一：核心控制器开发 (1-2天)
1. 创建 `FutuPaperTradingController` 类
2. 实现基础交易方法
3. 集成 FutuTradingAPI
4. 单元测试

### 阶段二：执行引擎开发 (2-3天)
1. 创建 `PaperTradingEngine` 类
2. 实现订单管理功能
3. 资金和仓位管理
4. 风险控制机制

### 阶段三：API 和集成 (1-2天)
1. RESTful API 接口
2. WebSocket 实时推送
3. 与现有系统集成
4. 集成测试

### 阶段四：仪表板开发 (2-3天)
1. 创建模拟交易仪表板
2. 实时数据展示
3. 交易历史查询
4. 性能指标计算

### 阶段五：测试和优化 (1-2天)
1. 端到端测试
2. 性能优化
3. 文档完善
4. 部署验证

## 验收标准

### 功能验收
- [ ] 能够连接到富途 DEMO 环境
- [ ] 能够执行买入/卖出订单
- [ ] 能够查询持仓和订单状态
- [ ] 风险控制机制有效
- [ ] 实时监控功能正常

### 性能验收
- [ ] 订单响应时间 < 1秒
- [ ] 支持并发交易
- [ ] 内存使用合理
- [ ] 无内存泄漏

### 安全验收
- [ ] 仅使用模拟环境
- [ ] 所有操作有日志记录
- [ ] 异常情况有告警
- [ ] 配置信息加密存储

## 风险评估

### 技术风险
- **富途 API 变更**: 中等风险 - 通过版本锁定和兼容性测试降低
- **网络连接问题**: 低风险 - 实现重连机制和超时处理
- **数据同步问题**: 中等风险 - 通过 WebSocket 实时更新和定期同步

### 业务风险
- **模拟环境限制**: 低风险 - 仅用于测试，不影响真实交易
- **策略验证准确性**: 中等风险 - 通过回测对比验证

## 依赖关系

### 前置依赖
- ✅ FutuTradingAPI 已实现
- ✅ FutuLiveTradingSystem 已实现
- ✅ RealtimeExecutionEngine 已实现

### 后置影响
- 📋 可能需要更新 API 文档
- 📋 需要更新仪表板界面
- 📋 需要更新部署脚本

## 参考资料

1. 富途 OpenAPI 文档: https://openapi.futunn.com/futu-api-doc/intro/intro.html
2. 现有 FutuTradingAPI 实现: `src/trading/futu_trading_api.py`
3. 现有配置: `src/trading/futu_config.py`
4. 执行引擎: `src/trading/realtime_execution_engine.py`
