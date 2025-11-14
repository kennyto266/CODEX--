# 示例策略和模板

本目录包含港股量化交易系统的示例策略、模板和实战案例，帮助您快速上手和深入学习。

## 📁 目录结构

```
examples/
├── README.md                           # 本文件
├── basic_strategies/                   # 基础策略
│   ├── simple_ma_strategy.py           # 简单移动平均策略
│   ├── rsi_strategy.py                 # RSI策略
│   ├── macd_strategy.py                # MACD策略
│   └── bollinger_bands_strategy.py     # 布林带策略
├── advanced_strategies/                # 高级策略
│   ├── kdj_strategy.py                 # KDJ策略
│   ├── cci_strategy.py                 # CCI策略
│   ├── adx_strategy.py                 # ADX策略
│   ├── atr_strategy.py                 # ATR策略
│   ├── obv_strategy.py                 # OBV策略
│   ├── ichimoku_strategy.py            # 一目均衡图策略
│   └── parabolic_sar_strategy.py       # Parabolic SAR策略
├── combined_strategies/                # 组合策略
│   ├── kdj_rsi_combined.py             # KDJ+RSI组合
│   ├── ma_macd_combined.py             # MA+MACD组合
│   └── multi_indicator.py              # 多指标组合
├── templates/                          # 策略模板
│   ├── basic_strategy_template.py      # 基础策略模板
│   ├── enhanced_strategy_template.py   # 增强策略模板
│   ├── multi_symbol_template.py        # 多股票模板
│   └── portfolio_template.py           # 投资组合模板
├── data_analysis/                      # 数据分析
│   ├── alternative_data_demo.py        # 替代数据分析
│   ├── data_quality_check.py           # 数据质量检查
│   └── data_visualization.py           # 数据可视化
├── backtesting/                        # 回测相关
│   ├── simple_backtest.py              # 简单回测
│   ├── enhanced_backtest.py            # 增强回测
│   ├── parameter_optimization.py       # 参数优化
│   └── walk_forward_analysis.py        # 走步分析
├── risk_management/                    # 风险管理
│   ├── position_sizing.py              # 仓位管理
│   ├── stop_loss_management.py         # 止损管理
│   ├── portfolio_risk.py               # 投资组合风险
│   └── var_calculation.py              # VaR计算
├── system_demo/                        # 系统演示
│   ├── full_system_demo.py             # 完整系统演示
│   ├── telegram_bot_demo.py            # Telegram机器人演示
│   └── dashboard_demo.py               # 仪表板演示
└── tutorials/                          # 教程配套代码
    ├── quickstart/                     # 快速开始
    │   ├── 01_first_strategy.py
    │   ├── 02_data_fetching.py
    │   └── 03_basic_backtest.py
    ├── strategies/                     # 策略教程
    │   ├── lesson1_ma.py
    │   ├── lesson2_rsi.py
    │   └── lesson3_combined.py
    └── advanced/                       # 高级教程
        ├── machine_learning.py
        ├── alternative_data.py
        └── portfolio_management.py
```

---

## 🚀 快速开始

### 运行第一个策略

```bash
# 进入示例目录
cd examples

# 运行简单移动平均策略
python basic_strategies/simple_ma_strategy.py

# 运行RSI策略
python basic_strategies/rsi_strategy.py

# 运行增强回测
python backtesting/enhanced_backtest.py
```

### 自定义策略

使用模板创建新策略:

```python
# 1. 复制模板
cp templates/basic_strategy_template.py my_custom_strategy.py

# 2. 编辑文件，修改策略名称和逻辑
# 3. 运行策略
python my_custom_strategy.py
```

---

## 📚 策略详解

### 基础策略 (basic_strategies/)

#### 1. 简单移动平均策略 (simple_ma_strategy.py)

**策略原理:**
- 计算短期和长期移动平均线
- 短期MA上穿长期MA时买入
- 短期MA下穿长期MA时卖出

**关键参数:**
- `short_window`: 短期MA周期 (默认: 5)
- `long_window`: 长期MA周期 (默认: 20)

**使用示例:**
```python
strategy = MovingAverageStrategy(
    symbol="0700.hk",
    short_window=5,
    long_window=20,
    start_date="2022-01-01",
    end_date="2023-12-31"
)
result = strategy.run()
print(f"总收益率: {result['total_return']:.2f}%")
```

**回测结果示例:**
```
=== 回测结果 ===
股票: 0700.hk (腾讯控股)
时间范围: 2022-01-01 到 2023-12-31
策略: 简单移动平均 (5日/20日)

收益指标:
  总收益率: 12.34%
  年化收益率: 6.17%
  波动率: 18.45%

风险指标:
  最大回撤: -12.67%
  夏普比率: 0.68
  索提诺比率: 0.91

交易统计:
  总交易次数: 8
  胜率: 62.50%
  平均持仓时间: 15.3天
```

---

#### 2. RSI策略 (rsi_strategy.py)

**策略原理:**
- 计算RSI相对强弱指标
- RSI < 30时买入 (超卖)
- RSI > 70时卖出 (超买)

**关键参数:**
- `rsi_period`: RSI计算周期 (默认: 14)
- `oversold`: 超卖阈值 (默认: 30)
- `overbought`: 超买阈值 (默认: 70)

