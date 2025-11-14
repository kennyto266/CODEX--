系统配置
========

配置文件说明
------------

系统使用 `.env` 文件进行配置管理。主要配置文件包括：

.. list-table::
   :header-rows: 1

   * - 文件
     - 用途
     - 位置
   * - .env
     - 环境变量配置
     - 项目根目录
   * - config.py
     - Python配置模块
     - src/config.py
   * - api_config.yaml
     - API配置
     - config/api_config.yaml

基础配置
--------

在项目根目录创建 `.env` 文件：

.. code-block:: bash

   # ===========================================
   # 港股量化交易系统 - 环境配置
   # ===========================================

   # ===========================================
   # 服务器配置
   # ===========================================
   API_HOST=0.0.0.0
   API_PORT=8001
   DEBUG=False
   WORKERS=4

   # ===========================================
   # 数据库配置
   # ===========================================
   DATABASE_URL=sqlite:///./quant_system.db
   # 或使用PostgreSQL
   # DATABASE_URL=postgresql://user:password@localhost:5432/quant_db

   # ===========================================
   # API密钥配置
   # ===========================================

   # Alpha Vantage API
   ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key

   # Futu API (港股交易)
   FUTU_CLIENT_ID=your_futu_client_id
   FUTU_PASSWORD=your_futu_password

   # Telegram Bot
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   TELEGRAM_CHAT_ID=your_chat_id

   # ===========================================
   # 数据源配置
   # ===========================================

   # HKEX数据源
   HKEX_DATA_SOURCE=http://18.180.162.113:9191/inst/getInst
   DATA_API_KEY=your_data_api_key

   # Yahoo Finance
   YAHOO_FINANCE_ENABLED=True

   # ===========================================
   # 缓存配置
   # ===========================================
   REDIS_URL=redis://localhost:6379/0
   CACHE_TTL=3600
   CACHE_MAX_SIZE=10000

   # ===========================================
   # 日志配置
   # ===========================================
   LOG_LEVEL=INFO
   LOG_FILE=quant_system.log
   LOG_MAX_SIZE=100MB
   LOG_BACKUP_COUNT=5

   # ===========================================
   # 性能配置
   # ===========================================
   MAX_WORKERS=8
   BACKTEST_PARALLEL_WORKERS=8
   REQUEST_TIMEOUT=30
   MAX_RETRIES=3

   # ===========================================
   # 安全配置
   # ===========================================
   SECRET_KEY=your_secret_key_here
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   ALGORITHM=HS256

   # ===========================================
   # 前端配置
   # ===========================================
   FRONTEND_URL=http://localhost:8001
   WEBSOCKET_URL=ws://localhost:8001

   # ===========================================
   # 监控配置
   # ===========================================
   MONITORING_ENABLED=True
   HEALTH_CHECK_INTERVAL=30
   METRICS_RETENTION_DAYS=30

服务器配置
----------

修改API服务器设置：

.. code-block:: bash

   # 服务器地址
   API_HOST=0.0.0.0

   # 端口号
   API_PORT=8001

   # 调试模式
   DEBUG=True

   # 工作进程数
   WORKERS=4

**推荐配置:**

* **开发环境:** DEBUG=True, WORKERS=1
* **测试环境:** DEBUG=False, WORKERS=2
* **生产环境:** DEBUG=False, WORKERS=4或CPU核心数

数据库配置
----------

SQLite（默认）
~~~~~~~~~~~~~

.. code-block:: bash

   DATABASE_URL=sqlite:///./quant_system.db

适合开发和测试，数据存储在本地文件。

PostgreSQL（推荐生产环境）
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   DATABASE_URL=postgresql://username:password@localhost:5432/quant_db

高性能，适合生产环境。

MySQL
~~~~~

.. code-block:: bash

   DATABASE_URL=mysql://username:password@localhost:3306/quant_db

API密钥配置
-----------

获取API密钥的步骤：

1. **Alpha Vantage**
   ~~~~~~~~~~~~~~~

   访问: https://www.alphavantage.co/support/#api-key

   注册后获取免费API密钥。

   .. code-block:: bash

      ALPHA_VANTAGE_API_KEY=your_key_here

2. **Futu API**
   ~~~~~~~~~~

   访问: https://www.futuhk.com/

   注册开发者账号，获取客户端ID和密码。

   .. code-block:: bash

      FUTU_CLIENT_ID=12345
      FUTU_PASSWORD=your_password

3. **Telegram Bot**
   ~~~~~~~~~~~~~~

   通过 @BotFather 创建机器人：

   .. code-block:: text

      1. 发送 /newbot 给 @BotFather
      2. 按提示设置机器人名称
      3. 获取API Token
      4. 发送 /myid 给 @userinfobot 获取Chat ID

   .. code-block:: bash

      TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
      TELEGRAM_CHAT_ID=123456789

数据源配置
----------

统一数据API
~~~~~~~~~~

使用OpenSpec指定的统一API：

.. code-block:: bash

   HKEX_DATA_SOURCE=http://18.180.162.113:9191/inst/getInst
   DATA_API_KEY=your_api_key

