"""
CODEX 策略優化框架

這個模塊提供完整的策略參數優化能力，支援多種優化算法：
- 網格搜索 (Grid Search)
- 隨機搜索 (Random Search)
- 暴力搜索 (Brute Force)

所有優化器都支援：
- 5折交叉驗證
- 多進程並行執行
- 完整的性能指標計算
- 參數穩定性分析
- 內存管理

Usage:
    from src.optimization import ProductionOptimizer

    optimizer = ProductionOptimizer('0700.hk', '2020-01-01')
    optimizer.load_data()

    # 定義策略工廠函數
    def rsi_factory(params):
        return RSIStrategy(
            period=params['period'],
            overbought=params['overbought'],
            oversold=params['oversold']
        )

    # 運行網格搜索
    results = optimizer.grid_search(
        strategy_factory=rsi_factory,
        param_grid={
            'period': [10, 14, 20],
            'overbought': [60, 70, 80],
            'oversold': [20, 30, 40]
        }
    )

    print(f"最佳參數: {results['best_params']}")
    print(f"Sharpe 比率: {results['validation_metrics']['sharpe_ratio']:.4f}")
"""

from .production_optimizer import ProductionOptimizer

__version__ = '1.0.0'
__all__ = ['ProductionOptimizer']
