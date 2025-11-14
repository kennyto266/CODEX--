系统架构概览
============

概述
----

港股量化交易系统采用现代微服务架构和事件驱动设计模式，集成了多智能体协作、统一数据适配、高性能回测引擎和实时数据处理等核心功能。

系统目标
--------

1. **高可用性** - 7x24小时稳定运行
2. **高性能** - 支持千亿级数据处理
3. **可扩展** - 模块化设计，易于扩展
4. **可维护** - 清晰的代码结构和文档
5. **安全性** - 完整的权限控制和数据保护

总体架构
--------

系统采用分层架构设计：

.. mermaid

   graph TB
      subgraph "表示层"
         A[Web界面] --> B[REST API]
         A --> C[WebSocket]
         A --> D[静态资源]
      end

      subgraph "应用层"
         B --> E[FastAPI网关]
         C --> E
         E --> F[业务逻辑层]
      end

      subgraph "业务层"
         F --> G[智能体系统]
         F --> H[回测引擎]
         F --> I[策略管理]
         F --> J[组合管理]
         F --> K[风险管理]
      end

      subgraph "数据层"
         L[(数据适配器)]
         M[(缓存层)]
         N[(数据库)]
         O[(文件系统)]
      end

      subgraph "基础设施层"
         P[消息队列]
         Q[监控告警]
         R[日志系统]
         S[配置管理]
      end

      F -.-> L
      F -.-> M
      F -.-> N
      F -.-> O
      G -.-> P
      F -.-> Q
      F -.-> R
      F -.-> S

架构分层详解
------------

1. **表示层 (Presentation Layer)**
   ~~~~~~~~~~~~~~~~~~~~~~~~~

   **职责:**
   * 提供用户界面
   * 处理用户请求
   * 数据展示和交互

   **组件:**
   * **Web界面** - Vue 3 + TypeScript开发的SPA应用
   * **REST API** - FastAPI实现的RESTful接口
   * **WebSocket** - 实时数据推送
   * **静态资源** - 图表、样式、脚本

   **技术栈:**
   * 前端: Vue 3, TypeScript, Vite, TailwindCSS
   * 图表: ECharts, D3.js
   * 状态管理: Pinia
   * HTTP客户端: Axios

2. **应用层 (Application Layer)**
   ~~~~~~~~~~~~~~~~~~~~~~

   **职责:**
   * 请求路由和分发
   * 业务逻辑编排
   * 数据验证和转换
   * 权限控制

   **组件:**
   * **FastAPI网关** - 统一API入口
   * **路由管理** - 请求分发
   * **中间件** - 认证、日志、限流
   * **依赖注入** - 管理依赖

   **设计模式:**
   * Gateway模式
   * Middleware模式
   * Dependency Injection

3. **业务层 (Business Layer)**
   ~~~~~~~~~~~~~~~~~~~~

   **职责:**
   * 实现业务规则
   * 执行核心算法
   * 协调多智能体
   * 策略回测执行

   **组件:**

   **智能体系统 (7个AI Agent)**

   .. list-table::
      :header-rows: 1

      * - Agent名称
        - 职责
        - 主要功能
      * - Coordinator
        - 工作流协调
        - 任务分配、状态管理、异常处理
      * - Data Scientist
        - 数据分析
        - 数据收集、清洗、异常检测
      * - Quantitative Analyst
        - 量化分析
        - 策略开发、回测、参数优化
      * - Portfolio Manager
        - 投资组合
        - 资产配置、再平衡、绩效归因
      * - Research Analyst
        - 策略研究
        - 市场研究、文献调研
      * - Risk Analyst
        - 风险管理
        - 风险评估、对冲策略
      * - Quantitative Engineer
        - 系统优化
        - 性能调优、监控、故障诊断

   **回测引擎**
   * 多策略并行执行
   * 参数自动优化
   * 性能指标计算
   * 结果可视化

   **策略管理**
   * 11种技术指标策略
   * 策略生命周期管理
   * 策略组合优化
   * 实盘信号生成

   **组合管理**
   * 资产配置
   * 风险预算
   * 业绩归因
   * 实时监控

   **风险管理**
   * VaR计算
   * 压力测试
   * 止损策略
   * 风险告警

4. **数据层 (Data Layer)**
   ~~~~~~~~~~~~~~~~

   **职责:**
   * 数据存储
   * 数据访问
   * 数据缓存
   * 数据同步

   **组件:**

   **数据适配器**
   * 统一接口设计
   * 支持多种数据源
   * 错误处理和重试
   * 数据验证

   **支持的适配器:**

   .. list-table::
      :header-rows: 1

      * - 适配器
        - 数据源
        - 描述
      * - HKEXAdapter
        - 港交所
        - 实时和历史行情
      * - YahooFinanceAdapter
        - Yahoo Finance
        - 全球市场数据
      * - AlphaVantageAdapter
        - Alpha Vantage
        - 技术指标和基本面数据
      * - AlternativeDataAdapter
        - 政府数据
        - HIBOR、GDP、房地产等宏观数据
      * - CCXTAdapter
        - 加密货币
        - 数字货币交易数据

   **缓存层**
   * Redis内存缓存
   * LRU策略
   * 分布式缓存
   * 缓存预热

   **数据库**
   * SQLite - 开发环境
   * PostgreSQL - 生产环境
   * 数据库连接池
   * 读写分离

