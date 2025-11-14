代码规范
========

概述
----

港股量化交易系统遵循以下代码规范：

* **PEP 8** - Python代码风格指南
* **Google风格** - 文档字符串格式
* **Type Hints** - 类型提示
* **SOLID原则** - 面向对象设计
* **Clean Architecture** - 架构设计

代码风格
--------

1. 格式化
~~~~~~~~

使用 **black** 自动格式化代码:

.. code-block:: bash

   # 格式化所有代码
   black src/ tests/

   # 检查格式但不修改
   black --check src/ tests/

**最大行长度:** 88字符 (black默认)

**示例:**

.. code-block:: python

   # 好的代码
   def calculate_kdj(
       high: pd.Series,
       low: pd.Series,
       close: pd.Series,
       k_period: int = 9,
       d_period: int = 3,
   ) -> tuple[pd.Series, pd.Series]:
       """计算KDJ指标

       Args:
           high: 最高价序列
           low: 最低价序列
           close: 收盘价序列
           k_period: K值计算周期
           d_period: D值平滑周期

       Returns:
           (K值, D值)
       """
       # 计算RSV (未成熟随机值)
       rsv = (close - low.rolling(k_period).min()) / (
           high.rolling(k_period).max() - low.rolling(k_period).min()
       )
       # 计算K值
       k = rsv.ewm(alpha=1 / d_period).mean()
       # 计算D值
       d = k.ewm(alpha=1 / d_period).mean()

       return k, d

2. 导入顺序
~~~~~~~~~~

使用 **isort** 排序导入:

.. code-block:: bash

   isort src/ tests/

**导入顺序:**

.. code-block:: python

   # 1. 标准库
   import os
   import sys
   from typing import Dict, List
   from datetime import datetime

   # 2. 第三方库
   import pandas as pd
   import numpy as np
   import structlog
   from fastapi import APIRouter

   # 3. 本地导入
   from src.data_adapters import BaseAdapter
   from src.backtest import BacktestEngine
   from .models import Trade

3. 命名规范
~~~~~~~~~~

**变量和函数:** 小写字母加下划线

.. code-block:: python

   # 好的命名
   total_return = 0.15
   max_drawdown = -0.05
   calculate_sharpe_ratio()
   fetch_market_data()

   # 避免
   TotalReturn = 0.15
   Max_Drawdown = -0.05
   calculateSharpeRatio()  # 驼峰命名

**类名:** 驼峰命名法

.. code-block:: python

   class QuantitativeAnalyst:
       pass

   class BacktestEngine:
       pass

   class KDJStrategy:
       pass

**常量:** 全大写加下划线

.. code-block:: python

   MAX_WORKERS = 8
   DEFAULT_CACHE_TTL = 3600
   API_VERSION = "v1"

**私有成员:** 前置单下划线

.. code-block:: python

   class Agent:
       def __init__(self):
           self._private_var = "private"
           self.public_var = "public"

       def _private_method(self):
           pass

**魔术方法:** 双下划线包围

.. code-block:: python

   class MyClass:
       def __init__(self):
           self.value = 0

       def __str__(self):
           return f"MyClass(value={self.value})"

文档字符串
----------

使用 **Google风格** 文档字符串:

1. 函数文档字符串
~~~~~~~~~~~~~~~~

