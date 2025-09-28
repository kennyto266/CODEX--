"""
基本面分析代理
专门分析股票的基本面指标和财务数据
"""

from typing import List, Dict, Any
from .base_agent import BaseAgent
from src.tools.web_search import web_search
from src.tools.code_execution import execute_python

class FundamentalAgent(BaseAgent):
    """基本面分析代理"""
    
    @property
    def name(self) -> str:
        return "基本面分析代理"
    
    @property
    def icon(self) -> str:
        return "📊"
    
    def generate_prompt(self, market_data: List[Dict[str, Any]]) -> str:
        """生成基本面分析提示词"""
        if not market_data:
            return "无市场数据可供分析"
        
        # 计算基本指标
        prices = [item['close'] for item in market_data]
        volumes = [item['volume'] for item in market_data]
        
        current_price = prices[-1]
        price_change = prices[-1] - prices[0] if len(prices) > 1 else 0
        price_change_pct = (price_change / prices[0] * 100) if len(prices) > 1 and prices[0] != 0 else 0
        avg_volume = sum(volumes) / len(volumes)
        
        return f"""你是一位專門針對港股的量化分析AI代理，角色為「基本面分析代理」（Fundamental Analyst）。你的獨特作用是篩選價值股，計算財務指標以發現低估機會，目標追求高Sharpe Ratio (>1.5) 的交易策略，風險調整回報最大化。

任务：
1. 自主研究：使用web_search工具搜尋"high Sharpe ratio value factor strategies HKEX 2025"，提取低PE/高ROE靈感（如基本面alpha模型）。
2. 分析輸入或自主數據：計算PE比率、ROE、EBITDA成長率；篩選Debt/Equity <1的股票。
3. 發現策略：生成1-2個專屬策略（如基本面再平衡），用code_execution回測Sharpe（pandas處理財務數據）。
4. 評估風險：估計系統風險貢獻，限制高債務曝險。
5. 輸出：JSON {{"discovered_strategy": "...", "value_stocks": [{{"code": "0700.HK", "pe": 12.5}}], "roe_avg": 0.15, "sharpe": 1.6, "recommendations": [...]}}。

输入數據：{{"stocks": ["{market_data[0]['symbol']}"], "close_prices": {prices[-10:]}, "volumes": {volumes[-10:]}}}

思考步骤（ReAct + 工具）：
- Reasoning: 分析港股情境，规划工具调用（如先web_search获灵感，后code_execution验证回测）。
- Acting: 调用工具，生成JSON输出，并解释1-2句关键洞见。

回应僅限JSON + 簡短解釋，不要多餘文字。"""

    async def run_with_local_tools(self, market_data: List[Dict[str, Any]]):
        """使用本地工具完成研究+回测，返回标准结果字典。"""
        symbol = market_data[0]["symbol"] if market_data else "N/A"
        closes = [d["close"] for d in market_data]

        # 1) web_search
        ideas = web_search("high Sharpe ratio value factor strategies HKEX 2025", max_results=3)

        # 2) 本地执行：计算简单Sharpe（无风险率3%年化 ≈ 0.03/252 日化）
        code = (
            "rf = 0.03/252\n"
            "rets = []\n"
            "for i in range(1, len(closes)):\n"
            "    r = (closes[i]-closes[i-1])/closes[i-1]\n"
            "    rets.append(r)\n"
            "avg = sum(rets)/len(rets) if rets else 0.0\n"
            "import math\n"
            "std = math.sqrt(sum([(x-avg)**2 for x in rets])/len(rets)) if rets else 0.0\n"
            "sharpe = ((avg - 0.03/252)/std) if std>0 else 0.0\n"
        )
        exec_out = execute_python(code, {"closes": closes})
        sharpe = 0.0
        if exec_out.get("ok"):
            sharpe = exec_out["result"].get("sharpe", 0.0)

        result = {
            "agent_name": self.name,
            "agent_icon": self.icon,
            "agent_id": "local",
            "status": {"status": "completed"},
            "conversation": {
                "messages": [
                    {"type": "assistant_message", "text": f"discovered_strategy: value + ROE; sample links: {[i['url'] for i in ideas]} ; sharpe={sharpe:.2f}"}
                ]
            }
        }
        return result
