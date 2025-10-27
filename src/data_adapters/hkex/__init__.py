#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HKEX 数据适配器模块

提供从 HKEX 网站提取期货、期权、指数、股票等金融数据的功能。

主要组件:
- HKEXChromeController: Chrome DevTools MCP 控制器
- SelectorDiscoveryEngine: 选择器自动发现引擎
- PageMonitor: 页面变化监控器
- FuturesDataScraper: 期货数据提取器

作者: Claude Code
创建日期: 2025-10-27
"""

from .hkex_chrome_controller import HKEXChromeController, PagePool
from .selector_discovery import (
    SelectorDiscoveryEngine,
    SelectorType,
    SelectorCandidate,
    DiscoveredElement
)
from .page_monitor import (
    PageMonitor,
    MonitoringConfig,
    PageChange,
    ChangeType
)
from .futures_scraper import FuturesDataScraper

__all__ = [
    "HKEXChromeController",
    "PagePool",
    "SelectorDiscoveryEngine",
    "SelectorType",
    "SelectorCandidate",
    "DiscoveredElement",
    "PageMonitor",
    "MonitoringConfig",
    "PageChange",
    "ChangeType",
    "FuturesDataScraper"
]
