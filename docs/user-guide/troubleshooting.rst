故障排除
========

常见问题与解决方案
------------------

系统启动问题
~~~~~~~~~~~~

**问题1: 端口被占用**

.. code-block:: text

   错误信息: OSError: [Errno 10048] Only one usage of each socket address
   解决方案:
     1. 查看占用进程: lsof -i :8001 (Linux/Mac) / netstat -ano | findstr :8001 (Windows)
     2. 终止进程: kill -9 <PID> (Linux/Mac) / taskkill /PID <PID> /F (Windows)
     3. 或使用其他端口: python complete_project_system.py --port 8002

**问题2: 依赖包安装失败**

.. code-block:: text

   错误信息: ERROR: Could not install packages due to an OSError
   解决方案:
     1. 升级pip: pip install --upgrade pip
     2. 使用国内镜像:
        pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
     3. 安装TA-Lib:
        Windows: 下载对应whl文件后 pip install 文件名.whl
        Linux: sudo apt-get install ta-lib-dev && pip install TA-Lib
        Mac: brew install ta-lib && pip install TA-Lib

**问题3: 虚拟环境问题**

.. code-block:: text

   错误信息: ModuleNotFoundError: No module named 'src'
   解决方案:
     1. 确保虚拟环境已激活 (提示符前有 (.venv))
     2. 重新安装依赖: pip install -r requirements.txt
     3. 检查Python路径: python -c "import sys; print(sys.path)"

数据获取问题
~~~~~~~~~~~~

**问题4: API连接失败**

.. code-block:: text

   错误信息: ConnectionError: HTTPSConnectionPool
   解决方案:
     1. 检查网络连接: ping 18.180.162.113
     2. 检查防火墙设置
     3. 验证API密钥: 在 .env 中正确配置
     4. 查看日志: tail -f quant_system.log

**问题5: 数据返回异常**

.. code-block:: text

   错误信息: KeyError: 'data' 或数据为空
   解决方案:
     1. 检查股票代码格式: 必须为小写 (如 0700.hk)
     2. 验证日期范围: 确保结束日期 >= 开始日期
     3. 检查数据源状态: 访问 http://18.180.162.113:9191/health
     4. 尝试其他股票代码进行测试

**问题6: 数据延迟**

.. code-block:: text

   现象: 数据更新缓慢或滞后
   解决方案:
     1. 检查网络延迟: 使用 ping 命令
     2. 启用数据缓存: 在 .env 中设置 CACHE_ENABLED=True
     3. 调整缓存时间: CACHE_TTL=1800 (30分钟)
     4. 重启服务: 重启后强制刷新缓存

回测问题
~~~~~~~~

**问题7: 回测运行缓慢**

.. code-block:: text

   现象: 回测需要很长时间才能完成
   解决方案:
     1. 减少数据范围: 使用更短的回测期间
     2. 减少并行线程: 设置 BACKTEST_PARALLEL_WORKERS=4
     3. 禁用详细日志: 设置 LOG_LEVEL=WARNING
     4. 使用SSD硬盘存储

**问题8: 内存不足**

.. code-block:: text

   错误信息: MemoryError 或系统卡死
   解决方案:
     1. 减少并行工作数: MAX_WORKERS=4
     2. 分批处理数据: 设置 batch_size=1000
     3. 启用内存映射: 使用 numpy memmap
     4. 升级硬件: 增加系统内存

**问题9: 策略参数错误**

.. code-block:: text

   错误信息: ValueError: invalid parameters
   解决方案:
     1. 检查参数范围:
        KDJ: k_period [5-30], oversold [10-40], overbought [60-90]
        RSI: period [2-50]
        MACD: fast [2-50], slow [10-100]
     2. 参考API文档中的参数说明
     3. 使用系统提供的默认参数开始

**问题10: 回测结果异常**

.. code-block:: text

   现象: 收益率过高/过低，明显不合理
   解决方案:
     1. 检查数据质量: 查看原始数据是否有异常值
     2. 验证交易逻辑: 确认买卖信号计算正确
     3. 考虑交易成本: 设置合理的佣金费率
     4. 检查数据对齐: 确保价格和指标数据日期一致

Web界面问题
~~~~~~~~~~~~

**问题11: 页面无法访问**

.. code-block:: text

   现象: 浏览器显示"无法访问此网站"
   解决方案:
     1. 确认服务启动: 检查终端输出中的 "启动API服务: http://localhost:8001"
     2. 检查端口: 访问 http://localhost:8001/api/v1/health
     3. 清除浏览器缓存: Ctrl+Shift+Delete
     4. 尝试其他浏览器: Chrome, Firefox, Edge

**问题12: WebSocket连接失败**

.. code-block:: text

   错误信息: WebSocket connection failed
   解决方案:
     1. 检查防火墙: 允许WebSocket连接
     2. 验证URL: ws://localhost:8001/api/v1/websocket
     3. 查看浏览器控制台: F12打开开发者工具
     4. 重新连接: 刷新页面

**问题13: 图表不显示**

.. code-block:: text

   现象: 图表区域显示空白
   解决方案:
     1. 检查数据: 确认有数据返回
     2. 查看控制台: F12查看JavaScript错误
     3. 清除缓存: 强制刷新 Ctrl+F5
     4. 检查网络: 确保静态资源加载正常

智能体问题
~~~~~~~~~~

**问题14: Agent无响应**

