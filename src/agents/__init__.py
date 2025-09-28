"""
港股AI代理系统Agent模块

这个模块包含了7个专业的AI Agent实现：
1. 基本面分析代理
2. 技术分析代理
3. 情绪分析代理
4. 新闻分析代理
5. 研究辩论代理
6. 交易代理
7. 风险管理代理

以及代理管理器，负责管理所有代理的生命周期和协调。
"""

from .agent_manager import AgentManager
from .base_agent import BaseAgent

__all__ = [
    "AgentManager",
    "BaseAgent"
]
