多智能体系统架构
===============

概述
----

港股量化交易系统采用多智能体架构，通过7个专业AI Agent的协作，实现复杂的量化分析、投资决策和风险管理。每个Agent专注特定领域，通过消息队列进行通信，实现高效、可靠的系统运行。

Agent设计原则
-------------

1. **单一职责** - 每个Agent负责特定领域的任务
2. **松耦合** - Agent间通过消息通信，依赖最小化
3. **自主性** - Agent可以独立决策和执行
4. **协作性** - Agent间可以共享信息和资源
5. **可扩展性** - 易于添加新的Agent

Agent架构图
-----------

.. mermaid

   graph TB
      subgraph "消息层"
         MQ[消息队列]
      end

      subgraph "Agent层"
         C[Coordinator<br/>协调者]
         DS[Data Scientist<br/>数据科学家]
         QA[Quantitative Analyst<br/>量化分析师]
         PM[Portfolio Manager<br/>投资组合经理]
         RA[Research Analyst<br/>研究分析师]
         RS[Risk Analyst<br/>风险分析师]
         QE[Quantitative Engineer<br/>量化工程师]
      end

      C -.->|协调| DS
      C -.->|协调| QA
      C -.->|协调| PM
      C -.->|协调| RA
      C -.->|协调| RS
      C -.->|协调| QE

      DS -.->|数据| QA
      DS -.->|数据| PM
      DS -.->|数据| RA
      QA -.->|策略| PM
      QA -.->|策略| RS
      PM -.->|组合| RS
      RA -.->|研究| QA

      subgraph "外部系统"
         DB[(数据库)]
         API[外部API]
         MONITOR[监控系统]
      end

      DS -.-> DB
      DS -.-> API
      QA -.-> DB
      PM -.-> DB
      RS -.-> MONITOR
      QE -.-> MONITOR

Agent详解
--------

1. Coordinator (协调者)
   ~~~~~~~~~~~~~

   **职责** - 全局工作流协调和任务管理

   **核心功能:**

   * 任务分配和调度
   * Agent生命周期管理
   * 异常处理和恢复
   * 资源协调和分配
   * 工作流编排

   **实现示例:**

   .. code-block:: python

      class Coordinator(BaseAgent):
          """协调者Agent - 负责全局任务协调"""

          def __init__(self):
              super().__init__(agent_id="coordinator")
              self.task_queue = asyncio.Queue()
              self.running_tasks = {}
              self.agent_registry = {}

          async def distribute_task(self, task: Task) -> None:
              """分发任务给合适的Agent"""
              # 根据任务类型选择Agent
              target_agent = self.select_agent(task.type)

              # 发送任务
              await self.send_message(
                  to_agent=target_agent,
                  message_type="TASK_ASSIGNMENT",
                  content=task.to_dict(),
              )

          async def select_agent(self, task_type: str) -> str:
              """选择合适的Agent"""
              agent_mapping = {
                  "DATA_ANALYSIS": "data_scientist",
                  "STRATEGY_DEVELOPMENT": "quantitative_analyst",
                  "PORTFOLIO_OPTIMIZATION": "portfolio_manager",
                  "RISK_ASSESSMENT": "risk_analyst",
                  "RESEARCH": "research_analyst",
                  "SYSTEM_OPTIMIZATION": "quantitative_engineer",
              }
              return agent_mapping.get(task_type, "quantitative_analyst")

   **消息处理:**

   .. code-block:: python

      async def handle_message(self, message: Message) -> None:
          """处理接收到的消息"""
          if message.type == "TASK_COMPLETION":
              await self._handle_task_completion(message)
          elif message.type == "AGENT_ERROR":
              await self._handle_agent_error(message)
          elif message.type == "HEARTBEAT":
              await self._update_agent_status(message)

