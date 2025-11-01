#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生命周期管理器 (LifecycleManager)
管理Agent的启动、停止、重启、故障恢复等生命周期事件
"""

import os
import sys
import asyncio
import logging
import time
from typing import Dict, List, Optional, Set, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path

# 添加项目根目录
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from infrastructure.logging.context_logger import get_context_logger
from agent_registry import AgentRegistry, AgentStatus, get_agent_registry

logger = get_context_logger("agent.lifecycle")

class LifecycleState(Enum):
    """生命周期状态"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    PAUSING = "pausing"
    PAUSED = "paused"
    RESUMING = "resuming"
    RESTARTING = "restarting"
    ERROR = "error"

class RestartStrategy(Enum):
    """重启策略"""
    NEVER = "never"
    ON_FAILURE = "on_failure"
    ALWAYS = "always"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    FIXED_INTERVAL = "fixed_interval"

@dataclass
class LifecycleConfig:
    """生命周期配置"""
    max_restart_attempts: int = 3
    restart_delay: float = 5.0
    health_check_interval: float = 30.0
    shutdown_timeout: float = 30.0
    startup_timeout: float = 60.0
    restart_strategy: RestartStrategy = RestartStrategy.ON_FAILURE
    restart_interval: float = 10.0
    max_restarts_per_hour: int = 10

@dataclass
class LifecycleMetrics:
    """生命周期指标"""
    start_count: int = 0
    stop_count: int = 0
    restart_count: int = 0
    failure_count: int = 0
    uptime_seconds: float = 0.0
    last_start_time: Optional[datetime] = None
    last_stop_time: Optional[datetime] = None
    last_failure_time: Optional[datetime] = None
    last_health_check: Optional[datetime] = None
    average_startup_time: float = 0.0
    restart_times: List[float] = field(default_factory=list)
    restarts_in_last_hour: List[datetime] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'start_count': self.start_count,
            'stop_count': self.stop_count,
            'restart_count': self.restart_count,
            'failure_count': self.failure_count,
            'uptime_seconds': self.uptime_seconds,
            'last_start_time': self.last_start_time.isoformat() if self.last_start_time else None,
            'last_stop_time': self.last_stop_time.isoformat() if self.last_stop_time else None,
            'last_failure_time': self.last_failure_time.isoformat() if self.last_failure_time else None,
            'last_health_check': self.last_health_check.isoformat() if self.last_health_check else None,
            'average_startup_time': self.average_startup_time,
            'recent_restarts': len(self.restarts_in_last_hour)
        }

