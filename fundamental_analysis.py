import pandas as pd
import numpy as np
import json
from datetime import datetime

# Input data for 0700.HK (Tencent)
stock_data = {
    "stocks": ["0700.HK"],
    "close_prices": [643.5, 645.0, 661.5, 642.0, 642.5, 641.0, 635.5, 648.5, 650.0, 644.0],
    "volumes": [16371242, 13339685, 22349048, 29989898, 20805608, 12899662, 15293080, 18440788, 17384258, 19504951]
}

# Create DataFrame for analysis
df = pd.DataFrame({
    'close_price': stock_data['close_prices'],
    'volume': stock_data['volumes']
})

# Calculate price statistics
price_mean = df['close_price'].mean()
price_volatility = df['close_price'].std()
volume_mean = df['volume'].mean()

# Calculate daily returns
df['returns'] = df['close_price'].pct_change().dropna()
daily_returns = df['returns'].dropna()

# Calculate Sharpe ratio (assuming risk-free rate of 3% annually)
risk_free_rate = 0.03 / 252  # Daily risk-free rate
excess_returns = daily_returns - risk_free_rate
sharpe_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(252) if excess_returns.std() > 0 else 0

# Tencent fundamental estimates (based on recent data)
tencent_fundamentals = {
    "pe_ratio": 15.2,  # Current P/E ratio
    "roe": 0.168,      # Return on Equity ~16.8%
    "debt_equity": 0.31,  # Debt/Equity ratio ~0.31
    "ebitda_growth": 0.12,  # EBITDA growth rate ~12%
    "market_cap_hkd": 3100000000000,  # ~3.1T HKD
    "revenue_growth": 0.08  # Revenue growth ~8%
}

# Value stock screening criteria
def screen_value_stock(pe, roe, debt_equity):
    """Screen stocks based on value criteria"""
    criteria_met = []
    
    if pe < 20:  # Low P/E
        criteria_met.append("Low PE")
    if roe > 0.15:  # High ROE (>15%)
        criteria_met.append("High ROE")
    if debt_equity < 1.0:  # Low debt
        criteria_met.append("Low Debt")
    
    return criteria_met, len(criteria_met) >= 2

# Screen Tencent
criteria_met, is_value_stock = screen_value_stock(
    tencent_fundamentals["pe_ratio"],
    tencent_fundamentals["roe"],
    tencent_fundamentals["debt_equity"]
)

# Calculate fundamental score
fundamental_score = (
    (20 - tencent_fundamentals["pe_ratio"]) / 20 * 0.3 +  # PE component
    tencent_fundamentals["roe"] * 0.4 +  # ROE component
    (1 - tencent_fundamentals["debt_equity"]) * 0.3  # Debt component
)

# Generate strategy
strategy = {
    "name": "港股基本面價值再平衡策略",
    "description": "基於低PE、高ROE、低負債比率的價值股篩選和季度再平衡",
    "criteria": {
        "pe_threshold": 20,
        "roe_threshold": 0.15,
        "debt_equity_threshold": 1.0
    }
}

# Risk assessment
risk_factors = []
if tencent_fundamentals["debt_equity"] > 0.5:
    risk_factors.append("中等負債水平")
if price_volatility > 50:
    risk_factors.append("高價格波動性")

# Generate final analysis
analysis_result = {
    "discovered_strategy": strategy["name"],
    "value_stocks": [{
        "code": "0700.HK",
        "pe": tencent_fundamentals["pe_ratio"],
        "roe": tencent_fundamentals["roe"],
        "debt_equity": tencent_fundamentals["debt_equity"],
        "fundamental_score": round(fundamental_score, 3),
        "is_value_stock": is_value_stock,
        "criteria_met": criteria_met
    }],
    "roe_avg": tencent_fundamentals["roe"],
    "sharpe": round(sharpe_ratio, 2),
    "price_volatility": round(price_volatility, 2),
    "volume_avg": int(volume_mean),
    "recommendations": [
        "騰訊符合價值股標準：PE 15.2 < 20, ROE 16.8% > 15%, 債務比率 0.31 < 1.0",
        "建議季度再平衡，維持基本面驅動的投資組合",
        "監控科技股監管風險和市場情緒變化",
        "目標Sharpe比率 >1.5，當前計算值需更長時間序列驗證"
    ],
    "risk_assessment": {
        "systematic_risk": "中等",
        "sector_concentration": "科技股集中風險",
        "regulatory_risk": "中港監管環境變化",
        "risk_factors": risk_factors
    },
    "expected_return": {
        "annual_target": "12-18%",
        "risk_adjusted": "基於ROE 16.8%和合理估值",
        "time_horizon": "1-3年中長期持有"
    }
}

print(json.dumps(analysis_result, indent=2, ensure_ascii=False))