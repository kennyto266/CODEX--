"""
策略优化后台任务

支援 Celery 和 APScheduler 两种任務隊列方式
負責長時間運行的優化任務，不阻塞 API 請求
"""

import logging
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, Callable, Tuple

from src.database import db_manager
from src.optimization import ProductionOptimizer

logger = logging.getLogger(__name__)


class OptimizationTaskManager:
    """
    優化任務管理器 - 統一介面支援多種任務隊列後端
    """

    def __init__(self, backend: str = 'simple'):
        """
        初始化任務管理器

        Args:
            backend: 'celery', 'apscheduler', 或 'simple'（同步執行）
        """
        self.backend = backend
        self.tasks = {}  # 跟蹤運行中的任務
        self._init_backend()

    def _init_backend(self):
        """初始化任務隊列後端"""
        if self.backend == 'celery':
            try:
                from celery import Celery
                self.celery_app = Celery('codex_optimization')
                self.celery_app.conf.update(
                    broker_url='redis://localhost:6379/0',
                    result_backend='redis://localhost:6379/0',
                    task_serializer='json',
                    accept_content=['json'],
                    result_serializer='json',
                    timezone='UTC',
                    enable_utc=True
                )
                logger.info("Celery backend initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Celery backend: {e}")
                self.backend = 'simple'

        elif self.backend == 'apscheduler':
            try:
                from apscheduler.schedulers.background import BackgroundScheduler
                self.scheduler = BackgroundScheduler()
                if not self.scheduler.running:
                    self.scheduler.start()
                logger.info("APScheduler backend initialized")
            except Exception as e:
                logger.error(f"Failed to initialize APScheduler backend: {e}")
                self.backend = 'simple'

        else:
            logger.info("Using simple synchronous backend")

    async def submit_optimization_task(self, run_id: str, run_db_id: int, symbol: str,
                                       strategy_name: str, start_date: str, end_date: str,
                                       method: str = 'grid_search',
                                       metric: str = 'sharpe_ratio') -> str:
        """
        提交優化任務到後台隊列

        Args:
            run_id: 唯一運行ID
            run_db_id: 數據庫運行ID
            symbol: 股票代碼
            strategy_name: 策略名稱
            start_date: 開始日期
            end_date: 結束日期
            method: 優化方法
            metric: 優化指標

        Returns:
            任務ID
        """
        if self.backend == 'celery':
            task = self.celery_app.send_task(
                'src.tasks.optimization_tasks.run_optimization_celery',
                args=(run_id, run_db_id, symbol, strategy_name, start_date, end_date,
                      method, metric)
            )
            task_id = task.id
            logger.info(f"Submitted Celery task: {task_id}")

        elif self.backend == 'apscheduler':
            task_id = self.scheduler.add_job(
                run_optimization_sync,
                args=(run_id, run_db_id, symbol, strategy_name, start_date, end_date,
                      method, metric),
                id=run_id,
                name=f"Optimize {symbol}/{strategy_name}",
                replace_existing=True
            ).id
            logger.info(f"Scheduled APScheduler task: {task_id}")

        else:
            # 同步執行（用於測試或簡單部署）
            task_id = await run_optimization_async(
                run_id, run_db_id, symbol, strategy_name, start_date, end_date,
                method, metric
            )

        self.tasks[run_id] = {
            'task_id': task_id,
            'status': 'pending',
            'created_at': datetime.utcnow().isoformat()
        }

        return task_id

    async def get_task_status(self, run_id: str) -> Dict[str, Any]:
        """獲取任務狀態"""
        if run_id not in self.tasks:
            # 從數據庫查詢
            result = db_manager.get_optimization_run(run_id)
            if not result:
                return {'status': 'not_found'}
            return result

        task_info = self.tasks[run_id]

        if self.backend == 'celery':
            try:
                task_result = self.celery_app.AsyncResult(task_info['task_id'])
                task_info['status'] = task_result.status
                if task_result.ready():
                    if task_result.successful():
                        task_info['result'] = task_result.result
                    else:
                        task_info['error'] = str(task_result.info)
            except Exception as e:
                logger.error(f"Failed to get Celery task status: {e}")

        elif self.backend == 'apscheduler':
            try:
                job = self.scheduler.get_job(run_id)
                if job:
                    task_info['status'] = 'running' if job.next_run_time else 'completed'
                else:
                    task_info['status'] = 'not_found'
            except Exception as e:
                logger.error(f"Failed to get APScheduler task status: {e}")

        return task_info

    async def cancel_task(self, run_id: str) -> bool:
        """取消運行中的任務"""
        if run_id not in self.tasks:
            return False

        task_info = self.tasks[run_id]

        if self.backend == 'celery':
            try:
                self.celery_app.control.revoke(task_info['task_id'], terminate=True)
                logger.info(f"Cancelled Celery task: {task_info['task_id']}")
                return True
            except Exception as e:
                logger.error(f"Failed to cancel Celery task: {e}")
                return False

        elif self.backend == 'apscheduler':
            try:
                self.scheduler.remove_job(run_id)
                logger.info(f"Cancelled APScheduler task: {run_id}")
                return True
            except Exception as e:
                logger.error(f"Failed to cancel APScheduler task: {e}")
                return False

        return False


# ============ 優化執行函數 ============

async def run_optimization_async(run_id: str, run_db_id: int, symbol: str,
                                 strategy_name: str, start_date: str, end_date: str,
                                 method: str = 'grid_search',
                                 metric: str = 'sharpe_ratio') -> str:
    """
    異步執行優化（用於簡單後端）

    Returns:
        run_id
    """
    _run_optimization_impl(run_id, run_db_id, symbol, strategy_name, start_date,
                         end_date, method, metric)
    return run_id


