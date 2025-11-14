测试指南
========

概述
----

测试是保证代码质量的重要手段。港股量化交易系统要求所有代码必须有充分的测试覆盖。

测试类型
--------

1. **单元测试** (Unit Tests)
   ~~~~~~~~~~~~~

   测试单个函数或方法的功能

2. **集成测试** (Integration Tests)
   ~~~~~~~~~~~~~~~~

   测试多个模块之间的交互

3. **功能测试** (Functional Tests)
   ~~~~~~~~~~~~~

   测试完整的用户场景

4. **性能测试** (Performance Tests)
   ~~~~~~~~~~~~~

   测试系统性能和响应时间

5. **端到端测试** (E2E Tests)
   ~~~~~~~~~~~

   测试完整的用户流程

测试框架
--------

**主要工具:**

* **pytest** - 测试运行器和断言库
* **pytest-asyncio** - 异步测试支持
* **pytest-cov** - 代码覆盖率
* **pytest-mock** - Mock对象
* **pytest-xdist** - 并行测试
* **Hypothesis** - 属性测试
* **factory_boy** - 测试数据生成

项目结构
--------

.. code-block::

   tests/
   ├── __init__.py
   ├── conftest.py              # pytest配置和fixture
   ├── unit/                    # 单元测试
   │   ├── test_strategies/
   │   │   ├── __init__.py
   │   │   ├── test_kdj.py
   │   │   ├── test_rsi.py
   │   │   └── test_macd.py
   │   ├── test_backtest/
   │   │   ├── __init__.py
   │   │   └── test_engine.py
   │   └── test_agents/
   │       ├── __init__.py
   │       └── test_base_agent.py
   ├── integration/             # 集成测试
   │   ├── test_api/
   │   │   ├── __init__.py
   │   │   ├── test_health.py
   │   │   └── test_backtest_api.py
   │   └── test_data_flow/
   │       └── __init__.py
   ├── performance/             # 性能测试
   │   ├── __init__.py
   │   ├── test_backtest_speed.py
   │   └── test_memory_usage.py
   └── fixtures/                # 共享测试数据
       ├── __init__.py
       ├── market_data.py
       └── strategies.py

测试配置
--------

**pytest.ini:**

.. code-block:: ini

   [tool:pytest]
   minversion = 6.0
   addopts =
       -ra
       -q
       --strict-markers
       --strict-config
       --cov=src
       --cov-report=html
       --cov-report=term-missing
       --cov-fail-under=80
   testpaths = tests
   python_files = test_*.py *_test.py
   python_classes = Test*
   python_functions = test_*
   asyncio_mode = auto
   markers =
       unit: Unit tests
       integration: Integration tests
       performance: Performance tests
       slow: Slow running tests
       api: API tests

**conftest.py:**

.. code-block:: python

   """pytest全局配置和fixture"""

   import pytest
   import pandas as pd
   import asyncio
   from typing import AsyncGenerator

   from src.backtest import BacktestEngine
   from src.strategies import KDJStrategy
   from src.data_adapters import HKEXAdapter

   @pytest.fixture(scope="session")
   def event_loop():
       """创建事件循环"""
       loop = asyncio.get_event_loop_policy().new_event_loop()
       yield loop
       loop.close()

   @pytest.fixture
   def sample_market_data():
       """示例市场数据"""
       dates = pd.date_range("2020-01-01", periods=1000, freq="D")
       return pd.DataFrame(
           {
               "open": 100 + pd.cumsum(pd.random.randn(1000) * 0.5),
               "high": 100 + pd.cumsum(pd.random.randn(1000) * 0.5) + 2,
               "low": 100 + pd.cumsum(pd.random.randn(1000) * 0.5) - 2,
               "close": 100 + pd.cumsum(pd.random.randn(1000) * 0.5),
               "volume": pd.random.randint(1000000, 10000000, 1000),
           },
           index=dates,
       )

   @pytest.fixture
   def kdj_strategy():
       """KDJ策略实例"""
       return KDJStrategy(
           k_period=9,
           d_period=3,
           oversold=20,
           overbought=80,
       )

   @pytest.fixture
   def backtest_engine():
       """回测引擎实例"""
       return BacktestEngine(initial_capital=100000)

编写测试
--------

1. 基础单元测试
~~~~~~~~~~~~~

