"""
港股AI代理系统 - Dashboard模块

提供Web界面展示AI代理分析结果。
"""

from .web_server import DashboardServer
from .html_generator import HTMLGenerator

__all__ = [
    "DashboardServer",
    "HTMLGenerator",
]
