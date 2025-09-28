#!/usr/bin/env python3
"""
Hong Kong Stock Fundamental Analysis Agent
专门针对港股的基本面分析，追求高Sharpe Ratio策略
"""

import json
from typing import Dict, List, Any
import statistics

class HKFundamentalAnalyst:
    def __init__(self):
        # 港股行业基准数据 (基于恒生指数成分股历史数据)
        self.industry_benchmarks = {
            'tech': {'pe_median': 25.0, 'roe_median': 0.18},
            'finance': {'pe_median': 8.5, 'roe_median': 0.12},
            'utilities': {'pe_median': 12.0, 'roe_median': 0.08},
            'consumer': {'pe_median': 18.0, 'roe_median': 0.15},
            'default': {'pe_median': 16.0, 'roe_median': 0.13}
        }
        
        # 风险参数设置
        self.max_drawdown_target = 0.10  # 10% drawdown限制
        self.target_sharpe = 1.5  # 目标Sharpe比率
        self.debt_equity_threshold = 1.0  # 债务股权比上限
        
    def calculate_pe_ratio(self, close_price: float, eps: float) -> float:
        """计算市盈率 PE = Price / EPS"""
        if eps <= 0:
            return float('inf')  # 负盈利或零盈利
        return close_price / eps
    
    def calculate_growth_rate(self, values: List[float]) -> float:
        """计算YoY增长率"""
        if len(values) < 2:
            return 0.0
        return (values[-1] - values[0]) / values[0] if values[0] != 0 else 0.0
    
    def assess_valuation(self, pe_ratio: float, industry: str = 'default') -> str:
        """评估股票估值水平"""
        benchmark = self.industry_benchmarks[industry]['pe_median']
        
        if pe_ratio < benchmark * 0.7:  # PE < 行业中位数70%
            return 'undervalued'
        elif pe_ratio > benchmark * 1.3:  # PE > 行业中位数130%
            return 'overvalued'
        else:
            return 'fairly_valued'
    
    def calculate_sharpe_contribution(self, pe_ratio: float, roe: float, growth_rate: float) -> float:
        """
        估算对Sharpe Ratio的贡献度 (-1 到 1)
        考虑PE估值、ROE质量、增长率
        """
        # PE贡献 (低PE更好)
        pe_score = max(-1, min(1, (20 - pe_ratio) / 20))
        
        # ROE贡献 (高ROE更好)
        roe_score = max(-1, min(1, (roe - 0.10) / 0.20))
        
        # 增长率贡献
        growth_score = max(-1, min(1, growth_rate / 0.30))
        
        # 加权平均 (PE权重更高，因为追求价值投资)
        contribution = (pe_score * 0.5 + roe_score * 0.3 + growth_score * 0.2)
        return round(contribution, 3)
    
    def analyze_stock_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分析单只股票数据"""
        stock_code = data.get('stock', 'Unknown')
        close_prices = data.get('close_prices', [])
        eps_estimates = data.get('eps_estimates', [])
        roe_values = data.get('roe', [])
        debt_equity = data.get('debt_equity', 0.5)  # 默认债务股权比
        
        if not close_prices or not eps_estimates:
            return {'error': f'Insufficient data for {stock_code}'}
        
        # 使用最新数据计算指标
        latest_price = close_prices[-1]
        latest_eps = eps_estimates[-1]
        latest_roe = roe_values[-1] if roe_values else 0.15
        
        # 计算关键指标
        pe_ratio = self.calculate_pe_ratio(latest_price, latest_eps)
        eps_growth = self.calculate_growth_rate(eps_estimates)
        price_growth = self.calculate_growth_rate(close_prices)
        
        # 估值评估
        industry = self.get_industry_by_stock(stock_code)
        valuation = self.assess_valuation(pe_ratio, industry)
        
        # Sharpe贡献度
        sharpe_contrib = self.calculate_sharpe_contribution(pe_ratio, latest_roe, eps_growth)
        
        # 风险评估
        risk_level = self.assess_risk(debt_equity, pe_ratio, latest_roe)
        
        return {
            'stock_code': stock_code,
            'pe_ratio': round(pe_ratio, 2),
            'roe': round(latest_roe, 3),
            'eps_growth': round(eps_growth, 3),
            'price_growth': round(price_growth, 3),
            'valuation': valuation,
            'sharpe_contribution': sharpe_contrib,
            'risk_level': risk_level,
            'debt_equity': debt_equity
        }
    
    def get_industry_by_stock(self, stock_code: str) -> str:
        """根据股票代码推断行业"""
        # 港股主要股票行业分类
        tech_stocks = ['0700.HK', '9988.HK', '1810.HK', '9618.HK']
        finance_stocks = ['0005.HK', '1398.HK', '3988.HK', '0939.HK']
        
        if stock_code in tech_stocks:
            return 'tech'
        elif stock_code in finance_stocks:
            return 'finance'
        else:
            return 'default'
    
    def assess_risk(self, debt_equity: float, pe_ratio: float, roe: float) -> str:
        """评估风险水平"""
        risk_score = 0
        
        # 债务风险
        if debt_equity > self.debt_equity_threshold:
            risk_score += 2
        
        # 估值风险
        if pe_ratio > 30:
            risk_score += 2
        elif pe_ratio < 5:
            risk_score += 1  # 极低PE可能有隐藏问题
        
        # 盈利质量风险
        if roe < 0.08:
            risk_score += 1
        
        if risk_score >= 4:
            return 'high'
        elif risk_score >= 2:
            return 'medium'
        else:
            return 'low'
    
    def generate_recommendations(self, analysis_results: List[Dict]) -> List[str]:
        """生成交易建议"""
        recommendations = []
        
        # 筛选低估股票
        undervalued = [r for r in analysis_results if r.get('valuation') == 'undervalued' and r.get('risk_level') != 'high']
        
        if undervalued:
            best_stock = max(undervalued, key=lambda x: x.get('sharpe_contribution', -1))
            recommendations.append(f"建议买入 {best_stock['stock_code']}：PE={best_stock['pe_ratio']}，预期Sharpe贡献={best_stock['sharpe_contribution']}")
        
        # 风险警示
        high_risk_stocks = [r for r in analysis_results if r.get('risk_level') == 'high']
        if high_risk_stocks:
            codes = [s['stock_code'] for s in high_risk_stocks]
            recommendations.append(f"风险警示：避免 {', '.join(codes)}，债务或估值风险过高")
        
        # 仓位建议
        avg_sharpe = statistics.mean([r.get('sharpe_contribution', 0) for r in analysis_results])
        if avg_sharpe > 0.3:
            recommendations.append("整体基本面良好，建议适度加仓，控制单股仓位<15%")
        elif avg_sharpe < -0.2:
            recommendations.append("基本面偏弱，建议减仓观望，等待更好入场时机")
        
        # 港股特有风险提示
        recommendations.append("注意中美关系、港股通资金流向对估值影响")
        
        return recommendations[:5]  # 限制在5条以内
    
    def analyze_portfolio(self, input_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析整个组合"""
        if not input_data:
            return {'error': 'No input data provided'}
        
        # 分析每只股票
        analysis_results = []
        for stock_data in input_data:
            result = self.analyze_stock_data(stock_data)
            if 'error' not in result:
                analysis_results.append(result)
        
        if not analysis_results:
            return {'error': 'No valid stock data to analyze'}
        
        # 筛选低估股票
        undervalued_stocks = [
            {'code': r['stock_code'], 'pe': r['pe_ratio'], 'sharpe_contrib': r['sharpe_contribution']}
            for r in analysis_results 
            if r.get('valuation') == 'undervalued' and r.get('risk_level') != 'high'
        ]
        
        # 计算平均指标
        pe_avg = round(statistics.mean([r['pe_ratio'] for r in analysis_results if r['pe_ratio'] != float('inf')]), 2)
        sharpe_avg = round(statistics.mean([r['sharpe_contribution'] for r in analysis_results]), 3)
        
        # 生成建议
        recommendations = self.generate_recommendations(analysis_results)
        
        return {
            'undervalued_stocks': undervalued_stocks,
            'pe_avg': pe_avg,
            'sharpe_contribution': sharpe_avg,
            'recommendations': recommendations,
            'analysis_summary': {
                'total_stocks': len(analysis_results),
                'undervalued_count': len(undervalued_stocks),
                'avg_roe': round(statistics.mean([r['roe'] for r in analysis_results]), 3)
            }
        }

def main():
    """主函数 - 处理示例数据"""
    analyst = HKFundamentalAnalyst()
    
    # 示例输入数据（基于用户提供的格式）
    sample_data = [
        {
            "stock": "0700.HK",  # 腾讯
            "close_prices": [100, 102, 98],
            "eps_estimates": [5.2, 5.5, 5.1],
            "roe": [0.15, 0.16, 0.14],
            "debt_equity": 0.3
        },
        {
            "stock": "0005.HK",  # 汇丰
            "close_prices": [45, 47, 44],
            "eps_estimates": [4.8, 5.0, 4.6],
            "roe": [0.11, 0.12, 0.10],
            "debt_equity": 0.8
        }
    ]
    
    # 执行分析
    result = analyst.analyze_portfolio(sample_data)
    
    # 输出JSON结果
    print("=== 港股基本面分析结果 ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 简短解释
    print("\n=== 关键洞见 ===")
    if result.get('undervalued_stocks'):
        print(f"发现 {len(result['undervalued_stocks'])} 只低估股票，建议重点关注。")
    print(f"组合平均PE={result.get('pe_avg', 'N/A')}，预期Sharpe贡献={result.get('sharpe_contribution', 'N/A')}。")

if __name__ == "__main__":
    main()