.. code-block:: python

   import pytest
   import pandas as pd
   from src.strategies import KDJStrategy

   class TestKDJStrategy:
       """KDJ策略测试"""

       @pytest.fixture
       def sample_data(self):
           """测试数据"""
           return pd.DataFrame(
               {
                   "high": [10, 12, 13, 12, 14, 13, 11, 9, 8, 10],
                   "low": [8, 9, 10, 9, 11, 10, 8, 7, 6, 8],
                   "close": [9, 11, 12, 10, 13, 11, 9, 8, 7, 9],
               }
           )

       def test_init(self):
           """测试初始化"""
           strategy = KDJStrategy(
               k_period=9,
               d_period=3,
               oversold=20,
               overbought=80,
           )
           assert strategy.k_period == 9
           assert strategy.d_period == 3
           assert strategy.oversold == 20
           assert strategy.overbought == 80

       def test_calculate_kdj(self, sample_data):
           """测试KDJ计算"""
           strategy = KDJStrategy()
           k, d = strategy._calculate_kdj(sample_data)

           # 验证长度
           assert len(k) == len(sample_data)
           assert len(d) == len(sample_data)

           # 验证范围
           assert k.min() >= 0
           assert k.max() <= 100
           assert d.min() >= 0
           assert d.max() <= 100

           # 验证K值 >= D值（计算方式决定）
           assert k.iloc[8] == d.iloc[8]  # 初始值相同
           assert k.iloc[9] == d.iloc[9]

       def test_invalid_parameters(self):
           """测试无效参数"""
           with pytest.raises(ValueError):
               KDJStrategy(k_period=0)

           with pytest.raises(ValueError):
               KDJStrategy(d_period=0)

           with pytest.raises(ValueError):
               KDJStrategy(oversold=90, overbought=80)

       @pytest.mark.parametrize(
           "k_period,d_period",
           [(9, 3), (14, 5), (5, 3)],
       )
       def test_different_periods(self, k_period, d_period, sample_data):
           """测试不同周期参数"""
           strategy = KDJStrategy(k_period=k_period, d_period=d_period)
           k, d = strategy._calculate_kdj(sample_data)

           assert len(k) == len(sample_data)
           assert len(d) == len(sample_data)

       def test_insufficient_data(self):
           """测试数据不足"""
           strategy = KDJStrategy()
           # 数据少于KDJ周期
           data = pd.DataFrame(
               {
                   "high": [10, 11],
                   "low": [9, 10],
                   "close": [9.5, 10.5],
               }
           )

           with pytest.raises(ValueError):
               strategy._calculate_kdj(data)

2. 异步测试
~~~~~~~~~

.. code-block:: python

   import pytest
   from src.data_adapters import HKEXAdapter

   class TestHKEXAdapter:
       """港交所适配器测试"""

       @pytest.mark.asyncio
       async def test_fetch_data(self):
           """测试获取数据"""
           adapter = HKEXAdapter()
           data = await adapter.fetch_data(
               symbol="0700.hk",
               start_date="2020-01-01",
               end_date="2020-01-31",
           )

           assert isinstance(data, pd.DataFrame)
           assert not data.empty
           assert set(data.columns) >= {"open", "high", "low", "close", "volume"}

       @pytest.mark.asyncio
       async def test_invalid_symbol(self):
           """测试无效股票代码"""
           adapter = HKEXAdapter()

           with pytest.raises(ValueError):
               await adapter.fetch_data(
                   symbol="invalid",
                   start_date="2020-01-01",
                   end_date="2020-01-31",
               )

       @pytest.mark.asyncio
       async def test_api_error(self, mock_httpx_get):
           """测试API错误处理"""
           import httpx

           adapter = HKEXAdapter()

           # 模拟API错误
           mock_httpx_get.side_effect = httpx.HTTPError("API错误")

           with pytest.raises(Exception):
               await adapter.fetch_data(
                   symbol="0700.hk",
                   start_date="2020-01-01",
                   end_date="2020-01-31",
               )

3. Mock测试
~~~~~~~~~

