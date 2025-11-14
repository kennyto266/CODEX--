开发者概览
==========

欢迎开发者！

本指南将帮助您了解港股量化交易系统的技术架构、开发环境搭建、代码规范和贡献流程。

项目概述
--------

**技术栈**

* **后端:** Python 3.10+, FastAPI, Asyncio
* **数据处理:** Pandas, NumPy, TA-Lib
* **前端:** Vue 3, TypeScript, Vite
* **数据库:** SQLite (开发), PostgreSQL (生产)
* **缓存:** Redis
* **消息队列:** Asyncio Queue
* **图表:** Plotly, D3.js
* **测试:** pytest, pytest-asyncio
* **代码质量:** black, flake8, mypy, pre-commit
* **Rust组件:** Rust, PyO3, Maturin

**核心特性**

* 多智能体协作架构
* 11种技术指标策略
* 高性能并行回测
* 实时数据处理
* WebSocket实时通信
* 完整风险控制
* 统一数据适配器
* 自动化测试覆盖

系统架构
--------

系统采用分层架构设计：

.. code-block::

   ┌─────────────────────────────────────────┐
   │              Web界面层                   │
   │    (Vue 3 + TypeScript + Vite)         │
   └─────────────────────────────────────────┘
                        │
   ┌─────────────────────────────────────────┐
   │              API层                      │
   │      (FastAPI + REST + WebSocket)       │
   └─────────────────────────────────────────┘
                        │
   ┌─────────────────────────────────────────┐
   │              业务逻辑层                  │
   │  ┌───────────┐ ┌───────────┐ ┌────────┐ │
   │  │  Agent层  │ │ 策略回测  │ │ 组合   │ │
   │  │  (7个AI)  │ │   引擎    │ │ 管理   │ │
   │  └───────────┘ └───────────┘ └────────┘ │
   └─────────────────────────────────────────┘
                        │
   ┌─────────────────────────────────────────┐
   │              数据层                     │
   │  ┌───────────┐ ┌───────────┐ ┌────────┐ │
   │  │ 数据适配  │ │   缓存    │ │ 数据   │ │
   │  │   器      │ │ (Redis)   │ │ 存储   │ │
   │  └───────────┘ └───────────┘ └────────┘ │
   └─────────────────────────────────────────┘
                        │
   ┌─────────────────────────────────────────┐
   │              基础设施层                  │
   │    (数据库 + 消息队列 + 日志)           │
   └─────────────────────────────────────────┘

目录结构
--------

.. code-block::

   quant-system/
   │
   ├── src/                      # 源代码
   │   ├── agents/              # 智能体模块
   │   │   ├── base_agent.py    # Agent基类
   │   │   ├── coordinator.py   # 协调者
   │   │   ├── data_scientist.py
   │   │   ├── quantitative_analyst.py
   │   │   ├── portfolio_manager.py
   │   │   ├── research_analyst.py
   │   │   ├── risk_analyst.py
   │   │   └── quantitative_engineer.py
   │   │
   │   ├── data_adapters/       # 数据适配器
   │   │   ├── base_adapter.py  # 适配器基类
   │   │   ├── hkex_adapter.py  # 港交所
   │   │   ├── alpha_vantage_adapter.py
   │   │   ├── yahoo_finance_adapter.py
   │   │   └── ...
   │   │
   │   ├── api/                 # API层
   │   │   ├── routes/          # 路由
   │   │   │   ├── health.py
   │   │   │   ├── backtest.py
   │   │   │   └── ...
   │   │   ├── middleware/      # 中间件
   │   │   └── dependencies/    # 依赖注入
   │   │
   │   ├── dashboard/           # Web界面
   │   │   ├── api_*.py         # API接口
   │   │   ├── agent_control.py # 智能体控制
   │   │   └── ...
   │   │
   │   ├── backtest/            # 回测引擎
   │   ├── strategies/          # 策略实现
   │   ├── risk/                # 风险管理
   │   ├── monitoring/          # 系统监控
   │   ├── utils/               # 工具函数
   │   └── config.py            # 配置管理
   │
   ├── tests/                   # 测试代码
   │   ├── unit/                # 单元测试
   │   ├── integration/         # 集成测试
   │   └── performance/         # 性能测试
   │
   ├── docs/                    # 文档
   │   ├── user-guide/          # 用户指南
   │   ├── developer-guide/     # 开发者指南
   │   ├── api/                 # API文档
   │   └── architecture/        # 架构文档
   │
   ├── frontend/                # 前端代码
   │   ├── src/
   │   │   ├── components/      # Vue组件
   │   │   ├── views/           # 页面视图
   │   │   ├── stores/          # 状态管理
   │   │   └── ...
   │   └── package.json
   │
   ├── examples/                # 示例代码
   ├── scripts/                 # 脚本工具
   ├── config/                  # 配置文件
   ├── .env                     # 环境变量
   ├── requirements.txt         # Python依赖
   ├── docs_requirements.txt    # 文档依赖
   ├── Cargo.toml              # Rust配置
   ├── pytest.ini              # 测试配置
   ├── .pre-commit-config.yaml # 代码检查
   └── README.md               # 项目说明

关键概念
--------

1. **数据适配器模式**
   ~~~~~~~~~~~~~~~

   所有数据源通过统一的适配器接口访问：

   .. code-block:: python

      from src.data_adapters import BaseAdapter

      class HKEXAdapter(BaseAdapter):
          async def fetch_data(self, symbol: str, start_date: str) -> pd.DataFrame:
              # 实现港交所数据获取
              pass

   优点:
   * 统一的数据访问接口
   * 易于扩展新的数据源
   * 解耦数据源和业务逻辑

