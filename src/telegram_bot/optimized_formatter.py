#!/usr/bin/env python3
"""
優化的消息格式化模組
簡化所有命令的回應格式，保留核心信息
"""

from typing import Dict, List, Any
import time


def format_technical_analysis_optimized(data: Dict) -> str:
    """格式化技術分析結果 - 優化版"""
    if not data:
        return "❌ 無法獲取技術分析數據"

    # 簡化標題
    lines = ["📈 技術分析"]

    # RSI - 最重要
    if 'rsi' in data:
        rsi = data['rsi']
        if rsi > 70:
            status = "🔴 超買"
        elif rsi < 30:
            status = "🟢 超賣"
        else:
            status = "🟡 中性"
        lines.append(f"RSI(14): {rsi:.1f} {status}")

    # MACD
    if 'macd' in data:
        macd = data['macd']
        signal = data.get('macd_signal', 0)
        lines.append(f"MACD: {macd:.3f} (Signal: {signal:.3f})")

    # 移動平均
    if 'sma_20' in data:
        lines.append(f"SMA20: {data['sma_20']:.2f}")

    # 當前價格
    if 'close' in data:
        lines.append(f"現價: {data['close']:.2f}")

    # 布林帶
    if 'bb_upper' in data:
        lines.append(f"布林帶: {data['bb_lower']:.1f}-{data['bb_upper']:.1f}")

    return "\n".join(lines)


def format_strategy_results_optimized(results: List[Dict], limit: int = 5) -> str:
    """格式化策略優化結果 - 優化版"""
    if not results:
        return "❌ 沒有找到有效的策略結果"

    # 簡化標題
    lines = [f"🎯 策略結果 (前{min(limit, len(results))}名)\n"]

    for i, result in enumerate(results[:limit], 1):
        # 只顯示核心指標
        sharpe = result.get('sharpe_ratio', 0)
        annual_return = result.get('annual_return', 0)
        win_rate = result.get('win_rate', 0)
        trades = result.get('trade_count', 0)

        lines.append(f"{i}. Sharpe: {sharpe:.2f}")
        lines.append(f"   年化: {annual_return:.1f}% 勝率: {win_rate:.0f}% 交易: {trades}")

    return "\n".join(lines)


def format_mark6_message_optimized(data: Dict) -> str:
    """格式化Mark6信息 - 優化版"""
    lines = ["🎰 六合彩"]

    if data.get('draw_no'):
        lines.append(f"期數: {data['draw_no']}")

    if data.get('draw_date'):
        lines.append(f"日期: {data['draw_date']}")

    if data.get('estimated_prize'):
        prize = data['estimated_prize']
        if isinstance(prize, str) and prize.replace(',', '').replace('.', '').isdigit():
            prize_value = float(prize.replace(',', ''))
            if prize_value >= 100000000:
                lines.append(f"頭獎: {prize_value/100000000:.1f}億")
            elif prize_value >= 10000:
                lines.append(f"頭獎: {prize_value/10000:.0f}萬")
            else:
                lines.append(f"頭獎: {prize}")
        else:
            lines.append(f"頭獎: {prize}")

    return " ".join(lines)


def format_risk_assessment_optimized(data: Dict) -> str:
    """格式化風險評估 - 優化版"""
    if not data:
        return "❌ 無法獲取風險數據"

    lines = ["⚠️ 風險評估"]

    var_95 = data.get('var_95', 0)
    var_99 = data.get('var_99', 0)
    max_drawdown = data.get('max_drawdown', 0)
    volatility = data.get('volatility', 0)

    lines.append(f"VaR(95%): {var_95:.2f}%")
    lines.append(f"最大回撤: {max_drawdown:.2f}%")
    lines.append(f"波動率: {volatility:.2f}%")

    # 風險評級
    risk_score = data.get('risk_score', 5)
    if risk_score <= 3:
        lines.append("🟢 風險等級: 低")
    elif risk_score <= 6:
        lines.append("🟡 風險等級: 中")
    else:
        lines.append("🔴 風險等級: 高")

    return "\n".join(lines)