class LifecycleManager:
    """Agent生命周期管理器"""

    def __init__(self, registry: Optional[AgentRegistry] = None, config: Optional[LifecycleConfig] = None):
        self.registry = registry or get_agent_registry()
        self.config = config or LifecycleConfig()
        self._lifecycles: Dict[str, LifecycleState] = {}
        self._metrics: Dict[str, LifecycleMetrics] = {}
        self._health_checks: Dict[str, Callable] = {}
        self._event_handlers: Dict[str, List[Callable]] = {}
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

    async def initialize(self):
        """初始化生命周期管理器"""
        logger.info("初始化生命周期管理器...")

        # 为所有已注册的Agent初始化生命周期
        agents = await self.registry.list_agents()
        for agent in agents:
            await self._initialize_agent_lifecycle(agent.id)

        # 启动监控
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_lifecycles())

        logger.info(f"生命周期管理器初始化完成，管理 {len(agents)} 个Agent")

    async def shutdown(self):
        """关闭生命周期管理器"""
        logger.info("关闭生命周期管理器...")

        # 停止监控
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

        # 停止所有Agent
        await self.stop_all_agents()

        logger.info("生命周期管理器已关闭")

    async def _initialize_agent_lifecycle(self, agent_id: str):
        """初始化单个Agent的生命周期"""
        async with self._lock:
            if agent_id not in self._lifecycles:
                self._lifecycles[agent_id] = LifecycleState.STOPPED
                self._metrics[agent_id] = LifecycleMetrics()

            # 注册健康检查
            if agent_id not in self._health_checks:
                self._health_checks[agent_id] = self._default_health_check

    async def start_agent(self, agent_id: str, config: Optional[Dict[str, Any]] = None,
                         wait_for_healthy: bool = True) -> bool:
        """启动Agent"""
        logger.info(f"启动Agent: {agent_id}")

        # 检查状态
        if agent_id in self._lifecycles:
            current_state = self._lifecycles[agent_id]
            if current_state in [LifecycleState.STARTING, LifecycleState.RUNNING]:
                logger.warning(f"Agent {agent_id} 已在运行中: {current_state.value}")
                return True

        # 初始化生命周期
        await self._initialize_agent_lifecycle(agent_id)

        # 更新状态
        await self._set_state(agent_id, LifecycleState.STARTING)

        # 记录启动时间
        start_time = time.time()

        try:
            # 注册事件
            await self._emit_event(agent_id, "before_start", None)

            # 启动Agent
            success = await self.registry.start_agent(agent_id, config)

            if success:
                # 更新指标
                metrics = self._metrics[agent_id]
                metrics.start_count += 1
                metrics.last_start_time = datetime.now()

                # 更新状态
                await self._set_state(agent_id, LifecycleState.RUNNING)

                # 等待健康检查（可选）
                if wait_for_healthy:
                    healthy = await self._wait_for_healthy(agent_id, timeout=self.config.startup_timeout)
                    if not healthy:
                        logger.warning(f"Agent {agent_id} 启动后未通过健康检查")
                        return False

                # 注册事件
                await self._emit_event(agent_id, "after_start", None)

                # 记录启动耗时
                startup_time = time.time() - start_time
                metrics.uptime_seconds += startup_time

                logger.info(f"Agent启动成功: {agent_id}")
                return True
            else:
                # 启动失败
                await self._handle_start_failure(agent_id, "Agent启动失败")
                return False

        except Exception as e:
            logger.error(f"启动Agent异常 {agent_id}: {e}", exc_info=True)
            await self._handle_start_failure(agent_id, str(e))
            return False

    async def _handle_start_failure(self, agent_id: str, reason: str):
        """处理启动失败"""
        await self._set_state(agent_id, LifecycleState.ERROR)

        metrics = self._metrics[agent_id]
        metrics.failure_count += 1
        metrics.last_failure_time = datetime.now()

        await self._emit_event(agent_id, "start_failed", {"reason": reason})

    async def stop_agent(self, agent_id: str, force: bool = False) -> bool:
        """停止Agent"""
        logger.info(f"停止Agent: {agent_id}")

        if agent_id not in self._lifecycles:
            logger.warning(f"Agent {agent_id} 未初始化")
            return True

        current_state = self._lifecycles[agent_id]
        if current_state in [LifecycleState.STOPPING, LifecycleState.STOPPED]:
            logger.warning(f"Agent {agent_id} 已在停止中或已停止")
            return True

        # 更新状态
        await self._set_state(agent_id, LifecycleState.STOPPING)

        try:
            # 注册事件
            await self._emit_event(agent_id, "before_stop", {"force": force})

            # 停止Agent
            success = await self.registry.stop_agent(agent_id)

            if success:
                # 更新指标
                metrics = self._metrics[agent_id]
                metrics.stop_count += 1
                metrics.last_stop_time = datetime.now()

                # 更新状态
                await self._set_state(agent_id, LifecycleState.STOPPED)

                # 注册事件
                await self._emit_event(agent_id, "after_stop", None)

                logger.info(f"Agent停止成功: {agent_id}")
                return True
            else:
                if force:
                    logger.warning(f"强制停止Agent: {agent_id}")
                    await self._set_state(agent_id, LifecycleState.STOPPED)
                    return True
                else:
                    logger.error(f"Agent停止失败: {agent_id}")
                    await self._set_state(agent_id, LifecycleState.ERROR)
                    return False

        except Exception as e:
            logger.error(f"停止Agent异常 {agent_id}: {e}", exc_info=True)
            if force:
                await self._set_state(agent_id, LifecycleState.STOPPED)
                return True
            else:
                await self._set_state(agent_id, LifecycleState.ERROR)
                return False

    async def restart_agent(self, agent_id: str, config: Optional[Dict[str, Any]] = None,
                           force: bool = False) -> bool:
        """重启Agent"""
        logger.info(f"重启Agent: {agent_id}")

        # 检查重启频率
        if not await self._check_restart_rate_limit(agent_id):
            logger.warning(f"Agent {agent_id} 重启频率超限")
            return False

        # 更新状态
        await self._set_state(agent_id, LifecycleState.RESTARTING)

        # 停止
        stop_success = await self.stop_agent(agent_id, force)

        # 等待停止完成
        if stop_success:
            await asyncio.sleep(self.config.restart_delay)

        # 启动
        start_success = await self.start_agent(agent_id, config)

        if start_success:
            # 更新指标
            metrics = self._metrics[agent_id]
            metrics.restart_count += 1
            metrics.restart_times.append(time.time())
            metrics.restarts_in_last_hour.append(datetime.now())

            await self._emit_event(agent_id, "after_restart", None)

            logger.info(f"Agent重启成功: {agent_id}")
        else:
            logger.error(f"Agent重启失败: {agent_id}")

        return start_success

    async def pause_agent(self, agent_id: str) -> bool:
        """暂停Agent"""
        logger.info(f"暂停Agent: {agent_id}")

        if agent_id not in self._lifecycles:
            logger.warning(f"Agent {agent_id} 未初始化")
            return False

        await self._set_state(agent_id, LifecycleState.PAUSING)

        try:
            await self._emit_event(agent_id, "before_pause", None)

            success = await self.registry.pause_agent(agent_id)

            if success:
                await self._set_state(agent_id, LifecycleState.PAUSED)
                await self._emit_event(agent_id, "after_pause", None)
                logger.info(f"Agent暂停成功: {agent_id}")
            else:
                await self._set_state(agent_id, LifecycleState.ERROR)
                logger.error(f"Agent暂停失败: {agent_id}")

            return success

        except Exception as e:
            logger.error(f"暂停Agent异常 {agent_id}: {e}", exc_info=True)
            await self._set_state(agent_id, LifecycleState.ERROR)
            return False

    async def resume_agent(self, agent_id: str) -> bool:
        """恢复Agent"""
        logger.info(f"恢复Agent: {agent_id}")

        if agent_id not in self._lifecycles:
            logger.warning(f"Agent {agent_id} 未初始化")
            return False

        await self._set_state(agent_id, LifecycleState.RESUMING)

        try:
            await self._emit_event(agent_id, "before_resume", None)

            success = await self.registry.resume_agent(agent_id)

            if success:
                await self._set_state(agent_id, LifecycleState.RUNNING)
                await self._emit_event(agent_id, "after_resume", None)
                logger.info(f"Agent恢复成功: {agent_id}")
            else:
                await self._set_state(agent_id, LifecycleState.ERROR)
                logger.error(f"Agent恢复失败: {agent_id}")

            return success

        except Exception as e:
            logger.error(f"恢复Agent异常 {agent_id}: {e}", exc_info=True)
            await self._set_state(agent_id, LifecycleState.ERROR)
            return False

    async def stop_all_agents(self):
        """停止所有Agent"""
        logger.info("停止所有Agent...")

        agents = list(self._lifecycles.keys())
        tasks = [self.stop_agent(agent_id) for agent_id in agents]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        success_count = sum(1 for r in results if r is True)
        logger.info(f"停止Agent完成: {success_count}/{len(agents)} 成功")

    async def _monitor_lifecycles(self):
        """监控Agent生命周期"""
        logger.info("启动Agent生命周期监控...")

        while self._running:
            try:
                # 检查所有运行中的Agent
                for agent_id, state in list(self._lifecycles.items()):
                    if state == LifecycleState.RUNNING:
                        await self._check_agent_health(agent_id)

                await asyncio.sleep(self.config.health_check_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"生命周期监控异常: {e}", exc_info=True)
                await asyncio.sleep(5)

        logger.info("Agent生命周期监控已停止")

    async def _check_agent_health(self, agent_id: str):
        """检查Agent健康状态"""
        try:
            health_check = self._health_checks.get(agent_id)
            if health_check:
                is_healthy = await health_check(agent_id)

                if not is_healthy:
                    logger.warning(f"Agent健康检查失败: {agent_id}")

                    # 根据重启策略处理
                    if self.config.restart_strategy in [RestartStrategy.ON_FAILURE, RestartStrategy.ALWAYS]:
                        await self.restart_agent(agent_id)

        except Exception as e:
            logger.error(f"健康检查异常 {agent_id}: {e}", exc_info=True)

    async def _default_health_check(self, agent_id: str) -> bool:
        """默认健康检查"""
        try:
            # 检查Agent是否在注册表中正常运行
            agent_meta = await self.registry.get_agent(agent_id)
            if not agent_meta:
                return False

            # 检查状态
            if agent_meta.status != AgentStatus.RUNNING:
                return False

            # 检查最后活动时间
            if agent_meta.last_seen:
                time_since_last_seen = (datetime.now() - agent_meta.last_seen).total_seconds()
                if time_since_last_seen > self.config.health_check_interval * 2:
                    return False

            return True

        except Exception as e:
            logger.error(f"默认健康检查失败 {agent_id}: {e}")
            return False

    async def _wait_for_healthy(self, agent_id: str, timeout: float = 60.0) -> bool:
        """等待Agent变健康"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                if await self._default_health_check(agent_id):
                    return True
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"等待健康检查异常 {agent_id}: {e}")
                await asyncio.sleep(1)

        return False

    async def _check_restart_rate_limit(self, agent_id: str) -> bool:
        """检查重启频率限制"""
        metrics = self._metrics.get(agent_id)
        if not metrics:
            return True

        # 清理一小时前的记录
        cutoff = datetime.now() - timedelta(hours=1)
        metrics.restarts_in_last_hour = [
            t for t in metrics.restarts_in_last_hour if t > cutoff
        ]

        # 检查限制
        return len(metrics.restarts_in_last_hour) < self.config.max_restarts_per_hour

    async def _set_state(self, agent_id: str, state: LifecycleState):
        """设置状态"""
        async with self._lock:
            self._lifecycles[agent_id] = state

        logger.debug(f"Agent状态变更: {agent_id} -> {state.value}")

    async def _emit_event(self, agent_id: str, event_type: str, data: Optional[Dict[str, Any]]):
        """发送事件"""
        handlers = self._event_handlers.get(event_type, [])

        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(agent_id, data)
                else:
                    handler(agent_id, data)
            except Exception as e:
                logger.error(f"事件处理器异常 {event_type}: {e}", exc_info=True)

    def on(self, event_type: str, handler: Callable):
        """注册事件处理器"""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)

    def get_lifecycle_state(self, agent_id: str) -> Optional[LifecycleState]:
        """获取Agent生命周期状态"""
        return self._lifecycles.get(agent_id)

    def get_lifecycle_metrics(self, agent_id: str) -> Optional[LifecycleMetrics]:
        """获取Agent生命周期指标"""
        return self._metrics.get(agent_id)

    async def get_all_lifecycle_info(self) -> Dict[str, Dict[str, Any]]:
        """获取所有Agent生命周期信息"""
        result = {}

        for agent_id in self._lifecycles.keys():
            result[agent_id] = {
                'state': self._lifecycles[agent_id].value,
                'metrics': self._metrics.get(agent_id).to_dict() if agent_id in self._metrics else {}
            }

        return result

# 全局生命周期管理器实例
_global_lifecycle_manager: Optional[LifecycleManager] = None

def get_lifecycle_manager() -> LifecycleManager:
    """获取全局生命周期管理器"""
    global _global_lifecycle_manager
    if _global_lifecycle_manager is None:
        _global_lifecycle_manager = LifecycleManager()
    return _global_lifecycle_manager

async def initialize_lifecycle_manager():
    """初始化全局生命周期管理器"""
    manager = get_lifecycle_manager()
    await manager.initialize()
    return manager

# 使用示例
if __name__ == "__main__":
    async def test_lifecycle_manager():
        """测试生命周期管理器"""
        print("🧪 测试生命周期管理器...")

        # 初始化注册表和生命周期管理器
        registry = await initialize_agent_registry()
        lifecycle = await initialize_lifecycle_manager()

        # 等待发现Agent
        await asyncio.sleep(2)

        # 列出Agent
        agents = await registry.list_agents()
        print(f"\n📋 发现 {len(agents)} 个Agent")

        # 启动第一个Agent（如果有）
        if agents:
            first_agent = agents[0]
            print(f"\n🚀 启动Agent: {first_agent.name}")

            success = await lifecycle.start_agent(first_agent.id)
            print(f"启动结果: {'✅ 成功' if success else '❌ 失败'}")

            if success:
                # 检查状态
                state = lifecycle.get_lifecycle_state(first_agent.id)
                print(f"当前状态: {state.value if state else '未知'}")

                # 等待一段时间
                await asyncio.sleep(5)

                # 停止
                print(f"\n🛑 停止Agent: {first_agent.name}")
                success = await lifecycle.stop_agent(first_agent.id)
                print(f"停止结果: {'✅ 成功' if success else '❌ 失败'}")

        # 关闭
        await lifecycle.shutdown()

        print("\n✅ 生命周期管理器测试完成")

    asyncio.run(test_lifecycle_manager())
