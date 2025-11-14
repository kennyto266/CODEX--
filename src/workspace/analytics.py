"""
個人分析
提供個人化的交易分析和洞察
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from .portfolio import PortfolioManager
from .trade_history import TradeHistoryManager

logger = logging.getLogger(__name__)


class PersonalAnalytics:
    """個人分析引擎"""

    def __init__(self, portfolio_manager: PortfolioManager, trade_manager: TradeHistoryManager):
        self.portfolio_manager = portfolio_manager
        self.trade_manager = trade_manager

    def analyze_trading_behavior(self, user_id: str) -> Dict[str, Any]:
        """
        分析交易行為

        Args:
            user_id: 用戶ID

        Returns:
            交易行為分析
        """
        trades = self.trade_manager.get_trades(user_id)

        if not trades:
            return {
                'total_trades': 0,
                'message': 'No trading data available'
            }

        # 計算基本統計
        stats = self.trade_manager.get_statistics(user_id)

        # 分析交易時機
        trade_times = [datetime.fromisoformat(t.timestamp) for t in trades]
        hour_distribution = {}
        weekday_distribution = {}

        for time in trade_times:
            hour = time.hour
            weekday = time.weekday()  # 0=Monday

            hour_distribution[hour] = hour_distribution.get(hour, 0) + 1
            weekday_distribution[weekday] = weekday_distribution.get(weekday, 0) + 1

        # 找出最常交易的時段
        peak_hour = max(hour_distribution.items(), key=lambda x: x[1]) if hour_distribution else None
        peak_weekday = max(weekday_distribution.items(), key=lambda x: x[1]) if weekday_distribution else None

        # 分析盈虧分布
        pnl_values = [t.pnl for t in trades]
        pnl_distribution = {
            'positive': len([p for p in pnl_values if p > 0]),
            'zero': len([p for p in pnl_values if p == 0]),
            'negative': len([p for p in pnl_values if p < 0]),
        }

        # 計算平均持有時間（簡化版）
        symbol_trades = {}
        for trade in trades:
            if trade.symbol not in symbol_trades:
                symbol_trades[trade.symbol] = []
            symbol_trades[trade.symbol].append(trade)

        hold_times = []
        for symbol, trades_list in symbol_trades.items():
            if len(trades_list) >= 2:
                # 按時間排序
                trades_list.sort(key=lambda t: t.timestamp)
                # 假設buy-sell配對計算持有時間
                for i in range(0, len(trades_list) - 1, 2):
                    if i + 1 < len(trades_list):
                        buy_time = datetime.fromisoformat(trades_list[i].timestamp)
                        sell_time = datetime.fromisoformat(trades_list[i + 1].timestamp)
                        hold_days = (sell_time - buy_time).days
                        hold_times.append(hold_days)

        avg_hold_time = np.mean(hold_times) if hold_times else 0

        # 最喜歡交易的股票
        symbol_counts = {}
        for trade in trades:
            symbol_counts[trade.symbol] = symbol_counts.get(trade.symbol, 0) + 1

        favorite_symbols = sorted(symbol_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        # 策略使用情況
        strategy_counts = {}
        for trade in trades:
            strategy = trade.strategy or 'Unknown'
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1

        return {
            'total_trades': stats.total_trades,
            'win_rate': stats.win_rate,
            'profit_factor': stats.profit_factor,
            'avg_trade': stats.avg_trade,
            'total_pnl': stats.total_pnl,
            'total_fees': stats.total_fees,
            'trading_timing': {
                'peak_hour': peak_hour[0] if peak_hour else None,
                'peak_weekday': peak_weekday[0] if peak_weekday else None,
                'hour_distribution': hour_distribution,
                'weekday_distribution': weekday_distribution,
            },
            'pnl_distribution': pnl_distribution,
            'avg_hold_time_days': round(avg_hold_time, 2),
            'favorite_symbols': favorite_symbols,
            'strategy_usage': strategy_counts,
        }

    def analyze_performance(self, user_id: str, portfolio_name: str) -> Dict[str, Any]:
        """
        分析組合表現

        Args:
            user_id: 用戶ID
            portfolio_name: 組合名稱

        Returns:
            表現分析
        """
        portfolio = self.portfolio_manager.get_portfolio(user_id, portfolio_name)
        if not portfolio:
            return {'error': 'Portfolio not found'}

        # 獲取交易統計
        stats = self.trade_manager.get_statistics(user_id, portfolio_name)

        # 獲取每日PNL
        daily_pnl = self.trade_manager.get_daily_pnl_series(user_id)

        # 計算表現指標
        performance = {
            'total_return_pct': portfolio.total_pnl_pct,
            'day_return_pct': portfolio.day_change_pct,
            'win_rate': stats.win_rate,
            'profit_factor': stats.profit_factor,
            'total_trades': stats.total_trades,
            'position_count': len(portfolio.positions),
            'cash_percentage': (portfolio.cash / portfolio.total_value * 100) if portfolio.total_value > 0 else 100,
        }

        # 風險指標
        if len(daily_pnl) > 1:
            daily_returns = daily_pnl['pnl'].pct_change().dropna()
            if len(daily_returns) > 0:
                volatility = daily_returns.std() * np.sqrt(252) * 100  # 年化波動率
                sharpe_ratio = daily_returns.mean() / daily_returns.std() * np.sqrt(252) if daily_returns.std() > 0 else 0

                performance['volatility_pct'] = round(volatility, 2)
                performance['sharpe_ratio'] = round(sharpe_ratio, 2)
            else:
                performance['volatility_pct'] = 0
                performance['sharpe_ratio'] = 0
        else:
            performance['volatility_pct'] = 0
            performance['sharpe_ratio'] = 0

        # 最大回撤（簡化）
        cumulative_pnl = daily_pnl['pnl'].cumsum()
        running_max = cumulative_pnl.expanding().max()
        drawdown = (cumulative_pnl - running_max) / running_max * 100
        max_drawdown = drawdown.min() if len(drawdown) > 0 else 0

        performance['max_drawdown_pct'] = round(max_drawdown, 2)

        return performance

    def get_risk_profile(self, user_id: str) -> Dict[str, Any]:
        """
        獲取風險概況

        Args:
            user_id: 用戶ID

        Returns:
            風險概況
        """
        portfolios = self.portfolio_manager.list_portfolios(user_id)

        if not portfolios:
            return {'message': 'No portfolios found'}

        risk_metrics = {
            'portfolio_count': len(portfolios),
            'diversification': 0,
            'concentration_risk': 0,
            'volatility': 0,
            'risk_level': 'Unknown',
        }

        total_value = 0
        max_weight = 0

        for portfolio_name in portfolios:
            portfolio = self.portfolio_manager.get_portfolio(user_id, portfolio_name)
            if portfolio:
                total_value += portfolio.total_value

                # 計算最大權重
                for pos in portfolio.positions.values():
                    weight = (pos.quantity * pos.current_price) / portfolio.total_value if portfolio.total_value > 0 else 0
                    max_weight = max(max_weight, weight)

        if total_value > 0:
            # 集中度風險
            risk_metrics['concentration_risk'] = max_weight * 100

            # 分散化程度（簡化）
            if len(portfolios) > 1:
                risk_metrics['diversification'] = 100
            else:
                risk_metrics['diversification'] = 50

        # 風險等級
        if max_weight > 0.5:
            risk_level = 'High'
        elif max_weight > 0.3:
            risk_level = 'Medium'
        else:
            risk_level = 'Low'

        risk_metrics['risk_level'] = risk_level

        return risk_metrics

    def get_recommendations(self, user_id: str) -> List[Dict[str, Any]]:
        """
        獲取個人化建議

        Args:
            user_id: 用戶ID

        Returns:
            建議列表
        """
        recommendations = []

        # 交易行為分析
        behavior = self.analyze_trading_behavior(user_id)

        if behavior.get('total_trades', 0) > 0:
            # 勝率建議
            win_rate = behavior.get('win_rate', 0)
            if win_rate < 40:
                recommendations.append({
                    'type': 'performance',
                    'priority': 'high',
                    'title': 'Improve Win Rate',
                    'message': f'Your win rate is {win_rate:.1f}%. Consider improving your entry timing or using additional filters.',
                    'action': 'Review your trading strategy and consider adding more filters or improving risk management.'
                })

            # 手續費建議
            total_fees = behavior.get('total_fees', 0)
            if total_fees > 0:
                avg_trade_value = sum(t.value for t in self.trade_manager.get_trades(user_id)) / behavior['total_trades']
                fee_ratio = total_fees / (avg_trade_value * behavior['total_trades']) * 100
                if fee_ratio > 1:
                    recommendations.append({
                        'type': 'cost',
                        'priority': 'medium',
                        'title': 'High Transaction Costs',
                        'message': f'Your average transaction cost is {fee_ratio:.2f}% of trade value.',
                        'action': 'Consider reducing trading frequency or switching to a broker with lower fees.'
                    })

        # 風險分析
        risk = self.get_risk_profile(user_id)
        concentration = risk.get('concentration_risk', 0)

        if concentration > 50:
            recommendations.append({
                'type': 'risk',
                'priority': 'high',
                'title': 'High Concentration Risk',
                'message': f'{concentration:.1f}% of your portfolio is in a single position.',
                'action': 'Consider diversifying your holdings to reduce risk.'
            })

        # 現金比例建議
        for portfolio_name in self.portfolio_manager.list_portfolios(user_id):
            portfolio = self.portfolio_manager.get_portfolio(user_id, portfolio_name)
            if portfolio:
                cash_pct = (portfolio.cash / portfolio.total_value * 100) if portfolio.total_value > 0 else 100
                if cash_pct > 30:
                    recommendations.append({
                        'type': 'allocation',
                        'priority': 'medium',
                        'title': 'High Cash Position',
                        'message': f'Your portfolio has {cash_pct:.1f}% cash.',
                        'action': 'Consider investing excess cash to improve returns.'
                    })
                elif cash_pct < 5:
                    recommendations.append({
                        'type': 'liquidity',
                        'priority': 'low',
                        'title': 'Low Cash Position',
                        'message': f'Your portfolio has only {cash_pct:.1f}% cash.',
                        'action': 'Consider maintaining more cash for emergency needs or opportunities.'
                    })

        return recommendations

    def generate_report(self, user_id: str, portfolio_name: str) -> str:
        """
        生成分析報告

        Args:
            user_id: 用戶ID
            portfolio_name: 組合名稱

        Returns:
            格式化的報告
        """
        behavior = self.analyze_trading_behavior(user_id)
        performance = self.analyze_performance(user_id, portfolio_name)
        risk = self.get_risk_profile(user_id)
        recommendations = self.get_recommendations(user_id)

        report = f"""