5. **基础设施层 (Infrastructure Layer)**
   ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

   **职责:**
   * 系统支撑
   * 公共服务
   * 运维监控
   * 配置管理

   **组件:**

   **消息队列**
   * Asyncio Queue
   * Agent间通信
   * 事件驱动
   * 消息持久化

   **监控告警**
   * 系统健康检查
   * 性能指标采集
   * 异常告警
   * 监控面板

   **日志系统**
   * 结构化日志
   * 日志级别控制
   * 日志轮转
   * ELK集成

   **配置管理**
   * 环境变量
   * 配置文件
   * 配置热更新
   - 多环境支持

核心设计模式
------------

1. **适配器模式 (Adapter Pattern)**
   ~~~~~~~~~~~~~~~~~~~~~~~~~~~

   统一数据访问接口，隔离数据源差异

   .. code-block:: python

      from abc import ABC, abstractmethod

      class BaseAdapter(ABC):
          """数据适配器基类"""

          @abstractmethod
          async def fetch_data(
              self, symbol: str, start_date: str, end_date: str
          ) -> pd.DataFrame:
              """获取市场数据"""
              pass

      class HKEXAdapter(BaseAdapter):
          """港交所适配器"""
          async def fetch_data(
              self, symbol: str, start_date: str, end_date: str
          ) -> pd.DataFrame:
              # 实现港交所数据获取
              pass

2. **策略模式 (Strategy Pattern)**
   ~~~~~~~~~~~~~~~~~~~~~~~~~~

   支持多种交易策略，便于扩展

   .. code-block:: python

      class BaseStrategy(ABC):
          """策略基类"""

          @abstractmethod
          def generate_signals(self, data: pd.DataFrame) -> pd.Series:
              """生成交易信号"""
              pass

      class KDJStrategy(BaseStrategy):
          """KDJ策略"""
          def generate_signals(self, data: pd.DataFrame) -> pd.Series:
              # 实现KDJ策略逻辑
              pass

3. **观察者模式 (Observer Pattern)**
   ~~~~~~~~~~~~~~~~~~~~~~~~~~~

   实现事件驱动架构

   .. code-block:: python

      class EventManager:
          def __init__(self):
              self._listeners = {}

          def subscribe(self, event_type: str, callback: Callable):
              if event_type not in self._listeners:
                  self._listeners[event_type] = []
              self._listeners[event_type].append(callback)

          def emit(self, event_type: str, data: dict):
              if event_type in self._listeners:
                  for callback in self._listeners[event_type]:
                      callback(data)

4. **工厂模式 (Factory Pattern)**
   ~~~~~~~~~~~~~~~~~~~~~~~~~

   动态创建对象

   .. code-block:: python

      class StrategyFactory:
          _strategies = {
              "kdj": KDJStrategy,
              "rsi": RSIStrategy,
              "macd": MACDStrategy,
          }

          @classmethod
          def create_strategy(cls, strategy_type: str, **kwargs) -> BaseStrategy:
              strategy_class = cls._strategies.get(strategy_type)
              if not strategy_class:
                  raise ValueError(f"Unknown strategy: {strategy_type}")
              return strategy_class(**kwargs)

5. **单例模式 (Singleton Pattern)**
   ~~~~~~~~~~~~~~~~~~~~~~~~~~~

   确保唯一实例

   .. code-block:: python

      class ConfigManager:
          _instance = None

          def __new__(cls):
              if cls._instance is None:
                  cls._instance = super().__new__(cls)
              return cls._instance

数据流设计
----------

1. **数据获取流程**
   ~~~~~~~~~~~~~~

   .. mermaid

      sequenceDiagram
         participant C as Client
         participant A as API
         participant D as DataAdapter
         participant R as Redis
         participant DB as Database

         C->>A: 请求数据(symbol, date_range)
         A->>R: 检查缓存
         alt 缓存命中
             R-->>A: 返回缓存数据
         else 缓存未命中
             A->>D: fetch_data()
             D->>DB: 查询数据库
             D->>R: 缓存数据
             D-->>A: 返回数据
         end
         A-->>C: 返回响应

