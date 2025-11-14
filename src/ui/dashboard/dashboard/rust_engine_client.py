"""
Rust引擎客户端 - 用于与高性能Rust回测引擎通信
"""

import asyncio
import aiohttp
import json
import logging
import time
import psutil
import os
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class RustEngineClient:
    """Rust引擎HTTP客户端"""

    def __init__(self, host: str = "127.0.0.1", port: int = 8002):
        self.base_url = f"http://{host}:{port}"
        self.host = host
        self.port = port
        self._session: Optional[aiohttp.ClientSession] = None
        self._process = None

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.start_engine()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.stop_engine()

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建HTTP会话"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def start_engine(self) -> bool:
        """启动Rust引擎服务"""
        try:
            # 检查是否已经运行
            if await self.health_check():
                logger.info("Rust引擎已在运行")
                return True

            # 启动Rust引擎进程
            import subprocess
            engine_path = "/c/Users/Penguin8n/CODEX--/CODEX--/quant-api/target/release/quant-api.exe"

            if not os.path.exists(engine_path):
                logger.error(f"Rust引擎未找到: {engine_path}")
                return False

            logger.info(f"启动Rust引擎: {engine_path} --port {self.port}")
            self._process = subprocess.Popen(
                [engine_path, "--port", str(self.port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd="/c/Users/Penguin8n/CODEX--/CODEX--/quant-api"
            )

            # 等待引擎启动
            for i in range(30):
                await asyncio.sleep(0.5)
                if await self.health_check():
                    logger.info("Rust引擎启动成功")
                    return True

            logger.error("Rust引擎启动超时")
            return False

        except Exception as e:
            logger.error(f"启动Rust引擎失败: {e}")
            return False

    async def stop_engine(self):
        """停止Rust引擎服务"""
        if self._process:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
            self._process = None

        if self._session:
            await self._session.close()
            self._session = None

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/api/health") as response:
                return response.status == 200
        except:
            return False

    async def run_backtest(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        strategy_type: str,
        parameters: Dict[str, float],
        initial_capital: float = 100000.0
    ) -> Dict[str, Any]:
        """
        运行回测

        Args:
            symbol: 股票代码 (例如: 0700.hk)
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            strategy_type: 策略类型 (ma, rsi, macd, bb, kdj, cci, adx, atr, obv, ichimoku, sar)
            parameters: 策略参数
            initial_capital: 初始资金

        Returns:
            回测结果
        """
        start_time = time.time()
        memory_before = psutil.Process().memory_info().rss / 1024 / 1024  # MB

        try:
            # 验证输入
            if not symbol or not symbol.endswith('.hk'):
                raise ValueError("Symbol must end with '.hk' (e.g., 0700.hk)")

            symbol = symbol.lower()

            # 准备请求数据
            request_data = {
                "symbol": symbol,
                "start_date": start_date,
                "end_date": end_date,
                "strategy_type": strategy_type,
                "parameters": parameters,
                "initial_capital": initial_capital
            }

            logger.info(
                f"运行回测: {symbol} {strategy_type} "
                f"{start_date} 到 {end_date}"
            )

            # 发送请求
            session = await self._get_session()
            async with session.post(
                f"{self.base_url}/api/backtest/run",
                json=request_data
            ) as response:

                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Rust引擎错误 ({response.status}): {error_text}")

                result = await response.json()

                # 添加性能指标
                execution_time = time.time() - start_time
                memory_after = psutil.Process().memory_info().rss / 1024 / 1024  # MB
                memory_used = memory_after - memory_before

                result["performance"] = {
                    "execution_time_ms": round(execution_time * 1000, 2),
                    "memory_before_mb": round(memory_before, 2),
                    "memory_after_mb": round(memory_after, 2),
                    "memory_delta_mb": round(memory_used, 2),
                    "timestamp": datetime.now().isoformat()
                }

                logger.info(
                    f"回测完成: {execution_time:.2f}s, "
                    f"内存使用: {memory_used:.2f}MB, "
                    f"交易次数: {len(result.get('trades', []))}"
                )

                return result

        except Exception as e:
            logger.error(f"回测执行失败: {e}")
            raise

    async def run_optimization(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        strategy_type: str,
        param_grid: Dict[str, list],
        initial_capital: float = 100000.0,
        max_workers: int = 4
    ) -> Dict[str, Any]:
        """
        运行参数优化

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            strategy_type: 策略类型
            param_grid: 参数网格
            initial_capital: 初始资金
            max_workers: 最大并行数

        Returns:
            优化结果
        """
        start_time = time.time()
        memory_before = psutil.Process().memory_info().rss / 1024 / 1024  # MB

        try:
            # 验证参数网格
            if not param_grid:
                raise ValueError("参数网格不能为空")

            symbol = symbol.lower()

            # 计算参数组合数量
            total_combinations = 1
            for param, values in param_grid.items():
                total_combinations *= len(values)

            logger.info(
                f"开始优化: {symbol} {strategy_type}, "
                f"参数组合: {total_combinations}, "
                f"并行数: {max_workers}"
            )

            # 准备请求数据
            request_data = {
                "symbol": symbol,
                "start_date": start_date,
                "end_date": end_date,
                "strategy_type": strategy_type,
                "param_grid": param_grid,
                "initial_capital": initial_capital,
                "max_workers": max_workers
            }

            # 发送请求
            session = await self._get_session()
            async with session.post(
                f"{self.base_url}/api/backtest/optimize",
                json=request_data
            ) as response:

                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"优化请求失败 ({response.status}): {error_text}")

                result = await response.json()

                # 添加性能指标
                execution_time = time.time() - start_time
                memory_after = psutil.Process().memory_info().rss / 1024 / 1024  # MB
                memory_used = memory_after - memory_before

                result["performance"] = {
                    "execution_time_ms": round(execution_time * 1000, 2),
                    "total_combinations": total_combinations,
                    "throughput_per_second": round(
                        total_combinations / execution_time if execution_time > 0 else 0, 2
                    ),
                    "memory_before_mb": round(memory_before, 2),
                    "memory_after_mb": round(memory_after, 2),
                    "memory_delta_mb": round(memory_used, 2),
                    "max_workers": max_workers,
                    "timestamp": datetime.now().isoformat()
                }

                logger.info(
                    f"优化完成: {execution_time:.2f}s, "
                    f"组合数: {total_combinations}, "
                    f"吞吐量: {result['performance']['throughput_per_second']} 组合/秒, "
                    f"最佳参数: {result.get('best_params', {})}"
                )

                return result

        except Exception as e:
            logger.error(f"参数优化失败: {e}")
            raise

    async def get_metrics(self) -> Dict[str, Any]:
        """获取引擎性能指标"""
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/api/metrics") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {}
        except Exception as e:
            logger.error(f"获取指标失败: {e}")
            return {}


# 全局Rust引擎客户端实例
rust_engine = RustEngineClient()
