"""
CODEX 後台任務模塊

支援多種任務隊列後端：
- Celery (基於 Redis)
- APScheduler (基於內存或數據庫)
- Simple (同步執行，用於測試/簡單部署)

Usage:
    from src.tasks.optimization_tasks import optimization_task_manager

    # 提交優化任務
    task_id = await optimization_task_manager.submit_optimization_task(
        run_id='opt_0700hk_rsi_123456',
        run_db_id=1,
        symbol='0700.hk',
        strategy_name='rsi',
        start_date='2023-01-01',
        end_date='2024-01-01',
        method='grid_search',
        metric='sharpe_ratio'
    )

    # 獲取任務狀態
    status = await optimization_task_manager.get_task_status(run_id)
"""

from .optimization_tasks import OptimizationTaskManager, optimization_task_manager

__all__ = ['OptimizationTaskManager', 'optimization_task_manager']