.. code-block:: text

   现象: 智能体状态显示为"无响应"或"离线"
   解决方案:
     1. 查看Agent日志: 检查quant_system.log中的Agent相关日志
     2. 重启Agent: 在界面中点击"重启"按钮
     3. 检查资源使用: 确认CPU和内存充足
     4. 查看异常信息: 启用DEBUG日志级别

**问题15: Agent通信失败**

.. code-block:: text

   错误信息: Message delivery failed
   解决方案:
     1. 检查消息队列: 确认Redis服务正常运行
     2. 验证网络连接: Agent间网络通信正常
     3. 查看队列状态: redis-cli llen message_queue
     4. 重启消息服务: 重启系统

**问题16: 任务执行失败**

.. code-block:: text

   现象: Agent任务长时间无结果
   解决方案:
     1. 查看任务队列: 确认任务已加入队列
     2. 检查资源竞争: 避免多个Agent同时使用同一资源
     3. 设置任务超时: 修改 agent_task_timeout 配置
     4. 手动终止任务: 在界面上取消任务

性能问题
~~~~~~~~

**问题17: 系统响应缓慢**

.. code-block:: text

   现象: API请求响应时间超过5秒
   解决方案:
     1. 检查负载: 查看CPU和内存使用率
     2. 优化数据库: 对常用查询添加索引
     3. 启用缓存: 增加缓存命中率和TTL
     4. 增加工作进程: 设置 WORKERS=4

**问题18: 磁盘空间不足**

.. code-block:: text

   错误信息: No space left on device
   解决方案:
     1. 清理日志: rm quant_system.log.* 或日志轮转
     2. 删除临时文件: rm -rf /tmp/quant_*
     3. 清理缓存: rm -rf ~/.cache/quant_system
     4. 扩大磁盘空间: 添加硬盘或清理数据

配置问题
~~~~~~~~

**问题19: 环境变量未生效**

.. code-block:: text

   现象: 修改 .env 文件后配置未改变
   解决方案:
     1. 重启系统: 修改环境变量后需要重启
     2. 检查文件位置: .env 必须在项目根目录
     3. 验证格式: KEY=VALUE 格式，注意等号无空格
     4. 重新加载: source .env

**问题20: 配置文件冲突**

.. code-block:: text

   现象: 出现两个配置值，不知道哪个生效
   解决方案:
     1. 查看启动日志: 系统会显示加载的配置文件
     2. 检查优先级: 环境变量 > .env > 默认值
     3. 验证配置: GET /api/v1/config 查看实际配置
     4. 统一配置: 删除重复的配置文件

诊断工具
--------

日志查看
~~~~~~~~

系统日志位置: `quant_system.log`

.. code-block:: bash

   # 查看最新日志
   tail -f quant_system.log

   # 搜索特定错误
   grep "ERROR" quant_system.log

   # 按时间范围查看
   grep "2025-11-09" quant_system.log

   # 查看Agent日志
   grep "agent" quant_system.log

健康检查
~~~~~~~~

.. code-block:: bash

   # API健康状态
   curl http://localhost:8001/api/v1/health

   # 就绪检查
   curl http://localhost:8001/api/v1/health/ready

   # 存活检查
   curl http://localhost:8001/api/v1/health/live

系统状态检查
~~~~~~~~~~~~

.. code-block:: bash

   # 检查端口占用
   lsof -i :8001

   # 检查进程
   ps aux | grep python

   # 检查内存使用
   free -h

   # 检查磁盘空间
   df -h

   # 检查网络连接
   netstat -tuln | grep 8001

性能分析
~~~~~~~~

.. code-block:: bash

   # CPU使用率
   top

   # 内存使用详情
   ps aux --sort=-%mem | head

   # I/O统计
   iostat -x 1

   # 网络监控
   nethogs

调试模式
--------

启用详细日志
~~~~~~~~~~~~

在 .env 中设置:

.. code-block:: bash

   LOG_LEVEL=DEBUG
   STRUCTURED_LOGGING=True

启用性能分析
~~~~~~~~~~~~

.. code-block:: python

   from src.monitoring import performance_monitor

   # 启动性能监控
   performance_monitor.start()

   # 生成性能报告
   performance_monitor.generate_report()

添加自定义日志
~~~~~~~~~~~~~~

.. code-block:: python

   import structlog

   logger = structlog.get_logger("custom.module")

   # 记录信息
   logger.info("操作成功", user_id=123, action="buy")

   # 记录错误
   logger.error("操作失败", error_code=500, detail="网络超时")

   # 记录调试信息
   logger.debug("调试信息", data=some_data)

联系支持
--------

如果问题仍未解决，请提供以下信息：

1. **系统信息**
   ~~~~~~~~~~

   .. code-block:: text

      操作系统: Windows 11 / Ubuntu 20.04 / macOS 14.0
      Python版本: 3.10.8
      系统架构: x86_64 / ARM64

2. **错误信息**
   ~~~~~~~~~~

   完整的错误信息和堆栈跟踪

3. **日志文件**
   ~~~~~~~~~~

   quant_system.log（最近100行）

4. **配置信息**
   ~~~~~~~~~~

   .env文件（隐藏敏感信息）

5. **复现步骤**
   ~~~~~~~~~~

   详细描述问题复现步骤

**联系方式:**

* 邮箱: support@quant-system.com
* GitHub: https://github.com/org/quant-system/issues
* 文档: https://docs.quant-system.com/troubleshooting

**响应时间:**

* 一般问题: 1-2个工作日
* 严重问题: 4小时内
* 紧急问题: 1小时内
