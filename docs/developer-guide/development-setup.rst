开发环境搭建
============

系统要求
--------

* **操作系统:** Windows 10+, Ubuntu 20.04+, macOS 10.15+
* **Python:** 3.10 或更高版本 (推荐 3.11)
* **Node.js:** 18+ (用于前端开发)
* **Git:** 2.30+
* **Redis:** 6.0+ (可选，用于缓存)
* **PostgreSQL:** 13+ (可选，用于生产数据库)
* **Rust:** 1.70+ (可选，用于Rust组件开发)

Python环境安装
--------------

1. 安装Python
~~~~~~~~~~~~

**Windows:**

.. code-block:: bash

   # 下载: https://www.python.org/downloads/
   # 或使用 winget
   winget install Python.Python.3.11

   # 验证安装
   python --version
   pip --version

**Ubuntu/Debian:**

.. code-block:: bash

   sudo apt update
   sudo apt install python3.11 python3.11-venv python3.11-dev

**macOS:**

.. code-block:: bash

   # 使用 Homebrew
   brew install python@3.11

**验证Python安装:**

.. code-block:: bash

   $ python --version
   Python 3.11.8

   $ pip --version
   pip 24.0

2. 配置pip国内镜像
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   mkdir -p ~/.pip
   cat > ~/.pip/pip.conf << EOF
   [global]
   index-url = https://pypi.tuna.tsinghua.edu.cn/simple
   trusted-host = pypi.tuna.tsinghua.edu.cn
   EOF

3. 安装基础工具
~~~~~~~~~~~~~~

.. code-block:: bash

   pip install --upgrade pip setuptools wheel
   pip install virtualenv

项目克隆与配置
--------------

1. 克隆代码仓库
~~~~~~~~~~~~~~

.. code-block:: bash

   git clone https://github.com/org/quant-system.git
   cd quant-system

2. 创建虚拟环境
~~~~~~~~~~~~~~

.. code-block:: bash

   # 使用 venv
   python -m venv .venv

   # 激活虚拟环境
   # Windows
   .venv\Scripts\activate

   # Linux/Mac
   source .venv/bin/activate

   # 验证激活 (提示符前应显示 (.venv))
   which python
   # 输出: .../quant-system/.venv/bin/python

3. 安装Python依赖
~~~~~~~~~~~~~~~

.. code-block:: bash

   # 核心依赖
   pip install -r requirements.txt

   # 开发依赖
   pip install -r test_requirements.txt

   # 文档依赖
   pip install -r docs_requirements.txt

   # 验证安装
   pip list | grep -E "(fastapi|pandas|numpy|pytest)"