2. **智能体协作模式**
   ~~~~~~~~~~~~~~~~

   7个专业AI Agent通过消息队列协作：

   .. code-block:: python

      from src.agents import BaseAgent, Message

      class QuantitativeAnalyst(BaseAgent):
          async def analyze(self, market_data: dict) -> dict:
              # 分析市场数据
              result = await self.run_analysis(market_data)

              # 发送结果给Portfolio Manager
              await self.send_message(
                  to_agent="portfolio_manager",
                  message_type="ANALYSIS_RESULT",
                  content=result
              )
              return result

   优点:
   * 专业化分工
   * 并行处理
   * 可扩展性

3. **策略回测框架**
   ~~~~~~~~~~~~~~

   统一的回测接口支持多种策略：

   .. code-block:: python

      from src.backtest import BaseStrategy, BacktestEngine

      class KDJStrategy(BaseStrategy):
          def generate_signals(self, data: pd.DataFrame) -> pd.Series:
              # 计算KDJ信号
              k = self.calculate_k(data)
              d = self.calculate_d(k)
              signals = pd.Series(0, index=data.index)
              signals[(k > d) & (k.shift(1) <= d.shift(1))] = 1  # 买入
              signals[(k < d) & (k.shift(1) >= d.shift(1))] = -1  # 卖出
              return signals

      # 运行回测
      engine = BacktestEngine()
      result = engine.run(KDJStrategy(), data, initial_capital=100000)

4. **配置管理**
   ~~~~~~~~~~

   使用Pydantic Settings管理配置：

   .. code-block:: python

      from pydantic_settings import BaseSettings

      class Settings(BaseSettings):
          API_HOST: str = "0.0.0.0"
          API_PORT: int = 8001
          DATABASE_URL: str = "sqlite:///./quant_system.db"
          LOG_LEVEL: str = "INFO"

          class Config:
              env_file = ".env"

      settings = Settings()

开发流程
--------

1. **需求分析**
   ~~~~~~~~~~

   * 创建GitHub Issue描述需求
   * 讨论技术方案
   * 获得评审通过

2. **开发实现**
   ~~~~~~~~~~

   * 创建功能分支
   * 编写代码和测试
   * 确保代码质量

3. **测试验证**
   ~~~~~~~~~~

   * 运行单元测试
   * 运行集成测试
   * 手动测试验证

4. **提交代码**
   ~~~~~~~~~~

   * 提交Pull Request
   * 代码评审
   * 合并到主分支

5. **部署上线**
   ~~~~~~~~~~

   * 构建和部署
   * 监控系统运行
   * 收集反馈

代码质量标准
------------

1. **代码规范**
   ~~~~~~~~~~

   严格遵循PEP 8，使用black格式化：

   .. code-block:: bash

      # 格式化代码
      black src/ tests/

      # 检查代码风格
      flake8 src/ tests/

      # 类型检查
      mypy src/

2. **测试要求**
   ~~~~~~~~~~

   * 测试覆盖率 ≥ 80%
   * 核心模块覆盖率 ≥ 90%
   * 所有公共API必须有测试
   * 关键逻辑必须单元测试

3. **文档要求**
   ~~~~~~~~~~

   * 所有公共API必须有docstring
   * 复杂函数需要详细注释
   * 新功能需要更新文档
   * 保持API文档同步

4. **安全要求**
   ~~~~~~~~~~

   * 不提交密钥到Git
   * 验证用户输入
   * 避免SQL注入
   * 使用HTTPS

快速开始
--------

1. **克隆代码**

   .. code-block:: bash

      git clone https://github.com/org/quant-system.git
      cd quant-system

2. **安装依赖**

   .. code-block:: bash

      python -m venv .venv
      source .venv/bin/activate  # Linux/Mac
      # 或 .venv\Scripts\activate  # Windows
      pip install -r requirements.txt
      pip install -r docs_requirements.txt
      pip install -r test_requirements.txt

3. **设置环境**

   .. code-block:: bash

      cp .env.example .env
      # 编辑 .env 配置API密钥

4. **运行测试**

   .. code-block:: bash

      pytest tests/ -v --cov=src --cov-report=html

5. **启动开发服务器**

   .. code-block:: bash

      python complete_project_system.py

6. **访问系统**

   * Web界面: http://localhost:8001
   * API文档: http://localhost:8001/docs

资源链接
--------

* **GitHub仓库:** https://github.com/org/quant-system
* **API文档:** http://localhost:8001/docs
* **问题追踪:** https://github.com/org/quant-system/issues
* **开发讨论:** https://github.com/org/quant-system/discussions
* **技术博客:** https://blog.quant-system.com

联系方式
--------

* **开发团队邮箱:** dev@quant-system.com
* **技术负责人:** lead-dev@quant-system.com
* **Slack频道:** #quant-system-dev
* **微信群:** 扫描二维码加入

常用命令速查
------------

.. code-block:: bash

   # 运行测试
   pytest tests/ -v

   # 运行特定测试
   pytest tests/test_backtest.py -v

   # 生成覆盖率报告
   pytest --cov=src --cov-report=html

   # 代码格式化
   black src/ tests/

   # 代码检查
   flake8 src/ tests/

   # 类型检查
   mypy src/

   # 启动系统
   python complete_project_system.py

   # 生成文档
   sphinx-build docs/ docs/_build/

   # 清理缓存
   find . -type d -name __pycache__ -exec rm -rf {} +
   find . -type f -name "*.pyc" -delete

   # 创建新Agent
   python scripts/create_agent.py --name MyAgent

   # 创建新策略
   python scripts/create_strategy.py --name MyStrategy