**使用示例:**
```python
strategy = RSIStrategy(
    symbol="0700.hk",
    rsi_period=14,
    oversold=30,
    overbought=70
)
result = strategy.run()
```

**回测结果示例:**
```
=== 回测结果 ===
策略: RSI策略 (14日)

收益指标:
  总收益率: 15.67%
  年化收益率: 7.83%
  波动率: 20.12%

风险指标:
  最大回撤: -9.45%
  夏普比率: 0.82
  索提诺比率: 1.15

交易统计:
  总交易次数: 15
  胜率: 66.67%
```

---

#### 3. MACD策略 (macd_strategy.py)

**策略原理:**
- 计算MACD指标 (快线、慢线、柱状图)
- MACD线上穿信号线时买入
- MACD线下穿信号线时卖出

**关键参数:**
- `fast_period`: 快线周期 (默认: 12)
- `slow_period`: 慢线周期 (默认: 26)
- `signal_period`: 信号线周期 (默认: 9)

**使用示例:**
```python
strategy = MACDStrategy(
    symbol="0700.hk",
    fast_period=12,
    slow_period=26,
    signal_period=9
)
```

---

#### 4. 布林带策略 (bollinger_bands_strategy.py)

**策略原理:**
- 计算布林带 (上轨、中轨、下轨)
- 价格触及下轨时买入
- 价格触及上轨时卖出

**关键参数:**
- `period`: 周期 (默认: 20)
- `std_dev`: 标准差倍数 (默认: 2)

**使用示例:**
```python
strategy = BollingerBandsStrategy(
    symbol="0700.hk",
    period=20,
    std_dev=2
)
```

---

### 高级策略 (advanced_strategies/)

#### 1. KDJ策略 (kdj_strategy.py)

**策略原理:**
- 随机指标KDJ
- K线上穿D线且K < 20时买入
- K线下穿D线且K > 80时卖出

**关键参数:**
- `k_period`: K值周期 (默认: 9)
- `d_period`: D值周期 (默认: 3)
- `oversold`: 超卖线 (默认: 20)
- `overbought`: 超买线 (默认: 80)

**使用示例:**
```python
strategy = KDJStrategy(
    symbol="0700.hk",
    k_period=9,
    d_period=3,
    oversold=20,
    overbought=80
)
```

**回测结果示例:**
```
=== 回测结果 ===
策略: KDJ策略 (9,3,20,80)

收益指标:
  总收益率: 18.45%
  年化收益率: 9.22%
  波动率: 22.34%

风险指标:
  最大回撤: -11.23%
  夏普比率: 0.95
  索提诺比率: 1.32

交易统计:
  总交易次数: 22
  胜率: 68.18%
  平均持仓时间: 8.7天
```

---

#### 2. CCI策略 (cci_strategy.py)

**策略原理:**
- 商品通道指数
- CCI < -100时买入
- CCI > 100时卖出

**关键参数:**
- `period`: 周期 (默认: 20)

**使用示例:**
```python
strategy = CCIStrategy(
    symbol="0700.hk",
    period=20
)
```

---

#### 3. ADX策略 (adx_strategy.py)

**策略原理:**
- 趋势强度指标
- +DI > -DI且ADX > 25时买入

**关键参数:**
- `period`: 周期 (默认: 14)
- `adx_threshold`: ADX阈值 (默认: 25)

**使用示例:**
```python
strategy = ADXStrategy(
    symbol="0700.hk",
    period=14,
    adx_threshold=25
)
```

---

#### 4. ATR策略 (atr_strategy.py)

**策略原理:**
- 平均真实波幅
- 价格突破上轨时买入
- 价格跌破下轨时卖出

**关键参数:**
- `period`: 周期 (默认: 14)
- `multiplier`: 倍数 (默认: 2)

**使用示例:**
```python
strategy = ATRStrategy(
    symbol="0700.hk",
    period=14,
    multiplier=2
)
```

---

### 组合策略 (combined_strategies/)

#### 1. KDJ+RSI组合 (kdj_rsi_combined.py)

**策略原理:**
- 同时使用KDJ和RSI两个指标
- KDJ发出买入信号且RSI < 40时买入
- KDJ发出卖出信号且RSI > 60时卖出
- 提高信号准确性

**使用示例:**
```python
from combined_strategies.kdj_rsi_combined import KDJRSICombined

strategy = KDJRSICombined(
    symbol="0700.hk",
    # KDJ参数
    kdj_k=9,
    kdj_d=3,
    kdj_oversold=20,
    kdj_overbought=80,
    # RSI参数
    rsi_period=14,
    rsi_oversold=40,
    rsi_overbought=60
)

result = strategy.run()
print(f"总收益率: {result['total_return']:.2f}%")
```

**优势:**
- 减少假信号
- 提高胜率
- 降低交易频率

**回测结果示例:**
```
=== 回测结果 ===
策略: KDJ+RSI组合

收益指标:
  总收益率: 21.34%
  年化收益率: 10.67%
  波动率: 20.89%

风险指标:
  最大回撤: -10.45%
  夏普比率: 1.15
  索提诺比率: 1.56

交易统计:
  总交易次数: 12
  胜率: 75.00%  (高于单一策略)
```

---

#### 2. 多指标组合 (multi_indicator.py)

