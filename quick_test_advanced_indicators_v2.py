#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级技术指标 - 快速验证脚本 V2
使用更长的数据范围以确保足够的数据点
"""

import sys
import logging
import time
from enhanced_strategy_backtest import EnhancedStrategyBacktest

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """运行快速验证"""
    logger.info("=" * 80)
    logger.info("🚀 高级技术指标快速验证 V2 (3年数据)")
    logger.info("=" * 80)

    try:
        # 初始化 - 使用3年数据
        logger.info("\n📊 初始化回测引擎 (使用3年数据)...")
        backtest = EnhancedStrategyBacktest('0700.HK', '2021-01-01', '2024-01-01')

        logger.info("📥 加载数据...")
        if not backtest.load_data():
            logger.error("❌ 数据加载失败")
            return False

        logger.info(f"✅ 数据加载成功: {len(backtest.data)} 个交易日")

        # 测试技术指标计算
        logger.info("\n📈 测试1: 技术指标计算")
        df = backtest.calculate_technical_indicators(backtest.data.copy())
        required_cols = ['K', 'D', 'CCI', 'ADX', 'ATR', 'OBV', 'Ichimoku', 'SAR']

        found_cols = 0
        for col in required_cols:
            matches = [c for c in df.columns if col in c]
            if matches:
                logger.info(f"  ✓ {col:12} - 找到 {matches}")
                found_cols += 1

        logger.info(f"✅ 指标计算测试: {found_cols}/{len(required_cols)} 通过")

        # 快速测试7个新策略
        strategies = [
            ('KDJ', lambda: backtest.run_kdj_strategy()),
            ('CCI', lambda: backtest.run_cci_strategy()),
            ('ADX', lambda: backtest.run_adx_strategy()),
            ('ATR', lambda: backtest.run_atr_strategy()),
            ('OBV', lambda: backtest.run_obv_strategy()),
            ('Ichimoku', lambda: backtest.run_ichimoku_strategy()),
            ('Parabolic SAR', lambda: backtest.run_parabolic_sar_strategy()),
        ]

        logger.info("\n🧪 测试2-8: 策略执行")
        logger.info(f"{'策略':<15} {'状态':>10} {'收益率':>12} {'夏普比率':>12} {'时间(秒)':>12}")
        logger.info("-" * 65)

        successful = 0
        for name, func in strategies:
            start = time.time()
            try:
                result = func()
                elapsed = time.time() - start

                if result:
                    status = "✅"
                    logger.info(
                        f"{name:<15} {status:>10} {result['total_return']:>11.2f}% "
                        f"{result['sharpe_ratio']:>11.3f} {elapsed:>11.3f}s"
                    )
                    successful += 1
                else:
                    logger.warning(f"{name:<15} {'⚠️ None':>10} {'--':>11} {'--':>11} {elapsed:>11.3f}s")
            except Exception as e:
                elapsed = time.time() - start
                logger.error(f"{name:<15} {'❌':>10} 错误: {str(e)[:40]}")

        logger.info("-" * 65)
        logger.info(f"✅ 策略执行测试: {successful}/{len(strategies)} 成功")

        # 测试参数优化
        logger.info("\n⚙️  测试9: 参数优化 (KDJ - 小范围测试)")
        start = time.time()

        try:
            results = backtest.optimize_parameters(strategy_type='kdj', max_workers=2)
            elapsed = time.time() - start

            if results and len(results) > 0:
                logger.info(f"✅ KDJ参数优化:")
                logger.info(f"   • 测试组合数: {len(results)}")
                logger.info(f"   • 最佳Sharpe: {results[0]['sharpe_ratio']:.3f}")
                logger.info(f"   • 最佳策略: {results[0]['strategy_name']}")
                logger.info(f"   • 执行时间: {elapsed:.2f}秒")
            else:
                logger.warning("⚠️ 优化返回空结果")
        except Exception as e:
            logger.error(f"❌ 参数优化失败: {e}")
            import traceback
            traceback.print_exc()

        # 与基础策略对比
        logger.info("\n📊 测试10: 新旧策略对比")
        logger.info(f"{'策略':<15} {'类型':>8} {'总收益率':>12} {'夏普比率':>12}")
        logger.info("-" * 50)

        # 基础策略
        ma_result = backtest.run_ma_crossover_strategy(short_window=5, long_window=20)
        if ma_result:
            logger.info(
                f"{'MA':<15} {'基础':>8} {ma_result['total_return']:>11.2f}% {ma_result['sharpe_ratio']:>11.3f}"
            )

        rsi_result = backtest.run_rsi_strategy(rsi_period=14, oversold=30, overbought=70)
        if rsi_result:
            logger.info(
                f"{'RSI':<15} {'基础':>8} {rsi_result['total_return']:>11.2f}% {rsi_result['sharpe_ratio']:>11.3f}"
            )

        # 新策略
        kdj_result = backtest.run_kdj_strategy()
        if kdj_result:
            logger.info(
                f"{'KDJ':<15} {'新增':>8} {kdj_result['total_return']:>11.2f}% {kdj_result['sharpe_ratio']:>11.3f}"
            )

        atr_result = backtest.run_atr_strategy()
        if atr_result:
            logger.info(
                f"{'ATR':<15} {'新增':>8} {atr_result['total_return']:>11.2f}% {atr_result['sharpe_ratio']:>11.3f}"
            )

        # 总结
        logger.info("\n" + "=" * 80)
        logger.info("✅ 快速验证完成!")
        logger.info(f"📊 总成功策略数: {successful}/7")
        logger.info("=" * 80)

        return True

    except Exception as e:
        logger.error(f"❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