启用/禁用数据源：

.. code-block:: bash

   # HKEX官方数据
   HKEX_ENABLED=True

   # Yahoo Finance
   YAHOO_FINANCE_ENABLED=True

   # Alpha Vantage
   ALPHA_VANTAGE_ENABLED=True

缓存配置
--------

Redis缓存（推荐）
~~~~~~~~~~~~~~~~

.. code-block:: bash

   REDIS_URL=redis://localhost:6379/0
   CACHE_TTL=3600
   CACHE_MAX_SIZE=10000

内存缓存
~~~~~~~~

.. code-block:: bash

   CACHE_TYPE=memory
   CACHE_TTL=3600
   CACHE_MAX_SIZE=100

禁用缓存
~~~~~~~~

.. code-block:: bash

   CACHE_ENABLED=False

日志配置
--------

日志级别
~~~~~~~~

.. code-block:: bash

   # 可选值: DEBUG, INFO, WARNING, ERROR, CRITICAL
   LOG_LEVEL=INFO

日志文件
~~~~~~~~

.. code-block:: bash

   LOG_FILE=quant_system.log
   LOG_MAX_SIZE=100MB
   LOG_BACKUP_COUNT=5

结构化日志
~~~~~~~~~~

使用JSON格式的结构化日志：

.. code-block:: bash

   STRUCTURED_LOGGING=True

性能配置
--------

并行处理
~~~~~~~~

.. code-block:: bash

   # 回测并行工作线程
   BACKTEST_PARALLEL_WORKERS=8

   # 最大工作线程数
   MAX_WORKERS=8

网络超时
~~~~~~~~

.. code-block:: bash

   REQUEST_TIMEOUT=30
   MAX_RETRIES=3

监控配置
--------

启用监控
~~~~~~~~

.. code-block:: bash

   MONITORING_ENABLED=True

健康检查
~~~~~~~~

.. code-block:: bash

   HEALTH_CHECK_INTERVAL=30

指标保留
~~~~~~~~

.. code-block:: bash

   METRICS_RETENTION_DAYS=30

安全配置
--------

密钥管理
~~~~~~~~

.. code-block:: bash

   # JWT密钥（生产环境请使用强密钥）
   SECRET_KEY=your_very_secure_secret_key_change_this

   # 访问令牌过期时间（分钟）
   ACCESS_TOKEN_EXPIRE_MINUTES=30

   # JWT算法
   ALGORITHM=HS256

HTTPS配置
~~~~~~~~~

生产环境建议启用HTTPS：

.. code-block:: bash

   SSL_CERT_FILE=/path/to/cert.pem
   SSL_KEY_FILE=/path/to/key.pem

高级配置
--------

自定义配置模块
~~~~~~~~~~~~~~

创建 `config/custom_config.py`：

.. code-block:: python

   from pydantic_settings import BaseSettings

   class CustomConfig(BaseSettings):
       """自定义配置"""
       custom_api_url: str = "https://api.example.com"
       custom_timeout: int = 60

       class Config:
           env_file = ".env"

环境变量验证
------------

系统会自动验证配置：

.. code-block:: python

   from pydantic import BaseSettings, validator

   class Config(BaseSettings):
       API_PORT: int

       @validator('API_PORT')
       def validate_port(cls, v):
           if not 1 <= v <= 65535:
               raise ValueError('端口号必须在1-65535之间')
           return v

配置验证
--------

启动时会自动验证配置：

.. code-block:: bash

   python -c "from src.config import validate_config; validate_config()"

配置管理最佳实践
----------------

1. **环境分离**
   ~~~~~~~~~~

   * 开发环境: .env.development
   * 测试环境: .env.testing
   * 生产环境: .env.production

2. **敏感信息**
   ~~~~~~~~~~

   * 永远不要将API密钥提交到Git
   * 使用 .env.example 作为模板
   * 在 .gitignore 中添加 .env

3. **配置验证**
   ~~~~~~~~~~

   启动时自动验证所有必需的配置项。

4. **文档更新**
   ~~~~~~~~~~

   保持配置项文档与代码同步。

配置示例
--------

开发环境配置
~~~~~~~~~~~~

.. code-block:: bash

   # .env.development
   DEBUG=True
   API_PORT=8001
   LOG_LEVEL=DEBUG
   WORKERS=1
   DATABASE_URL=sqlite:///./dev.db

测试环境配置
~~~~~~~~~~~~

.. code-block:: bash

   # .env.testing
   DEBUG=False
   API_PORT=8002
   LOG_LEVEL=WARNING
   WORKERS=2
   DATABASE_URL=sqlite:///:memory:

生产环境配置
~~~~~~~~~~~~

.. code-block:: bash

   # .env.production
   DEBUG=False
   API_PORT=8001
   LOG_LEVEL=INFO
   WORKERS=4
   DATABASE_URL=postgresql://user:pass@db:5432/quant_prod
   SECRET_KEY=your_secure_key_here
   SSL_ENABLED=True
   MONITORING_ENABLED=True