2. **回测执行流程**
   ~~~~~~~~~~~~~~

   .. mermaid

      sequenceDiagram
         participant C as Client
         participant A as API
         participant E as BacktestEngine
         participant S as Strategy
         participant M as MarketData

         C->>A: 启动回测请求
         A->>E: run_backtest()
         E->>M: 获取历史数据
         E->>S: 生成交易信号
         S-->>E: 返回信号
         E->>E: 计算交易
         E->>E: 计算收益
         E-->>A: 返回结果
         A-->>C: 返回回测报告

3. **智能体协作流程**
   ~~~~~~~~~~~~~~

   .. mermaid

      sequenceDiagram
         participant C as Coordinator
         participant D as DataScientist
         participant Q as QuantAnalyst
         participant P as PortfolioManager

         C->>D: 分析市场数据
         D-->>C: 返回分析结果
         C->>Q: 制定交易策略
         Q-->>C: 返回策略信号
         C->>P: 更新投资组合
         P-->>C: 确认执行

技术决策记录 (ADR)
------------------

**ADR-001: 选择FastAPI作为API框架**

.. code-block:: markdown

   ## 背景
   需要选择Python web框架构建API服务

   ## 决策
   选择FastAPI而不是Django或Flask

   ## 理由
   * 优秀的性能 - 接近Node.js和Go
   * 类型安全 - 基于Pydantic
   * 自动文档 - 内置OpenAPI/Swagger
   * 异步支持 - 原生async/await
   * 现代化 - 使用最新Python特性

**ADR-002: 采用多智能体架构**

.. code-block:: markdown

   ## 背景
   系统需要处理复杂的量化分析任务

   ## 决策
   采用多智能体协作架构

   ## 理由
   * 专业化分工 - 每个Agent专注特定任务
   * 并行处理 - 提高系统吞吐量
   * 易于扩展 - 可添加新的Agent
   * 容错性强 - 单个Agent故障不影响全局
   * 符合实际 - 模拟真实投资团队结构

**ADR-003: 统一数据适配器模式**

.. code-block:: markdown

   ## 背景
   需要接入多个不同的数据源

   ## 决策
   实施统一的数据适配器模式

   ## 理由
   * 统一接口 - 简化业务代码
   * 易于扩展 - 新增数据源只需实现接口
   * 解耦 - 数据源变化不影响业务逻辑
   * 便于测试 - 可以使用Mock适配器
   * 一致性 - 所有数据源格式统一

**ADR-004: 使用Redis作为缓存层**

.. code-block:: markdown

   ## 背景
   需要提高数据访问性能

   ## 决策
   使用Redis作为分布式缓存

   ## 理由
   * 高性能 - 内存存储，毫秒级响应
   * 丰富数据结构 - 支持多种数据类型
   * 持久化 - 支持RDB和AOF
   * 集群 - 支持水平扩展
   * 成熟稳定 - 广泛使用的开源方案

性能设计
--------

1. **水平扩展**
   ~~~~~~~~~~

   * **多进程** - 使用Gunicorn或Uvicorn多worker
   * **异步处理** - asyncio提升并发能力
   * **负载均衡** - Nginx反向代理
   * **微服务** - 拆分独立服务

2. **垂直优化**
   ~~~~~~~~~~

   * **代码优化** - 向量化计算，避免循环
   * **缓存策略** - 多级缓存，LRU算法
   * **数据库优化** - 索引、连接池、读写分离
   * **资源复用** - 对象池、连接池

3. **并行处理**
   ~~~~~~~~~~

   .. code-block:: python

      # 使用concurrent.futures进行并行回测
      from concurrent.futures import ProcessPoolExecutor

      def optimize_strategies_parallel(
          strategies: List[str], data: pd.DataFrame
      ) -> Dict[str, dict]:
          with ProcessPoolExecutor(max_workers=8) as executor:
              futures = {
                  executor.submit(optimize_single_strategy, s, data): s
                  for s in strategies
              }
              results = {}
              for future in as_completed(futures):
                  strategy = futures[future]
                  results[strategy] = future.result()
          return results

4. **数据分片**
   ~~~~~~~~~~

   * **时间分片** - 按时间范围分批处理
   * **股票分片** - 按股票代码分批处理
   * **策略分片** - 按策略类型并行执行

安全性设计
----------

1. **认证授权**
   ~~~~~~~~~~

   * JWT令牌认证
   * 基于角色的访问控制 (RBAC)
   * API密钥管理
   * 会话管理

2. **数据保护**
   ~~~~~~~~~~

   * 敏感数据加密
   * HTTPS传输
   * 密码哈希
   * 数据脱敏