**策略原理:**
- 融合多个技术指标
- 综合评分系统
- 智能权重分配

**使用示例:**
```python
from combined_strategies.multi_indicator import MultiIndicatorStrategy

strategy = MultiIndicatorStrategy(
    symbol="0700.hk",
    indicators=['ma', 'rsi', 'macd', 'kdj'],
    weights=[0.25, 0.25, 0.25, 0.25],  # 等权重
    threshold=0.6  # 买入阈值
)

result = strategy.run()
```

---

## 🔧 模板使用 (templates/)

### 1. 基础策略模板 (basic_strategy_template.py)

创建新策略的基础模板:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础策略模板
请复制此文件并修改为您的策略
"""

import pandas as pd
import numpy as np
from typing import Dict, Any

class MyCustomStrategy:
    """自定义策略"""

    def __init__(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        **params
    ):
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.params = params
        self.data = None
        self.signals = None

    def load_data(self):
        """加载数据"""
        # TODO: 实现数据加载逻辑
        # 示例:
        # from enhanced_strategy_backtest import EnhancedStrategyBacktest
        # backtest = EnhancedStrategyBacktest(self.symbol, self.start_date, self.end_date)
        # backtest.load_data()
        # self.data = backtest.data
        pass

    def calculate_indicators(self):
        """计算技术指标"""
        # TODO: 实现技术指标计算
        pass

    def generate_signals(self):
        """生成交易信号"""
        # TODO: 实现信号生成逻辑
        # self.signals = ...
        pass

    def backtest(self):
        """运行回测"""
        # TODO: 实现回测逻辑
        # 返回回测结果
        pass

    def run(self) -> Dict[str, Any]:
        """执行完整流程"""
        self.load_data()
        self.calculate_indicators()
        self.generate_signals()
        return self.backtest()

if __name__ == "__main__":
    # 使用示例
    strategy = MyCustomStrategy(
        symbol="0700.hk",
        start_date="2022-01-01",
        end_date="2023-12-31",
        # 添加您的参数
    )

    result = strategy.run()
    print(f"总收益率: {result['total_return']:.2f}%")
```

---

### 2. 增强策略模板 (enhanced_strategy_template.py)

更完整的策略模板，包含参数优化和性能分析:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强策略模板
包含参数优化、性能分析等高级功能
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
from itertools import product
from concurrent.futures import ProcessPoolExecutor
import matplotlib.pyplot as plt

class EnhancedStrategy:
    """增强策略基类"""

    def __init__(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        **params
    ):
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.params = params
        self.data = None
        self.signals = None
        self.returns = None

    def load_data(self):
        """加载数据"""
        from enhanced_strategy_backtest import EnhancedStrategyBacktest
        backtest = EnhancedStrategyBacktest(self.symbol, self.start_date, self.end_date)
        backtest.load_data()
        self.data = backtest.data
        return self

    def calculate_indicators(self):
        """计算技术指标"""
        raise NotImplementedError("子类必须实现此方法")

    def generate_signals(self):
        """生成交易信号"""
        raise NotImplementedError("子类必须实现此方法")

    def calculate_returns(self):
        """计算收益率"""
        if self.signals is None:
            raise ValueError("请先生成交易信号")

        # 简单收益计算
        self.returns = self.signals.pct_change().fillna(0)
        return self

    def calculate_metrics(self) -> Dict[str, float]:
        """计算性能指标"""
        if self.returns is None:
            self.calculate_returns()

        returns = self.returns.dropna()

        # 基础指标
        total_return = (1 + returns).prod() - 1
        annual_return = (1 + total_return) ** (252 / len(returns)) - 1
        volatility = returns.std() * np.sqrt(252)

        # 风险指标
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()

        # 夏普比率
        risk_free_rate = 0.02  # 假设2%无风险利率
        sharpe_ratio = (annual_return - risk_free_rate) / volatility

        # 胜率
        win_rate = (returns > 0).mean()

        return {
            'total_return': total_return * 100,
            'annual_return': annual_return * 100,
            'volatility': volatility * 100,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown * 100,
            'win_rate': win_rate * 100,
            'trades': (self.signals.diff().abs() > 0).sum()
        }

    def optimize_parameters(
        self,
        param_grid: Dict[str, List],
        max_workers: int = 4
    ) -> List[Dict[str, Any]]:
        """参数优化"""

        # 生成参数组合
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        param_combinations = list(product(*param_values))

        print(f"测试 {len(param_combinations)} 个参数组合...")

        def test_params(params):
            """测试单个参数组合"""
            test_params = dict(zip(param_names, params))
            strategy = type(self)(
                self.symbol,
                self.start_date,
                self.end_date,
                **test_params
            )
            try:
                strategy.load_data()
                strategy.calculate_indicators()
                strategy.generate_signals()
                metrics = strategy.calculate_metrics()
                metrics['params'] = test_params
                return metrics
            except Exception as e:
                print(f"参数 {test_params} 测试失败: {e}")
                return None

        # 并行测试
        results = []
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(test_params, params): params
                      for params in param_combinations}

            for future in futures:
                result = future.result()
                if result:
                    results.append(result)

        # 按收益率排序
        results.sort(key=lambda x: x['total_return'], reverse=True)
        return results

    def plot_results(self, save_path: str = None):
        """绘制结果图表"""
        if self.returns is None:
            self.calculate_returns()

        fig, axes = plt.subplots(2, 2, figsize=(15, 10))

        # 收益曲线
        cumulative = (1 + self.returns).cumprod()
        axes[0, 0].plot(cumulative.index, cumulative.values)
        axes[0, 0].set_title('累积收益率')
        axes[0, 0].set_ylabel('累积收益率')

        # 回撤
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        axes[0, 1].fill_between(drawdown.index, drawdown.values, 0)
        axes[0, 1].set_title('回撤')
        axes[0, 1].set_ylabel('回撤')

        # 交易信号
        if self.signals is not None:
            axes[1, 0].scatter(
                self.signals.index,
                self.signals,
                c=self.signals,
                cmap='RdYlGn',
                alpha=0.6
            )
            axes[1, 0].set_title('交易信号')
            axes[1, 0].set_ylabel('信号')

        # 收益分布
        axes[1, 1].hist(self.returns, bins=50, alpha=0.7)
        axes[1, 1].set_title('收益分布')
        axes[1, 1].set_xlabel('日收益率')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path)
            print(f"图表已保存到: {save_path}")
        else:
            plt.show()

    def run(self) -> Dict[str, Any]:
        """执行完整流程"""
        self.load_data()
        self.calculate_indicators()
        self.generate_signals()
        self.calculate_returns()
        return self.calculate_metrics()

# 使用示例
if __name__ == "__main__":
    # 创建策略实例
    strategy = EnhancedStrategy(
        symbol="0700.hk",
        start_date="2022-01-01",
        end_date="2023-12-31"
    )

    # 运行回测
    result = strategy.run()
    print("=== 回测结果 ===")
    for key, value in result.items():
        if key != 'params':
            print(f"{key}: {value:.2f}")

    # 参数优化
    param_grid = {
        'param1': [5, 10, 15],
        'param2': [20, 30, 40]
    }

    best_results = strategy.optimize_parameters(param_grid, max_workers=4)

    print("\n=== 最佳参数 ===")
    print(f"最佳参数: {best_results[0]['params']}")
    print(f"最佳收益率: {best_results[0]['total_return']:.2f}%")

    # 绘制图表
    strategy.plot_results('strategy_results.png')
```

---

### 3. 投资组合模板 (portfolio_template.py)

多股票投资组合管理模板:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
投资组合管理模板
管理多个股票和策略的组合
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class Position:
    """持仓信息"""
    symbol: str
    weight: float
    strategy: str
    params: Dict

class Portfolio:
    """投资组合管理"""

    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        self.positions: List[Position] = []
        self.performance_history = []

    def add_position(
        self,
        symbol: str,
        weight: float,
        strategy: str,
        params: Dict = None
    ):
        """添加持仓"""
        if params is None:
            params = {}

        position = Position(
            symbol=symbol,
            weight=weight,
            strategy=strategy,
            params=params
        )
        self.positions.append(position)

        # 归一化权重
        total_weight = sum(p.weight for p in self.positions)
        for pos in self.positions:
            pos.weight /= total_weight

    def calculate_portfolio_return(self, returns_data: Dict[str, pd.Series]) -> pd.Series:
        """计算投资组合收益率"""
        portfolio_returns = pd.Series(0, index=list(returns_data.values())[0].index)

        for position in self.positions:
            symbol = position.symbol
            if symbol in returns_data:
                symbol_returns = returns_data[symbol]
                portfolio_returns += symbol_returns * position.weight

        return portfolio_returns

    def backtest(self) -> Dict[str, Any]:
        """回测投资组合"""
        returns_data = {}

        # 获取各股票收益率
        for position in self.positions:
            if position.symbol not in returns_data:
                # TODO: 从回测引擎获取收益率数据
                # returns_data[position.symbol] = ...
                pass

        # 计算投资组合收益率
        portfolio_returns = self.calculate_portfolio_return(returns_data)

        # 计算性能指标
        total_return = (1 + portfolio_returns).prod() - 1
        annual_return = (1 + total_return) ** (252 / len(portfolio_returns)) - 1
        volatility = portfolio_returns.std() * np.sqrt(252)

        cumulative = (1 + portfolio_returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()

        risk_free_rate = 0.02
        sharpe_ratio = (annual_return - risk_free_rate) / volatility

        return {
            'total_return': total_return * 100,
            'annual_return': annual_return * 100,
            'volatility': volatility * 100,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown * 100,
            'final_value': self.initial_capital * (1 + total_return)
        }

    def optimize_weights(
        self,
        returns_data: Dict[str, pd.Series],
        method: str = 'equal_weight'
    ) -> Dict[str, float]:
        """优化权重分配"""

        if method == 'equal_weight':
            # 等权重
            weight = 1.0 / len(self.positions)
            return {pos.symbol: weight for pos in self.positions}

        elif method == 'risk_parity':
            # 风险平价 (简化版)
            # TODO: 实现风险平价算法
            pass

        elif method == 'max_sharpe':
            # 最大夏普比率 (简化版)
            # TODO: 实现最大夏普比率优化
            pass

        return {pos.symbol: pos.weight for pos in self.positions}

# 使用示例
if __name__ == "__main__":
    # 创建投资组合
    portfolio = Portfolio(initial_capital=100000)

    # 添加持仓
    portfolio.add_position(
        symbol="0700.hk",
        weight=0.3,
        strategy="kdj",
        params={'k_period': 9, 'd_period': 3}
    )

    portfolio.add_position(
        symbol="0388.hk",
        weight=0.3,
        strategy="rsi",
        params={'rsi_period': 14}
    )

    portfolio.add_position(
        symbol="1398.hk",
        weight=0.4,
        strategy="macd",
        params={'fast': 12, 'slow': 26}
    )

    # 回测
    result = portfolio.backtest()
    print("=== 投资组合回测结果 ===")
    print(f"总收益率: {result['total_return']:.2f}%")
    print(f"年化收益率: {result['annual_return']:.2f}%")
    print(f"夏普比率: {result['sharpe_ratio']:.2f}")
    print(f"最大回撤: {result['max_drawdown']:.2f}%")
    print(f"最终价值: ${result['final_value']:,.2f}")
```

---

## 📊 数据分析示例 (data_analysis/)

### 1. 替代数据分析 (alternative_data_demo.py)

演示如何使用35种替代数据指标:

```python
#!/usr/bin/env python3
"""
替代数据分析示例
使用HIBOR、地产、零售等多种数据
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from correlation_analysis import CorrelationAnalyzer

