API 端点详情
=============

健康检查端点
-------------

GET /api/v1/health
~~~~~~~~~~~~~~~~~~

系统健康检查端点，返回系统运行状态。

**响应示例:**

.. code-block:: json

   {
     "status": "healthy",
     "timestamp": 1701234567.89,
     "uptime_seconds": 3600.0,
     "version": "1.0.0",
     "service": "港股量化交易系统 API",
     "checks": {
       "api": {
         "status": "ok",
         "message": "API服务正常",
         "critical": true
       },
       "memory": {
         "status": "ok",
         "usage_percent": 45.2,
         "available_gb": 8.5,
         "critical": false
       },
       "disk": {
         "status": "ok",
         "usage_percent": 30.1,
         "free_gb": 120.5,
         "critical": false
       }
     }
   }

GET /api/v1/health/ready
~~~~~~~~~~~~~~~~~~~~~~~~

就绪检查端点，用于容器编排系统。

**响应示例:**

.. code-block:: json

   {
     "status": "ready",
     "timestamp": 1701234567.89,
     "checks": {
       "database": {"status": "ok", "critical": true},
       "cache": {"status": "ok", "critical": false}
     }
   }

GET /api/v1/health/live
~~~~~~~~~~~~~~~~~~~~~~~

存活检查端点。

**响应示例:**

.. code-block:: json

   {
     "status": "alive",
     "timestamp": "1701234567.89"
   }

GET /api/v1/info
~~~~~~~~~~~~~~~~

服务信息端点。

**响应示例:**

.. code-block:: json

   {
     "name": "港股量化交易系统 API",
     "version": "1.0.0",
     "status": "running",
     "description": "基于多智能体协作的港股量化交易系统"
   }

回测引擎端点
-------------

POST /api/v1/backtest/run
~~~~~~~~~~~~~~~~~~~~~~~~~~

运行策略回测。

**请求体:**

.. code-block:: json

   {
     "symbol": "0700.HK",
     "start_date": "2020-01-01",
     "end_date": "2023-01-01",
     "strategy": "kdj",
     "initial_capital": 100000.0,
     "parameters": {
       "k_period": 9,
       "d_period": 3,
       "oversold": 20,
       "overbought": 80
     }
   }

**响应示例:**

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
     "parameters": {
       "k_period": 9,
       "d_period": 3,
       "oversold": 20,
       "overbought": 80
     }
   }

**参数说明:**

.. list-table::
   :header-rows: 1

   * - 参数
     - 类型
     - 必填
     - 描述
   * - symbol
     - string
     - 是
     - 股票代码（港股格式，如0700.HK）
   * - start_date
     - string
     - 是
     - 开始日期（YYYY-MM-DD）
   * - end_date
     - string
     - 是
     - 结束日期（YYYY-MM-DD）
   * - strategy
     - string
     - 是
     - 策略类型（kdj, rsi, macd, ma, bb, cci, adx, atr, obv, ichimoku, sar）
   * - initial_capital
     - number
     - 否
     - 初始资金（默认10万元）
   * - parameters
     - object
     - 否
     - 策略特定参数

GET /api/v1/backtest/optimize
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

策略参数优化端点。

**查询参数:**

.. list-table::
   :header-rows: 1

   * - 参数
     - 类型
     - 必填
     - 默认值
     - 描述
   * - symbol
     - string
     - 是
     - -
     - 股票代码
   * - strategy
     - string
     - 是
     - -
     - 策略类型
   * - start_date
     - string
     - 是
     - -
     - 开始日期
   * - end_date
     - string
     - 是
     - -
     - 结束日期
   * - max_workers
     - integer
     - 否
     - 8
     - 并行工作线程数

**响应示例:**

返回最优参数组合的列表。

GET /api/v1/backtest/strategies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

获取支持的策略列表。

**响应示例:**

.. code-block:: json

   [
     "kdj",
     "rsi",
     "macd",
     "ma",
     "bb",
     "cci",
     "adx",
     "atr",
     "obv",
     "ichimoku",
     "sar"
   ]

GET /api/v1/backtest/history
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

获取历史回测记录。

**查询参数:**

.. list-table::
   :header-rows: 1

   * - 参数
     - 类型
     - 必填
     - 默认值
     - 描述
   * - page
     - integer
     - 否
     - 1
     - 页码（从1开始）
   * - size
     - integer
     - 否
     - 20
     - 每页数量（1-100）

配置管理端点
-------------

GET /api/v1/config
~~~~~~~~~~~~~~~~~~

获取当前配置。

POST /api/v1/config
~~~~~~~~~~~~~~~~~~~

更新配置。

界面布局端点
-------------

GET /api/v1/layout
~~~~~~~~~~~~~~~~~~

获取界面布局配置。

POST /api/v1/layout
~~~~~~~~~~~~~~~~~~~

更新界面布局配置。

错误码参考
----------

.. list-table::
   :header-rows: 1

   * - 状态码
     - 描述
   * - 200
     - 请求成功
   * - 400
     - 请求参数错误
   * - 401
     - 未认证
   * - 403
     - 无权限
   * - 404
     - 资源不存在
   * - 429
     - 请求频率超限
   * - 500
     - 服务器内部错误
   * - 503
     - 服务不可用
