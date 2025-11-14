# 个人工作区系统 (Personal Workspace System)

## 概述

个人工作区系统是一个完整的投资组合管理和分析平台，提供个人化的投资跟踪、交易分析、风险管理和交易日志功能。该系统专为港股投资者设计，支持多工作区、实时数据更新和深度分析。

## 核心功能

### 1. 工作区管理器 (T128)
- **多工作区支持**: 支持每个用户创建多个独立工作区
- **个性化设置**: 主题、语言、时区、界面布局等
- **用户偏好**: 策略类型、风险承受度、投资风格等
- **数据同步**: 自动保存和同步工作区数据
- **导入导出**: 支持工作区数据的导入导出

### 2. 投资组合管理 (T129)
- **多资产组合**: 支持股票、基金等多种资产
- **实时仓位跟踪**: 实时更新持仓和市场价值
- **收益计算**: 自动计算未实现和已实现损益
- **风险分析**: 集中度、分散化、波动率等风险指标
- **组合再平衡**: 支持智能再平衡建议

### 3. 交易历史管理 (T130)
- **完整交易记录**: 记录所有买卖交易
- **智能分类**: 按组合、股票、策略自动分类
- **盈亏分析**: 详细计算每笔交易的盈亏
- **交易统计**: 胜率、利润因子、平均持仓等
- **手续费跟踪**: 自动计算和统计交易成本

### 4. 个人分析模块 (T131)
- **交易行为分析**: 分析交易时机、频率、模式
- **绩效归因**: 识别表现来源和驱动因素
- **风险评估**: 实时风险监控和预警
- **个性化建议**: 基于历史数据的智能建议
- **可视化报告**: 生成专业分析报告

### 5. 交易日志和笔记 (T132)
- **交易笔记**: 记录每笔交易的思考和理由
- **市场观察**: 记录市场情绪和关键事件
- **策略反思**: 定期回顾和评估策略表现
- **情绪跟踪**: 分析交易情绪对表现的影响
- **搜索功能**: 快速检索历史记录

## 技术架构

### 核心组件

```
src/workspace/
├── __init__.py              # 模块初始化
├── manager.py               # 工作区管理器
├── portfolio.py             # 投资组合管理
├── trade_history.py         # 交易历史
├── analytics.py             # 个人分析
├── journal.py               # 交易日志
├── dashboard_integration.py # 仪表板API集成
├── init_database.py         # 数据库初始化
├── demo_workspace_en.py     # 演示脚本
└── README.md                # 文档
```

### 数据存储

- **文件存储**: 使用JSON格式存储，支持直接查看和编辑
- **数据库**: SQLite数据库提供结构化存储和查询
- **目录结构**:
  ```
  workspace_data/
  ├── portfolios/        # 投资组合数据
  ├── trades/            # 交易记录
  ├── journal/           # 交易日志
  └── workspace.db       # SQLite数据库
  ```

### API集成

通过 FastAPI 提供RESTful API，支持：

- 工作区管理
- 投资组合CRUD
- 交易记录管理
- 分析数据查询
- 日志条目管理
- 数据导入导出

## 快速开始

### 1. 初始化数据库

```bash
python src/workspace/init_database.py --init
```

### 2. 运行演示

```bash
python src/workspace/demo_workspace_en.py
```

### 3. 在代码中使用

```python
from workspace import (
    WorkspaceManager,
    PortfolioManager,
    TradeHistoryManager,
    PersonalAnalytics,
    TradingJournal,
)

# 创建管理器
ws_manager = WorkspaceManager()
pf_manager = PortfolioManager()
trade_manager = TradeHistoryManager()
journal = TradingJournal()

# 创建工作区
workspace = ws_manager.create_workspace(
    user_id="user_001",
    name="我的投资工作区"
)

# 创建投资组合
portfolio = pf_manager.create_portfolio(
    user_id="user_001",
    name="核心组合",
    initial_cash=100000.0
)

# 添加持仓
pf_manager.add_position(
    user_id="user_001",
    portfolio_name="核心组合",
    symbol="0700.HK",
    quantity=1000,
    price=380.50
)

# 添加交易记录
trade = trade_manager.add_trade(
    user_id="user_001",
    portfolio_name="核心组合",
    symbol="0700.HK",
    side="buy",
    quantity=1000,
    price=380.50
)

# 添加交易笔记
note = journal.add_trade_note(
    user_id="user_001",
    symbol="0700.HK",
    note_type="entry",
    content="看好公司基本面",
    strategy="value",
    emotion="confident"
)

# 获取分析
analytics = PersonalAnalytics(pf_manager, trade_manager)
behavior = analytics.analyze_trading_behavior("user_001")
recommendations = analytics.get_recommendations("user_001")
```

## API端点

### 工作区
- `GET /api/workspace/workspace/{user_id}` - 获取工作区
- `POST /api/workspace/workspace` - 创建工作区
- `PUT /api/workspace/workspace/{user_id}` - 更新工作区

### 投资组合
- `GET /api/workspace/portfolios/{user_id}` - 获取所有组合
- `GET /api/workspace/portfolio/{user_id}/{name}` - 获取特定组合
- `POST /api/workspace/portfolio` - 创建组合
- `POST /api/workspace/portfolio/{user_id}/{name}/position` - 添加持仓

