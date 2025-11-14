安装指南
========

系统要求
--------

**操作系统:**
* Windows 10/11
* Linux (Ubuntu 20.04+, CentOS 7+)
* macOS 10.15+

**Python版本:**
* Python 3.10 或更高版本
* 推荐使用 Python 3.11

**硬件要求:**
* CPU: 4核心以上
* 内存: 8GB以上（推荐16GB）
* 硬盘: 20GB可用空间
* 网络: 宽带互联网连接

**浏览器支持:**
* Chrome 90+
* Firefox 88+
* Safari 14+
* Edge 90+

安装步骤
--------

1. 克隆代码仓库
~~~~~~~~~~~~~~~

.. code-block:: bash

   git clone https://github.com/org/quant-system.git
   cd quant-system

2. 创建虚拟环境
~~~~~~~~~~~~~~~

.. code-block:: bash

   # 使用 venv
   python -m venv .venv

   # 激活虚拟环境
   # Windows
   .venv\Scripts\activate

   # Linux/Mac
   source .venv/bin/activate

3. 安装依赖
~~~~~~~~~~~

.. code-block:: bash

   # 安装核心依赖
   pip install -r requirements.txt

   # 安装文档依赖（可选）
   pip install -r docs_requirements.txt

   # 安装开发依赖（可选）
   pip install -r test_requirements.txt

4. 安装TA-Lib
~~~~~~~~~~~~~

TA-Lib是技术分析库，安装较为复杂：

**Windows:**

.. code-block:: bash

   # 下载对应的whl文件
   # 从 https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib 下载
   pip install TA_Lib-0.4.XX-cpXX-cpXXm-win_amd64.whl

**Linux:**

.. code-block:: bash

   sudo apt-get install ta-lib
   pip install TA-Lib

**macOS:**

.. code-block:: bash

   brew install ta-lib
   pip install TA-Lib

5. 配置环境变量
~~~~~~~~~~~~~~~

.. code-block:: bash

   # 复制环境变量模板
   cp .env.example .env

   # 编辑配置文件
   # 添加你的API密钥和配置

6. 验证安装
~~~~~~~~~~~

.. code-block:: bash

   python -m pytest tests/ -v

启动系统
--------

1. 开发模式启动
~~~~~~~~~~~~~~~

.. code-block:: bash

   # 启动完整系统
   python complete_project_system.py

   # 或启动简化版
   python simple_dashboard.py

2. 访问系统
~~~~~~~~~~~

启动后访问：

* **Web界面:** http://localhost:8001
* **API文档:** http://localhost:8001/docs
* **健康检查:** http://localhost:8001/api/v1/health

Docker部署
----------

使用Docker可以简化部署过程：

.. code-block:: bash

   # 构建镜像
   docker build -t quant-system .

   # 运行容器
   docker run -p 8001:8001 -v $(pwd)/.env:/app/.env quant-system

或使用docker-compose：

.. code-block:: bash

   docker-compose up -d

常见问题
--------

1. TA-Lib安装失败
~~~~~~~~~~~~~~~~~~

**问题:** 编译TA-Lib时出现错误

**解决方案:**

.. code-block:: bash

   # 安装编译工具
   # Ubuntu/Debian
   sudo apt-get install build-essential
   sudo apt-get install libta-lib-dev

   # CentOS/RHEL
   sudo yum groupinstall "Development Tools"
   sudo yum install ta-lib-devel

   # 重新安装
   pip install TA-Lib

2. 端口被占用
~~~~~~~~~~~~~

**问题:** 端口8001已被占用

**解决方案:**

.. code-block:: bash

   # 使用其他端口
   python complete_project_system.py --port 8002

3. 依赖安装慢
~~~~~~~~~~~~~

**解决方案:**

.. code-block:: bash

   # 使用国内镜像源
   pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

4. 权限问题（Linux/Mac）
~~~~~~~~~~~~~~~~~~~~~~~~

**问题:** 虚拟环境权限不足

**解决方案:**

.. code-block:: bash

   # 修复权限
   chmod -R 755 .venv

5. 中文路径问题
~~~~~~~~~~~~~~

**问题:** 项目路径包含中文导致模块加载失败

**解决方案:**

将项目放在纯英文路径下，如：

.. code-block:: text

   C:\projects\quant-system
   /home/user/projects/quant-system

升级指南
--------

从旧版本升级：

.. code-block:: bash

   # 获取最新代码
   git pull origin main

   # 更新依赖
   pip install -r requirements.txt --upgrade

   # 运行数据库迁移（如有）
   python manage.py migrate

   # 重启服务
   python complete_project_system.py

卸载
----

完全卸载系统：

.. code-block:: bash

   # 停止所有服务
   pkill -f "python.*complete_project_system"

   # 删除虚拟环境
   rm -rf .venv

   # 删除项目目录
   cd ..
   rm -rf quant-system

验证卸载：

.. code-block:: bash

   # 检查端口
   lsof -i :8001

   # 应该无输出