.. code-block:: python

   def calculate_rsi(
       close_prices: pd.Series, period: int = 14
   ) -> pd.Series:
       """计算相对强弱指数 (RSI)

       RSI是一种动量指标，用于衡量价格变动的速度和变化幅度。
       RSI值在0-100之间，通常认为70以上为超买，30以下为超卖。

       Args:
           close_prices: 收盘价时间序列
           period: RSI计算周期，默认14

       Returns:
           RSI值时间序列

       Raises:
           ValueError: 当period小于2时

       Examples:
           >>> prices = pd.Series([1, 2, 3, 4, 5, 4, 3, 2, 1])
           >>> rsi = calculate_rsi(prices, period=3)
           >>> rsi.iloc[-1]
           20.0

       Note:
           该函数使用指数移动平均计算RSI，公式为:
           RSI = 100 - (100 / (1 + RS))
           其中 RS = EMA(涨幅, period) / EMA(跌幅, period)
       """
       if period < 2:
           raise ValueError("period必须大于等于2")

       # 计算价格变化
       delta = close_prices.diff()

       # 分离涨幅和跌幅
       gains = delta.where(delta > 0, 0)
       losses = -delta.where(delta < 0, 0)

       # 计算指数移动平均
       avg_gains = gains.ewm(alpha=1 / period).mean()
       avg_losses = losses.ewm(alpha=1 / period).mean()

       # 计算RS
       rs = avg_gains / avg_losses

       # 计算RSI
       rsi = 100 - (100 / (1 + rs))

       return rsi

2. 类文档字符串
~~~~~~~~~~~~~~

.. code-block:: python

   class KDJStrategy:
       """KDJ随机指标策略

       该策略基于KDJ指标进行交易决策：
       - K线上穿D线且D线低于超卖阈值时买入
       - K线下穿D线且D线高于超买阈值时卖出

       Attributes:
           k_period: K值计算周期
           d_period: D值平滑周期
           oversold: 超卖阈值
           overbought: 超买阈值

       Examples:
           >>> strategy = KDJStrategy(
           ...     k_period=9,
           ...     d_period=3,
           ...     oversold=20,
           ...     overbought=80
           ... )
           >>> data = fetch_data("0700.HK")
           >>> signals = strategy.generate_signals(data)
       """

       def __init__(
           self,
           k_period: int = 9,
           d_period: int = 3,
           oversold: float = 20,
           overbought: float = 80,
       ):
           self.k_period = k_period
           self.d_period = d_period
           self.oversold = oversold
           self.overbought = overbought

3. 模块文档字符串
~~~~~~~~~~~~~~~

.. code-block:: python

   """技术指标策略模块

   该模块提供各种技术指标的交易策略实现，包括：
   - 趋势跟踪策略 (MA, MACD)
   - 动量策略 (RSI, KDJ)
   - 波动率策略 (Bollinger Bands, ATR)

   所有策略都继承自 BaseStrategy 基类，实现统一的接口。

   Attributes:
       VERSION: 策略版本号

   Examples:
       >>> from src.strategies import KDJStrategy
       >>> strategy = KDJStrategy()
       >>> signals = strategy.run(data)
   """

   VERSION = "1.0.0"

类型提示
--------

1. 基本类型提示
~~~~~~~~~~~~~~

.. code-block:: python

   from typing import List, Dict, Optional, Union, Tuple

   def process_data(
       data: List[Dict[str, Union[int, float]]],
       threshold: Optional[float] = None,
   ) -> Tuple[List[Dict], int]:
       """处理数据

       Args:
           data: 要处理的数据列表
           threshold: 过滤阈值，可选

       Returns:
           (处理后的数据, 处理数量)
       """
       if threshold is not None:
           filtered = [d for d in data if d["value"] > threshold]
       else:
           filtered = data

       return filtered, len(filtered)

2. 复杂类型提示
~~~~~~~~~~~~~

.. code-block:: python

   from typing import Protocol, Generic, TypeVar

   T = TypeVar("T")

   class DataAdapter(Protocol):
       """数据适配器协议"""

       async def fetch_data(
           self, symbol: str, start_date: str, end_date: str
       ) -> Dict[str, pd.DataFrame]:
           """获取市场数据

           Args:
               symbol: 股票代码
               start_date: 开始日期
               end_date: 结束日期

           Returns:
               包含各字段数据的字典
           """
           ...

3. 泛型类型
~~~~~~~~~