def analyze_alternative_data():
    """分析替代数据"""
    # 加载替代数据
    from gov_crawler.collect_all_alternative_data import AlternativeDataCollector

    collector = AlternativeDataCollector()
    data = collector.collect_all_data(mode="mock")  # 当前为模拟数据

    # 分析相关性
    analyzer = CorrelationAnalyzer(data)

    # 1. 计算相关性矩阵
    correlation_matrix = analyzer.calculate_correlation()

    # 2. 绘制相关性热力图
    analyzer.plot_correlation_heatmap()

    # 3. 找出最强相关性
    strong_correlations = analyzer.find_strong_correlations(threshold=0.7)

    print("=== 强相关性指标 (|r| > 0.7) ===")
    for indicator1, indicator2, corr in strong_correlations:
        print(f"{indicator1} <-> {indicator2}: {corr:.3f}")

    # 4. 趋势分析
    trends = analyzer.analyze_trends()

    print("\n=== 趋势分析 ===")
    for indicator, trend in trends.items():
        print(f"{indicator}: {trend}")

    # 5. 预测分析
    predictions = analyzer.predict_indicators(target_indicator='hibor_6m')

    print("\n=== HIBOR 6个月预测 ===")
    for date, value in predictions.items():
        print(f"{date}: {value:.3f}%")

    return data