.. code-block:: python

   import pytest
   from unittest.mock import Mock, patch, AsyncMock
   from src.backtest import BacktestEngine
   from src.strategies import BaseStrategy

   class TestBacktestEngine:
       """回测引擎测试"""

       def test_run_backtest(self, sample_market_data, kdj_strategy):
           """测试运行回测"""
           engine = BacktestEngine(initial_capital=100000)

           result = engine.run(kdj_strategy, sample_market_data)

           assert isinstance(result, dict)
           assert "total_return" in result
           assert "trades_count" in result
           assert "final_value" in result
           assert result["initial_capital"] == 100000

       @patch("src.backtest.BacktestEngine._calculate_performance")
       def test_performance_calculation(self, mock_calc, sample_market_data, kdj_strategy):
           """测试性能计算"""
           mock_calc.return_value = {
               "total_return": 0.15,
               "sharpe_ratio": 1.2,
               "max_drawdown": -0.05,
           }

           engine = BacktestEngine()
           result = engine.run(kdj_strategy, sample_market_data)

           mock_calc.assert_called_once()
           assert result["total_return"] == 0.15

       def test_with_mock_strategy(self, sample_market_data):
           """使用模拟策略测试"""
           # 创建模拟策略
           mock_strategy = Mock(spec=BaseStrategy)
           mock_strategy.generate_signals.return_value = pd.Series(
               [0, 1, -1, 0, 1], index=sample_market_data.index[:5]
           )

           engine = BacktestEngine()
           result = engine.run(mock_strategy, sample_market_data)

           mock_strategy.generate_signals.assert_called_once_with(
               sample_market_data
           )

4. 参数化测试
~~~~~~~~~~~

.. code-block:: python

   import pytest
   from src.strategies import RSIStrategy

   class TestRSIStrategy:
       """RSI策略测试"""

       @pytest.mark.parametrize(
           "period,oversold,overbought",
           [
               (14, 30, 70),
               (10, 20, 80),
               (20, 25, 75),
           ],
       )
       def test_different_parameters(self, period, oversold, overbought, sample_data):
           """测试不同参数组合"""
           strategy = RSIStrategy(
               period=period,
               oversold=oversold,
               overbought=overbought,
           )

           signals = strategy.generate_signals(sample_data)

           assert len(signals) == len(sample_data)
           assert signals.isin([-1, 0, 1]).all()

       @pytest.mark.parametrize(
           "price_sequence,expected_signal",
           [
               ([1, 2, 3, 2, 1], -1),  # 超买后下跌
               ([1, 0.5, 0.2, 0.5, 1], 1),  # 超卖后上涨
               ([1, 1, 1, 1, 1], 0),  # 横盘
           ],
       )
       def test_signal_generation(self, price_sequence, expected_signal, sample_data):
           """测试信号生成"""
           # 使用指定的收盘价序列
           data = sample_data.copy()
           data["close"] = price_sequence[: len(data)]

           strategy = RSIStrategy()
           signals = strategy.generate_signals(data)

           # 检查最后一个信号
           assert signals.iloc[-1] == expected_signal

5. 属性测试 (使用Hypothesis)
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import pytest
   from hypothesis import given, strategies as st
   from src.strategies import MAStrategy

   class TestMAStrategy:
       """MA策略属性测试"""

       @given(
           short_period=st.integers(min_value=5, max_value=50),
           long_period=st.integers(min_value=20, max_value=200),
       )
       def test_golden_cross_always_followed_by_death_cross(self, short_period, long_period):
           """黄金交叉后必然出现死亡交叉的测试（假设性测试）"""
           if short_period >= long_period:
               # 跳过无效参数
               return

           strategy = MAStrategy(short_period=short_period, long_period=long_period)

           # 生成随机价格数据
           prices = [100 + i + (i % 3 - 1) * 0.1 for i in range(200)]
           data = pd.DataFrame({"close": prices})

           signals = strategy.generate_signals(data)

           # 验证信号的有效性
           assert signals.isin([-1, 0, 1]).all()

   # 属性测试示例
   @given(st.lists(st.floats(min_value=0.1, max_value=1000)))
   def test_calculate_returns(prices):
       """测试收益率计算"""
       from src.backtest.utils import calculate_returns

       if len(prices) < 2:
           return  # 跳过

       returns = calculate_returns(pd.Series(prices))
       assert len(returns) == len(prices) - 1
       # 验证没有无穷大或NaN
       assert returns.replace([float("inf"), float("-inf")], 0).isna().sum() == 0

6. 集成测试
~~~~~~~~~

.. code-block:: python

   import pytest
   from fastapi.testclient import TestClient
   from src.api.main import app

   class TestBacktestAPI:
       """回测API集成测试"""

       @pytest.fixture
       def client(self):
           """测试客户端"""
           return TestClient(app)

       def test_health_endpoint(self, client):
           """测试健康检查端点"""
           response = client.get("/api/v1/health")
           assert response.status_code == 200
           assert "status" in response.json()

       def test_run_backtest_endpoint(self, client):
           """测试运行回测端点"""
           payload = {
               "symbol": "0700.HK",
               "start_date": "2020-01-01",
               "end_date": "2020-01-31",
               "strategy": "kdj",
           }

           response = client.post("/api/v1/backtest/run", json=payload)

           assert response.status_code == 200
           data = response.json()
           assert "total_return" in data
           assert "strategy" in data
           assert data["strategy"] == "kdj"

       def test_invalid_request(self, client):
           """测试无效请求"""
           payload = {
               "symbol": "invalid",
               "start_date": "invalid-date",
           }

           response = client.post("/api/v1/backtest/run", json=payload)

           assert response.status_code == 422  # Validation error

