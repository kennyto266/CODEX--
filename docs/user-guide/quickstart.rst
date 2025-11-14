快速开始
========

本指南将帮助你在5分钟内完成首次回测。

前置准备
--------

确保已按照 :doc:`installation` 完成安装。

步骤1: 启动系统
---------------

打开终端/命令提示符，运行：

.. code-block:: bash

   python complete_project_system.py

看到以下输出说明启动成功：

.. code-block:: text

   [INFO] 启动港股量化交易系统
   [INFO] 加载配置: .env
   [INFO] 初始化数据库
   [INFO] 启动API服务: http://localhost:8001
   [INFO] 启动WebSocket服务
   [INFO] 系统启动完成

步骤2: 访问Web界面
------------------

打开浏览器访问 http://localhost:8001

你会看到：

.. image:: /images/quickstart/dashboard.png
   :alt: 仪表板界面

主要功能区域：

* **顶部导航** - 快速访问各功能模块
* **左侧菜单** - 功能分类导航
* **主要内容区** - 数据展示和操作
* **右侧面板** - 实时监控信息

步骤3: 运行首次回测
-------------------

1. 点击左侧菜单的 **"策略回测"**

2. 填写回测参数：

.. code-block:: text

   股票代码: 0700.HK (腾讯控股)
   开始日期: 2020-01-01
   结束日期: 2023-01-01
   策略类型: KDJ
   初始资金: 100,000

3. 点击 **"开始回测"** 按钮

4. 观察回测进度：

.. image:: /images/quickstart/backtest-progress.png
   :alt: 回测进度

步骤4: 查看回测结果
-------------------

回测完成后，你会看到详细的结果：

.. image:: /images/quickstart/backtest-results.png
   :alt: 回测结果

关键指标：

* **总收益率:** 15.67%
* **年化收益率:** 8.32%
* **夏普比率:** 1.23
* **最大回撤:** -5.45%
* **胜率:** 62.5%
* **交易次数:** 48次

还可以查看：

* **收益曲线图** - 显示资产增长趋势
* **回撤分析** - 显示最大回撤期间
* **交易记录** - 详细的买卖点
* **持仓分析** - 各期持仓情况

步骤5: 策略参数优化
-------------------

1. 在回测结果页面，点击 **"优化参数"**

2. 选择优化策略：

.. code-block:: text

   策略: KDJ
   优化目标: 最大化夏普比率
   并行工作线程: 8

3. 点击 **"开始优化"**

4. 等待优化完成（通常需要5-15分钟）

5. 查看优化结果：

.. image:: /images/quickstart/optimization-results.png
   :alt: 优化结果

系统会显示Top 10最优参数组合。

步骤6: 实时数据监控
-------------------

1. 点击 **"实时监控"** 查看市场数据

2. 选择要监控的股票：

.. code-block:: text

   0700.HK - 腾讯控股
   0388.HK - 港交所
   0939.HK - 建设银行

3. 观察实时价格变化：

.. image:: /images/quickstart/realtime-monitor.png
   :alt: 实时监控

步骤7: 查看智能体状态
---------------------

1. 点击 **"智能体管理"**

2. 查看7个AI Agent的状态：

.. code-block:: text

   ✓ Coordinator - 运行中
   ✓ Data Scientist - 运行中
   ✓ Quantitative Analyst - 运行中
   ✓ Portfolio Manager - 运行中
   ✓ Research Analyst - 运行中
   ✓ Risk Analyst - 运行中
   ✓ Quantitative Engineer - 运行中

3. 点击任意Agent查看详细信息：

.. image:: /images/quickstart/agent-details.png
   :alt: Agent详情

常见操作
--------

查询历史数据
~~~~~~~~~~~~

在API文档页面（http://localhost:8001/docs）测试：

.. code-block:: http

   GET /api/v1/backtest/history?page=1&size=20

导出回测结果
~~~~~~~~~~~~

在回测结果页面，点击 **"导出"** 按钮，支持：

* PDF报告
* Excel表格
* JSON数据
* CSV文件

设置告警
~~~~~~~~

1. 点击 **"告警管理"**

2. 创建新告警：

.. code-block:: text

   告警名称: 腾讯涨幅超5%
   触发条件: 0700.HK涨幅 > 5%
   通知方式: 邮件 + Web界面

3. 点击 **"保存"**

API使用示例
-----------

使用Python调用API：

.. code-block:: python

   import requests

   # 运行回测
   response = requests.post(
       'http://localhost:8001/api/v1/backtest/run',
       json={
           'symbol': '0700.HK',
           'start_date': '2020-01-01',
           'end_date': '2023-01-01',
           'strategy': 'kdj',
           'initial_capital': 100000
       }
   )

   result = response.json()
   print(f"总收益率: {result['total_return']:.2f}%")

使用WebSocket接收实时数据：

.. code-block:: javascript

   const ws = new WebSocket('ws://localhost:8001/api/v1/websocket');

   ws.onmessage = (event) => {
       const data = JSON.parse(event.data);
       if (data.type === 'market_data') {
           console.log(`股价更新: ${data.symbol} = $${data.data.price}`);
       }
   };

   // 订阅市场数据
   ws.send(JSON.stringify({
       type: 'subscribe',
       channel: 'market_data',
       symbol: '0700.HK'
   }));

下一步
------

现在你已经掌握了基本操作，可以：

* :doc:`configuration` - 学习配置系统参数
* :doc:`usage` - 深入了解高级功能
* 查看 :doc:`../developer-guide/overview` - 了解技术架构
* 访问 http://localhost:8001/docs - 阅读完整API文档

故障排除
--------

如果遇到问题：

1. 检查系统日志：

.. code-block:: bash

   tail -f quant_system.log

2. 查看API健康状态：

.. code-block:: bash

   curl http://localhost:8001/api/v1/health

3. 重启系统：

.. code-block:: bash

   # 停止服务 (Ctrl+C)
   # 重新启动
   python complete_project_system.py

4. 查阅 :doc:`troubleshooting` 获取详细解决方案
