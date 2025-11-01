"""
Pytest 配置与 Fixtures

为Phase 4测试提供测试数据和公共fixtures。
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


# ==================== 价格和收益率数据 ====================

@pytest.fixture
def sample_price_data():
    """生成样本价格数据 (252天交易日)"""
    dates = pd.date_range('2023-01-01', periods=252, freq='D')
    base_price = 100
    returns = np.random.normal(0.001, 0.02, 252)
    prices = base_price * np.exp(np.cumsum(returns))

    return pd.DataFrame({
        'date': dates,
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, 252)
    }).set_index('date')


@pytest.fixture
def sample_returns():
    """生成样本收益率序列"""
    returns = np.random.normal(0.001, 0.02, 252)
    dates = pd.date_range('2023-01-01', periods=252, freq='D')
    return pd.Series(returns, index=dates)


# ==================== 另类数据 ====================

@pytest.fixture
def hibor_series():
    """生成样本HIBOR数据"""
    dates = pd.date_range('2023-01-01', periods=252, freq='D')
    hibor = 3.5 + np.random.normal(0, 0.3, 252)
    hibor = np.clip(hibor, 2.5, 5.5)  # 限制在合理范围
    return pd.Series(hibor, index=dates, name='HIBOR')


@pytest.fixture
def visitor_arrivals():
    """生成样本访客到达数据"""
    dates = pd.date_range('2023-01-01', periods=252, freq='D')
    base_visitors = 1000
    seasonal = 200 * np.sin(np.arange(252) * 2 * np.pi / 365)
    visitors = base_visitors + seasonal + np.random.normal(0, 100, 252)
    visitors = np.clip(visitors, 500, 1500)
    return pd.Series(visitors, index=dates, name='Visitors')


@pytest.fixture
def correlation_series():
    """生成样本相关性序列"""
    dates = pd.date_range('2023-01-01', periods=252, freq='D')
    # 在0.3到0.8之间波动，有一些制度变化
    correlation = 0.55 + 0.15 * np.sin(np.arange(252) * 2 * np.pi / 100)
    correlation += np.random.normal(0, 0.05, 252)
    correlation = np.clip(correlation, 0.1, 0.95)
    return pd.Series(correlation, index=dates, name='Correlation')


@pytest.fixture
def macro_alerts():
    """生成样本宏观警报数据"""
    dates = pd.date_range('2023-01-01', periods=252, freq='D')
    data = {
        'HIBOR': 3.5 + np.random.normal(0, 0.3, 252),
        'VOLATILITY': 20 + np.random.normal(0, 5, 252),
        'CREDIT_SPREAD': 100 + np.random.normal(0, 20, 252),
        'FORWARD_PBV': 0.85 + np.random.normal(0, 0.05, 252)
    }
    return pd.DataFrame(data, index=dates)


# ==================== 交易数据 ====================

@pytest.fixture
def sample_trades():
    """生成样本交易记录"""
    trades = [
        {
            'signal_type': 'price_only',
            'pnl': 500,
            'confidence': 0.7,
            'entry_price': 100,
            'exit_price': 105,
            'quantity': 100,
            'symbol': '0700.HK',
            'entry_date': '2023-01-01',
            'exit_date': '2023-01-05',
            'duration_days': 4
        },
        {
            'signal_type': 'alt_data_only',
            'pnl': 300,
            'confidence': 0.65,
            'entry_price': 100,
            'exit_price': 103,
            'quantity': 100,
            'symbol': '0700.HK',
            'entry_date': '2023-01-06',
            'exit_date': '2023-01-10',
            'duration_days': 4
        },
        {
            'signal_type': 'combined',
            'pnl': 1200,
            'confidence': 0.85,
            'entry_price': 100,
            'exit_price': 112,
            'quantity': 100,
            'symbol': '0700.HK',
            'entry_date': '2023-01-11',
            'exit_date': '2023-01-20',
            'duration_days': 9
        },
        {
            'signal_type': 'price_only',
            'pnl': -200,
            'confidence': 0.55,
            'entry_price': 110,
            'exit_price': 108,
            'quantity': 100,
            'symbol': '0700.HK',
            'entry_date': '2023-01-21',
            'exit_date': '2023-01-25',
            'duration_days': 4
        },
        {
            'signal_type': 'combined',
            'pnl': 800,
            'confidence': 0.80,
            'entry_price': 108,
            'exit_price': 116,
            'quantity': 100,
            'symbol': '0700.HK',
            'entry_date': '2023-01-26',
            'exit_date': '2023-02-05',
            'duration_days': 10
        }
    ]
    return trades


@pytest.fixture
def winning_trades():
    """生成全部盈利交易"""
    trades = [
        {'signal_type': 'price_only', 'pnl': 500 + i*100, 'confidence': 0.7 + i*0.01, 'quantity': 100}
        for i in range(10)
    ]
    return trades


@pytest.fixture
def losing_trades():
    """生成全部亏损交易"""
    trades = [
        {'signal_type': 'price_only', 'pnl': -300 - i*50, 'confidence': 0.5, 'quantity': 100}
        for i in range(5)
    ]
    return trades


# ==================== 信号数据 ====================

@pytest.fixture
def price_signals():
    """生成价格信号"""
    return [
        {'symbol': '0700.HK', 'side': 'buy', 'quantity': 100, 'confidence': 0.75},
        {'symbol': '0700.HK', 'side': 'sell', 'quantity': 100, 'confidence': 0.65},
        {'symbol': '0700.HK', 'side': 'hold', 'quantity': 0, 'confidence': 0.45}
    ]


@pytest.fixture
def alt_data_signals():
    """生成另类数据信号"""
    return [
        {'symbol': '0700.HK', 'side': 'buy', 'quantity': 80, 'confidence': 0.70},
        {'symbol': '0700.HK', 'side': 'hold', 'quantity': 0, 'confidence': 0.50}
    ]


# ==================== 性能指标 ====================

@pytest.fixture
def train_metrics():
    """生成训练集性能指标"""
    return {
        'sharpe': 1.5,
        'win_rate': 0.65,
        'total_return': 0.25,
        'max_drawdown': -0.15,
        'max_loss': -500,
        'profit_factor': 2.0
    }


@pytest.fixture
def test_metrics():
    """生成测试集性能指标"""
    return {
        'sharpe': 0.8,
        'win_rate': 0.55,
        'total_return': 0.15,
        'max_drawdown': -0.25,
        'max_loss': -800,
        'profit_factor': 1.2
    }


# ==================== 宏观数据 ====================

@pytest.fixture
def macro_scenario_normal():
    """生成正常宏观场景"""
    return {
        'name': 'Normal Market',
        'HIBOR': 0,
        'VOLATILITY': 0,
        'CREDIT_SPREAD': 0
    }


@pytest.fixture
def macro_scenario_stress():
    """生成压力宏观场景"""
    return {
        'name': 'Market Stress',
        'HIBOR': 1.0,
        'VOLATILITY': 10.0,
        'CREDIT_SPREAD': 50
    }


@pytest.fixture
def portfolio_sensitivity():
    """生成投资组合敏感性"""
    return {
        'HIBOR': -0.5,
        'VOLATILITY': -0.3,
        'CREDIT_SPREAD': -0.4
    }


# ==================== 配置 ====================

@pytest.fixture
def alt_data_signal_config():
    """AltDataSignalStrategy 配置"""
    return {
        'price_weight': 0.6,
        'alt_weight': 0.4,
        'min_confidence': 0.3,
        'max_position_size': 1000,
        'use_correlation_weighting': True,
        'volatility_adjustment': True
    }


@pytest.fixture
def correlation_strategy_config():
    """CorrelationStrategy 配置"""
    return {
        'deviation_threshold': 2.0,
        'min_observations': 20,
        'regime_change_threshold': 1.5,
        'min_regime_duration': 5,
        'significance_level': 0.05
    }


@pytest.fixture
def macro_hedge_strategy_config():
    """MacroHedgeStrategy 配置"""
    return {
        'hedge_ratio': 0.2,
        'max_hedge_ratio': 0.5,
        'alert_threshold_multiplier': 2.0,
        'min_cost_bps': 5,
        'max_cost_bps': 50
    }


@pytest.fixture
def validator_config():
    """SignalValidator 配置"""
    return {
        'min_sample_size': 30,
        'overfitting_threshold': 0.2,
        'significance_level': 0.05,
        'degradation_threshold': 0.25
    }


# ==================== 测试参数 ====================

@pytest.mark.parametrize('price_signal,alt_signal,expected_direction', [
    (0.8, 0.6, 'buy'),      # 都是买信号
    (-0.7, -0.5, 'sell'),   # 都是卖信号
    (0.3, 0.2, 'hold'),     # 弱信号 -> hold
    (0.9, -0.4, 'buy'),     # 冲突但价格更强
])
def test_parameterized_signal_direction(price_signal, alt_signal, expected_direction):
    """参数化测试: 信号方向"""
    pass  # 实际测试在测试文件中


# ==================== 辅助函数 ====================

def create_sample_dataframe(n_rows=100):
    """创建样本数据框"""
    dates = pd.date_range('2023-01-01', periods=n_rows, freq='D')
    return pd.DataFrame({
        'close': 100 + np.cumsum(np.random.normal(0, 1, n_rows)),
        'volume': np.random.randint(1000000, 10000000, n_rows),
        'HIBOR': 3.5 + np.random.normal(0, 0.2, n_rows),
        'Visitors': 1000 + np.random.normal(0, 100, n_rows)
    }, index=dates)


def assert_signal_valid(signal):
    """验证信号有效性"""
    assert signal is not None, "Signal should not be None"
    assert hasattr(signal, 'direction'), "Signal should have direction"
    assert hasattr(signal, 'confidence'), "Signal should have confidence"
    assert 0 <= signal.confidence <= 1, "Confidence should be 0-1"


def assert_trades_valid(trades):
    """验证交易记录有效性"""
    assert isinstance(trades, list), "Trades should be a list"
    for trade in trades:
        assert 'pnl' in trade, "Trade should have pnl"
        assert 'confidence' in trade, "Trade should have confidence"
        assert 0 <= trade['confidence'] <= 1, "Confidence should be 0-1"


# ==================== 基准测试 ====================

class SimpleBenchmark:
    """简单的基准测试类"""
    def __init__(self):
        self.results = []

    def __call__(self, func, *args, **kwargs):
        """运行函数并测量执行时间"""
        import time
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()

        elapsed = end - start
        self.results.append(elapsed)
        return result


@pytest.fixture
def benchmark():
    """基准测试fixture - 用于性能测试"""
    return SimpleBenchmark()

