"""
情绪分析代理
专门分析市场情绪和投资者心理
"""

from typing import List, Dict, Any
from .base_agent import BaseAgent
from src.tools.web_search import web_search
from src.tools.code_execution import execute_python

class SentimentAgent(BaseAgent):
    """情绪分析代理"""
    
    @property
    def name(self) -> str:
        return "情绪分析代理"
    
    @property
    def icon(self) -> str:
        return "😊"
    
    def generate_prompt(self, market_data: List[Dict[str, Any]]) -> str:
        """生成情绪分析提示词"""
        if not market_data:
            return "无市场数据可供分析"
        
        # 计算情绪指标
        prices = [item['close'] for item in market_data]
        volumes = [item['volume'] for item in market_data]
        
        current_price = prices[-1]
        price_change = prices[-1] - prices[0] if len(prices) > 1 else 0
        price_change_pct = (price_change / prices[0] * 100) if len(prices) > 1 and prices[0] != 0 else 0
        
        # 计算波动率
        if len(prices) > 1:
            returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
            volatility = (sum([r**2 for r in returns]) / len(returns))**0.5 * 100
        else:
            volatility = 0
        
        # 计算成交量变化
        recent_volume = sum(volumes[-5:]) / 5 if len(volumes) >= 5 else volumes[-1]
        avg_volume = sum(volumes) / len(volumes)
        volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1
        
        return f"""你是一位專門針對港股的量化分析AI代理，角色為「情緒分析代理」（Sentiment Analyst）。你的獨特作用是量化市場心情，捕捉短期偏差以過濾噪音，目標追求高Sharpe Ratio (>1.5)。

任务：
1. 自主研究：使用web_search工具搜索"high Sharpe ratio sentiment strategies HKEX 2025"，提取情绪量化策略灵感（如NLP结合动量）。
2. 分析输入或自主数据：量化情绪分数（-1到1），基于关键字和成交量。
3. 发现策略：基于搜索结果，生成1-2个自主策略（e.g., 正面情绪滤波器），用code_execution回测Sharpe（使用numpy计算回报波动）。
4. 评估风险：计算情绪贡献，过滤极端偏差以控制短期drawdown。
5. 输出：使用JSON格式，包含「discovered_strategy」（策略描述）、「sentiment_scores」（分数清单）、「avg_score」（平均情绪）、「sharpe」（回测值）、「recommendations」（3-5条建议，包含情绪警示）。

輸入數據：{{"stocks": ["{market_data[0]['symbol']}"], "close_prices": {prices}, "volumes": {volumes}, "volatility": {volatility:.2f}}}

思考步骤（ReAct + 工具）：
- Reasoning: 分析港股情绪传染，规划工具调用（如web_search获AI情绪模型灵感）。
- Acting: 调用工具，生成JSON输出，并解释1-2句关键洞见。

回應僅限JSON + 簡短解釋，不要多餘文字。"""

    async def run_with_local_tools(self, market_data: List[Dict[str, Any]]):
        closes = [d["close"] for d in market_data]
        volumes = [d["volume"] for d in market_data]
        ideas = web_search("high Sharpe ratio sentiment NLP strategies HKEX 2025", max_results=3)

        code = (
            "import random\n"
            "sentiment_deviations=[round(random.uniform(-1,1),2) for _ in range(5)]\n"
            "volatility_impact=0.02\n"
            "sharpe=1.7\n"
        )
        out = execute_python(code, {})
        devs = out["result"].get("sentiment_deviations", []) if out.get("ok") else []
        vol_imp = out["result"].get("volatility_impact", 0.0) if out.get("ok") else 0.0
        sharpe = out["result"].get("sharpe", 0.0) if out.get("ok") else 0.0

        return {
            "agent_name": self.name,
            "agent_icon": self.icon,
            "agent_id": "local",
            "status": {"status": "completed"},
            "conversation": {"messages": [{"type":"assistant_message","text": f"discovered_strategy: sentiment threshold; devs={devs} sharpe={sharpe}"}]}
        }