.. code-block:: python

   from typing import TypeVar, Generic

   T = TypeVar("T")

   class BaseCache(Generic[T]):
       """基础缓存类

       Type Parameters:
           T: 缓存数据类型
       """

       def __init__(self, max_size: int = 1000):
           self._cache: Dict[str, T] = {}
           self.max_size = max_size

       def get(self, key: str) -> Optional[T]:
           return self._cache.get(key)

       def set(self, key: str, value: T) -> None:
           self._cache[key] = value

4. 联合类型和类型别名
~~~~~~~~~~~~~~~~~

.. code-block:: python

   from typing import Literal

   StrategyType = Literal["kdj", "rsi", "macd", "ma", "bb"]

   MarketData = Dict[str, Union[int, float, str]]

   def run_strategy(
       strategy: StrategyType, data: MarketData
   ) -> Dict[str, float]:
       ...

错误处理
--------

1. 使用特定异常
~~~~~~~~~~~~~

.. code-block:: python

   class StrategyError(Exception):
       """策略执行错误"""
       pass

   class InsufficientDataError(StrategyError):
       """数据不足错误"""
       pass

   class InvalidParameterError(StrategyError):
       """参数错误"""
       pass

   def calculate_indicator(data: pd.DataFrame, period: int) -> pd.Series:
       if len(data) < period:
           raise InsufficientDataError(
               f"数据长度 {len(data)} 小于所需周期 {period}"
           )
       if period <= 0:
           raise InvalidParameterError(f"周期必须大于0，实际为 {period}")

       return data.rolling(period).mean()

2. 记录详细日志
~~~~~~~~~~~~~

.. code-block:: python

   import structlog

   logger = structlog.get_logger(__name__)

   def run_backtest(strategy: BaseStrategy, data: pd.DataFrame) -> dict:
       try:
           logger.info(
               "开始回测",
               strategy=strategy.__class__.__name__,
               data_points=len(data),
               start_date=str(data.index[0]),
               end_date=str(data.index[-1]),
           )

           result = strategy.backtest(data)

           logger.info(
               "回测完成",
               total_return=result["total_return"],
               trades_count=result["trades_count"],
           )

           return result

       except Exception as e:
           logger.error(
               "回测失败",
               error=str(e),
               error_type=type(e).__name__,
               exc_info=True,
           )
           raise

3. 使用上下文管理器
~~~~~~~~~~~~~~~

.. code-block:: python

   from contextlib import contextmanager

   @contextmanager
       def measure_time(name: str):
       """测量执行时间"""
       start = time.time()
       logger.info(f"{name} 开始")
       try:
           yield
       finally:
           duration = time.time() - start
           logger.info(f"{name} 完成", duration=duration)

   # 使用
   with measure_time("策略回测"):
       result = backtest_strategy(data)

代码组织
--------

1. 模块结构
~~~~~~~~~~

.. code-block:: python

   """模块描述

   详细说明模块功能、使用方法等。
   """

   from __future__ import annotations

   import logging
   from typing import List, Optional

   from .submodule import helper_function
   from .models import DataModel

   __version__ = "1.0.0"
   __all__ = ["public_function", "DataModel"]

   logger = logging.getLogger(__name__)

   def public_function(param: str) -> bool:
       """公开函数

       Args:
           param: 参数说明

       Returns:
           返回值说明
       """
       pass

2. 导入最佳实践
~~~~~~~~~~~~~

.. code-block:: python

   # ✅ 推荐
   from src.strategies import KDJStrategy
   from src.backtest import BacktestEngine
   from src.data_adapters.base import BaseAdapter

   # ❌ 避免
   import src
   from src.strategies.kdj import KDJStrategy as K  # 避免别名

3. 包结构
~~~~~~~~

每个包应该有 `__init__.py`:

.. code-block:: python

   """数据适配器包

   提供统一的数据源访问接口。

   Examples:
       >>> from src.data_adapters import HKEXAdapter
       >>> adapter = HKEXAdapter()
       >>> data = await adapter.fetch("0700.HK", "2020-01-01")
   """

   from .base_adapter import BaseAdapter
   from .hkex_adapter import HKEXAdapter
   from .yahoo_finance_adapter import YahooFinanceAdapter
   from .alpha_vantage_adapter import AlphaVantageAdapter

   __all__ = [
       "BaseAdapter",
       "HKEXAdapter",
       "YahooFinanceAdapter",
       "AlphaVantageAdapter",
   ]