7. 性能测试
~~~~~~~~~

.. code-block:: python

   import pytest
   import time
   from src.backtest import BacktestEngine
   from src.strategies import KDJStrategy

   class TestBacktestPerformance:
       """回测性能测试"""

       @pytest.mark.performance
       def test_backtest_speed(self, sample_market_data):
           """测试回测速度"""
           strategy = KDJStrategy()
           engine = BacktestEngine()

           start_time = time.time()
           result = engine.run(strategy, sample_market_data)
           end_time = time.time()

           duration = end_time - start_time

           # 应该在1秒内完成
           assert duration < 1.0
           assert result is not None

       @pytest.mark.performance
       def test_large_dataset(self):
           """测试大数据集处理"""
           # 生成更大的数据集
           dates = pd.date_range("2020-01-01", periods=10000, freq="H")
           data = pd.DataFrame(
               {
                   "open": 100 + pd.cumsum(pd.random.randn(10000) * 0.1),
                   "high": 100 + pd.cumsum(pd.random.randn(10000) * 0.1) + 0.5,
                   "low": 100 + pd.cumsum(pd.random.randn(10000) * 0.1) - 0.5,
                   "close": 100 + pd.cumsum(pd.random.randn(10000) * 0.1),
                   "volume": pd.random.randint(10000, 100000, 10000),
               },
               index=dates,
           )

           strategy = KDJStrategy()
           engine = BacktestEngine()

           start_time = time.time()
           result = engine.run(strategy, data)
           end_time = time.time()

           duration = end_time - start_time

           # 应该在合理时间内完成
           assert duration < 10.0
           assert result["trades_count"] >= 0

运行测试
--------

1. 运行所有测试
~~~~~~~~~~~~~

.. code-block:: bash

   # 运行所有测试
   pytest

   # 详细输出
   pytest -v

   # 显示本地变量
   pytest -l

2. 运行特定测试
~~~~~~~~~~~~~

.. code-block:: bash

   # 运行特定文件
   pytest tests/unit/test_strategies/test_kdj.py

   # 运行特定测试类
   pytest tests/unit/test_strategies/test_kdj.py::TestKDJStrategy

   # 运行特定测试方法
   pytest tests/unit/test_strategies/test_kdj.py::TestKDJStrategy::test_calculate_kdj

   # 按标记运行
   pytest -m unit
   pytest -m "not slow"
   pytest -m "integration"

3. 并行运行
~~~~~~~~~

.. code-block:: bash

   # 使用所有CPU核心
   pytest -n auto

   # 指定进程数
   pytest -n 4

   # 基于CPU数量
   pytest -n logical

4. 生成覆盖率报告
~~~~~~~~~~~~~~~

.. code-block:: bash

   # 生成HTML报告
   pytest --cov=src --cov-report=html

   # 在终端显示报告
   pytest --cov=src --cov-report=term-missing

   # 包含测试文件
   pytest --cov=src --cov-report=term-missing --cov=tests

   # 最低覆盖率要求
   pytest --cov=src --cov-fail-under=80

5. 性能测试
~~~~~~~~~

.. code-block:: bash

   # 运行性能测试
   pytest tests/performance/ -v

   # 使用pytest-benchmark
   pytest tests/performance/ --benchmark-only

6. 测试过滤
~~~~~~~~~

.. code-block:: bash

   # 关键词匹配
   pytest -k "kdj"

   # 排除
   pytest -k "not slow"

   # 或条件
   pytest -k "kdj or rsi"

测试数据管理
------------

1. 使用fixture
~~~~~~~~~~~~~