2. Data Scientist (数据科学家)
   ~~~~~~~~~~~~~~~~~~~~~

   **职责** - 数据获取、清洗、分析和异常检测

   **核心功能:**

   * 收集多源市场数据
   * 数据质量检查和清洗
   * 数据特征工程
   * 异常数据检测
   * 生成数据质量报告

   **实现示例:**

   .. code-block:: python

      class DataScientist(BaseAgent):
          """数据科学家Agent - 负责数据处理"""

          def __init__(self):
              super().__init__(agent_id="data_scientist")
              self.data_adapters = {
                  "hkex": HKEXAdapter(),
                  "yahoo": YahooFinanceAdapter(),
                  "alpha_vantage": AlphaVantageAdapter(),
              }
              self.quality_checker = DataQualityChecker()

          async def fetch_and_clean_data(
              self, symbol: str, start_date: str, end_date: str
          ) -> pd.DataFrame:
              """获取并清洗数据"""
              try:
                  # 1. 从多个数据源获取数据
                  raw_data = await self._fetch_from_sources(
                      symbol, start_date, end_date
                  )

                  # 2. 数据质量检查
                  quality_report = self.quality_checker.check(raw_data)

                  if quality_report.has_issues:
                      # 3. 数据清洗
                      cleaned_data = await self._clean_data(raw_data)
                  else:
                      cleaned_data = raw_data

                  # 4. 存储数据
                  await self._store_data(symbol, cleaned_data)

                  # 5. 通知其他Agent
                  await self.broadcast_message(
                      message_type="DATA_READY",
                      content={
                          "symbol": symbol,
                          "data_points": len(cleaned_data),
                          "quality": quality_report,
                      },
                  )

                  return cleaned_data

              except Exception as e:
                  await self.handle_error("数据获取失败", e)
                  raise

   **数据质量检查:**

   .. code-block:: python

      class DataQualityChecker:
          """数据质量检查器"""

          def check(self, data: pd.DataFrame) -> QualityReport:
              """执行数据质量检查"""
              report = QualityReport()

              # 检查缺失值
              missing_pct = data.isnull().sum() / len(data) * 100
              if missing_pct.max() > 5:  # 超过5%缺失
                  report.add_issue("HIGH_MISSING_VALUES", missing_pct.to_dict())

              # 检查异常值
              for col in ["open", "high", "low", "close"]:
                  if col in data.columns:
                      z_scores = np.abs((data[col] - data[col].mean()) / data[col].std())
                      outliers = (z_scores > 3).sum()
                      if outliers > len(data) * 0.01:  # 超过1%异常值
                          report.add_issue("HIGH_OUTLIERS", {"column": col, "count": outliers})

              # 检查价格逻辑
              if all(col in data.columns for col in ["open", "high", "low", "close"]):
                  invalid = (data["high"] < data["low"]) | \
                           (data["close"] < data["low"]) | \
                           (data["close"] > data["high"])
                  if invalid.any():
                      report.add_issue("PRICE_LOGIC_ERROR", invalid.sum())

              return report

3. Quantitative Analyst (量化分析师)
   ~~~~~~~~~~~~~~~~~~~~~~~~~~

   **职责** - 策略开发、回测验证和参数优化

   **核心功能:**

   * 量化模型开发
   * 策略回测验证
   * 参数优化
   * 策略性能评估
   * 因子研究

   **实现示例:**

   .. code-block:: python

      class QuantitativeAnalyst(BaseAgent):
          """量化分析师Agent - 负责策略开发"""

          def __init__(self):
              super().__init__(agent_id="quantitative_analyst")
              self.backtest_engine = BacktestEngine()
              self.optimization_engine = OptimizationEngine()
              self.strategy_registry = {
                  "kdj": KDJStrategy,
                  "rsi": RSIStrategy,
                  "macd": MACDStrategy,
              }

          async def develop_strategy(
              self, strategy_type: str, market_data: pd.DataFrame
          ) -> StrategyResult:
              """开发新策略"""
              # 1. 策略研究
              strategy_class = self.strategy_registry[strategy_type]
              strategy = strategy_class()

              # 2. 生成信号
              signals = strategy.generate_signals(market_data)

              # 3. 回测验证
              backtest_result = await self.backtest_engine.run(
                  strategy=strategy,
                  data=market_data,
                  initial_capital=100000,
              )

              # 4. 评估策略
              evaluation = self._evaluate_strategy(backtest_result)

              # 5. 保存策略
              await self._save_strategy(strategy, backtest_result, evaluation)

              return StrategyResult(
                  strategy=strategy_type,
                  performance=backtest_result,
                  evaluation=evaluation,
              )

          async def optimize_parameters(
              self, strategy_type: str, data: pd.DataFrame
          ) -> OptimizationResult:
              """优化策略参数"""
              # 使用遗传算法或贝叶斯优化
              return await self.optimization_engine.optimize(
                  strategy=strategy_type,
                  data=data,
                  objective="sharpe_ratio",
                  max_iterations=100,
              )

