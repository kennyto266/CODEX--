"""
Workspace Demo - English Version
Showcases all workspace functionality
"""

import sys
import os
import json
from datetime import datetime, timedelta
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workspace import (
    WorkspaceManager,
    PortfolioManager,
    TradeHistoryManager,
    PersonalAnalytics,
    TradingJournal,
)


def print_section(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_json(data):
    print(json.dumps(data, indent=2, ensure_ascii=False, default=str))


def demo_workspace_manager():
    print_section("1. Workspace Manager Demo")

    ws_manager = WorkspaceManager("workspace_data/demo")

    workspace = ws_manager.create_workspace(
        user_id="user_001",
        name="My Investment Workspace",
        theme="dark",
        language="en"
    )

    print(f"Created workspace: {workspace.settings.name}")
    print(f"  User ID: {workspace.settings.user_id}")
    print(f"  Theme: {workspace.settings.theme}")
    print(f"  Language: {workspace.settings.language}")

    updated = ws_manager.update_workspace(
        user_id="user_001",
        strategy_type="technical",
        risk_tolerance="medium",
        investment_style="growth",
        technical_indicators=['sma', 'rsi', 'macd', 'kdj']
    )

    print(f"\nUpdated preferences:")
    print(f"  Strategy: {updated.preferences.strategy_type}")
    print(f"  Risk: {updated.preferences.risk_tolerance}")
    print(f"  Style: {updated.preferences.investment_style}")
    print(f"  Indicators: {updated.preferences.technical_indicators}")


def demo_portfolio_manager():
    print_section("2. Portfolio Manager Demo")

    pf_manager = PortfolioManager("workspace_data/demo/portfolios")

    portfolio = pf_manager.create_portfolio(
        user_id="user_001",
        name="Core Portfolio",
        initial_cash=100000.0
    )

    print(f"Created portfolio: {portfolio.name}")
    print(f"  Initial cash: ${portfolio.cash:,.2f}")

    print(f"\nAdding positions:")
    positions_data = [
        ("0700.HK", 1000, 380.50),
        ("0388.HK", 500, 280.30),
        ("1398.HK", 2000, 4.85),
        ("0939.HK", 1500, 5.20),
    ]

    for symbol, qty, price in positions_data:
        pf_manager.add_position("user_001", "Core Portfolio", symbol, qty, price)
        print(f"  {symbol}: {qty} shares @ ${price}")

    print(f"\nUpdating prices:")
    prices = {
        "0700.HK": 385.60,
        "0388.HK": 285.40,
        "1398.HK": 4.90,
        "0939.HK": 5.25
    }
    for symbol, price in prices.items():
        print(f"  {symbol}: ${price}")

    pf_manager.update_prices("user_001", "Core Portfolio", prices)

    summary = pf_manager.get_portfolio_summary("user_001", "Core Portfolio")
    print(f"\nPortfolio summary:")
    print(f"  Total value: ${summary['total_value']:,.2f}")
    print(f"  Cash: ${summary['cash']:,.2f}")
    print(f"  Total P&L: ${summary['total_pnl']:,.2f} ({summary['total_pnl_pct']:+.2f}%)")
    print(f"  Day change: ${summary['day_change']:,.2f} ({summary['day_change_pct']:+.2f}%)")
    print(f"  Positions: {summary['position_count']}")

    print(f"\n  Position weights:")
    for symbol, weight in summary['position_weights'].items():
        print(f"    {symbol}: {weight:.2f}%")


def demo_trade_history():
    print_section("3. Trade History Demo")

    trade_manager = TradeHistoryManager("workspace_data/demo/trades")

    print(f"Adding trades:")
    trades_data = [
        ("Core Portfolio", "0700.HK", "buy", 500, 370.00, 50.0, "Initial position", "kdj"),
        ("Core Portfolio", "0700.HK", "sell", 500, 385.00, 50.0, "Profit taking", "kdj"),
        ("Core Portfolio", "0388.HK", "buy", 200, 275.00, 30.0, "Bullish on HKEX", "rsi"),
        ("Core Portfolio", "0388.HK", "sell", 200, 285.00, 30.0, "Short-term trade", "rsi"),
        ("Core Portfolio", "1398.HK", "buy", 1000, 4.80, 20.0, "Value play", "sma"),
    ]

    for portfolio, symbol, side, qty, price, fees, note, strategy in trades_data:
        trade = trade_manager.add_trade(
            user_id="user_001",
            portfolio_name=portfolio,
            symbol=symbol,
            side=side,
            quantity=qty,
            price=price,
            fees=fees,
            notes=note,
            strategy=strategy
        )
        print(f"  {trade.timestamp[:19]} - {side.upper()} {qty} {symbol} @ ${price}")

    stats = trade_manager.get_statistics("user_001", "Core Portfolio")
    print(f"\nTrade statistics:")
    print(f"  Total trades: {stats.total_trades}")
    print(f"  Winning trades: {stats.winning_trades}")
    print(f"  Losing trades: {stats.losing_trades}")
    print(f"  Win rate: {stats.win_rate:.2f}%")
    print(f"  Total P&L: ${stats.total_pnl:,.2f}")
    print(f"  Average win: ${stats.avg_win:,.2f}")
    print(f"  Average loss: ${stats.avg_loss:,.2f}")
    print(f"  Profit factor: {stats.profit_factor:.2f}")
    print(f"  Max win: ${stats.largest_win:,.2f}")
    print(f"  Max loss: ${stats.largest_loss:,.2f}")
    print(f"  Consecutive wins: {stats.max_consecutive_wins}")
    print(f"  Consecutive losses: {stats.max_consecutive_losses}")
    print(f"  Total fees: ${stats.total_fees:,.2f}")


def demo_analytics():
    print_section("4. Personal Analytics Demo")

    pf_manager = PortfolioManager("workspace_data/demo/portfolios")
    trade_manager = TradeHistoryManager("workspace_data/demo/trades")
    analytics = PersonalAnalytics(pf_manager, trade_manager)

    behavior = analytics.analyze_trading_behavior("user_001")
    print(f"Trading behavior analysis:")
    print(f"  Total trades: {behavior.get('total_trades', 0)}")
    if 'win_rate' in behavior:
        print(f"  Win rate: {behavior['win_rate']:.2f}%")
        print(f"  Profit factor: {behavior['profit_factor']:.2f}")
        print(f"  Avg hold time: {behavior['avg_hold_time_days']:.2f} days")
        print(f"  Total fees: ${behavior['total_fees']:,.2f}")
    else:
        print(f"  Message: {behavior.get('message', 'No data')}")

    if 'pnl_distribution' in behavior:
        print(f"\n  P&L distribution:")
        print(f"    Profitable: {behavior['pnl_distribution']['positive']}")
        print(f"    Breakeven: {behavior['pnl_distribution']['zero']}")
        print(f"    Losing: {behavior['pnl_distribution']['negative']}")

        print(f"\n  Favorite symbols:")
        for symbol, count in behavior['favorite_symbols']:
            print(f"    {symbol}: {count} trades")

    performance = analytics.analyze_performance("user_001", "Core Portfolio")
    print(f"\nPortfolio performance:")
    print(f"  Total return: {performance['total_return_pct']:+.2f}%")
    print(f"  Day return: {performance['day_return_pct']:+.2f}%")
    print(f"  Sharpe ratio: {performance['sharpe_ratio']:.2f}")
    print(f"  Max drawdown: {performance['max_drawdown_pct']:.2f}%")
    print(f"  Volatility: {performance['volatility_pct']:.2f}%")
    print(f"  Cash %: {performance['cash_percentage']:.2f}%")

    risk = analytics.get_risk_profile("user_001")
    print(f"\nRisk profile:")
    print(f"  Risk level: {risk['risk_level']}")
    print(f"  Concentration: {risk['concentration_risk']:.2f}%")
    print(f"  Diversification: {risk['diversification']:.2f}%")

    recommendations = analytics.get_recommendations("user_001")
    print(f"\nRecommendations:")
    for rec in recommendations:
        print(f"  [{rec['priority'].upper()}] {rec['title']}")
        print(f"    {rec['message']}")
        print(f"    Action: {rec['action']}\n")


def demo_trading_journal():
    print_section("5. Trading Journal Demo")

    journal = TradingJournal("workspace_data/demo/journal")

    print(f"Adding trade notes:")
    notes_data = [
        ("0700.HK", "entry", "Bullish on KDJ golden cross", "kdj", "excited", ["technical", "golden-cross"]),
        ("0700.HK", "exit", "KDJ high, consider profit taking", "kdj", "cautious", ["technical", "profit-taking"]),
        ("0388.HK", "entry", "RSI oversold bounce", "rsi", "hopeful", ["technical", "reversal"]),
    ]

    for symbol, note_type, content, strategy, emotion, tags in notes_data:
        note = journal.add_trade_note(
            user_id="user_001",
            symbol=symbol,
            note_type=note_type,
            content=content,
            strategy=strategy,
            emotion=emotion,
            tags=tags
        )
        print(f"  {note.timestamp[:19]} - {note.symbol} ({note.note_type})")
        print(f"    Emotion: {note.emotion} | Tags: {', '.join(note.tags)}")
        print(f"    {note.content}\n")

    print(f"Adding market observation:")
    obs = journal.add_market_observation(
        user_id="user_001",
        market="Hong Kong",
        mood="bullish",
        observations="Market sentiment optimistic, tech stocks lead",
        key_events=["Fed pause expected", "China policy support"],
        tags=["macro", "policy"]
    )
    print(f"  {obs.timestamp[:19]} - {obs.market}")
    print(f"    Mood: {obs.mood}")
    print(f"    Events: {', '.join(obs.key_events)}")
    print(f"    Notes: {obs.observations}\n")

    print(f"Adding strategy reflection:")
    reflection = journal.add_strategy_reflection(
        user_id="user_001",
        strategy_name="KDJ Strategy",
        period_start="2024-01-01",
        period_end="2024-03-31",
        performance=8.5,
        what_worked=["Golden cross accuracy", "High win rate"],
        what_didnt_work=["Frequent false signals in choppy market"],
        improvements=["Add trend filter", "Adjust parameters"],
        overall_rating=7
    )
    print(f"  {reflection.timestamp[:19]} - {reflection.strategy_name}")
    print(f"    Performance: {reflection.performance}%")
    print(f"    Rating: {reflection.overall_rating}/10")
    print(f"    What worked: {', '.join(reflection.what_worked)}")
    print(f"    Improvements: {', '.join(reflection.improvements)}\n")

    emotion_analysis = journal.get_emotion_analysis("user_001")
    print(f"Emotion analysis:")
    print(f"  Total notes: {emotion_analysis['total_notes']}")
    print(f"  Distribution: {emotion_analysis['emotion_distribution']}")

    search_results = journal.search_journal("user_001", "KDJ")
    print(f"\nSearch 'KDJ' results:")
    print(f"  Trade notes: {len(search_results['trade_notes'])}")
    print(f"  Market observations: {len(search_results['market_observations'])}")
    print(f"  Strategy reflections: {len(search_results['strategy_reflections'])}")

    tags = journal.get_most_active_tags("user_001")
    print(f"\nMost active tags (Top 5):")
    for tag_info in tags[:5]:
        print(f"  {tag_info['tag']}: {tag_info['count']} times")


def main():
    print("\n" + "=" * 60)
    print("  Personal Workspace System - Feature Demo")
    print("=" * 60)

    try:
        demo_workspace_manager()
        demo_portfolio_manager()
        demo_trade_history()
        demo_analytics()
        demo_trading_journal()

        print_section("Demo Complete")
        print("All features demonstrated successfully!")
        print("\nData saved to workspace_data/demo/ directory")
        print("Check the following files:")
        print("  - workspace_data/demo/portfolios/ - Portfolio data")
        print("  - workspace_data/demo/trades/ - Trade history")
        print("  - workspace_data/demo/journal/ - Trading journal")

    except Exception as e:
        print(f"\nError during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
