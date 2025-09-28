#!/usr/bin/env python3
"""
港股基本面分析代理 (HK Stock Fundamental Analyst)
专注于高Sharpe Ratio交易策略的量化分析系统
"""

import json
import math
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
import statistics

@dataclass
class StockData:
    """股票数据结构"""
    symbol: str
    close_prices: List[float]
    eps_estimates: List[float]
    roe: List[float]
    debt_equity_ratio: float = 0.5  # 默认债务股权比
    
class HKFundamentalAnalyst:
    """港股基本面分析代理"""
    
    def __init__(self):
        self.target_sharpe_ratio = 1.5
        self.max_drawdown = 0.10
        self.pe_discount_threshold = 0.30  # PE低于行业中位数30%
        self.max_debt_equity = 1.0  # 最大债务股权比
        
    def calculate_pe_ratio(self, close_price: float, eps: float) -> float:
        """计算PE比率"""
        if eps <= 0:
            return float('inf')
        return close_price / eps
    
    def calculate_roe_growth(self, roe_values: List[float]) -> float:
        """计算ROE年同比增长率"""
        if len(roe_values) < 2:
            return 0.0
        return (roe_values[-1] - roe_values[0]) / roe_values[0] if roe_values[0] != 0 else 0.0
    
    def calculate_earnings_growth(self, eps_values: List[float]) -> float:
        """计算盈利成长率(YoY)"""
        if len(eps_values) < 2:
            return 0.0
        return (eps_values[-1] - eps_values[0]) / eps_values[0] if eps_values[0] != 0 else 0.0
    
    def calculate_price_volatility(self, prices: List[float]) -> float:
        """计算价格波动率"""
        if len(prices) < 2:
            return 0.0
        returns = [(prices[i] / prices[i-1] - 1) for i in range(1, len(prices))]
        return statistics.stdev(returns) if len(returns) > 1 else 0.0
    
    def assess_fundamental_quality(self, stock_data: StockData) -> Dict[str, float]:
        """评估基本面质量"""
        latest_price = stock_data.close_prices[-1]
        latest_eps = stock_data.eps_estimates[-1]
        latest_roe = stock_data.roe[-1]
        
        pe_ratio = self.calculate_pe_ratio(latest_price, latest_eps)
        roe_growth = self.calculate_roe_growth(stock_data.roe)
        earnings_growth = self.calculate_earnings_growth(stock_data.eps_estimates)
        price_volatility = self.calculate_price_volatility(stock_data.close_prices)
        
        return {
            'pe_ratio': pe_ratio,
            'roe': latest_roe,
            'roe_growth': roe_growth,
            'earnings_growth': earnings_growth,
            'price_volatility': price_volatility,
            'debt_equity_ratio': stock_data.debt_equity_ratio
        }
    
    def identify_undervalued_stocks(self, stocks_data: List[StockData]) -> List[Dict[str, Any]]:
        """识别低估股票"""
        undervalued = []
        pe_ratios = []
        
        # 计算所有股票的PE比率
        for stock in stocks_data:
            fundamentals = self.assess_fundamental_quality(stock)
            pe_ratio = fundamentals['pe_ratio']
            
            if pe_ratio != float('inf'):
                pe_ratios.append(pe_ratio)
        
        if not pe_ratios:
            return undervalued
        
        # 计算PE中位数
        pe_median = statistics.median(pe_ratios)
        pe_threshold = pe_median * (1 - self.pe_discount_threshold)
        
        # 筛选低估股票
        for stock in stocks_data:
            fundamentals = self.assess_fundamental_quality(stock)
            pe_ratio = fundamentals['pe_ratio']
            debt_equity = fundamentals['debt_equity_ratio']
            
            # 筛选条件：PE低于阈值且债务比率合理
            if (pe_ratio < pe_threshold and 
                pe_ratio != float('inf') and 
                debt_equity <= self.max_debt_equity and
                fundamentals['roe'] > 0.10):  # ROE > 10%
                
                undervalued.append({
                    'symbol': stock.symbol,
                    'pe_ratio': round(pe_ratio, 2),
                    'roe': round(fundamentals['roe'], 3),
                    'earnings_growth': round(fundamentals['earnings_growth'], 3),
                    'debt_equity_ratio': round(debt_equity, 2)
                })
        
        return undervalued
    
    def calculate_sharpe_contribution(self, stock_data: StockData) -> float:
        """计算对Sharpe Ratio的预估贡献值"""
        fundamentals = self.assess_fundamental_quality(stock_data)
        
        # 基于基本面指标计算贡献分数
        pe_score = max(0, (20 - fundamentals['pe_ratio']) / 20) if fundamentals['pe_ratio'] != float('inf') else 0
        roe_score = min(1, fundamentals['roe'] / 0.20)  # ROE 20%为满分
        growth_score = max(0, min(1, fundamentals['earnings_growth'] / 0.15))  # 15%增长为满分
        volatility_penalty = max(0, 1 - fundamentals['price_volatility'] / 0.30)  # 30%波动率为惩罚阈值
        debt_penalty = max(0, 1 - fundamentals['debt_equity_ratio'] / self.max_debt_equity)
        
        # 综合评分 (-1 到 1)
        contribution = (pe_score * 0.3 + roe_score * 0.25 + growth_score * 0.2 + 
                       volatility_penalty * 0.15 + debt_penalty * 0.1) * 2 - 1
        
        return max(-1, min(1, contribution))
    
    def generate_recommendations(self, stocks_data: List[StockData], 
                               undervalued_stocks: List[Dict[str, Any]]) -> List[str]:
        """生成交易建议"""
        recommendations = []
        
        if undervalued_stocks:
            # 按PE比率排序，推荐最低估的股票
            sorted_undervalued = sorted(undervalued_stocks, key=lambda x: x['pe_ratio'])
            top_pick = sorted_undervalued[0]
            
            recommendations.append(
                f"买入推荐: {top_pick['symbol']} (PE: {top_pick['pe_ratio']}, "
                f"ROE: {top_pick['roe']*100:.1f}%) - 估值偏低，基本面稳健"
            )
            
            # 仓位建议
            recommendations.append(
                f"建议仓位: 单股不超过15%，总仓位控制在70%以内，预留现金应对市场波动"
            )
        else:
            recommendations.append("当前无明显低估标的，建议持有现金等待更好机会")
        
        # 风险提示
        recommendations.append(
            "风险警示: 港股受中美关系、人民币汇率影响较大，注意地缘政治风险"
        )
        
        recommendations.append(
            f"止损设置: 个股跌幅超过15%或组合回撤达到{self.max_drawdown*100:.0f}%时考虑减仓"
        )
        
        recommendations.append(
            "监控指标: 密切关注美联储政策、中国经济数据和港股通资金流向"
        )
        
        return recommendations[:5]  # 限制为5条建议
    
    def analyze(self, input_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """主分析函数"""
        # 解析输入数据
        stocks_data = []
        for data in input_data:
            stock = StockData(
                symbol=data.get('stock', 'UNKNOWN'),
                close_prices=data.get('close_prices', []),
                eps_estimates=data.get('eps_estimates', []),
                roe=data.get('roe', []),
                debt_equity_ratio=data.get('debt_equity_ratio', 0.5)
            )
            stocks_data.append(stock)
        
        # 识别低估股票
        undervalued_stocks = self.identify_undervalued_stocks(stocks_data)
        
        # 计算平均PE
        pe_values = []
        sharpe_contributions = []
        
        for stock in stocks_data:
            fundamentals = self.assess_fundamental_quality(stock)
            if fundamentals['pe_ratio'] != float('inf'):
                pe_values.append(fundamentals['pe_ratio'])
            
            sharpe_contrib = self.calculate_sharpe_contribution(stock)
            sharpe_contributions.append(sharpe_contrib)
        
        pe_avg = statistics.mean(pe_values) if pe_values else 0.0
        avg_sharpe_contribution = statistics.mean(sharpe_contributions) if sharpe_contributions else 0.0
        
        # 生成建议
        recommendations = self.generate_recommendations(stocks_data, undervalued_stocks)
        
        return {
            "undervalued_stocks": undervalued_stocks,
            "pe_avg": round(pe_avg, 2),
            "sharpe_contribution": round(avg_sharpe_contribution, 3),
            "recommendations": recommendations,
            "analysis_summary": {
                "total_stocks_analyzed": len(stocks_data),
                "undervalued_count": len(undervalued_stocks),
                "market_sentiment": "谨慎乐观" if avg_sharpe_contribution > 0 else "保守观望"
            }
        }

def main():
    """主函数 - 示例用法"""
    # 示例数据
    sample_data = [
        {
            "stock": "0700.HK",  # 腾讯
            "close_prices": [320, 315, 325, 330, 318],
            "eps_estimates": [12.5, 13.2, 12.8, 13.5, 13.0],
            "roe": [0.16, 0.15, 0.17, 0.16, 0.15],
            "debt_equity_ratio": 0.25
        },
        {
            "stock": "0005.HK",  # 汇丰
            "close_prices": [45, 46, 44, 47, 45.5],
            "eps_estimates": [3.2, 3.5, 3.1, 3.6, 3.4],
            "roe": [0.08, 0.09, 0.07, 0.10, 0.09],
            "debt_equity_ratio": 0.15
        },
        {
            "stock": "0941.HK",  # 中国移动
            "close_prices": [58, 60, 57, 59, 58.5],
            "eps_estimates": [4.8, 5.1, 4.9, 5.2, 5.0],
            "roe": [0.12, 0.13, 0.11, 0.14, 0.13],
            "debt_equity_ratio": 0.45
        }
    ]
    
    analyst = HKFundamentalAnalyst()
    result = analyst.analyze(sample_data)
    
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()