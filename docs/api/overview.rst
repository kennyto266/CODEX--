API 概览
========

港股量化交易系统提供了完整的RESTful API和WebSocket接口，支持：

* 策略回测和参数优化
* 实时数据获取
* 智能体状态监控
* 投资组合管理
* 风险管理

API特性
-------

* **基于FastAPI** - 高性能、类型安全的API框架
* **OpenAPI 3.0规范** - 自动生成交互式API文档
* **异步支持** - 所有端点都支持异步处理
* **完整验证** - 使用Pydantic进行数据验证
* **实时通信** - WebSocket支持实时数据推送

基础URL
-------

.. code-block:: text

   开发环境: http://localhost:8001/api/v1
   生产环境: https://your-domain.com/api/v1

认证方式
--------

API使用Bearer Token认证：

.. code-block:: http

   Authorization: Bearer <your-token>

错误处理
--------

所有API响应使用统一的错误格式：

.. code-block:: json

   {
       "error": "Error message",
       "detail": "Detailed error information",
       "status_code": 400
   }

API端点总览
-----------

.. list-table::
   :header-rows: 1

   * - 端点
     - 方法
     - 描述
   * - /api/v1/health
     - GET
     - 系统健康检查
   * - /api/v1/backtest/run
     - POST
     - 运行策略回测
   * - /api/v1/backtest/optimize
     - GET
     - 策略参数优化
   * - /api/v1/backtest/strategies
     - GET
     - 获取可用策略
   * - /api/v1/config
     - GET/POST
     - 配置管理
   * - /api/v1/layout
     - GET/POST
     - 界面布局
   * - /api/v1/websocket
     - WebSocket
     - 实时数据推送

版本控制
--------

API使用URL路径进行版本控制。当前版本为v1，未来版本将保持向后兼容。

SDK和代码示例
--------------

我们提供多种编程语言的SDK：

* **Python** - 使用httpx或requests
* **JavaScript/TypeScript** - fetch API或axios
* **Rust** - reqwest或tokio
* **Go** - net/http

快速开始
--------

1. 获取API令牌
2. 使用提供的SDK或HTTP客户端
3. 调用API端点
4. 处理响应和错误

详细使用指南请参考 :doc:`/user-guide/usage`

API限制
-------

* 速率限制：每分钟1000次请求
* 批量请求：最大100项
* 文件上传：最大10MB
* 数据范围：最多5年历史数据

联系支持
--------

如需技术支持，请访问：

* 文档: https://docs.quant-system.com
* 支持邮箱: support@quant-system.com
* GitHub Issues: https://github.com/org/quant-system/issues
