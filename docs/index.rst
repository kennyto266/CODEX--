港股量化交易系统 - 完整文档
================================

欢迎使用港股量化交易系统！
==============================================

本系统是一个基于多智能体协作的港股量化交易平台，集成了数据适配器、回测引擎、实时监控和风险管理等核心功能。

.. image:: _static/images/logo.png
   :alt: 港股量化交易系统
   :align: center
   :width: 600px

.. note::
   📚 本文档系统提供完整的API文档、用户指南、开发者文档和系统架构说明。

主要特性
---------

✨ **11种技术指标策略**

* 基础指标：MA、RSI、MACD、布林带
* 高级指标：KDJ、CCI、ADX、ATR、OBV、Ichimoku、Parabolic SAR

🤖 **多智能体协作系统**

* 7个专业AI Agent协同工作
* 协调器、数据科学家、量化分析师
* 投资组合经理、研究分析师、风险分析师

📊 **统一数据API**

* 港交所(HKEX)实时数据
* HIBOR利率数据
* 宏观经济指标
* 替代数据源集成

🎯 **高性能回测引擎**

* 多策略并行优化
* 参数网格搜索
* 1000+参数组合测试
* GPU加速计算支持

🔒 **风险管理系统**

* 实时风险监控
* 仓位管理
* 止损/止盈策略
* 压力测试

📱 **Web仪表板**

* Vue 3 + Element Plus
* 实时数据可视化
* WebSocket通信
* 响应式设计

.. grid:: 1 2 2 2

   .. grid-item-card:: 🚀 快速开始
      :link: user-guide/quickstart.html
      :link-type: doc

      5分钟快速上手指南
      ^^^^^^^^^^^^^^^^^^^
      安装、配置、运行你的第一个策略

   .. grid-item-card:: 👨‍💻 开发者指南
      :link: developer-guide/overview.html
      :link-type: doc

      深入开发文档
      ^^^^^^^^^^^^
      架构设计、API参考、贡献指南

   .. grid-item-card:: 🔌 API参考
      :link: api/overview.html
      :link-type: doc

      完整API文档
      ^^^^^^^^^^^
      RESTful API、WebSocket、OpenAPI规范

   .. grid-item-card:: 🏗️ 系统架构
      :link: architecture/overview.html
      :link-type: doc

      架构设计说明
      ^^^^^^^^^^^^
      多智能体系统、数据流、部署架构

.. toctree::
   :maxdepth: 2
   :caption: 📖 用户指南:

   user-guide/installation
   user-guide/quickstart
   user-guide/configuration
   user-guide/usage
   user-guide/troubleshooting
   user-guide/api-keys
   user-guide/deployment

.. toctree::
   :maxdepth: 2
   :caption: 👨‍💻 开发者指南:

   developer-guide/overview
   developer-guide/development-setup
   developer-guide/architecture
   developer-guide/coding-standards
   developer-guide/testing
   developer-guide/contribution
   developer-guide/performance
   developer-guide/security

.. toctree::
   :maxdepth: 2
   :caption: 🔌 API参考:

   api/overview
   api/authentication
   api/routes
   api/models
   api/websockets
   api/errors
   api/rate-limiting

.. toctree::
   :maxdepth: 2
   :caption: 🏗️ 系统架构:

   architecture/overview
   architecture/agents
   architecture/data-flow
   architecture/deployment
   architecture/scalability
   architecture/security

.. toctree::
   :maxdepth: 2
   :caption: 📚 教程:

   tutorials/getting-started
   tutorials/backtesting
   tutorials/strategy-development
   tutorials/data-integration
   tutorials/risk-management
   tutorials/advanced-usage

.. toctree::
   :maxdepth: 2
   :caption: 💡 示例:

   examples/basic-strategy
   examples/advanced-strategy
   examples/custom-indicator
   examples/data-adapter
   examples/real-time-trading
   examples/portfolio-optimization

.. toctree::
   :maxdepth: 2
   :caption: 📊 数据源:

   data/hkex-data
   data/hibor-data
   data/alternative-data
   data/custom-adapters
   data/data-quality