=== 個人交易分析報告 ===

組合名稱: {portfolio_name}
生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

--- 表現摘要 ---
總回報: {performance.get('total_return_pct', 0):.2f}%
日回報: {performance.get('day_return_pct', 0):.2f}%
夏普比率: {performance.get('sharpe_ratio', 0):.2f}
最大回撤: {performance.get('max_drawdown_pct', 0):.2f}%
波動率: {performance.get('volatility_pct', 0):.2f}%

--- 交易統計 ---
總交易次數: {behavior.get('total_trades', 0)}
勝率: {behavior.get('win_rate', 0):.1f}%
利潤因子: {behavior.get('profit_factor', 0):.2f}
平均每筆: {behavior.get('avg_trade', 0):.2f}
總手續費: {behavior.get('total_fees', 0):.2f}

--- 風險概況 ---
風險等級: {risk.get('risk_level', 'Unknown')}
集中度: {risk.get('concentration_risk', 0):.1f}%
分散化: {risk.get('diversification', 0):.1f}%

--- 建議 ---
"""

        for rec in recommendations:
            report += f"\n[{rec['priority'].upper()}] {rec['title']}\n"
            report += f"  {rec['message']}\n"
            report += f"  建議行動: {rec['action']}\n"

        return report


# 導出
__all__ = [
    'PersonalAnalytics',
]
