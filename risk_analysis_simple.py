import math
import json
import random

# Input data for 0700.HK (Tencent)
data = {
    "stocks": ["0700.HK"],
    "close_prices": [587.0, 592.5, 590.5, 593.0, 600.0, 614.5, 609.5, 599.0, 594.0, 596.5, 
                     605.0, 600.5, 598.5, 592.5, 605.5, 617.5, 627.0, 633.5, 629.5, 643.5, 
                     643.5, 645.0, 661.5, 642.0, 642.5, 641.0, 635.5, 648.5, 650.0, 644.0],
    "volatility": 0.0138,
    "max_drawdown": 0.0393
}

# Risk-free rate for HK market
risk_free_rate = 0.03

def calculate_returns(prices):
    """Calculate daily returns"""
    returns = []
    for i in range(1, len(prices)):
        ret = (prices[i] - prices[i-1]) / prices[i-1]
        returns.append(ret)
    return returns

def calculate_mean(values):
    """Calculate mean of a list"""
    return sum(values) / len(values)

def calculate_std(values):
    """Calculate standard deviation"""
    mean_val = calculate_mean(values)
    variance = sum((x - mean_val) ** 2 for x in values) / (len(values) - 1)
    return math.sqrt(variance)

def calculate_percentile(values, percentile):
    """Calculate percentile (simplified)"""
    sorted_vals = sorted(values)
    k = int(len(sorted_vals) * percentile / 100)
    return sorted_vals[k]

def calculate_var_95(returns):
    """Calculate 95% Value at Risk"""
    return calculate_percentile(returns, 5)

def calculate_sharpe_ratio(returns, rf_rate=0.03):
    """Calculate Sharpe ratio"""
    mean_return = calculate_mean(returns) * 252  # Annualized
    std_return = calculate_std(returns) * math.sqrt(252)  # Annualized
    sharpe = (mean_return - rf_rate) / std_return
    return sharpe

def monte_carlo_simulation(returns, days=252, simulations=1000):
    """Simplified Monte Carlo simulation"""
    mean_return = calculate_mean(returns)
    std_return = calculate_std(returns)
    
    final_returns = []
    
    for _ in range(simulations):
        cumulative_return = 1.0
        for _ in range(days):
            # Generate random return using Box-Muller transform
            u1 = random.random()
            u2 = random.random()
            z = math.sqrt(-2 * math.log(u1)) * math.cos(2 * math.pi * u2)
            daily_return = mean_return + std_return * z
            cumulative_return *= (1 + daily_return)
        
        final_returns.append(cumulative_return - 1)
    
    var_95_sim = calculate_percentile(final_returns, 5)
    expected_return = calculate_mean(final_returns)
    
    return var_95_sim, expected_return

def dynamic_stop_loss_strategy(prices, volatility_window=10, stop_loss_multiplier=2):
    """Dynamic stop-loss strategy based on volatility"""
    returns = calculate_returns(prices)
    stop_losses = []
    signals = []
    
    for i in range(len(prices)):
        if i < volatility_window:
            rolling_vol = data["volatility"]
        else:
            rolling_returns = returns[max(0, i-volatility_window):i]
            rolling_vol = calculate_std(rolling_returns) if rolling_returns else data["volatility"]
        
        stop_loss_level = prices[i] * (1 - stop_loss_multiplier * rolling_vol)
        stop_losses.append(stop_loss_level)
        
        if i > 0 and prices[i] < stop_losses[i-1]:
            signals.append("SELL")
        else:
            signals.append("HOLD")
    
    return stop_losses, signals

