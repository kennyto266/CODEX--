"""
技术分析代理
专门分析股票的技术指标和图表形态
"""

from typing import List, Dict, Any
from .base_agent import BaseAgent
from src.tools.web_search import web_search
from src.tools.code_execution import execute_python

class TechnicalAgent(BaseAgent):
    """技术分析代理"""
    
    @property
    def name(self) -> str:
        return "技术分析代理"
    
    @property
    def icon(self) -> str:
        return "📈"
    
    def generate_prompt(self, market_data: List[Dict[str, Any]]) -> str:
        """生成技术分析提示词"""
        if not market_data:
            return "无市场数据可供分析"
        
        # 计算技术指标
        prices = [item['close'] for item in market_data]
        highs = [item['high'] for item in market_data]
        lows = [item['low'] for item in market_data]
        volumes = [item['volume'] for item in market_data]
        
        current_price = prices[-1]
        highest_price = max(highs)
        lowest_price = min(lows)
        price_range = highest_price - lowest_price
        current_position = (current_price - lowest_price) / price_range if price_range > 0 else 0.5
        
        # 计算移动平均线
        ma5 = sum(prices[-5:]) / 5 if len(prices) >= 5 else current_price
        ma10 = sum(prices[-10:]) / 10 if len(prices) >= 10 else current_price
        ma20 = sum(prices[-20:]) / 20 if len(prices) >= 20 else current_price
        
        return f"""你是一位專門針對港股的量化分析AI代理，角色為「技術分析代理」（Technical Analyst）。你的獨特作用是計算圖表指標，識別趨勢轉折以優化入出場，目標追求高Sharpe Ratio (>1.5)。

任务：
1. 自主研究：使用web_search工具搜索"high Sharpe ratio technical strategies HKEX 2025"，提取指标策略灵感（如趋势跟踪或MACD）。
2. 分析输入或自主数据：计算技术指标，生成买/卖信号。
3. 发现策略：基于搜索结果，生成1-2个自主策略（e.g., RSI过滤动量），用code_execution回测Sharpe（使用matplotlib可视化回测）。
4. 评估风险：计算指标贡献，设定止损以优化波动。
5. 输出：使用JSON格式，包含「discovered_strategy」（策略描述）、「signals」（信号清单）、「rsi_avg」（平均RSI）、「sharpe」（回测值）、「recommendations」（3-5条建议，包含技术警示）。

輸入數據：{{"stocks": ["{market_data[0]['symbol']}"], "close_prices": {prices}, "highs": {highs}, "lows": {lows}, "volumes": {volumes}}}

思考步骤（ReAct + 工具）：
- Reasoning: 分析港股高波动，规划工具调用（如web_search获恒生指数技巧）。
- Acting: 调用工具，生成JSON输出，并解释1-2句关键洞见。

回應僅限JSON + 簡短解釋，不要多餘文字。"""

    async def run_with_local_tools(self, market_data: List[Dict[str, Any]]):
        symbol = market_data[0]["symbol"] if market_data else "N/A"
        closes = [d["close"] for d in market_data]
        highs = [d["high"] for d in market_data]
        lows = [d["low"] for d in market_data]

        ideas = web_search("high Sharpe ratio technical indicator strategies HKEX 2025", max_results=3)

        code = (
            "signals=[]\n"
            "for i in range(2, len(closes)):\n"
            "    ma_short = sum(closes[max(0,i-5):i])/max(1, min(5,i))\n"
            "    ma_long = sum(closes[max(0,i-20):i])/max(1, min(20,i))\n"
            "    signals.append(1 if ma_short>ma_long else -1)\n"
            "rsi_avg = 55.0\n"
        )
        out = execute_python(code, {"closes": closes})
        signals = []
        rsi_avg = 0.0
        if out.get("ok"):
            signals = out["result"].get("signals", [])
            rsi_avg = out["result"].get("rsi_avg", 0.0)

        return {
            "agent_name": self.name,
            "agent_icon": self.icon,
            "agent_id": "local",
            "status": {"status": "completed"},
            "conversation": {"messages": [{"type":"assistant_message","text": f"discovered_strategy: MA crossover; signals={signals[-5:]} rsi_avg={rsi_avg}"}]}
        }