4. Portfolio Manager (投资组合经理)
   ~~~~~~~~~~~~~~~~~~~~~~~~

   **职责** - 投资组合构建、资产配置和再平衡

   **核心功能:**

   * 资产配置优化
   * 组合风险预算
   * 业绩归因分析
   * 组合再平衡
   * 交易执行

   **实现示例:**

   .. code-block:: python

      class PortfolioManager(BaseAgent):
          """投资组合经理Agent - 负责组合管理"""

          def __init__(self):
              super().__init__(agent_id="portfolio_manager")
              self.risk_model = RiskModel()
              self.optimizer = PortfolioOptimizer()

          async def optimize_portfolio(
              self, market_data: dict, constraints: dict
          ) -> PortfolioResult:
              """优化投资组合"""
              # 1. 获取预期收益
              expected_returns = await self._calculate_expected_returns(market_data)

              # 2. 计算协方差矩阵
              cov_matrix = await self._calculate_covariance(market_data)

              # 3. 优化配置
              weights = await self.optimizer.optimize(
                  expected_returns=expected_returns,
                  cov_matrix=cov_matrix,
                  constraints=constraints,
              )

              # 4. 生成交易计划
              trade_plan = self._generate_trade_plan(weights)

              # 5. 执行交易（如果允许）
              if constraints.get("auto_trade", False):
                  await self._execute_trades(trade_plan)

              return PortfolioResult(
                  weights=weights,
                  trade_plan=trade_plan,
                  expected_return=self._calc_portfolio_return(weights, expected_returns),
                  expected_risk=self._calc_portfolio_risk(weights, cov_matrix),
              )

5. Research Analyst (研究分析师)
   ~~~~~~~~~~~~~~~~~~~

   **职责** - 策略研究、市场分析和文献调研

   **核心功能:**

   * 市场研究
   * 因子研究
   * 文献调研
   * 策略改进
   * 知识库管理

   **实现示例:**

   .. code-block:: python

      class ResearchAnalyst(BaseAgent):
          """研究分析师Agent - 负责研究工作"""

          def __init__(self):
              super().__init__(agent_id="research_analyst")
              self.knowledge_base = KnowledgeBase()
              self.paper_analyzer = PaperAnalyzer()

          async def research_strategy(
              self, strategy_type: str
          ) -> ResearchReport:
              """研究策略"""
              # 1. 文献调研
              papers = await self.paper_analyzer.search_papers(strategy_type)

              # 2. 分析关键发现
              key_findings = await self.paper_analyzer.extract_findings(papers)

              # 3. 对比现有实现
              comparison = await self._compare_with_implementation(
                  strategy_type, key_findings
              )

              # 4. 提出改进建议
              improvements = self._generate_improvements(
                  strategy_type, key_findings, comparison
              )

              # 5. 生成报告
              report = ResearchReport(
                  strategy=strategy_type,
                  papers_reviewed=len(papers),
                  key_findings=key_findings,
                  comparison=comparison,
                  improvements=improvements,
              )

              # 6. 更新知识库
              await self.knowledge_base.update(strategy_type, report)

              return report