.. code-block:: python

   @pytest.fixture
   def market_data_factory():
       """市场数据工厂"""
       def _create_data(length=100, start_price=100):
           dates = pd.date_range("2020-01-01", periods=length, freq="D")
           return pd.DataFrame(
               {
                   "open": start_price + pd.cumsum(pd.random.randn(length) * 0.5),
                   "high": start_price + pd.cumsum(pd.random.randn(length) * 0.5) + 2,
                   "low": start_price + pd.cumsum(pd.random.randn(length) * 0.5) - 2,
                   "close": start_price + pd.cumsum(pd.random.randn(length) * 0.5),
                   "volume": pd.random.randint(1000000, 10000000, length),
               },
               index=dates,
           )
       return _create_data

   # 使用
   def test_with_factory(market_data_factory):
       data = market_data_factory(length=500, start_price=50)
       ...

2. 使用数据驱动
~~~~~~~~~~~~~

.. code-block:: python

   @pytest.fixture
   def backtest_scenarios():
       """回测场景数据"""
       return [
           {
               "name": "牛市场景",
               "prices": list(range(100, 200, 2)),
               "expected_min_trades": 10,
           },
           {
               "name": "熊市场景",
               "prices": list(range(100, 0, -2)),
               "expected_min_trades": 5,
           },
           {
               "name": "震荡市",
               "prices": [100] * 50 + list(range(100, 120)) + [120] * 50,
               "expected_min_trades": 0,
           },
       ]

   @pytest.mark.parametrize("scenario", backtest_scenarios)
   def test_different_markets(scenario, market_data_factory):
       """测试不同市场场景"""
       data = market_data_factory()
       data["close"] = scenario["prices"][: len(data)]

       strategy = MAStrategy(short_period=10, long_period=30)
       engine = BacktestEngine()
       result = engine.run(strategy, data)

       assert result["trades_count"] >= scenario["expected_min_trades"]

CI/CD集成
--------

.github/workflows/test.yml:

.. code-block:: yaml

   name: Tests

   on: [push, pull_request]

   jobs:
     test:
       runs-on: ubuntu-latest
       strategy:
         matrix:
           python-version: [3.10, 3.11]

       steps:
         - uses: actions/checkout@v3

         - name: Set up Python ${{ matrix.python-version }}
           uses: actions/setup-python@v4
           with:
             python-version: ${{ matrix.python-version }}

         - name: Install dependencies
           run: |
             python -m pip install --upgrade pip
             pip install -r requirements.txt
             pip install -r test_requirements.txt

         - name: Run linters
           run: |
             flake8 src/ tests/
             mypy src/

         - name: Run tests
           run: |
             pytest tests/ -v --cov=src --cov-report=xml

         - name: Upload coverage
           uses: codecov/codecov-action@v3
           with:
             file: ./coverage.xml

测试最佳实践
------------

1. **测试结构**
   ~~~~~~~~~~

   * 使用AAA模式 (Arrange-Act-Assert)
   * 每个测试一个断言
   * 测试名称描述性

2. **避免测试污染**
   ~~~~~~~~~~~~~~

   * 每个测试独立运行
   * 清理测试数据
   * 不依赖其他测试

3. **Mock使用场景**
   ~~~~~~~~~~~~~~

   * 外部API调用
   * 数据库操作
   * 文件系统操作
   * 时间相关操作

4. **测试数据**
   ~~~~~~~~~~

   * 使用工厂模式
   * 提供边界值
   * 包含异常情况

5. **性能考虑**
   ~~~~~~~~~~

   * 使用合适的test fixture作用域
   * 避免不必要的计算
   * 标记慢测试

6. **可维护性**
   ~~~~~~~~~~

   * 重用公共fixture
   * 提取公共辅助函数
   * 保持测试简单

常见问题
--------

1. **测试运行缓慢**
   ~~~~~~~~~~~~~

   .. code-block:: bash

      # 使用并行测试
      pytest -n auto

      # 跳过慢测试
      pytest -m "not slow"

2. **异步测试问题**
   ~~~~~~~~~~~~~

   .. code-block:: python

      # 确保使用pytest-asyncio
      # @pytest.mark.asyncio
      # async def test_async():
      #     result = await async_function()

3. **Mock装饰器顺序**
   ~~~~~~~~~~~~~~

   .. code-block:: python

      # 正确顺序：从下到上
      @patch('module.function2')
      @patch('module.function1')
      def test_with_mocks(mock1, mock2):
          ...

4. **数据库测试**
   ~~~~~~~~~~

   .. code-block:: python

      @pytest.fixture
      def temp_db():
          db = create_test_db()
          yield db
          db.destroy()

5. **环境变量测试**
   ~~~~~~~~~~~~~

   .. code-block:: python

      import os
      from unittest.mock import patch

      @patch.dict(os.environ, {"KEY": "value"})
      def test_with_env():
          ...
