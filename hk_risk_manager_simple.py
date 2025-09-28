#!/usr/bin/env python3
"""
港股风险管理代理 (HK Stock Risk Manager) - 简化版
专门针对港股的量化风险分析工具，不依赖外部库
目标：追求高Sharpe Ratio交易策略，风险调整后回报最大化
"""

import json
import math
from typing import Dict, List, Any

class HKRiskManagerSimple:
    """港股风险管理代理 - 简化版"""
    
    def __init__(self, risk_free_rate: float = 0.03):
        self.risk_free_rate = risk_free_rate
        self.target_sharpe = 1.5  # 目标Sharpe Ratio
        self.max_var_threshold = -0.05  # VaR阈值 -5%
        self.max_drawdown_limit = 0.10  # 最大回撤限制 10%
        
    def calculate_percentile(self, data: List[float], percentile: float) -> float:
        """计算百分位数"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        n = len(sorted_data)
        index = (percentile / 100) * (n - 1)
        
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (index - int(index)) * (upper - lower)
    
    def calculate_mean(self, data: List[float]) -> float:
        """计算均值"""
        return sum(data) / len(data) if data else 0.0
    
    def calculate_std(self, data: List[float]) -> float:
        """计算标准差"""
        if len(data) <= 1:
            return 0.0
        mean = self.calculate_mean(data)
        variance = sum((x - mean) ** 2 for x in data) / (len(data) - 1)
        return math.sqrt(variance)
    
    def calculate_var_cvar(self, returns: List[float], confidence_level: float = 0.95) -> Dict[str, float]:
        """计算VaR和CVaR"""
        if not returns:
            return {"var_95": 0.0, "cvar_95": 0.0}
        
        # 计算95% VaR (Value at Risk)
        var_95 = self.calculate_percentile(returns, (1 - confidence_level) * 100)
        
        # 计算95% CVaR (Conditional Value at Risk)
        extreme_losses = [r for r in returns if r <= var_95]
        cvar_95 = self.calculate_mean(extreme_losses) if extreme_losses else var_95
        
        return {
            "var_95": var_95,
            "cvar_95": cvar_95
        }
    
    def calculate_sharpe_ratio(self, returns: List[float]) -> float:
        """计算Sharpe Ratio"""
        if not returns or self.calculate_std(returns) == 0:
            return 0.0
        
        # 计算超额收益
        daily_rf_rate = self.risk_free_rate / 252  # 日化无风险利率
        excess_returns = [r - daily_rf_rate for r in returns]
        
        mean_excess = self.calculate_mean(excess_returns)
        std_excess = self.calculate_std(excess_returns)
        
        if std_excess == 0:
            return 0.0
            
        # 年化Sharpe Ratio
        sharpe_ratio = (mean_excess / std_excess) * math.sqrt(252)
        return sharpe_ratio
    
    def calculate_max_drawdown(self, returns: List[float]) -> float:
        """计算最大回撤"""
        if not returns:
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
                
        return max_drawdown
    
    def check_risk_limits(self, var_95: float, max_drawdown: float, sharpe: float) -> List[Dict[str, Any]]:
        """检查风险限额"""
        risk_limits = []
        
        # VaR限额检查
        if var_95 < self.max_var_threshold:
            risk_limits.append({
                "type": "VaR_BREACH",
                "current": round(var_95, 4),
                "limit": self.max_var_threshold,
                "status": "EXCEEDED",
                "action": "REDUCE_POSITION"
            })
        else:
            risk_limits.append({
                "type": "VaR_CHECK",
                "current": round(var_95, 4),
                "limit": self.max_var_threshold,
                "status": "WITHIN_LIMIT",
                "action": "MONITOR"
            })
        
        # 最大回撤限额检查
        if abs(max_drawdown) > self.max_drawdown_limit:
            risk_limits.append({
                "type": "DRAWDOWN_BREACH",
                "current": round(max_drawdown, 4),
                "limit": -self.max_drawdown_limit,
                "status": "EXCEEDED",
                "action": "HEDGE_POSITION"
            })
        else:
            risk_limits.append({
                "type": "DRAWDOWN_CHECK",
                "current": round(max_drawdown, 4),
                "limit": -self.max_drawdown_limit,
                "status": "WITHIN_LIMIT",
                "action": "CONTINUE"
            })
        
        # Sharpe Ratio目标检查
        if sharpe < self.target_sharpe:
            risk_limits.append({
                "type": "SHARPE_TARGET",
                "current": round(sharpe, 3),
                "target": self.target_sharpe,
                "status": "BELOW_TARGET",
                "action": "OPTIMIZE_STRATEGY"
            })
        else:
            risk_limits.append({
                "type": "SHARPE_TARGET",
                "current": round(sharpe, 3),
                "target": self.target_sharpe,
                "status": "ABOVE_TARGET",
                "action": "MAINTAIN"
            })
            
        return risk_limits
    
    def generate_recommendations(self, returns: List[float], var_95: float, sharpe: float, 
                               max_drawdown: float, risk_limits: List[Dict]) -> List[str]:
        """生成风险建议"""
        recommendations = []
        
        # 基于VaR的建议
        if var_95 < self.max_var_threshold:
            recommendations.append(
                f"⚠️ 警告：VaR({var_95:.3f})超出限额({self.max_var_threshold})，建议立即减仓或对冲恒指期货"
            )
        
        # 基于Sharpe Ratio的建议  
        if sharpe < self.target_sharpe:
            recommendations.append(
                f"📊 Sharpe Ratio({sharpe:.2f})低于目标({self.target_sharpe})，建议优化选股策略或增加动量因子"
            )
        elif sharpe > 2.0:
            recommendations.append(
                f"🎯 优秀的Sharpe Ratio({sharpe:.2f})，建议适度加杠杆但注意流动性风险"
            )
        
        # 港股特有风险建议
        if returns:
            volatility = self.calculate_std(returns) * math.sqrt(252)
            if volatility > 0.25:
                recommendations.append(
                    "🌪️ 港股波动率偏高，建议关注中美关系、港元联系汇率制度风险"
                )
        
        # 黑天鹅情景警示
        if returns:
            extreme_loss_days = len([r for r in returns if r < -0.05]) / len(returns)
            if extreme_loss_days > 0.05:
                recommendations.append(
                    "🦢 检测到频繁极端损失日(>5%)，建议配置港股熊证或恒指看跌期权作为尾部对冲"
                )
        
        # 回撤控制建议
        if abs(max_drawdown) > 0.08:
            recommendations.append(
                f"📉 最大回撤({max_drawdown:.2%})接近限额，建议设置动态止损或使用恒指ETF对冲"
            )
        
        # 确保至少有3条建议
        while len(recommendations) < 3:
            if len(recommendations) == 0:
                recommendations.append("📈 建议定期监控恒生科技指数成分股变化，调整科技股敞口")
            elif len(recommendations) == 1:
                recommendations.append("💰 关注港股通南向资金流向，作为市场情绪指标")
            elif len(recommendations) == 2:
                recommendations.append("🔍 建议使用期权策略进行下行保护，特别是在地缘政治风险期间")
        
        return recommendations[:5]  # 最多5条建议
    
    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """主分析函数 - ReAct模式"""
        try:
            # Reasoning: 先提取和验证数据
            returns = data.get('returns', [])
            risk_free_rate = data.get('risk_free_rate', self.risk_free_rate)
            self.risk_free_rate = risk_free_rate
            
            if not returns:
                raise ValueError("收益率数据不能为空")
            
            # Acting: 计算核心风险指标
            var_cvar = self.calculate_var_cvar(returns)
            sharpe = self.calculate_sharpe_ratio(returns)
            max_drawdown = self.calculate_max_drawdown(returns)
            volatility = self.calculate_std(returns) * math.sqrt(252)
            
            # Reasoning: 审核限额，考虑港股系统风险
            risk_limits = self.check_risk_limits(var_cvar['var_95'], max_drawdown, sharpe)
            
            # Acting: 生成专业建议和情景警示
            recommendations = self.generate_recommendations(
                returns, var_cvar['var_95'], sharpe, max_drawdown, risk_limits
            )
            
            # 风险评估等级
            risk_level = "HIGH" if var_cvar['var_95'] < -0.08 else "MODERATE" if var_cvar['var_95'] < -0.03 else "LOW"
            
            # 构建标准化JSON输出
            result = {
                "var_95": round(var_cvar['var_95'], 4),
                "cvar_95": round(var_cvar['cvar_95'], 4), 
                "sharpe": round(sharpe, 3),
                "max_drawdown": round(max_drawdown, 4),
                "volatility": round(volatility, 3),
                "risk_limits": risk_limits,
                "recommendations": recommendations,
                "analysis_summary": {
                    "total_observations": len(returns),
                    "risk_free_rate": risk_free_rate,
                    "target_sharpe": self.target_sharpe,
                    "risk_assessment": risk_level,
                    "expected_return": round(self.calculate_mean(returns) * 252, 3),  # 年化收益
                    "sharpe_contribution": "POSITIVE" if sharpe > 1.0 else "NEGATIVE"
                }
            }
            
            return result
            
        except Exception as e:
            return {
                "error": f"分析过程中出现错误: {str(e)}",
                "var_95": 0.0,
                "sharpe": 0.0,
                "risk_limits": [],
                "recommendations": ["请检查输入数据格式"]
            }

def main():
    """示例用法和测试"""
    print("=== 港股风险管理代理 - 专业分析报告 ===\n")
    
    # 示例数据 - 模拟港股收益率
    sample_data = {
        "returns": [0.01, -0.02, 0.015, -0.008, 0.025, -0.012, 0.018, -0.035, 0.022, -0.015,
                   0.008, -0.018, 0.012, 0.005, -0.025, 0.030, -0.008, 0.016, -0.012, 0.020],
        "risk_free_rate": 0.03
    }
    
    # 创建风险管理器
    risk_manager = HKRiskManagerSimple()
    
    # 执行分析
    result = risk_manager.analyze(sample_data)
    
    # 输出JSON结果
    print("📊 分析结果 (JSON格式):")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 关键洞见
    if 'error' not in result:
        print(f"\n🎯 关键洞见: Sharpe Ratio为{result['sharpe']:.2f}，VaR为{result['var_95']:.3f}，风险等级为{result['analysis_summary']['risk_assessment']}")
        print(f"💡 投资建议: 当前策略{'符合' if result['sharpe'] >= 1.5 else '不符合'}高Sharpe目标，需要{'保持' if result['analysis_summary']['risk_assessment'] == 'LOW' else '调整'}风险敞口")

if __name__ == "__main__":
    main()