6. Risk Analyst (风险分析师)
   ~~~~~~~~~~~~~~~~

   **职责** - 风险评估、对冲策略和风险控制

   **核心功能:**

   * VaR和CVaR计算
   * 压力测试
   * 风险归因
   * 对冲策略
   * 实时风险监控

   **实现示例:**

   .. code-block:: python

      class RiskAnalyst(BaseAgent):
          """风险分析师Agent - 负责风险管理"""

          def __init__(self):
              super().__init__(agent_id="risk_analyst")
              self.var_model = VaRModel()
              self.stress_tester = StressTester()
              self.hedge_optimizer = HedgeOptimizer()

          async def assess_portfolio_risk(
              self, portfolio: Portfolio
          ) -> RiskAssessment:
              """评估投资组合风险"""
              # 1. VaR计算
              var_95 = await self.var_model.calculate_var(
                  portfolio, confidence_level=0.95
              )
              var_99 = await self.var_model.calculate_var(
                  portfolio, confidence_level=0.99
              )

              # 2. CVaR计算
              cvar_95 = await self.var_model.calculate_cvar(
                  portfolio, confidence_level=0.95
              )

              # 3. 压力测试
              stress_results = await self.stress_tester.run_scenarios(
                  portfolio, scenarios=["CRISIS_2008", "COVID_2020", "RATE_SHOCK"]
              )

              # 4. 风险归因
              risk_attribution = await self._attribute_risk(portfolio)

              # 5. 生成告警
              alerts = self._generate_risk_alerts(
                  var_95, var_99, stress_results
              )

              return RiskAssessment(
                  var_95=var_95,
                  var_99=var_99,
                  cvar_95=cvar_95,
                  stress_tests=stress_results,
                  risk_attribution=risk_attribution,
                  alerts=alerts,
              )

7. Quantitative Engineer (量化工程师)
   ~~~~~~~~~~~~~~~~~~~~~~~~~

   **职责** - 系统性能优化、监控和故障诊断

   **核心功能:**

   * 性能监控
   * 系统优化
   * 故障诊断
   * 容量规划
   * 技术升级

   **实现示例:**

   .. code-block:: python

      class QuantitativeEngineer(BaseAgent):
          """量化工程师Agent - 负责系统优化"""

          def __init__(self):
              super().__init__(agent_id="quantitative_engineer")
              self.monitor = SystemMonitor()
              self.profiler = PerformanceProfiler()
              self.optimizer = CodeOptimizer()

          async def optimize_system(self) -> OptimizationReport:
              """系统性能优化"""
              # 1. 收集性能数据
              performance_data = await self.monitor.collect_metrics()

              # 2. 识别瓶颈
              bottlenecks = self._identify_bottlenecks(performance_data)

              # 3. 制定优化方案
              optimization_plan = self._create_optimization_plan(bottlenecks)

              # 4. 实施优化
              for optimization in optimization_plan.optimizations:
                  await optimization.apply()

              # 5. 验证优化效果
              new_metrics = await self.monitor.collect_metrics()
              improvement = self._calculate_improvement(
                  performance_data, new_metrics
              )

              return OptimizationReport(
                  bottlenecks=bottlenecks,
                  optimizations=optimization_plan.optimizations,
                  improvement=improvement,
              )

消息通信机制
------------

**消息格式:**

.. code-block:: python

   from dataclasses import dataclass
   from typing import Any, Dict, Optional
   from datetime import datetime

   @dataclass
   class Message:
       """消息基类"""
       from_agent: str
       to_agent: str
       message_type: str
       content: Dict[str, Any]
       timestamp: datetime
       message_id: str
       priority: int = 1  # 1-5，5最高

**消息类型:**

.. code-block:: python

   class MessageType:
       # 任务相关
       TASK_ASSIGNMENT = "TASK_ASSIGNMENT"
       TASK_COMPLETION = "TASK_COMPLETION"
       TASK_FAILED = "TASK_FAILED"

       # 数据相关
       DATA_REQUEST = "DATA_REQUEST"
       DATA_READY = "DATA_READY"
       DATA_ERROR = "DATA_ERROR"

       # 策略相关
       STRATEGY_SIGNAL = "STRATEGY_SIGNAL"
       STRATEGY_UPDATE = "STRATEGY_UPDATE"

       # 风险相关
       RISK_ALERT = "RISK_ALERT"
       RISK_UPDATE = "RISK_UPDATE"

       # 系统相关
       HEARTBEAT = "HEARTBEAT"
       STATUS_UPDATE = "STATUS_UPDATE"
       ERROR = "ERROR"

