# -*- coding: utf-8 -*-
"""
Personal Workspace System
Provides portfolio management, trade history, personal analytics, and trading journal
"""

from .manager import (
    WorkspaceManager,
    Workspace,
    WorkspaceSettings,
    UserPreferences,
)

from .portfolio import (
    PortfolioManager,
    Portfolio,
    Position,
)

from .trade_history import (
    TradeHistoryManager,
    Trade,
    TradeStats,
)

from .analytics import PersonalAnalytics

from .journal import (
    TradingJournal,
    TradeNote,
    MarketObservation,
    StrategyReflection,
    JournalEntry,
)

__all__ = [
    # Manager
    'WorkspaceManager',
    'Workspace',
    'WorkspaceSettings',
    'UserPreferences',
    # Portfolio
    'PortfolioManager',
    'Portfolio',
    'Position',
    # Trade History
    'TradeHistoryManager',
    'Trade',
    'TradeStats',
    # Analytics
    'PersonalAnalytics',
    # Journal
    'TradingJournal',
    'TradeNote',
    'MarketObservation',
    'StrategyReflection',
    'JournalEntry',
]

__version__ = '1.0.0'
