#!/usr/bin/env python3
"""
港股风险管理代理 (HK Stock Risk Manager)
专门针对港股的量化风险分析工具
目标：追求高Sharpe Ratio交易策略，风险调整后回报最大化
"""

import numpy as np
import pandas as pd
import json
from scipy import stats
from typing import Dict, List, Any
import warnings
warnings.filterwarnings('ignore')

class HKRiskManager:
    """港股风险管理代理"""
    
    def __init__(self, risk_free_rate: float = 0.03):
        self.risk_free_rate = risk_free_rate
        self.target_sharpe = 1.5  # 目标Sharpe Ratio
        self.max_var_threshold = -0.05  # VaR阈值 -5%
        self.max_drawdown_limit = 0.10  # 最大回撤限制 10%
        
    def calculate_var_cvar(self, returns: np.array, confidence_level: float = 0.95) -> Dict[str, float]:
        """计算VaR和CVaR"""
        if len(returns) == 0:
            return {"var_95": 0.0, "cvar_95": 0.0}
            
        # 转换为numpy数组
        returns = np.array(returns)
        
        # 计算95% VaR (Value at Risk)
        var_95 = np.percentile(returns, (1 - confidence_level) * 100)
        
        # 计算95% CVaR (Conditional Value at Risk)
        cvar_95 = returns[returns <= var_95].mean() if len(returns[returns <= var_95]) > 0 else var_95
        
        return {
            "var_95": float(var_95),
            "cvar_95": float(cvar_95)
        }
    
    def calculate_sharpe_ratio(self, returns: np.array) -> float:
        """计算Sharpe Ratio"""
        if len(returns) == 0 or np.std(returns) == 0:
            return 0.0
            
        returns = np.array(returns)
        excess_returns = returns - self.risk_free_rate / 252  # 日化无风险利率
        sharpe_ratio = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)
        
        return float(sharpe_ratio)
    
    def calculate_max_drawdown(self, returns: np.array) -> float:
        """计算最大回撤"""
        if len(returns) == 0:
            return 0.0
            
        returns = np.array(returns)
        cumulative = np.cumprod(1 + returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = np.min(drawdown)
        
        return float(max_drawdown)
    
    def check_risk_limits(self, var_95: float, max_drawdown: float, sharpe: float) -> List[Dict[str, Any]]:
        """检查风险限额"""
        risk_limits = []
        
        # VaR限额检查
        if var_95 < self.max_var_threshold:
            risk_limits.append({
                "type": "VaR_BREACH",
                "current": var_95,
                "limit": self.max_var_threshold,
                "status": "EXCEEDED",
                "action": "REDUCE_POSITION"
            })
        else:
            risk_limits.append({
                "type": "VaR_CHECK",
                "current": var_95,
                "limit": self.max_var_threshold,
                "status": "WITHIN_LIMIT",
                "action": "MONITOR"
            })
        
        # 最大回撤限额检查
        if abs(max_drawdown) > self.max_drawdown_limit:
            risk_limits.append({
                "type": "DRAWDOWN_BREACH",
                "current": max_drawdown,
                "limit": -self.max_drawdown_limit,
                "status": "EXCEEDED",
                "action": "HEDGE_POSITION"
            })
        else:
            risk_limits.append({
                "type": "DRAWDOWN_CHECK",
                "current": max_drawdown,
                "limit": -self.max_drawdown_limit,
                "status": "WITHIN_LIMIT",
                "action": "CONTINUE"
            })
        
        # Sharpe Ratio目标检查
        if sharpe < self.target_sharpe:
            risk_limits.append({
                "type": "SHARPE_TARGET",
                "current": sharpe,
                "target": self.target_sharpe,
                "status": "BELOW_TARGET",
                "action": "OPTIMIZE_STRATEGY"
            })
        else:
            risk_limits.append({
                "type": "SHARPE_TARGET",
                "current": sharpe,
                "target": self.target_sharpe,
                "status": "ABOVE_TARGET",
                "action": "MAINTAIN"
            })
            
        return risk_limits
    
    def generate_recommendations(self, returns: np.array, var_95: float, sharpe: float, 
                               max_drawdown: float, risk_limits: List[Dict]) -> List[str]:
        """生成风险建议"""
        recommendations = []
        
        # 基于VaR的建议
        if var_95 < self.max_var_threshold:
            recommendations.append(
                f"警告：VaR({var_95:.3f})超出限额({self.max_var_threshold})，建议立即减仓或对冲恒指期货"
            )
        
        # 基于Sharpe Ratio的建议  
        if sharpe < self.target_sharpe:
            recommendations.append(
                f"Sharpe Ratio({sharpe:.2f})低于目标({self.target_sharpe})，建议优化选股策略或增加动量因子"
            )
        elif sharpe > 2.0:
            recommendations.append(
                f"优秀的Sharpe Ratio({sharpe:.2f})，建议适度加杠杆但注意流动性风险"
            )
        
        # 港股特有风险建议
        volatility = np.std(returns) * np.sqrt(252) if len(returns) > 0 else 0
        if volatility > 0.25:
            recommendations.append(
                "港股波动率偏高，建议关注中美关系、港元联系汇率制度风险"
            )
        
        # 黑天鹅情景警示
        if len(returns) > 0:
            extreme_loss_days = len(returns[returns < -0.05]) / len(returns)
            if extreme_loss_days > 0.05:
                recommendations.append(
                    "检测到频繁极端损失日(>5%)，建议配置港股熊证或恒指看跌期权作为尾部对冲"
                )
        
        # 回撤控制建议
        if abs(max_drawdown) > 0.08:
            recommendations.append(
                f"最大回撤({max_drawdown:.2%})接近限额，建议设置动态止损或使用恒指ETF对冲"
            )
        
        # 确保至少有3条建议
        if len(recommendations) < 3:
            recommendations.append("建议定期监控恒生科技指数成分股变化，调整科技股敞口")
            recommendations.append("关注港股通南向资金流向，作为市场情绪指标")
        
        return recommendations[:5]  # 最多5条建议
    
    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """主分析函数"""
        try:
            # 提取数据
            returns = np.array(data.get('returns', []))
            risk_free_rate = data.get('risk_free_rate', self.risk_free_rate)
            self.risk_free_rate = risk_free_rate
            
            if len(returns) == 0:
                raise ValueError("收益率数据不能为空")
            
            # 计算风险指标
            var_cvar = self.calculate_var_cvar(returns)
            sharpe = self.calculate_sharpe_ratio(returns)
            max_drawdown = self.calculate_max_drawdown(returns)
            
            # 检查风险限额
            risk_limits = self.check_risk_limits(var_cvar['var_95'], max_drawdown, sharpe)
            
            # 生成建议
            recommendations = self.generate_recommendations(
                returns, var_cvar['var_95'], sharpe, max_drawdown, risk_limits
            )
            
            # 构建输出
            result = {
                "var_95": round(var_cvar['var_95'], 4),
                "cvar_95": round(var_cvar['cvar_95'], 4),
                "sharpe": round(sharpe, 3),
                "max_drawdown": round(max_drawdown, 4),
                "volatility": round(np.std(returns) * np.sqrt(252), 3) if len(returns) > 0 else 0,
                "risk_limits": risk_limits,
                "recommendations": recommendations,
                "analysis_summary": {
                    "total_observations": len(returns),
                    "risk_free_rate": risk_free_rate,
                    "target_sharpe": self.target_sharpe,
                    "risk_assessment": "HIGH" if var_cvar['var_95'] < -0.08 else "MODERATE" if var_cvar['var_95'] < -0.03 else "LOW"
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
    """示例用法"""
    # 示例数据
    sample_data = {
        "returns": [0.01, -0.02, 0.015, -0.008, 0.025, -0.012, 0.018, -0.035, 0.022, -0.015],
        "risk_free_rate": 0.03
    }
    
    # 创建风险管理器
    risk_manager = HKRiskManager()
    
    # 执行分析
    result = risk_manager.analyze(sample_data)
    
    # 输出JSON结果
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()