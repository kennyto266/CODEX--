API 数据模型
=============

HealthStatus
------------

系统健康状态模型。

.. code-block:: json

   {
     "status": "healthy",
     "timestamp": 1701234567.89,
     "uptime_seconds": 3600.0,
     "version": "1.0.0",
     "service": "港股量化交易系统 API",
     "checks": {}
   }

**字段说明:**

.. list-table::
   :header-rows: 1

   * - 字段
     - 类型
     - 描述
   * - status
     - string
     - 系统状态：healthy/unhealthy/degraded
   * - timestamp
     - float
     - Unix时间戳
   * - uptime_seconds
     - float
     - 系统运行时间（秒）
   * - version
     - string
     - 系统版本号
   * - service
     - string
     - 服务名称
   * - checks
     - object
     - 各项健康检查结果

ServiceInfo
-----------

服务信息模型。

.. code-block:: json

   {
     "name": "港股量化交易系统 API",
     "version": "1.0.0",
     "status": "running",
     "description": "基于多智能体协作的港股量化交易系统"
   }

BacktestRequest
---------------

回测请求模型。

.. code-block:: json

   {
     "symbol": "0700.HK",
     "start_date": "2020-01-01",
     "end_date": "2023-01-01",
     "strategy": "kdj",
     "initial_capital": 100000.0,
     "parameters": {
       "k_period": 9,
       "d_period": 3
     }
   }

BacktestResult
--------------

回测结果模型。

.. code-block:: json

   {
     "strategy": "kdj",
     "symbol": "0700.HK",
     "start_date": "2020-01-01",
     "end_date": "2023-01-01",
     "total_return": 15.67,
     "annualized_return": 8.32,
     "sharpe_ratio": 1.23,
     "max_drawdown": -5.45,
     "win_rate": 62.5,
     "trades_count": 48,
     "final_value": 115670.0,
     "parameters": {}
   }

**字段说明:**

.. list-table::
   :header-rows: 1

   * - 字段
     - 类型
     - 单位
     - 描述
   * - strategy
     - string
     - -
     - 策略类型
   * - symbol
     - string
     - -
     - 股票代码
   * - start_date
     - string
     - -
     - 回测开始日期
   * - end_date
     - string
     - -
     - 回测结束日期
   * - total_return
     - number
     - %
     - 总收益率
   * - annualized_return
     - number
     - %
     - 年化收益率
   * - sharpe_ratio
     - number
     - -
     - 夏普比率
   * - max_drawdown
     - number
     - %
     - 最大回撤（负值）
   * - win_rate
     - number
     - %
     - 胜率
   * - trades_count
     - integer
     - 次
     - 交易次数
   * - final_value
     - number
     - 货币单位
     - 最终资产价值
   * - parameters
     - object
     - -
     - 使用的策略参数

AgentStatus
-----------

智能体状态模型。

.. code-block:: json

   {
     "agent_id": "coordinator",
     "status": "running",
     "last_heartbeat": 1701234567.89,
     "task_count": 5,
     "success_rate": 0.95
   }

MarketData
-----------

市场数据模型。

.. code-block:: json

   {
     "symbol": "0700.HK",
     "timestamp": 1701234567.89,
     "open": 350.0,
     "high": 355.0,
     "low": 345.0,
     "close": 352.0,
     "volume": 1000000
   }

Position
--------

持仓信息模型。

.. code-block:: json

   {
     "symbol": "0700.HK",
     "quantity": 1000,
     "avg_price": 350.0,
     "current_price": 352.0,
     "market_value": 352000.0,
     "unrealized_pnl": 2000.0,
     "unrealized_pnl_percent": 0.57
   }

ErrorResponse
-------------

错误响应模型。

.. code-block:: json

   {
     "error": "错误类型",
     "detail": "详细错误信息",
     "status_code": 400,
     "timestamp": 1701234567.89
   }