def run_optimization_sync(run_id: str, run_db_id: int, symbol: str,
                         strategy_name: str, start_date: str, end_date: str,
                         method: str = 'grid_search',
                         metric: str = 'sharpe_ratio'):
    """
    同步執行優化（用於 APScheduler）
    """
    _run_optimization_impl(run_id, run_db_id, symbol, strategy_name, start_date,
                         end_date, method, metric)


def run_optimization_celery(run_id: str, run_db_id: int, symbol: str,
                           strategy_name: str, start_date: str, end_date: str,
                           method: str = 'grid_search',
                           metric: str = 'sharpe_ratio'):
    """
    Celery 任務函數 - 在 Celery worker 中執行
    """
    _run_optimization_impl(run_id, run_db_id, symbol, strategy_name, start_date,
                         end_date, method, metric)


def _run_optimization_impl(run_id: str, run_db_id: int, symbol: str,
                          strategy_name: str, start_date: str, end_date: str,
                          method: str, metric: str):
    """
    優化實現 - 所有執行路徑的核心邏輯
    """
    try:
        logger.info(f"Starting optimization task: {run_id}")

        # 建立優化器
        optimizer = ProductionOptimizer(symbol, start_date, end_date)

        # 加載數據
        if optimizer.load_data() is None:
            db_manager.update_optimization_run(
                run_id=run_id,
                status='failed',
                duration=0,
                error_message='Failed to load data'
            )
            logger.error(f"Data loading failed for {run_id}")
            return

        # 獲取策略工廠和參數網格
        strategy_factory, param_grid = _get_strategy_factory(strategy_name)

        if strategy_factory is None:
            db_manager.update_optimization_run(
                run_id=run_id,
                status='failed',
                duration=0,
                error_message=f'Unsupported strategy: {strategy_name}'
            )
            logger.error(f"Unsupported strategy: {strategy_name}")
            return

        # 執行優化
        start_time = datetime.utcnow()

        try:
            if method == 'grid_search':
                result = optimizer.grid_search(strategy_factory, param_grid)
            elif method == 'random_search':
                result = optimizer.random_search(strategy_factory, param_grid)
            else:
                result = optimizer.grid_search(strategy_factory, param_grid)
        except Exception as e:
            logger.error(f"Optimization failed: {e}", exc_info=True)
            db_manager.update_optimization_run(
                run_id=run_id,
                status='failed',
                duration=(datetime.utcnow() - start_time).total_seconds(),
                error_message=str(e)
            )
            return

        duration = (datetime.utcnow() - start_time).total_seconds()

        # 保存結果
        if result and 'best_params' in result:
            best_params = result['best_params']
            best_metrics = result['validation_metrics']

            # 保存評估結果
            param_hash = hashlib.md5(
                json.dumps(best_params, sort_keys=True, default=str).encode()
            ).hexdigest()

            db_manager.save_optimization_result(
                run_id=run_db_id,
                rank=1,
                param_hash=param_hash,
                parameters=best_params,
                metrics=best_metrics
            )

            # 更新運行狀態
            db_manager.update_optimization_run(
                run_id=run_id,
                status='completed',
                duration=duration,
                best_parameters=best_params,
                best_metrics=best_metrics
            )

            logger.info(f"Optimization completed: {run_id}")
            logger.info(f"Best Sharpe Ratio: {best_metrics.get('sharpe_ratio', 0):.4f}")
        else:
            db_manager.update_optimization_run(
                run_id=run_id,
                status='failed',
                duration=duration,
                error_message='No valid results found'
            )
            logger.error(f"No valid results found for {run_id}")

    except Exception as e:
        logger.error(f"Optimization task failed: {e}", exc_info=True)
        db_manager.update_optimization_run(
            run_id=run_id,
            status='failed',
            duration=0,
            error_message=f"Task execution error: {str(e)}"
        )


def _get_strategy_factory(strategy_name: str) -> Tuple[Optional[Callable], Optional[Dict]]:
    """獲取策略工廠函數和參數網格"""
    try:
        strategy_name_lower = strategy_name.lower()

        if strategy_name_lower == 'rsi':
            def rsi_factory(params):
                from src.strategies import RSIStrategy
                return RSIStrategy(
                    period=params.get('period', 14),
                    overbought=params.get('overbought', 70),
                    oversold=params.get('oversold', 30)
                )

            param_grid = {
                'period': [10, 14, 20, 30],
                'overbought': [60, 70, 80],
                'oversold': [20, 30, 40]
            }
            return rsi_factory, param_grid

        elif strategy_name_lower == 'macd':
            def macd_factory(params):
                from src.strategies import MACDStrategy
                return MACDStrategy(
                    fast_period=params.get('fast_period', 12),
                    slow_period=params.get('slow_period', 26),
                    signal_period=params.get('signal_period', 9)
                )

            param_grid = {
                'fast_period': [5, 10, 12],
                'slow_period': [20, 26, 30],
                'signal_period': [8, 9, 10]
            }
            return macd_factory, param_grid

        elif strategy_name_lower == 'bollinger':
            def bollinger_factory(params):
                from src.strategies import BollingerStrategy
                return BollingerStrategy(
                    period=params.get('period', 20),
                    std_dev=params.get('std_dev', 2.0)
                )

            param_grid = {
                'period': [15, 20, 25, 30],
                'std_dev': [1.5, 2.0, 2.5, 3.0]
            }
            return bollinger_factory, param_grid

        else:
            logger.error(f"Unknown strategy: {strategy_name}")
            return None, None

    except Exception as e:
        logger.error(f"Failed to get strategy factory: {e}")
        return None, None


# ============ 全局任務管理器實例 ============

# 使用簡單後端作為默認（不需要 Redis 或 Celery）
optimization_task_manager = OptimizationTaskManager(backend='simple')
