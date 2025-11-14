"""
T066: 零售数据参数优化脚本

对零售销售数据回测进行参数优化
优化范围: buy_threshold (10-60, step=1), sell_threshold (50-90, step=1)

运行:
    python scripts/retail_parameter_optimization.py

Author: Claude Code
Version: 1.0.0
Date: 2025-11-10
"""

import asyncio
import json
import logging
import pandas as pd
from datetime import date, timedelta
from pathlib import Path
import sys

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from backtest.retail_backtest import RetailMultiSourceBacktest
from data_adapters.retail_adapter import RetailAdapter, RetailIndicator


async def main():
    """主函数"""
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger = logging.getLogger("retail_optimization")

    # 设置日期范围 (最近3年)
    end_date = date.today()
    start_date = end_date - timedelta(days=3*365)

    symbol = "0700.HK"  # 腾讯控股

    try:
        logger.info("Starting retail data parameter optimization...")
        logger.info(f"Symbol: {symbol}")
        logger.info(f"Period: {start_date} to {end_date}")

        # 初始化回测引擎
        backtest = RetailMultiSourceBacktest(
            config_path=Path("config/nonprice/retail_config.json")
        )

        # 加载数据
        logger.info("Loading data...")
        data = await backtest.load_data(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            data_sources=['retail', 'stock']
        )

        if 'combined' not in data or data['combined'].empty:
            logger.error("No data loaded for optimization")
            return

        logger.info(f"Loaded {len(data['combined'])} data points")

        # 运行参数优化
        logger.info("Running parameter optimization (this may take a while)...")
        optimization_results = backtest.optimize_parameters(
            data=data['combined'],
            symbol=symbol,
            max_workers=4  # 使用4个并行进程
        )

        if not optimization_results:
            logger.error("Optimization failed")
            return

        # 保存优化结果
        output_path = Path("config/retail_optimization_results.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(optimization_results, f, indent=2, default=str)

        logger.info(f"Optimization results saved to {output_path}")

        # 打印最佳参数
        best_params = optimization_results.get('best_params', {})
        best_perf = optimization_results.get('best_performance', {})

        print("\n" + "=" * 80)
        print("OPTIMIZATION COMPLETE")
        print("=" * 80)
        print(f"Best Buy Threshold: {best_params.get('buy_threshold', 'N/A')}")
        print(f"Best Sell Threshold: {best_params.get('sell_threshold', 'N/A')}")
        print(f"Best Sharpe Ratio: {best_perf.get('sharpe_ratio', 0):.2f}")
        print(f"Best Total Return: {best_perf.get('total_return', 0):.2%}")
        print(f"Best Max Drawdown: {best_perf.get('max_drawdown', 0):.2%}")
        print(f"Best Win Rate: {best_perf.get('win_rate', 0):.2%}")
        print("=" * 80)

        # 使用最佳参数运行回测
        logger.info("Running backtest with best parameters...")
        backtest_results = await backtest.run_backtest(
            data=data['combined'],
            symbol=symbol,
            buy_threshold=best_params.get('buy_threshold', 30),
            sell_threshold=best_params.get('sell_threshold', 70)
        )

        # 生成报告
        report_path = backtest.generate_report(
            output_path=Path("reports/retail_optimization_report.txt")
        )

        if report_path:
            print(f"\nReport saved to: {report_path}")

    except Exception as e:
        logger.error(f"Optimization error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