if __name__ == "__main__":
    data = analyze_alternative_data()
```

---

### 2. 数据质量检查 (data_quality_check.py)

检查数据完整性和质量:

```python
#!/usr/bin/env python3
"""
数据质量检查
验证数据完整性、异常值等
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple

class DataQualityChecker:
    """数据质量检查器"""

    def __init__(self, data: pd.DataFrame):
        self.data = data

    def check_completeness(self) -> Dict[str, float]:
        """检查数据完整性"""
        missing_percent = (self.data.isnull().sum() / len(self.data)) * 100

        return {
            'missing_count': self.data.isnull().sum().to_dict(),
            'missing_percent': missing_percent.to_dict(),
            'overall_completeness': (1 - self.data.isnull().sum().sum() /
                                   (self.data.shape[0] * self.data.shape[1])) * 100
        }

    def check_duplicates(self) -> Dict[str, int]:
        """检查重复数据"""
        duplicate_rows = self.data.duplicated().sum()
        duplicate_dates = self.data.index.duplicated().sum()

        return {
            'duplicate_rows': duplicate_rows,
            'duplicate_dates': duplicate_dates,
            'total_duplicates': duplicate_rows + duplicate_dates
        }

    def check_outliers(self, columns: List[str] = None) -> Dict[str, List]:
        """检查异常值"""
        if columns is None:
            columns = self.data.select_dtypes(include=[np.number]).columns

        outliers = {}
        for col in columns:
            if col in self.data.columns:
                Q1 = self.data[col].quantile(0.25)
                Q3 = self.data[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR

                col_outliers = self.data[
                    (self.data[col] < lower_bound) | (self.data[col] > upper_bound)
                ].index.tolist()

                outliers[col] = {
                    'count': len(col_outliers),
                    'percentage': len(col_outliers) / len(self.data) * 100,
                    'indices': col_outliers
                }

        return outliers

    def check_data_types(self) -> Dict[str, str]:
        """检查数据类型"""
        return {
            'expected_types': self.data.dtypes.to_dict(),
            'actual_types': {col: str(dtype) for col, dtype in self.data.dtypes.items()}
        }

    def check_date_range(self) -> Dict[str, str]:
        """检查日期范围"""
        if isinstance(self.data.index, pd.DatetimeIndex):
            return {
                'start_date': str(self.data.index.min()),
                'end_date': str(self.data.index.max()),
                'date_span': str(self.data.index.max() - self.data.index.min()),
                'total_days': len(self.data)
            }
        return {}

    def generate_report(self) -> str:
        """生成质量报告"""
        completeness = self.check_completeness()
        duplicates = self.check_duplicates()
        outliers = self.check_outliers()
        date_range = self.check_date_range()

        report = f"""
