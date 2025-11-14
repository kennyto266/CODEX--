"""
个人工作区演示
展示工作区的所有功能
"""

import sys
import os
import json
from datetime import datetime, timedelta
import random

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workspace import (
    WorkspaceManager,
    PortfolioManager,
    TradeHistoryManager,
    PersonalAnalytics,
    TradingJournal,
)


def print_section(title):
    """打印分节标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_json(data):
    """美化打印JSON"""
    print(json.dumps(data, indent=2, ensure_ascii=False, default=str))


def demo_workspace_manager():
    """演示工作区管理器"""
    print_section("1. 工作区管理器演示")

    # 创建工作区管理器
    ws_manager = WorkspaceManager("workspace_data/demo")

    # 创建工作区
    workspace = ws_manager.create_workspace(
        user_id="user_001",
        name="我的投资工作区",
        theme="dark",
        language="zh-TW"
    )

    print(f"✅ 创建工作区: {workspace.settings.name}")
    print(f"   用户ID: {workspace.settings.user_id}")
    print(f"   主题: {workspace.settings.theme}")
    print(f"   语言: {workspace.settings.language}")

    # 更新偏好
    updated = ws_manager.update_workspace(
        user_id="user_001",
        strategy_type="technical",
        risk_tolerance="medium",
        investment_style="growth",
        technical_indicators=['sma', 'rsi', 'macd', 'kdj']
    )

    print(f"\n✅ 更新用户偏好:")
    print(f"   策略类型: {updated.preferences.strategy_type}")
    print(f"   风险承受: {updated.preferences.risk_tolerance}")
    print(f"   投资风格: {updated.preferences.investment_style}")
    print(f"   技术指标: {updated.preferences.technical_indicators}")


def demo_portfolio_manager():
    """演示投资组合管理器"""
    print_section("2. 投资组合管理器演示")

    pf_manager = PortfolioManager("workspace_data/demo/portfolios")

    # 创建投资组合
    portfolio = pf_manager.create_portfolio(
        user_id="user_001",
        name="核心组合",
        initial_cash=100000.0
    )

    print(f"✅ 创建投资组合: {portfolio.name}")
    print(f"   初始现金: ¥{portfolio.cash:,.2f}")

    # 添加持仓
    print(f"\n✅ 添加持仓:")
    positions_data = [
        ("0700.HK", 1000, 380.50),  # 腾讯
        ("0388.HK", 500, 280.30),   # 港交所
        ("1398.HK", 2000, 4.85),    # 工商银行
        ("0939.HK", 1500, 5.20),    # 建设银行
    ]

    for symbol, qty, price in positions_data:
        pf_manager.add_position("user_001", "核心组合", symbol, qty, price)
        print(f"   {symbol}: {qty} 股 @ ¥{price}")

    # 更新价格
    print(f"\n✅ 更新价格:")
    prices = {
        "0700.HK": 385.60,
        "0388.HK": 285.40,
        "1398.HK": 4.90,
        "0939.HK": 5.25
    }
    for symbol, price in prices.items():
        print(f"   {symbol}: ¥{price}")

    pf_manager.update_prices("user_001", "核心组合", prices)

    # 获取组合摘要
    summary = pf_manager.get_portfolio_summary("user_001", "核心组合")
    print(f"\n✅ 组合摘要:")
    print(f"   总价值: ¥{summary['total_value']:,.2f}")
    print(f"   现金: ¥{summary['cash']:,.2f}")
    print(f"   总损益: ¥{summary['total_pnl']:,.2f} ({summary['total_pnl_pct']:+.2f}%)")
    print(f"   日变化: ¥{summary['day_change']:,.2f} ({summary['day_change_pct']:+.2f}%)")
    print(f"   持仓数量: {summary['position_count']}")

    print(f"\n   持仓分布:")
    for symbol, weight in summary['position_weights'].items():
        print(f"     {symbol}: {weight:.2f}%")


def demo_trade_history():
    """演示交易历史管理"""
    print_section("3. 交易历史管理演示")

    trade_manager = TradeHistoryManager("workspace_data/demo/trades")

    # 添加交易记录
    print(f"✅ 添加交易记录:")
    trades_data = [
        ("核心组合", "0700.HK", "buy", 500, 370.00, 50.0, "首次建仓", "kdj"),
        ("核心组合", "0700.HK", "sell", 500, 385.00, 50.0, "获利了结", "kdj"),
        ("核心组合", "0388.HK", "buy", 200, 275.00, 30.0, "看涨港交所", "rsi"),
        ("核心组合", "0388.HK", "sell", 200, 285.00, 30.0, "短线操作", "rsi"),
        ("核心组合", "1398.HK", "buy", 1000, 4.80, 20.0, "价值投资", "sma"),
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
        print(f"   {trade.timestamp[:19]} - {side.upper()} {qty} {symbol} @ ¥{price}")

    # 获取交易统计
    stats = trade_manager.get_statistics("user_001", "核心组合")
    print(f"\n✅ 交易统计:")
    print(f"   总交易次数: {stats.total_trades}")
    print(f"   盈利交易: {stats.winning_trades}")
    print(f"   亏损交易: {stats.losing_trades}")
    print(f"   胜率: {stats.win_rate:.2f}%")
    print(f"   总损益: ¥{stats.total_pnl:,.2f}")
    print(f"   平均盈利: ¥{stats.avg_win:,.2f}")
    print(f"   平均亏损: ¥{stats.avg_loss:,.2f}")
    print(f"   利润因子: {stats.profit_factor:.2f}")
    print(f"   最大盈利: ¥{stats.largest_win:,.2f}")
    print(f"   最大亏损: ¥{stats.largest_loss:,.2f}")
    print(f"   连续盈利: {stats.max_consecutive_wins} 次")
    print(f"   连续亏损: {stats.max_consecutive_losses} 次")
    print(f"   总手续费: ¥{stats.total_fees:,.2f}")

    # 获取股票表现
    symbol_perf = trade_manager.get_symbol_performance("user_001")
    print(f"\n✅ 股票表现:")
    for symbol, perf in symbol_perf.items():
        print(f"   {symbol}:")
        print(f"     交易次数: {perf['total_trades']}")
        print(f"     总损益: ¥{perf['total_pnl']:,.2f}")
        print(f"     买入: {perf['buy_count']} 次")
        print(f"     卖出: {perf['sell_count']} 次")


def demo_analytics():
    """演示个人分析"""
    print_section("4. 个人分析演示")

    # 创建管理器实例
    pf_manager = PortfolioManager("workspace_data/demo/portfolios")
    trade_manager = TradeHistoryManager("workspace_data/demo/trades")
    analytics = PersonalAnalytics(pf_manager, trade_manager)

    # 分析交易行为
    behavior = analytics.analyze_trading_behavior("user_001")
    print(f"✅ 交易行为分析:")
    print(f"   总交易: {behavior['total_trades']} 笔")
    print(f"   胜率: {behavior['win_rate']:.2f}%")
    print(f"   利润因子: {behavior['profit_factor']:.2f}")
    print(f"   平均持仓: {behavior['avg_hold_time_days']:.2f} 天")
    print(f"   总手续费: ¥{behavior['total_fees']:,.2f}")

    print(f"\n   交易时段分布 (小时):")
    for hour, count in sorted(behavior['trading_timing']['hour_distribution'].items()):
        print(f"     {hour:02d}:00 - {count} 笔")

    print(f"\n   盈亏分布:")
    print(f"     盈利: {behavior['pnl_distribution']['positive']} 笔")
    print(f"     持平: {behavior['pnl_distribution']['zero']} 笔")
    print(f"     亏损: {behavior['pnl_distribution']['negative']} 笔")

    print(f"\n   偏好股票:")
    for symbol, count in behavior['favorite_symbols']:
        print(f"     {symbol}: {count} 笔")

    # 分析组合表现
    performance = analytics.analyze_performance("user_001", "核心组合")
    print(f"\n✅ 组合表现分析:")
    print(f"   总回报: {performance['total_return_pct']:+.2f}%")
    print(f"   日回报: {performance['day_return_pct']:+.2f}%")
    print(f"   夏普比率: {performance['sharpe_ratio']:.2f}")
    print(f"   最大回撤: {performance['max_drawdown_pct']:.2f}%")
    print(f"   波动率: {performance['volatility_pct']:.2f}%")
    print(f"   现金占比: {performance['cash_percentage']:.2f}%")

    # 风险概况
    risk = analytics.get_risk_profile("user_001")
    print(f"\n✅ 风险概况:")
    print(f"   风险等级: {risk['risk_level']}")
    print(f"   集中度: {risk['concentration_risk']:.2f}%")
    print(f"   分散化: {risk['diversification']:.2f}%")

    # 获取建议
    recommendations = analytics.get_recommendations("user_001")
    print(f"\n✅ 个性化建议:")
    for rec in recommendations:
        print(f"   [{rec['priority'].upper()}] {rec['title']}")
        print(f"     {rec['message']}")
        print(f"     建议: {rec['action']}\n")

    # 生成报告
    report = analytics.generate_report("user_001", "核心组合")
    print(f"\n✅ 完整分析报告:")
    print(report)


def demo_trading_journal():
    """演示交易日志"""
    print_section("5. 交易日志演示")

    journal = TradingJournal("workspace_data/demo/journal")

    # 添加交易笔记
    print(f"✅ 添加交易笔记:")
    notes_data = [
        ("0700.HK", "entry", "看涨KDJ金叉信号", "kdj", "兴奋", ["技术面", "金叉"]),
        ("0700.HK", "exit", "KDJ高位，考虑获利了结", "kdj", "谨慎", ["技术面", "止盈"]),
        ("0388.HK", "entry", "RSI超卖反弹", "rsi", "期待", ["技术面", "反弹"]),
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
        print(f"   {note.timestamp[:19]} - {note.symbol} ({note.note_type})")
        print(f"     情绪: {note.emotion} | 标签: {', '.join(note.tags)}")
        print(f"     {note.content}\n")

    # 添加市场观察
    print(f"✅ 添加市场观察:")
    obs = journal.add_market_observation(
        user_id="user_001",
        market="港股",
        mood="bullish",
        observations="市场情绪乐观，科技股领涨",
        key_events=["美联储加息预期放缓", "中国政策支持"],
        tags=["宏观", "政策"]
    )
    print(f"   {obs.timestamp[:19]} - {obs.market}")
    print(f"     情绪: {obs.mood}")
    print(f"     事件: {', '.join(obs.key_events)}")
    print(f"     观察: {obs.observations}\n")

    # 添加策略反思
    print(f"✅ 添加策略反思:")
    reflection = journal.add_strategy_reflection(
        user_id="user_001",
        strategy_name="KDJ策略",
        period_start="2024-01-01",
        period_end="2024-03-31",
        performance=8.5,
        what_worked=["金叉信号准确", "高胜率"],
        what_didnt_work=["震荡市频繁假信号"],
        improvements=["加入趋势过滤", "调整参数"],
        overall_rating=7
    )
    print(f"   {reflection.timestamp[:19]} - {reflection.strategy_name}")
    print(f"     期间表现: {reflection.performance}%")
    print(f"     评分: {reflection.overall_rating}/10")
    print(f"     有效: {', '.join(reflection.what_worked)}")
    print(f"     改进: {', '.join(reflection.improvements)}\n")

    # 情绪分析
    emotion_analysis = journal.get_emotion_analysis("user_001")
    print(f"✅ 情绪分析:")
    print(f"   总笔记: {emotion_analysis['total_notes']}")
    print(f"   情绪分布: {emotion_analysis['emotion_distribution']}")

    # 搜索功能
    search_results = journal.search_journal("user_001", "KDJ")
    print(f"\n✅ 搜索 'KDJ' 结果:")
    print(f"   交易笔记: {len(search_results['trade_notes'])} 条")
    print(f"   市场观察: {len(search_results['market_observations'])} 条")
    print(f"   策略反思: {len(search_results['strategy_reflections'])} 条")

    # 活跃标签
    tags = journal.get_most_active_tags("user_001")
    print(f"\n✅ 活跃标签 (Top 5):")
    for tag_info in tags[:5]:
        print(f"   {tag_info['tag']}: {tag_info['count']} 次")


def main():
    """主演示函数"""
    print("\n" + "=" * 60)
    print("  个人工作区系统 - 功能演示")
    print("=" * 60)

    try:
        # 演示各个模块
        demo_workspace_manager()
        demo_portfolio_manager()
        demo_trade_history()
        demo_analytics()
        demo_trading_journal()

        print_section("演示完成")
        print("✅ 所有功能演示完成!")
        print("\n数据已保存到 workspace_data/demo/ 目录")
        print("可以查看以下文件:")
        print("  - workspace_data/demo/portfolios/ - 投资组合数据")
        print("  - workspace_data/demo/trades/ - 交易历史")
        print("  - workspace_data/demo/journal/ - 交易日志")

    except Exception as e:
        print(f"\n❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