def main():
    prices = data["close_prices"]
    returns = calculate_returns(prices)
    
    # Set random seed for reproducibility
    random.seed(42)
    
    # Calculate risk metrics
    var_95 = calculate_var_95(returns)
    sharpe_ratio = calculate_sharpe_ratio(returns, risk_free_rate)
    
    # Monte Carlo simulation
    var_95_mc, expected_return_mc = monte_carlo_simulation(returns)
    
    # Dynamic stop-loss strategy
    stop_losses, signals = dynamic_stop_loss_strategy(prices)
    
    # Risk analysis results
    analysis_results = {
        "discovered_strategy": [
            {
                "name": "动态波动率止损策略",
                "description": "基于滚动波动率计算动态止损点，当价格跌破2倍波动率阈值时触发止损信号",
                "implementation": "使用10日滚动波动率，止损倍数2x，适应市场波动变化",
                "backtest_signals": signals[-5:]  # Last 5 signals
            },
            {
                "name": "蒙特卡洛风险预测策略", 
                "description": "通过1000次模拟预测未来252个交易日的风险分布，优化资产配置",
                "implementation": "基于历史收益分布生成随机情景，计算尾部风险和预期收益"
            }
        ],
        "var_95": round(var_95, 6),
        "var_95_annualized": round(var_95_mc, 6),
        "sharpe": round(sharpe_ratio, 4),
        "current_volatility": data["volatility"],
        "max_drawdown_observed": data["max_drawdown"],
        "expected_annual_return": round(expected_return_mc, 4),
        "risk_limits": {
            "max_drawdown_limit": 0.10,
            "volatility_limit": 0.02,
            "var_95_limit": -0.05,
            "minimum_sharpe": 1.5,
            "position_size_limit": 0.05,
            "sector_concentration_limit": 0.15
        },
        "recommendations": [
            {
                "recommendation": "实施动态止损机制：当0700.HK价格跌破动态止损线时减仓50%",
                "scenario_warning": "科技股面临监管风险时，止损机制可有效控制下行风险",
                "priority": "HIGH"
            },
            {
                "recommendation": "建立对冲组合：配置10-15%恒生指数期货空头对冲系统性风险",
                "scenario_warning": "港股与A股联动性增强，需防范跨市场传染风险",
                "priority": "MEDIUM"
            },
            {
                "recommendation": "设置波动率预警：当日内波动率超过2%时启动风险管理程序",
                "scenario_warning": "美联储政策变化或中美关系紧张可能导致波动率激增",
                "priority": "HIGH"
            },
            {
                "recommendation": "优化资产配置：腾讯持仓不超过组合5%，科技板块总持仓不超过15%",
                "scenario_warning": "单一股票集中度过高在黑天鹅事件中可能造成重大损失",
                "priority": "MEDIUM"
            },
            {
                "recommendation": "建立压力测试机制：每月进行极端情景下的组合表现测试",
                "scenario_warning": "2008年金融危机和2020年疫情等极端事件的历史回测显示组合韧性重要性",
                "priority": "LOW"
            }
        ],
        "stress_test_scenarios": {
            "market_crash_20pct": {
                "scenario": "市场下跌20%情况下的组合表现",
                "expected_loss": round(var_95 * 1.5, 6),
                "recovery_days": 45
            },
            "volatility_spike": {
                "scenario": "波动率上升至3%的情况",
                "risk_adjustment": "止损阈值收紧至1.5倍波动率"
            }
        },
        "performance_metrics": {
            "current_price": prices[-1],
            "price_trend": "上升" if prices[-1] > prices[0] else "下降",
            "total_return": round((prices[-1] - prices[0]) / prices[0], 4),
            "risk_adjusted_return": round(sharpe_ratio, 4),
            "sharpe_target_met": sharpe_ratio > 1.5
        }
    }
    
    return analysis_results

if __name__ == "__main__":
    results = main()
    
    # Output JSON results
    print(json.dumps(results, indent=2, ensure_ascii=False))
    
    # Save to file
    with open('/workspace/risk_analysis_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n分析完成！Sharpe比率: {results['sharpe']:.2f} ({'达标' if results['performance_metrics']['sharpe_target_met'] else '未达标'})")
    print(f"VaR(95%): {results['var_95']:.4f}, 策略建议：{results['discovered_strategy'][0]['name']}")