=== 数据质量报告 ===

数据维度: {self.data.shape[0]} 行 × {self.data.shape[1]} 列
{date_range}

完整性:
  总体完整度: {completeness['overall_completeness']:.2f}%
  缺失数据最多的列:
"""

        # 找出缺失最多的5列
        missing_sorted = sorted(
            completeness['missing_percent'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        for col, percent in missing_sorted:
            if percent > 0:
                report += f"    {col}: {percent:.2f}%\n"

        report += f"""
重复数据:
  重复行数: {duplicates['duplicate_rows']}
  重复日期: {duplicates['duplicate_dates']}

异常值:
"""

        for col, info in outliers.items():
            if info['count'] > 0:
                report += f"  {col}: {info['count']} 个 ({info['percentage']:.2f}%)\n"

        return report

# 使用示例
if __name__ == "__main__":
    # 加载数据
    data = pd.read_csv('data.csv', index_col='date', parse_dates=True)

    # 检查质量
    checker = DataQualityChecker(data)
    report = checker.generate_report()
    print(report)

    # 保存报告
    with open('data_quality_report.txt', 'w', encoding='utf-8') as f:
        f.write(report)
```

---

## 🧪 回测示例 (backtesting/)

### 1. 参数优化 (parameter_optimization.py)

系统演示如何优化策略参数:

```python
#!/usr/bin/env python3
"""
参数优化示例
使用并行计算优化多个参数
"""

from enhanced_strategy_backtest import EnhancedStrategyBacktest
import pandas as pd
from concurrent.futures import ProcessPoolExecutor
import matplotlib.pyplot as plt

def optimize_kdj_parameters():
    """优化KDJ参数"""
    backtest = EnhancedStrategyBacktest("0700.hk", "2020-01-01", "2023-01-01")
    backtest.load_data()

    # 定义参数网格
    param_grid = {
        'k_period': [5, 9, 14, 20, 25],
        'd_period': [3, 5, 7],
        'oversold': [15, 20, 25, 30],
        'overbought': [70, 75, 80, 85]
    }

    print("开始优化KDJ参数...")
    print(f"参数组合数: {5 * 3 * 4 * 4} = {5*3*4*4}")

    # 执行优化
    results = backtest.optimize_parameters(
        strategy_type='kdj',
        max_workers=8
    )

    # 显示前10个最佳结果
    print("\n=== 最佳10个参数组合 ===")
    for i, result in enumerate(results[:10], 1):
        print(f"{i}. 收益率: {result['total_return']:.2f}%, "
              f"夏普: {result['sharpe_ratio']:.2f}, "
              f"回撤: {result['max_drawdown']:.2f}%, "
              f"参数: {result['params']}")

    # 绘制优化结果
    plot_optimization_results(results)

    return results

def plot_optimization_results(results):
    """绘制优化结果"""
    df_results = pd.DataFrame(results)

    fig, axes = plt.subplots(2, 2, figsize=(15, 10))

    # 收益率分布
    axes[0, 0].hist(df_results['total_return'], bins=30)
    axes[0, 0].set_title('收益率分布')
    axes[0, 0].set_xlabel('总收益率 (%)')

    # 夏普比率 vs 收益率
    axes[0, 1].scatter(df_results['sharpe_ratio'], df_results['total_return'], alpha=0.6)
    axes[0, 1].set_title('夏普比率 vs 收益率')
    axes[0, 1].set_xlabel('夏普比率')
    axes[0, 1].set_ylabel('总收益率 (%)')

    # 最大回撤 vs 收益率
    axes[1, 0].scatter(df_results['max_drawdown'], df_results['total_return'], alpha=0.6)
    axes[1, 0].set_title('最大回撤 vs 收益率')
    axes[1, 0].set_xlabel('最大回撤 (%)')
    axes[1, 0].set_ylabel('总收益率 (%)')

    # 参数热力图 (简化版)
    # 可以根据需要绘制

    plt.tight_layout()
    plt.savefig('optimization_results.png')
    print("优化结果图表已保存到: optimization_results.png")

if __name__ == "__main__":
    results = optimize_kdj_parameters()
```

---

### 2. 走步分析 (walk_forward_analysis.py)

时间序列交叉验证:

```python
#!/usr/bin/env python3
"""
走步分析
时间序列交叉验证，评估策略稳定性
"""

import pandas as pd
import numpy as np
from enhanced_strategy_backtest import EnhancedStrategyBacktest

class WalkForwardAnalysis:
    """走步分析"""

    def __init__(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        train_period: int = 252,  # 训练期: 1年
        test_period: int = 63,    # 测试期: 3个月
        step: int = 21            # 步长: 1个月
    ):
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.train_period = train_period
        self.test_period = test_period
        self.step = step

    def run_analysis(self, strategy_type: str = 'kdj'):
        """运行走步分析"""
        backtest = EnhancedStrategyBacktest(self.symbol, self.start_date, self.end_date)
        backtest.load_data()

        results = []
        current_date = pd.to_datetime(self.start_date)

        while current_date + pd.Timedelta(days=self.train_period + self.test_period) <= pd.to_datetime(self.end_date):
            # 训练期
            train_start = current_date
            train_end = current_date + pd.Timedelta(days=self.train_period)

            # 测试期
            test_start = train_end
            test_end = test_start + pd.Timedelta(days=self.test_period)

            print(f"训练期: {train_start.date()} 到 {train_end.date()}")
            print(f"测试期: {test_start.date()} 到 {test_end.date()}")

            # 在训练期优化参数
            backtest_train = EnhancedStrategyBacktest(
                self.symbol,
                str(train_start.date()),
                str(train_end.date())
            )
            backtest_train.load_data()

            best_params = backtest_train.optimize_parameters(
                strategy_type=strategy_type,
                max_workers=4
            )

            if not best_params:
                print("  优化失败，跳过")
                current_date += pd.Timedelta(days=self.step)
                continue

            # 在测试期验证
            backtest_test = EnhancedStrategyBacktest(
                self.symbol,
                str(test_start.date()),
                str(test_end.date())
            )
            backtest_test.load_data()

            result = backtest_test.run_kdj_strategy(**best_params[0]['params'])

            results.append({
                'train_start': train_start,
                'train_end': train_end,
                'test_start': test_start,
                'test_end': test_end,
                'train_return': best_params[0]['total_return'],
                'test_return': result['total_return'],
                'best_params': best_params[0]['params']
            })

            print(f"  训练收益: {best_params[0]['total_return']:.2f}%")
            print(f"  测试收益: {result['total_return']:.2f}%")
            print()

            # 移动到下一个窗口
            current_date += pd.Timedelta(days=self.step)

        return pd.DataFrame(results)

    def analyze_results(self, results_df: pd.DataFrame):
        """分析走步结果"""
        print("=== 走步分析结果 ===\n")

        print(f"总窗口数: {len(results_df)}")
        print(f"平均训练收益: {results_df['train_return'].mean():.2f}%")
        print(f"平均测试收益: {results_df['test_return'].mean():.2f}%")

        # 收益稳定性
        correlation = results_df['train_return'].corr(results_df['test_return'])
        print(f"训练-测试相关性: {correlation:.3f}")

        if correlation > 0.5:
            print("✅ 策略稳定性好")
        elif correlation > 0:
            print("⚠️  策略稳定性一般")
        else:
            print("❌ 策略稳定性差")

        # 收益分布
        print(f"\n收益统计:")
        print(f"  训练期 - 最大: {results_df['train_return'].max():.2f}%, "
              f"最小: {results_df['train_return'].min():.2f}%")
        print(f"  测试期 - 最大: {results_df['test_return'].max():.2f}%, "
              f"最小: {results_df['test_return'].min():.2f}%")

        # 胜率
        positive_tests = (results_df['test_return'] > 0).sum()
        print(f"\n测试期正收益窗口: {positive_tests}/{len(results_df)} "
              f"({positive_tests/len(results_df)*100:.1f}%)")

# 使用示例
if __name__ == "__main__":
    analysis = WalkForwardAnalysis(
        symbol="0700.hk",
        start_date="2020-01-01",
        end_date="2023-12-31",
        train_period=252,  # 1年
        test_period=63,    # 3个月
        step=21            # 1个月
    )

    results = analysis.run_analysis(strategy_type='kdj')
    analysis.analyze_results(results)

    # 保存结果
    results.to_csv('walk_forward_results.csv', index=False)
    print("\n结果已保存到: walk_forward_results.csv")
```

---

## 🛡️ 风险管理示例 (risk_management/)

### 1. 仓位管理 (position_sizing.py)

演示不同的仓位管理策略:

```python
#!/usr/bin/env python3
"""
仓位管理策略
演示固定比例、凯利公式、风险平价等方法
"""

import numpy as np
import pandas as pd

class PositionSizer:
    """仓位管理器"""

    @staticmethod
    def fixed_fractional(returns: pd.Series, fraction: float = 0.02) -> pd.Series:
        """固定比例法 - 每次交易风险固定比例的资本"""
        position_sizes = []
        for ret in returns:
            if ret > 0:
                size = fraction
            else:
                size = 0
            position_sizes.append(size)
        return pd.Series(position_sizes, index=returns.index)

    @staticmethod
    def kelly_criterion(
        returns: pd.Series,
        win_rate: float = None,
        avg_win: float = None,
        avg_loss: float = None
    ) -> float:
        """凯利公式计算最优仓位"""
        if win_rate is None:
            win_rate = (returns > 0).mean()
        if avg_win is None:
            avg_win = returns[returns > 0].mean()
        if avg_loss is None:
            avg_loss = abs(returns[returns < 0].mean())

        # 凯利公式: f = (bp - q) / b
        # b = 赔率 (平均盈利/平均亏损)
        # p = 胜率
        # q = 败率 (1-p)
        b = avg_win / avg_loss
        p = win_rate
        q = 1 - win_rate

        kelly_fraction = (b * p - q) / b

        # 限制在0-0.25之间 (保守使用)
        return max(0, min(kelly_fraction, 0.25))

    @staticmethod
    def volatility_scaling(
        returns: pd.Series,
        target_vol: float = 0.15,
        lookback: int = 60
    ) -> pd.Series:
        """波动率缩放 - 根据历史波动率调整仓位"""
        rolling_vol = returns.rolling(lookback).std() * np.sqrt(252)
        position_sizes = target_vol / rolling_vol
        return position_sizes.clip(0, 1)  # 限制在0-1之间

    @staticmethod
    def max_drawdown_adjusted(
        returns: pd.Series,
        max_risk: float = 0.05
    ) -> pd.Series:
        """基于最大回撤调整仓位"""
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max

        # 当前回撤
        current_dd = drawdown.iloc[-1]
        # 调整系数: 回撤越大，仓位越小
        adjustment = (max_risk - current_dd) / max_risk
        position_size = max(0, min(adjustment, 1))

        return pd.Series(position_size, index=returns.index)

def compare_position_sizing():
    """比较不同仓位管理方法"""
    # 生成示例数据
    np.random.seed(42)
    returns = pd.Series(np.random.normal(0.001, 0.02, 252))  # 252个交易日

    sizer = PositionSizer()

    # 方法1: 固定比例
    fixed_sizes = sizer.fixed_fractional(returns, fraction=0.02)

    # 方法2: 凯利公式
    kelly_size = sizer.kelly_criterion(returns)
    print(f"凯利公式建议仓位: {kelly_size:.3f}")

    # 方法3: 波动率缩放
    vol_sizes = sizer.volatility_scaling(returns, target_vol=0.15)

    # 方法4: 最大回撤调整
    dd_sizes = sizer.max_drawdown_adjusted(returns, max_risk=0.05)

    # 计算调整后的收益率
    adjusted_returns = {
        '固定比例': returns * fixed_sizes,
        '波动率缩放': returns * vol_sizes,
        '回撤调整': returns * dd_sizes
    }

    # 比较结果
    print("\n=== 仓位管理比较 ===")
    for name, adj_ret in adjusted_returns.items():
        total_ret = (1 + adj_ret).prod() - 1
        vol = adj_ret.std() * np.sqrt(252)
        sharpe = adj_ret.mean() / adj_ret.std() * np.sqrt(252) if adj_ret.std() > 0 else 0

        print(f"{name}:")
        print(f"  总收益: {total_ret*100:.2f}%")
        print(f"  波动率: {vol*100:.2f}%")
        print(f"  夏普比率: {sharpe:.3f}")

    return adjusted_returns

if __name__ == "__main__":
    results = compare_position_sizing()
```

---

## 🎯 使用建议

### 1. 学习路径

**初学者路径:**
1. 从 `basic_strategies/` 开始，理解基本策略
2. 学习 `backtesting/simple_backtest.py` 了解回测流程
3. 使用 `templates/basic_strategy_template.py` 创建自己的策略
4. 阅读 `data_analysis/` 学习数据分析

**进阶路径:**
1. 学习 `advanced_strategies/` 掌握高级指标
2. 使用 `combined_strategies/` 学习策略组合
3. 深入 `backtesting/parameter_optimization.py` 掌握参数优化
4. 研究 `risk_management/` 学习风险管理

**专业路径:**
1. 定制 `templates/enhanced_strategy_template.py`
2. 使用 `portfolio_template.py` 管理多股票组合
3. 开发机器学习策略 (`tutorials/advanced/machine_learning.py`)
4. 集成替代数据 (`tutorials/advanced/alternative_data.py`)

---

### 2. 最佳实践

**策略开发:**
- ✅ 先在历史数据上回测
- ✅ 使用样本外数据验证
- ✅ 避免过拟合
- ✅ 包含交易成本
- ✅ 设置止损/止盈

**风险管理:**
- ✅ 使用合理的仓位大小
- ✅ 分散投资
- ✅ 定期重新评估
- ✅ 设置最大回撤限制
- ✅ 记录交易日志

**代码质量:**
- ✅ 使用类型注解
- ✅ 添加文档字符串
- ✅ 编写单元测试
- ✅ 遵循PEP 8规范
- ✅ 使用版本控制

---

### 3. 性能优化

**提升回测速度:**
```python
# 使用向量化计算
df['ma'] = df['close'].rolling(20).mean()  # 快速
# 而不是
ma_values = []
for i in range(len(df)):
    ma_values.append(df['close'][:i+1].mean())  # 慢

# 使用并行处理
with ProcessPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(func, param_list))
```

**减少内存使用:**
```python
# 使用适当的数据类型
df = pd.read_csv('data.csv', dtype={
    'close': 'float32',  # 而不是float64
    'volume': 'int32'
})

# 分批处理大数据
for chunk in pd.read_csv('large_data.csv', chunksize=10000):
    process_chunk(chunk)
```

---

## 📖 更多资源

**官方文档:**
- 快速开始: `docs/quickstart.md`
- 用户指南: `docs/user_guide.md`
- API参考: http://localhost:8001/docs
- FAQ: `docs/faq.md`

**外部资源:**
- [技术指标指南](docs/technical_indicators_guide.md)
- [替代数据指南](docs/alternative-data-guide.md)
- [风险管理文档](docs/risk_management.md)

**社区:**
- GitHub Issues: 报告Bug和功能请求
- 论坛: 参与讨论和分享经验
- 邮件列表: 接收更新通知

---

**祝您使用愉快！** 🎉

如有问题，请查看FAQ或联系支持团队。