**发送消息:**

.. code-block:: python

   class BaseAgent:
       async def send_message(
           self,
           to_agent: str,
           message_type: str,
           content: Dict[str, Any],
           priority: int = 1,
       ) -> None:
           """发送消息"""
           message = Message(
               from_agent=self.agent_id,
               to_agent=to_agent,
               message_type=message_type,
               content=content,
               timestamp=datetime.now(),
               message_id=str(uuid.uuid4()),
               priority=priority,
           )

           await self.message_queue.put(message)

**消息处理:**

.. code-block:: python

   class BaseAgent:
       async def message_handler(self):
           """消息处理器"""
           while self.is_running:
               try:
                   # 从消息队列获取消息
                   message = await self.message_queue.get()

                   # 处理消息
                   await self._process_message(message)

                   # 标记任务完成
                   self.message_queue.task_done()

               except Exception as e:
                   await self.handle_error("消息处理失败", e)

       async def _process_message(self, message: Message) -> None:
           """处理消息"""
           handler_name = f"handle_{message.message_type.lower()}"
           handler = getattr(self, handler_name, self.handle_unknown)

           await handler(message)

Agent生命周期
------------

.. mermaid

   stateDiagram-v2
      [*] --> INITIALIZING: 启动
      INITIALIZING --> STARTING: 初始化完成
      STARTING --> RUNNING: 开始运行
      RUNNING --> PAUSING: 暂停
      PAUSING --> RUNNING: 恢复
      RUNNING --> STOPPING: 停止
      STOPPING --> STOPPED: 已停止
      RUNNING --> ERROR: 发生错误
      ERROR --> RECOVERING: 尝试恢复
      RECOVERING --> RUNNING: 恢复成功
      RECOVERING --> STOPPED: 恢复失败
      STOPPED --> [*]: 退出

**状态管理:**

.. code-block:: python

   from enum import Enum

   class AgentState(Enum):
       INITIALIZING = "initializing"
       STARTING = "starting"
       RUNNING = "running"
       PAUSING = "pausing"
       STOPPING = "stopping"
       ERROR = "error"
       RECOVERING = "recovering"
       STOPPED = "stopped"

   class BaseAgent:
       def __init__(self, agent_id: str):
           self.agent_id = agent_id
           self.state = AgentState.INITIALIZING
           self.message_queue = asyncio.Queue()
           self.is_running = True

       async def start(self) -> None:
           """启动Agent"""
           self.state = AgentState.STARTING
           await self.initialize()
           self.state = AgentState.RUNNING

           # 启动消息处理器
           asyncio.create_task(self.message_handler())

           # 启动心跳
           asyncio.create_task(self.heartbeat())

       async def stop(self) -> None:
           """停止Agent"""
           self.state = AgentState.STOPPING
           self.is_running = False
           await self.cleanup()
           self.state = AgentState.STOPPED

       async def heartbeat(self) -> None:
           """心跳机制"""
           while self.is_running:
               await self.send_message(
                   to_agent="coordinator",
                   message_type="HEARTBEAT",
                   content={"state": self.state.value},
               )
               await asyncio.sleep(30)  # 30秒心跳一次

协作工作流示例
--------------

**场景:** 新策略开发

.. mermaid

   sequenceDiagram
      participant U as User
      participant C as Coordinator
      participant DS as Data Scientist
      participant QA as Quantitative Analyst
      participant RA as Research Analyst
      participant PM as Portfolio Manager
      participant RS as Risk Analyst

      U->>C: 请求开发新策略
      C->>DS: 获取历史数据
      DS-->>C: 数据准备完成
      C->>RA: 研究现有策略
      RA-->>C: 研究报告
      C->>QA: 开发策略
      QA-->>C: 策略原型
      C->>QA: 回测验证
      QA-->>C: 回测结果
      C->>RS: 风险评估
      RS-->>C: 风险报告
      C->>PM: 组合影响分析
      PM-->>C: 建议
      C->>U: 返回完整报告