测试规范
--------

1. 测试文件命名
~~~~~~~~~~~~~

.. code-block:: text

   测试模块: tests/test_backtest.py
   测试类:   tests/test_strategies.py::TestKDJStrategy
   测试函数: tests/test_backtest.py::test_run_backtest

2. 测试结构
~~~~~~~~~

.. code-block:: python

   import pytest
   from src.strategies import KDJStrategy

   class TestKDJStrategy:
       """KDJ策略测试"""

       @pytest.fixture
       def sample_data(self):
           """测试数据"""
           return pd.DataFrame({
               "high": [10, 12, 13, 12, 14],
               "low": [8, 9, 10, 9, 11],
               "close": [9, 11, 12, 10, 13],
           })

       def test_calculate_kdj(self, sample_data):
           """测试KDJ计算"""
           strategy = KDJStrategy()
           k, d = strategy._calculate_kdj(sample_data)

           assert len(k) == len(sample_data)
           assert len(d) == len(sample_data)
           assert 0 <= k.iloc[-1] <= 100
           assert 0 <= d.iloc[-1] <= 100

       def test_invalid_parameters(self):
           """测试无效参数"""
           with pytest.raises(ValueError):
               KDJStrategy(period=0)

       @pytest.mark.asyncio
       async def test_async_method(self):
           """测试异步方法"""
           strategy = KDJStrategy()
           result = await strategy.async_process()
           assert result is not None

配置管理
--------

1. 使用Pydantic Settings
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from pydantic_settings import BaseSettings
   from pydantic import Field, validator

   class Settings(BaseSettings):
       """应用配置"""

       # API配置
       API_HOST: str = "0.0.0.0"
       API_PORT: int = Field(8001, ge=1, le=65535)

       # 数据库配置
       DATABASE_URL: str = Field(..., min_length=1)

       # 日志配置
       LOG_LEVEL: str = "INFO"

       @validator("LOG_LEVEL")
       def validate_log_level(cls, v):
           valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
           if v.upper() not in valid_levels:
               raise ValueError(f"无效的日志级别: {v}")
           return v.upper()

       class Config:
           env_file = ".env"
           case_sensitive = False

2. 环境特定配置
~~~~~~~~~~~~~

.. code-block:: python

   class DevelopmentSettings(Settings):
       """开发环境配置"""
       DEBUG: bool = True
       LOG_LEVEL: str = "DEBUG"

   class ProductionSettings(Settings):
       """生产环境配置"""
       DEBUG: bool = False
       LOG_LEVEL: str = "WARNING"

   def get_settings() -> Settings:
       env = os.getenv("ENV", "development")
       if env == "production":
           return ProductionSettings()
       return DevelopmentSettings()

性能优化
--------

1. 使用类型提示优化性能
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # ✅ 使用类型提示，利于缓存优化
   def process_data(data: pd.DataFrame) -> pd.DataFrame:
       return data.rolling(20).mean()

2. 避免在循环中创建对象
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # ❌ 避免
   for i in range(1000):
       logger.info(f"Processing {i}")  # 每次都创建字符串

   # ✅ 推荐
   log_msg = "Processing"
   for i in range(1000):
       logger.info(log_msg, i=i)

3. 使用生成器处理大数据
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # ✅ 推荐
   def process_large_dataset(data: pd.DataFrame) -> pd.Series:
       for chunk in pd.read_csv("large_file.csv", chunksize=10000):
           yield chunk.mean()

Git提交规范
-----------

使用 **约定式提交** 格式:

.. code-block:: text

   <type>[optional scope]: <description>

   [optional body]

   [optional footer(s)]

**类型 (type):**

