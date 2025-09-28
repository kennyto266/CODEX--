#!/usr/bin/env python3
"""
港股风险管理代理 (Hong Kong Stock Risk Manager)
专门针对港股的量化风险分析工具
目标：追求高Sharpe Ratio (>1.5)，控制风险调整后回报
"""

import json
import math
from typing import Dict, List, Any

class HKStockRiskManager:
    """港股风险管理代理"""
    
    def __init__(self, risk_free_rate: float = 0.03):
        self.risk_free_rate = risk_free_rate
        self.target_sharpe = 1.5
        self.max_var_threshold = -0.05  # VaR > -5%
        self.max_drawdown_limit = 0.10  # 最大回撤 < 10%
        
    def calculate_var_cvar(self, returns: List[float], confidence: float = 0.95) -> Dict[str, float]:
        """计算VaR和CVaR"""
        if len(returns) == 0:
            return {"var_95": 0.0, "cvar_95": 0.0}
            
        # 计算95% VaR (历史模拟法)
        sorted_returns = sorted(returns)
        var_index = int((1 - confidence) * len(sorted_returns))
        var_95 = sorted_returns[var_index] if var_index < len(sorted_returns) else sorted_returns[0]
        
        # 计算95% CVaR (条件VaR)
        tail_returns = [r for r in returns if r <= var_95]
        cvar_95 = sum(tail_returns) / len(tail_returns) if len(tail_returns) > 0 else var_95
        
        return {
            "var_95": float(var_95),
            "cvar_95": float(cvar_95)
        }
    
    def calculate_sharpe_ratio(self, returns: List[float]) -> float:
        """计算Sharpe比率"""
        if len(returns) == 0:
            return 0.0
            
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        std_return = math.sqrt(variance)
        
        if std_return == 0:
            return 0.0
            
        excess_returns = mean_return - self.risk_free_rate / 252  # 日化无风险利率
        return float(excess_returns / std_return * math.sqrt(252))  # 年化Sharpe
    
    def calculate_max_drawdown(self, returns: List[float]) -> float:
        """计算最大回撤"""
        if len(returns) == 0:
            return 0.0
            
        # 计算累积收益
        cumulative = [1.0]
        for r in returns:
            cumulative.append(cumulative[-1] * (1 + r))
        
        # 计算回撤
        max_drawdown = 0.0
        peak = cumulative[0]
        
        for value in cumulative[1:]:
            if value > peak:
                peak = value
            drawdown = (value - peak) / peak
            if drawdown < max_drawdown:
                max_drawdown = drawdown
                
        return float(max_drawdown)
    
    def stress_test_hk_market(self, returns: List[float]) -> Dict[str, Any]:
        """港股黑天鹅压力测试"""
        scenarios = {
            "2008_financial_crisis": -0.30,  # 2008年金融危机
            "2020_covid_crash": -0.25,       # 2020年疫情暴跌
            "china_policy_shock": -0.20,     # 中国政策冲击
            "us_interest_hike": -0.15        # 美联储加息冲击
        }
        
        stress_results = {}
        original_var = self.calculate_var_cvar(returns)["var_95"]
        
        for scenario, shock in scenarios.items():
            stressed_returns = returns + [shock]
            stressed_var = self.calculate_var_cvar(stressed_returns)["var_95"]
            stressed_sharpe = self.calculate_sharpe_ratio(stressed_returns)
            
            stress_results[scenario] = {
                "shock_magnitude": shock,
                "stressed_var": stressed_var,
                "stressed_sharpe": stressed_sharpe,
                "var_deterioration": stressed_var - original_var
            }
        
        return stress_results
    
    def generate_risk_limits(self, current_metrics: Dict[str, float]) -> List[str]:
        """生成风险限额清单"""
        limits = []
        
        # VaR限额检查
        if current_metrics["var_95"] <= self.max_var_threshold:
            limits.append(f"⚠️ VaR违规: {current_metrics['var_95']:.2%} < {self.max_var_threshold:.1%} (限额)")
        else:
            limits.append(f"✅ VaR合规: {current_metrics['var_95']:.2%} > {self.max_var_threshold:.1%}")
        
        # Sharpe比率检查
        if current_metrics["sharpe"] < self.target_sharpe:
            limits.append(f"⚠️ Sharpe不达标: {current_metrics['sharpe']:.2f} < {self.target_sharpe} (目标)")
        else:
            limits.append(f"✅ Sharpe达标: {current_metrics['sharpe']:.2f} ≥ {self.target_sharpe}")
        
        # 最大回撤检查
        if abs(current_metrics.get("max_drawdown", 0)) > self.max_drawdown_limit:
            limits.append(f"⚠️ 回撤超限: {current_metrics.get('max_drawdown', 0):.2%} < -{self.max_drawdown_limit:.1%}")
        else:
            limits.append(f"✅ 回撤可控: {current_metrics.get('max_drawdown', 0):.2%} > -{self.max_drawdown_limit:.1%}")
        
        return limits
    
    def generate_recommendations(self, metrics: Dict[str, float], stress_results: Dict[str, Any]) -> List[str]:
        """生成风险管理建议"""
        recommendations = []
        
        # 基于Sharpe比率的建议
        if metrics["sharpe"] < 1.0:
            recommendations.append("🔴 建议减仓: Sharpe<1，风险调整收益不佳，考虑降低仓位或优化选股")
        elif metrics["sharpe"] < self.target_sharpe:
            recommendations.append("🟡 谨慎操作: Sharpe偏低，建议加强风控，关注港股政策风险")
        else:
            recommendations.append("🟢 策略良好: Sharpe达标，可维持当前配置，但需持续监控")
        
        # 基于VaR的建议
        if metrics["var_95"] <= -0.10:
            recommendations.append("🔴 高风险警示: VaR<-10%，建议立即对冲或减仓，关注恒指期货套保")
        elif metrics["var_95"] <= self.max_var_threshold:
            recommendations.append("🟡 风险提醒: VaR接近限额，建议分散投资，增加防御性港股")
        
        # 压力测试建议
        worst_scenario = min(stress_results.items(), key=lambda x: x[1]["stressed_sharpe"])
        recommendations.append(f"📊 压力测试: {worst_scenario[0]}情景下Sharpe将降至{worst_scenario[1]['stressed_sharpe']:.2f}")
        
        # 港股特色建议
        recommendations.append("🇭🇰 港股特别提醒: 关注中美关系、港币汇率、南向资金流向等系统性风险因子")
        
        return recommendations[:5]  # 限制为3-5条建议
    
    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """主分析函数"""
        returns = data.get("returns", [])
        
        if len(returns) == 0:
            return {
                "error": "输入数据为空",
                "var_95": 0.0,
                "sharpe": 0.0,
                "risk_limits": ["❌ 无有效数据"],
                "recommendations": ["请提供有效的收益率数据"]
            }
        
        # 计算核心指标
        var_cvar = self.calculate_var_cvar(returns)
        sharpe = self.calculate_sharpe_ratio(returns)
        max_dd = self.calculate_max_drawdown(returns)
        
        metrics = {
            "var_95": var_cvar["var_95"],
            "cvar_95": var_cvar["cvar_95"],
            "sharpe": sharpe,
            "max_drawdown": max_dd
        }
        
        # 压力测试
        stress_results = self.stress_test_hk_market(returns)
        
        # 生成限额和建议
        risk_limits = self.generate_risk_limits(metrics)
        recommendations = self.generate_recommendations(metrics, stress_results)
        
        return {
            "var_95": round(var_cvar["var_95"], 4),
            "cvar_95": round(var_cvar["cvar_95"], 4),
            "sharpe": round(sharpe, 3),
            "max_drawdown": round(max_dd, 4),
            "risk_limits": risk_limits,
            "recommendations": recommendations,
            "stress_test": stress_results,
            "analysis_summary": {
                "risk_level": "高风险" if var_cvar["var_95"] <= -0.10 else "中风险" if var_cvar["var_95"] <= -0.05 else "低风险",
                "sharpe_rating": "优秀" if sharpe >= 2.0 else "良好" if sharpe >= 1.5 else "一般" if sharpe >= 1.0 else "较差",
                "overall_score": round(min(100, max(0, (sharpe * 30 + (1 + var_cvar["var_95"]) * 70))), 1)
            }
        }

def main():
    """主函数 - 示例分析"""
    # 示例港股数据
    sample_data = {
        "returns": [0.01, -0.02, 0.015, -0.008, 0.025, -0.012, 0.018, -0.005, 0.009, -0.015],
        "risk_free_rate": 0.03
    }
    
    # 创建风险管理器
    risk_manager = HKStockRiskManager(risk_free_rate=sample_data["risk_free_rate"])
    
    # 执行分析
    result = risk_manager.analyze(sample_data)
    
    # 输出JSON结果
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    return result

if __name__ == "__main__":
    main()