监控和告警
----------

**Agent状态监控:**

.. code-block:: python

   class AgentMonitor:
       """Agent状态监控"""

       def __init__(self):
           self.agent_status = {}
           self.alert_manager = AlertManager()

       async def monitor_agents(self):
           """监控所有Agent"""
           while True:
               for agent_id, status in self.agent_status.items():
                   # 检查心跳
                   if self._check_heartbeat(status):
                       continue

                   # 检查处理能力
                   if self._check_throughput(agent_id):
                       continue

                   # 检查错误率
                   if self._check_error_rate(agent_id):
                       await self.alert_manager.send_alert(
                           level="WARNING",
                           message=f"Agent {agent_id} 错误率过高",
                       )

               await asyncio.sleep(60)  # 60秒检查一次

**性能指标:**

.. code-block:: python

   class AgentMetrics:
       """Agent性能指标"""

       def __init__(self):
           self.metrics = {
               "message_count": 0,
               "processing_time": [],
               "error_count": 0,
               "throughput": 0,
           }

       def record_processing_time(self, duration: float):
           """记录处理时间"""
           self.metrics["processing_time"].append(duration)

       def get_average_processing_time(self) -> float:
           """获取平均处理时间"""
           if not self.metrics["processing_time"]:
               return 0
           return sum(self.metrics["processing_time"]) / len(
               self.metrics["processing_time"]
           )

最佳实践
--------

1. **消息设计**
   ~~~~~~~~~~

   * 消息内容简洁明确
   * 使用标准消息类型
   * 处理消息的幂等性
   * 包含错误处理

2. **错误处理**
   ~~~~~~~~~~

   * 实现重试机制
   * 记录详细错误日志
   * 设置超时时间
   * 优雅降级

3. **性能优化**
   ~~~~~~~~~~

   * 异步消息处理
   * 批量处理消息
   * 避免阻塞操作
   * 监控队列长度

4. **可观测性**
   ~~~~~~~~~~

   * 记录详细日志
   * 收集性能指标
   * 实现链路追踪
   * 设置告警

扩展指南
--------

**添加新Agent:**

1. 继承 `BaseAgent` 类
2. 实现 `initialize()` 方法
3. 实现消息处理器
4. 注册到Coordinator
5. 添加测试

.. code-block:: python

   class NewAgent(BaseAgent):
       """新Agent示例"""

       def __init__(self):
           super().__init__(agent_id="new_agent")
           # 初始化逻辑

       async def initialize(self):
           """初始化"""
           # 资源初始化
           pass

       async def handle_custom_message(self, message: Message):
           """处理自定义消息"""
           # 消息处理逻辑
           pass

测试策略
--------

**单元测试:**

.. code-block:: python

   class TestCoordinator:
       def test_distribute_task(self):
           coordinator = Coordinator()
           task = Task(type="DATA_ANALYSIS", symbol="0700.HK")

           asyncio.run(coordinator.distribute_task(task))

           # 验证消息已发送
           assert coordinator.message_queue.qsize() == 1

**集成测试:**

.. code-block:: python

   @pytest.mark.asyncio
   async def test_agent_collaboration():
       coordinator = Coordinator()
       data_scientist = DataScientist()

       # 模拟消息发送
       await coordinator.send_message(
           to_agent="data_scientist",
           message_type="DATA_REQUEST",
           content={"symbol": "0700.HK"},
       )

       # 验证响应
       # ...

未来改进
--------

1. **动态Agent创建** - 根据负载动态创建Agent
2. **Agent集群** - 支持多实例部署
3. **机器学习** - Agent学习用户偏好
4. **自适应调度** - 智能任务分配
5. **Agent可视化** - 可视化Agent工作流程