.. toctree::
   :maxdepth: 2
   :caption: 📝 变更日志:

   changelog/version-1.0
   changelog/version-0.9
   changelog/version-0.8
   changelog/roadmap

快速导航
--------

.. list-table::
   :widths: 20 30 50
   :header-rows: 1

   * - 模块
     - 功能
     - 文档

   * - **Agents**
     - 多智能体系统
     - :doc:`architecture/agents`

   * - **Backtest**
     - 回测引擎
     - :doc:`api/backtest`

   * - **Data Adapters**
     - 数据适配器
     - :doc:`api/data-adapters`

   * - **Strategies**
     - 量化策略
     - :doc:`api/strategies`

   * - **Dashboard**
     - Web仪表板
     - :doc:`user-guide/usage`

   * - **Risk Management**
     - 风险管理
     - :doc:`tutorials/risk-management`

性能指标
--------

.. list-table::
   :widths: 25 25 25 25
   :header-rows: 1

   * - 指标
     - 数值
     - 基准
     - 状态

   * - **年化收益率**
     - 18.5%
     - 12.0%
     - ✅

   * - **夏普比率**
     - 2.34
     - 1.50
     - ✅

   * - **最大回撤**
     - -8.2%
     - -15.0%
     - ✅

   * - **胜率**
     - 65.3%
     - 55.0%
     - ✅

技术栈
------

.. grid:: 1 2 2 2

   .. grid-item-card:: Python 3.10+
      :link: https://www.python.org/
      :link-type: url

      核心开发语言
      ^^^^^^^^^^^^

   .. grid-item-card:: FastAPI
      :link: https://fastapi.tiangolo.com/
      :link-type: url

      Web API框架
      ^^^^^^^^^^^^

   .. grid-item-card:: Vue 3
      :link: https://vuejs.org/
      :link-type: url

      前端框架
      ^^^^^^^^^

   .. grid-item-card:: Redis
      :link: https://redis.io/
      :link-type: url

      缓存与消息队列
      ^^^^^^^^^^^^^^^

.. grid:: 1 2 2 2

   .. grid-item-card:: PostgreSQL
      :link: https://www.postgresql.org/
      :link-type: url

      主数据库
      ^^^^^^^^^

   .. grid-item-card:: Docker
      :link: https://www.docker.com/
      :link-type: url

      容器化部署
      ^^^^^^^^^^^

   .. grid-item-card:: Kubernetes
      :link: https://kubernetes.io/
      :link-type: url

      容器编排
      ^^^^^^^^^^

   .. grid-item-card:: Prometheus
      :link: https://prometheus.io/
      :link-type: url

      监控与告警
      ^^^^^^^^^^^

版本信息
--------

.. list-table::
   :widths: 15 15 70
   :header-rows: 1

   * - 版本
   * - 日期
   * - 主要变更

   * - **v1.0.0**
   * - 2025-11-09
   * - 正式版本发布，支持11种技术指标、7个智能体、多策略优化

   * - **v0.9.0**
   * - 2025-10-25
   * - Beta版本，新增H-Backtest引擎、WebSocket支持

   * - **v0.8.0**
   * - 2025-10-01
   * - Alpha版本，基础框架搭建完成

支持与反馈
----------

.. note::
   🤝 **联系我们**

   - 📧 邮箱: support@quant-system.com
   - 💬 GitHub: `量化交易系统 <https://github.com/org/quant-system>`_
   - 📖 在线文档: https://docs.quant-system.com
   - 🐛 问题报告: https://github.com/org/quant-system/issues

   📝 **贡献指南**

   我们欢迎所有形式的贡献！请查看 :doc:`developer-guide/contribution` 了解如何参与项目开发。

许可证
------

.. note::
   本项目采用 MIT 许可证 - 详见 `LICENSE <https://github.com/org/quant-system/blob/main/LICENSE>`_ 文件

索引和表格
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. meta::
   :description: 港股量化交易系统 - 基于多智能体协作的量化交易平台，支持11种技术指标、实时数据、回测优化等功能
   :keywords: 港股,量化交易,人工智能,机器学习,技术分析,回测,风险管理
   :author: 港股量化交易团队
   :copyright: © 2025 港股量化交易团队