3. **输入验证**
   ~~~~~~~~~~

   .. code-block:: python

      from pydantic import BaseModel, validator

      class BacktestRequest(BaseModel):
          symbol: str
          start_date: str
          end_date: str
          strategy: str

          @validator("symbol")
          def validate_symbol(cls, v):
              if not re.match(r"^\d{4}\.HK$", v):
                  raise ValueError("股票代码格式错误")
              return v

          @validator("start_date", "end_date")
          def validate_date(cls, v):
              try:
                  datetime.strptime(v, "%Y-%m-%d")
              except ValueError:
                  raise ValueError("日期格式应为YYYY-MM-DD")
              return v

4. **安全中间件**
   ~~~~~~~~~~

   * CORS控制
   * XSS防护
   * CSRF保护
   * 限流防刷
   * SQL注入防护

可观测性设计
------------

1. **日志记录**
   ~~~~~~~~~~

   .. code-block:: python

      import structlog

      logger = structlog.get_logger("backtest")

      logger.info(
          "开始回测",
          strategy="KDJ",
          symbol="0700.HK",
          start_date="2020-01-01",
          user_id=12345,
      )

   * 结构化日志
   * 关联ID追踪
   * 性能日志
   * 错误日志

2. **指标监控**
   ~~~~~~~~~~

   * **系统指标** - CPU、内存、磁盘、网络
   * **应用指标** - 请求量、延迟、错误率
   * **业务指标** - 回测耗时、策略收益
   * **自定义指标** - 智能体状态、队列长度

3. **链路追踪**
   ~~~~~~~~~~

   * 请求链路追踪
   * 分布式追踪
   * 性能分析
   * 慢查询日志

4. **告警机制**
   ~~~~~~~~~~

   * 阈值告警
   * 异常告警
   * 邮件/短信通知
   * Webhook集成

部署架构
--------

1. **开发环境**
   ~~~~~~~~~~

   .. code-block::

      [Developer PC]
        ↓
      [Local Server:8001]
        - SQLite数据库
        - 简单前端

2. **测试环境**
   ~~~~~~~~~~

   .. code-block::

      [Test Server]
        ├─ API Service
        ├─ PostgreSQL
        ├─ Redis
        └─ Nginx

3. **生产环境**
   ~~~~~~~~~~

   .. code-block::

      [Load Balancer: Nginx]
              ↓
      ┌─────┴─────┐
      ↓           ↓
   [Server 1]  [Server 2]
      ↓           ↓
      └─────┬─────┘
            ↓
      [Database Cluster]
      - PostgreSQL主从
      - Redis集群
      - 共享存储

4. **容器化部署**
   ~~~~~~~~~~~

   Dockerfile:

   .. code-block:: dockerfile

      FROM python:3.11-slim

      WORKDIR /app

      COPY requirements.txt .
      RUN pip install -r requirements.txt

      COPY src/ src/
      COPY static/ static/

      EXPOSE 8001

      CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8001"]

   docker-compose.yml:

   .. code-block:: yaml

      version: '3.8'
      services:
        api:
          build: .
          ports:
            - "8001:8001"
          environment:
            - DATABASE_URL=postgresql://user:pass@db:5432/quant
            - REDIS_URL=redis://cache:6379/0
        db:
          image: postgres:15
        cache:
          image: redis:7

技术栈总结
----------

.. list-table::
   :header-rows: 1

   * - 层级
     - 技术
     - 版本
   * - 前端
     - Vue 3, TypeScript
     - 3.5, 5.0
   * - 后端
     - Python, FastAPI
     - 3.11, 0.115
   * - 数据处理
     - Pandas, NumPy, TA-Lib
     - 2.2, 2.1, 0.4
   * - 数据库
     - PostgreSQL, SQLite
     - 15, 3.x
   * - 缓存
     - Redis
     - 7.x
   * - 消息队列
     - Asyncio Queue
     - 内置
   * - 监控
     - Prometheus, Grafana
     - 最新
   * - 部署
     - Docker, Nginx
     - 24.x, 1.25
   * - 测试
     - pytest, Hypothesis
     - 8.0, 6.0
   * - 代码质量
     - black, mypy, flake8
     - 最新

未来规划
--------

1. **短期目标 (3-6个月)**
   ~~~~~~~~~~~~~~~~

   * 完善策略回测功能
   * 增加更多技术指标
   * 优化系统性能
   * 完善监控告警

2. **中期目标 (6-12个月)**
   ~~~~~~~~~~~~~~~~

   * 支持更多数据源
   * 实现自动交易
   * 机器学习模块
   * 移动端应用

3. **长期目标 (1-2年)**
   ~~~~~~~~~~~~~~~

   * 分布式计算
   - 云计算平台
   * 大数据分析
   * 社区生态建设

参考资料
--------

* `FastAPI官方文档 <https://fastapi.tiangolo.com/>`_
* `微服务架构设计模式 <https://microservices.io/>`_
* `领域驱动设计 <https://domaindrivendesign.org/>`_
* `事件驱动架构 <https://www.eventbrite.com/platform/>`_
* `12-Factor App <https://12factor.net/>`_