def format_sentiment_optimized(data: Dict) -> str:
    """格式化情緒分析 - 優化版"""
    if not data:
        return "❌ 無法獲取情緒數據"

    lines = ["📊 市場情緒"]

    sentiment = data.get('sentiment_score', 5)
    trend = data.get('trend_strength', 0)
    volatility = data.get('volatility_sentiment', 0)

    lines.append(f"情緒: {sentiment:.1f}/10")

    if sentiment >= 7:
        status = "🟢 樂觀"
    elif sentiment >= 4:
        status = "🟡 中性"
    else:
        status = "🔴 悲觀"

    lines.append(f"趨勢: {trend:.2f} {status}")

    return "\n".join(lines)


def format_portfolio_optimized(data: Dict) -> str:
    """格式化投資組合 - 優化版"""
    if not data or 'positions' not in data:
        return "📊 投資組合空"

    lines = ["📊 投資組合\n"]

    total_value = data.get('total_value', 0)
    total_pnl = data.get('total_pnl', 0)
    pnl_rate = data.get('pnl_rate', 0)

    # 總覽
    if pnl_rate >= 0:
        lines.append(f"總值: {total_value:,.0f} (+{pnl_rate:.1f}%)")
    else:
        lines.append(f"總值: {total_value:,.0f} ({pnl_rate:.1f}%)")

    # 只顯示前5個持倉
    positions = data.get('positions', [])[:5]
    for pos in positions:
        code = pos.get('symbol', '')
        qty = pos.get('quantity', 0)
        price = pos.get('current_price', 0)
        pnl = pos.get('pnl', 0)
        pnl_rate = pos.get('pnl_rate', 0)

        lines.append(f"{code}: {qty} @ {price:.2f}")

    if len(data.get('positions', [])) > 5:
        lines.append(f"... 還有 {len(data.get('positions', [])) - 5} 個持倉")

    return "\n".join(lines)


def format_weather_optimized(data: Dict) -> str:
    """格式化天氣信息 - 優化版"""
    if not data:
        return "❌ 無法獲取天氣數據"

    lines = ["🌤 天氣"]

    temp = data.get('temperature')
    if temp:
        lines.append(f"溫度: {temp:.0f}°C")

    humidity = data.get('humidity')
    if humidity:
        lines.append(f"濕度: {humidity:.0f}%")

    weather = data.get('weather') or data.get('condition', {}).get('text', '')
    if weather:
        lines.append(f"天氣: {weather}")

    uv_index = data.get('uv_index')
    if uv_index:
        level = data.get('level', '')
        lines.append(f"UV: {uv_index} ({level})")

    warning = data.get('warning')
    if warning:
        lines.append(f"⚠️ {warning}")

    return " ".join(lines)


def format_sports_scores_optimized(scores: List[Dict]) -> str:
    """格式化體育比分 - 優化版"""
    if not scores:
        return "⚠️ 暫無比賽數據"

    lines = ["⚽ 體育比分"]

    # 分組顯示
    by_source = {}
    for score in scores:
        source = score.get('data_source', '未知')
        if source not in by_source:
            by_source[source] = []
        by_source[source].append(score)

    # 顯示數據源
    for source, games in by_source.items():
        lines.append(f"\n📊 來源: {source}")

        # 只顯示前3場
        for game in games[:3]:
            home = game.get('home_team', 'N/A')[:10]
            away = game.get('away_team', 'N/A')[:10]
            home_score = game.get('home_score', '-')
            away_score = game.get('away_score', '-')
            status = game.get('status', '')

            lines.append(f"{home} {home_score}-{away_score} {away} ({status})")

    # 限制總長度
    message = "\n".join(lines)
    if len(message) > 800:
        message = message[:800] + "\n...（已截斷）"

    return message


def chunk_text_optimized(text: str, limit: int = 4096) -> List[str]:
    """智能分段處理 - 優化版"""
    if len(text) <= limit:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + limit, len(text))

        # 在換行處分割
        if '\n' in text[start:end]:
            split_point = text.rfind('\n', start, end)
            if split_point > start:
                end = split_point

        chunks.append(text[start:end])
        start = end

    return chunks