* feat: 新功能
* fix: 修复bug
* docs: 文档更新
* style: 代码格式调整
* refactor: 代码重构
* test: 测试相关
* chore: 构建/工具相关

**示例:**

.. code-block:: text

   feat(backtest): 添加MACD策略实现

   新增MACD技术指标策略，支持参数优化和回测。
   包括快线、慢线、信号线计算和交叉信号生成。

   Closes #123

安全规范
--------

1. 输入验证
~~~~~~~~~

.. code-block:: python

   from pydantic import BaseModel, validator

   class BacktestRequest(BaseModel):
       symbol: str
       start_date: str
       end_date: str

       @validator("symbol")
       def validate_symbol(cls, v):
           if not re.match(r"^\d{4}\.HK$", v):
               raise ValueError("股票代码格式错误")
           return v

       @validator("start_date", "end_date")
       def validate_date(cls, v):
           try:
               datetime.strptime(v, "%Y-%m-%d")
           except ValueError:
               raise ValueError("日期格式应为YYYY-MM-DD")
           return v

2. 避免安全漏洞
~~~~~~~~~~~~~

.. code-block:: python

   # ❌ 避免
   query = f"SELECT * FROM users WHERE id = {user_id}"
   # SQL注入风险!

   # ✅ 使用参数化查询
   query = "SELECT * FROM users WHERE id = %s"
   cursor.execute(query, (user_id,))

   # ❌ 避免
   eval(user_input)  # 代码注入风险!

   # ✅ 验证输入
   allowed_names = ["add", "subtract", "multiply"]
   if user_input not in allowed_names:
       raise ValueError("不支持的操作")

3. 密钥管理
~~~~~~~~~

.. code-block:: python

   # ❌ 避免
   API_KEY = "hardcoded_key_123456"

   # ✅ 从环境变量读取
   import os
   API_KEY = os.getenv("API_KEY")
   if not API_KEY:
       raise ValueError("API_KEY环境变量未设置")

工具和配置
----------

1. .flake8 配置
~~~~~~~~~~~~~~

.. code-block:: ini

   [flake8]
   max-line-length = 88
   extend-ignore = E203, W503
   exclude = .git, __pycache__, .venv, build, dist

2. .mypy 配置
~~~~~~~~~~~

.. code-block:: ini

   [mypy]
   python_version = 3.10
   warn_return_any = True
   warn_unused_configs = True
   disallow_untyped_defs = True
   disallow_incomplete_defs = True
   check_untyped_defs = True
   disallow_untyped_decorators = True
   no_implicit_optional = True
   warn_redundant_casts = True
   warn_unused_ignores = True
   warn_no_return = True
   warn_unreachable = True
   strict_equality = True

3. pyproject.toml
~~~~~~~~~~~~~~~

.. code-block:: toml

   [tool.black]
   line-length = 88
   target-version = ['py310']

   [tool.isort]
   profile = "black"

   [tool.pytest.ini_options]
   minversion = "6.0"
   addopts = "-ra -q --strict-markers"
   testpaths = ["tests"]
   asyncio_mode = "auto"

检查工具
--------

运行所有检查:

.. code-block:: bash

   # 格式化代码
   black src/ tests/

   # 排序导入
   isort src/ tests/

   # 代码风格检查
   flake8 src/ tests/

   # 类型检查
   mypy src/

   # 运行测试
   pytest tests/ -v

   # 完整检查
   pre-commit run --all-files

CI/CD集成
---------

在 `.github/workflows/ci.yml`:

.. code-block:: yaml

   name: CI

   on: [push, pull_request]

   jobs:
     test:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         - name: Set up Python
           uses: actions/setup-python@v4
           with:
             python-version: '3.11'
         - name: Install dependencies
           run: |
             pip install -r requirements.txt
             pip install -r test_requirements.txt
         - name: Run linters
           run: |
             black --check src/ tests/
             flake8 src/ tests/
             mypy src/
         - name: Run tests
           run: pytest tests/ -v --cov=src