4. 安装Rust工具链（可选）
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # 安装 Rust
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   source ~/.cargo/env

   # 安装 maturin (用于构建Python绑定)
   pip install maturin

   # 构建Rust组件
   cd quant-api
   maturin build --release
   pip install target/wheels/*.whl

5. 前端环境安装（可选）
~~~~~~~~~~~~~~~~~~~

如果您需要修改前端代码：

.. code-block:: bash

   # 安装 Node.js (推荐使用 nvm)
   curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
   source ~/.bashrc
   nvm install 18
   nvm use 18

   # 安装前端依赖
   cd frontend
   npm install

   # 构建前端
   npm run build

环境配置
--------

1. 创建环境变量文件
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   cp .env.example .env

2. 配置基础设置
~~~~~~~~~~~~~

编辑 `.env` 文件:

.. code-block:: bash

   # 开发环境配置
   DEBUG=True
   LOG_LEVEL=DEBUG
   API_PORT=8001
   WORKERS=1

   # 数据库
   DATABASE_URL=sqlite:///./dev.db

   # 缓存 (可选)
   REDIS_URL=redis://localhost:6379/0

   # API密钥 (填入真实密钥)
   ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
   TELEGRAM_BOT_TOKEN=your_telegram_token

3. 配置IDE
~~~~~~~~~

**VS Code (推荐):**

安装扩展:

.. code-block:: text

   - Python
   - Pylance
   - Python Docstring Generator
   - REST Client
   - Thunder Client
   - GitLens
   - Error Lens

配置 `settings.json`:

.. code-block:: json

   {
     "python.defaultInterpreterPath": "./.venv/bin/python",
     "python.linting.enabled": true,
     "python.linting.flake8Enabled": true,
     "python.linting.mypyEnabled": true,
     "python.formatting.provider": "black",
     "python.testing.pytestEnabled": true,
     "python.testing.pytestArgs": ["tests/"],
     "editor.formatOnSave": true,
     "editor.codeActionsOnSave": {
       "source.organizeImports": true
     }
   }

**PyCharm:**

.. code-block:: text

   1. 打开项目
   2. 设置Python解释器: File > Settings > Project > Python Interpreter
   3. 选择: .venv/bin/python
   4. 启用代码检查: File > Settings > Editor > Inspections
   5. 配置代码格式化: File > Settings > Tools > External Tools
   6. 设置测试运行器: pytest

验证环境
--------

1. 运行单元测试
~~~~~~~~~~~~~

.. code-block:: bash

   pytest tests/ -v
   # 应该看到所有测试通过

2. 检查代码质量
~~~~~~~~~~~~~

.. code-block:: bash

   # 检查代码风格
   flake8 src/ tests/

   # 检查类型
   mypy src/

   # 格式化代码
   black --check src/ tests/

3. 启动开发服务器
~~~~~~~~~~~~~~~

.. code-block:: bash

   python complete_project_system.py

   # 应该看到输出:
   # [INFO] 启动港股量化交易系统
   # [INFO] 启动API服务: http://localhost:8001

4. 访问系统
~~~~~~~~~

打开浏览器:

.. code-block:: text

   Web界面: http://localhost:8001
   API文档: http://localhost:8001/docs
   健康检查: http://localhost:8001/api/v1/health

5. 验证API调用
~~~~~~~~~~~~

.. code-block:: bash

   # 测试健康检查
   curl http://localhost:8001/api/v1/health
   # 返回JSON响应

   # 测试回测接口
   curl -X POST "http://localhost:8001/api/v1/backtest/run" \
        -H "Content-Type: application/json" \
        -d '{
          "symbol": "0700.HK",
          "start_date": "2020-01-01",
          "end_date": "2023-01-01",
          "strategy": "kdj"
        }'

开发工具配置
------------

1. Pre-commit钩子
~~~~~~~~~~~~~~~

安装pre-commit:

.. code-block:: bash

   pip install pre-commit

安装钩子:

.. code-block:: bash

   pre-commit install

手动运行检查:

.. code-block:: bash

   pre-commit run --all-files

2. Git配置
~~~~~~~~

设置Git用户:

.. code-block:: bash

   git config --global user.name "Your Name"
   git config --global user.email "your.email@example.com"

配置Git忽略:

.. code-block:: bash

   # 已在 .gitignore 中配置
   .env
   __pycache__/
   .pytest_cache/
   *.pyc
   .venv/
   quant_system.log

3. 日志配置
~~~~~~~~~

系统使用结构化日志，默认输出到控制台和文件:

.. code-block:: python

   # 在代码中使用
   import structlog

   logger = structlog.get_logger("module.name")

   logger.info(
       "操作执行",
       user_id=123,
       action="buy",
       symbol="0700.HK",
       quantity=1000
   )

日志文件位置: `quant_system.log`

常见问题
--------

1. 虚拟环境问题
~~~~~~~~~~~~~

**问题:** 激活虚拟环境后Python版本不对

**解决:**

.. code-block:: bash

   # 删除虚拟环境
   rm -rf .venv

   # 重新创建
   python -m venv .venv
   source .venv/bin/activate

2. 依赖安装失败
~~~~~~~~~~~~~

**问题:** TA-Lib安装失败

**解决:**

.. code-block:: bash

   # Ubuntu/Debian
   sudo apt-get install build-essential
   sudo apt-get install libta-lib-dev
   pip install TA-Lib

   # Windows
   # 下载预编译的 whl 文件
   # https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib
   pip install TA_Lib-0.4.XX-cpXX-cpXXm-win_amd64.whl

3. 端口占用
~~~~~~~~~

**问题:** 端口8001被占用

**解决:**

.. code-block:: bash

   # 查看端口占用
   lsof -i :8001
   # 终止进程
   kill -9 <PID>

   # 或使用其他端口
   python complete_project_system.py --port 8002

4. 权限问题（Linux/Mac）
~~~~~~~~~~~~~~~~~~~~~

**问题:** 虚拟环境权限不足

**解决:**

.. code-block:: bash

   chmod -R 755 .venv
   chown -R $USER:$USER .venv

5. MySQL/PostgreSQL连接问题
~~~~~~~~~~~~~~~~~~~~~~~~

**问题:** 数据库连接失败

**解决:**

.. code-block:: bash

   # 确认数据库服务运行
   sudo systemctl status postgresql

   # 检查连接信息
   psql -h localhost -U username -d database

   # 更新 DATABASE_URL
   DATABASE_URL=postgresql://user:pass@localhost:5432/dbname

6. 编码问题
~~~~~~~~~

**问题:** 中文路径或文件编码问题

**解决:**

.. code-block:: bash

   # 设置环境变量
   export LANG=en_US.UTF-8
   export LC_ALL=en_US.UTF-8

   # 在代码中指定编码
   with open('file.txt', 'r', encoding='utf-8') as f:
       content = f.read()

7. Rust组件编译问题
~~~~~~~~~~~~~~~~

**问题:** Rust编译错误

**解决:**

.. code-block:: bash

   # 更新 Rust 工具链
   rustup update

   # 清理构建
   cargo clean

   # 重新编译
   maturin build --release

性能优化
--------

1. 使用开发模式
~~~~~~~~~~~~~

.. code-block:: bash

   export DEBUG=True
   export LOG_LEVEL=DEBUG
   export WORKERS=1

2. 启用热重载
~~~~~~~~~~

使用 `watchdog` 监控文件变化:

.. code-block:: bash

   pip install watchdog
   uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8001

3. 优化数据库
~~~~~~~~~~

使用SQLite进行开发，配置优化:

.. code-block:: python

   # 在 .env 中设置
   DATABASE_URL=sqlite:///./dev.db?check_same_thread=false

4. 启用缓存
~~~~~~~~

配置Redis缓存:

.. code-block:: bash

   # 启动Redis
   redis-server

   # 在 .env 中启用
   REDIS_URL=redis://localhost:6379/0
   CACHE_ENABLED=True

生产环境准备
-----------

1. 环境变量分离
~~~~~~~~~~~~~

创建不同环境的配置:

.. code-block:: bash

   .env.development
   .env.staging
   .env.production

2. 安全检查
~~~~~~~~~

.. code-block:: bash

   # 检查敏感信息泄露
   gitleaks detect --source . --report-format json --report-path leak-report.json

   # 扫描安全漏洞
   safety check

3. 性能测试
~~~~~~~~~

.. code-block:: bash

   # 使用 pytest-benchmark
   pytest tests/performance/ -v

4. 监控配置
~~~~~~~~~

.. code-block:: bash

   # 启用监控
   MONITORING_ENABLED=True
   HEALTH_CHECK_INTERVAL=30

开发建议
--------

1. **遵循代码规范**
   ~~~~~~~~~~~~~~

   * 使用 black 格式化代码
   * 遵循 PEP 8
   * 编写清晰的注释

2. **充分测试**
   ~~~~~~~~~~

   * 单元测试覆盖核心逻辑
   * 集成测试验证系统功能
   * 性能测试确保性能

3. **文档同步**
   ~~~~~~~~~~

   * 更新代码时同步更新文档
   * 保持API文档最新
   * 添加使用示例

4. **版本控制**
   ~~~~~~~~~~

   * 使用语义化版本
   * 编写清晰的提交信息
   * 保持主分支稳定

5. **持续集成**
   ~~~~~~~~~~

   * 自动化测试
   * 自动化部署
   * 代码质量检查

下一步
------

环境搭建完成后，您可以：

1. 阅读 :doc:`architecture` 了解系统设计
2. 查看 :doc:`coding-standards` 学习代码规范
3. 阅读 :doc:`testing` 了解测试方法
4. 阅读 :doc:`contribution` 了解贡献流程
5. 开始 :doc:`overview` 探索代码