### 交易历史
- `GET /api/workspace/trades/{user_id}` - 获取交易记录
- `POST /api/workspace/trade` - 添加交易
- `GET /api/workspace/trades/{user_id}/statistics` - 获取统计

### 分析
- `GET /api/workspace/analytics/{user_id}/behavior` - 行为分析
- `GET /api/workspace/analytics/{user_id}/{name}/performance` - 表现分析
- `GET /api/workspace/analytics/{user_id}/risk` - 风险概况
- `GET /api/workspace/analytics/{user_id}/recommendations` - 建议

### 交易日志
- `GET /api/workspace/journal/{user_id}/notes` - 获取笔记
- `POST /api/workspace/journal/{user_id}/note` - 添加笔记
- `GET /api/workspace/journal/{user_id}/search?q=keyword` - 搜索日志

## 核心类说明

### WorkspaceManager
管理用户工作区和配置。

**主要方法**:
- `create_workspace()` - 创建工作区
- `get_workspace()` - 获取工作区
- `update_workspace()` - 更新工作区
- `delete_workspace()` - 删除工作区
- `export_workspace()` - 导出工作区
- `import_workspace()` - 导入工作区

### PortfolioManager
管理投资组合和持仓。

**主要方法**:
- `create_portfolio()` - 创建组合
- `add_position()` - 添加持仓
- `remove_position()` - 移除持仓
- `update_prices()` - 更新价格
- `get_portfolio_summary()` - 获取摘要
- `get_portfolio()` - 获取组合

### TradeHistoryManager
管理交易记录和统计。

**主要方法**:
- `add_trade()` - 添加交易
- `get_trades()` - 获取交易
- `get_statistics()` - 获取统计
- `get_symbol_performance()` - 股票表现
- `get_daily_pnl_series()` - 每日损益

### PersonalAnalytics
提供深度分析和洞察。

**主要方法**:
- `analyze_trading_behavior()` - 交易行为分析
- `analyze_performance()` - 表现分析
- `get_risk_profile()` - 风险概况
- `get_recommendations()` - 获取建议
- `generate_report()` - 生成报告

### TradingJournal
管理交易日志和笔记。

**主要方法**:
- `add_trade_note()` - 添加笔记
- `add_market_observation()` - 市场观察
- `add_strategy_reflection()` - 策略反思
- `search_journal()` - 搜索
- `get_emotion_analysis()` - 情绪分析

## 数据模型

### Position (持仓)
```python
@dataclass
class Position:
    symbol: str           # 股票代码
    quantity: float       # 数量
    avg_cost: float       # 平均成本
    current_price: float  # 当前价格
    market_value: float   # 市值
    unrealized_pnl: float # 未实现损益
    updated_at: str       # 更新时间
```

### Trade (交易)
```python
@dataclass
class Trade:
    id: str              # 交易ID
    symbol: str          # 股票代码
    side: str            # 买卖方向
    quantity: float      # 数量
    price: float         # 价格
    timestamp: str       # 时间
    fees: float          # 手续费
    pnl: float           # 损益
    notes: str           # 备注
    strategy: str        # 策略
```

### TradeNote (交易笔记)
```python
@dataclass
class TradeNote:
    id: str           # 笔记ID
    symbol: str       # 股票代码
    note_type: str    # 笔记类型
    content: str      # 内容
    emotion: str      # 情绪
    tags: List[str]   # 标签
    timestamp: str    # 时间
```

## 最佳实践

### 1. 定期记录
- 每笔交易后立即记录交易笔记
- 记录进出场理由和当时情绪
- 定期回顾和反思策略表现

### 2. 数据维护
- 定期备份工作区数据
- 及时更新持仓价格
- 清理无效或重复的交易记录

### 3. 风险控制
- 监控集中度风险
- 保持适当的现金比例
- 关注最大回撤

### 4. 持续优化
- 定期查看分析报告
- 根据建议调整策略
- 记录改进和心得

## 扩展功能

### 1. 数据加密
系统支持对敏感数据进行加密存储，保护用户隐私。

### 2. 数据导入
支持从 CSV、Excel 等格式导入历史数据。

### 3. 自定义指标
可以添加自定义技术指标和分析方法。

### 4. 多语言支持
系统支持多语言界面和内容。

## 性能优化

- 使用JSON文件存储，支持快速读写
- SQLite数据库提供高效查询
- 支持数据缓存减少重复计算
- 异步处理提升响应速度

## 测试

运行单元测试：

```bash
python -m pytest tests/test_workspace.py -v
```

测试覆盖：
- 工作区管理
- 投资组合操作
- 交易记录
- 分析功能
- 交易日志

## 贡献

欢迎提交Issue和Pull Request来改进系统。

## 许可证

本项目采用MIT许可证。

## 更新日志

### v1.0.0 (2025-11-09)
- 初始版本发布
- 实现T128-T132所有功能
- 完整的工作区管理系统
- 投资组合跟踪和分析
- 交易历史和日志功能
- 个人分析和建议系统
- API集成和演示
- 完整的单元测试

## 支持

如有问题或建议，请联系开发团队。
