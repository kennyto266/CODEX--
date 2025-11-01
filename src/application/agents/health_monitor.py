#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
健康监控器 (HealthMonitor)
实时监控Agent健康状态、收集性能指标、提供健康报告和告警
"""

import os
import sys
import asyncio
import logging
import psutil
import time
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import json

# 添加项目根目录
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from infrastructure.logging.context_logger import get_context_logger
from agent_registry import AgentRegistry, get_agent_registry
from lifecycle_manager import LifecycleManager, get_lifecycle_manager

logger = get_context_logger("agent.health")

class HealthStatus(Enum):
    """健康状态枚举"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"
    DEGRADED = "degraded"

class MetricType(Enum):
    """指标类型"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

@dataclass
class HealthMetric:
    """健康指标"""
    name: str
    value: float
    metric_type: MetricType
    timestamp: datetime
    unit: Optional[str] = None
    labels: Dict[str, str] = field(default_factory=dict)
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'name': self.name,
            'value': self.value,
            'type': self.metric_type.value,
            'timestamp': self.timestamp.isoformat(),
            'unit': self.unit,
            'labels': self.labels,
            'threshold_warning': self.threshold_warning,
            'threshold_critical': self.threshold_critical
        }

@dataclass
class HealthReport:
    """健康报告"""
    agent_id: str
    status: HealthStatus
    score: float  # 0-100, 100为完全健康
    timestamp: datetime
    metrics: List[HealthMetric] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    uptime_seconds: float = 0.0
    last_check: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'agent_id': self.agent_id,
            'status': self.status.value,
            'score': self.score,
            'timestamp': self.timestamp.isoformat(),
            'metrics': [m.to_dict() for m in self.metrics],
            'issues': self.issues,
            'recommendations': self.recommendations,
            'uptime_seconds': self.uptime_seconds,
            'last_check': self.last_check.isoformat() if self.last_check else None
        }

@dataclass
class SystemMetrics:
    """系统指标"""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_total_mb: float
    disk_usage_percent: float
    network_io_bytes: Dict[str, int]
    process_count: int
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'cpu_percent': self.cpu_percent,
            'memory_percent': self.memory_percent,
            'memory_used_mb': self.memory_used_mb,
            'memory_total_mb': self.memory_total_mb,
            'disk_usage_percent': self.disk_usage_percent,
            'network_io_bytes': self.network_io_bytes,
            'process_count': self.process_count,
            'timestamp': self.timestamp.isoformat()
        }

class HealthMonitor:
    """Agent健康监控器"""

    def __init__(self, registry: Optional[AgentRegistry] = None,
                 lifecycle_manager: Optional[LifecycleManager] = None):
        self.registry = registry or get_agent_registry()
        self.lifecycle = lifecycle_manager or get_lifecycle_manager()

        self._health_checks: Dict[str, Callable] = {}
        self._metric_collectors: Dict[str, Callable] = {}
        self._health_reports: Dict[str, HealthReport] = {}
        self._alert_handlers: List[Callable] = []
        self._monitoring_enabled = True
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._health_history: Dict[str, List[HealthReport]] = {}
        self._metric_history: Dict[str, List[HealthMetric]] = {}
        self._check_interval = 30.0
        self._history_limit = 100  # 保存最近100条记录

        # 注册默认健康检查
        self._register_default_checks()

    def _register_default_checks(self):
        """注册默认健康检查"""
        self._health_checks.update({
            'basic': self._basic_health_check,
            'heartbeat': self._heartbeat_check,
            'resource': self._resource_usage_check,
            'dependency': self._dependency_check
        })

        self._metric_collectors.update({
            'cpu': self._collect_cpu_metric,
            'memory': self._collect_memory_metric,
            'disk': self._collect_disk_metric,
            'network': self._collect_network_metric,
            'custom': self._collect_custom_metrics
        })

    async def start(self):
        """启动健康监控"""
        logger.info("启动健康监控器...")

        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())

        logger.info("健康监控器已启动")

    async def stop(self):
        """停止健康监控"""
        logger.info("停止健康监控器...")

        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

        logger.info("健康监控器已停止")

    async def _monitor_loop(self):
        """监控循环"""
        logger.info("开始Agent健康监控循环...")

        while self._running:
            try:
                # 获取所有Agent
                agents = await self.registry.list_agents()

                for agent in agents:
                    if agent.id not in self._health_reports:
                        await self.check_agent_health(agent.id)

                # 收集系统指标
                system_metrics = await self._collect_system_metrics()

                # 等待下一次检查
                await asyncio.sleep(self._check_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"健康监控循环异常: {e}", exc_info=True)
                await asyncio.sleep(5)

        logger.info("健康监控循环已停止")

    async def check_agent_health(self, agent_id: str) -> HealthReport:
        """检查单个Agent健康状态"""
        try:
            # 获取Agent信息
            agent_meta = await self.registry.get_agent(agent_id)
            if not agent_meta:
                report = self._create_unknown_report(agent_id, "Agent未注册")
                self._health_reports[agent_id] = report
                return report

            # 收集指标
            metrics = await self._collect_agent_metrics(agent_id)

            # 执行健康检查
            issues = []
            recommendations = []

            for check_name, check_func in self._health_checks.items():
                try:
                    check_result = await check_func(agent_id, metrics)
                    if not check_result.get('healthy', True):
                        issues.extend(check_result.get('issues', []))
                        recommendations.extend(check_result.get('recommendations', []))
                except Exception as e:
                    logger.error(f"健康检查异常 {check_name} - {agent_id}: {e}")
                    issues.append(f"健康检查失败: {check_name}")

            # 计算健康评分
            score = self._calculate_health_score(metrics, issues)

            # 确定状态
            status = self._determine_health_status(score, issues)

            # 创建报告
            lifecycle_metrics = self.lifecycle.get_lifecycle_metrics(agent_id)
            uptime = lifecycle_metrics.uptime_seconds if lifecycle_metrics else 0.0

            report = HealthReport(
                agent_id=agent_id,
                status=status,
                score=score,
                timestamp=datetime.now(),
                metrics=metrics,
                issues=issues,
                recommendations=recommendations,
                uptime_seconds=uptime,
                last_check=datetime.now()
            )

            # 存储报告
            self._health_reports[agent_id] = report

            # 添加到历史
            if agent_id not in self._health_history:
                self._health_history[agent_id] = []
            self._health_history[agent_id].append(report)
            if len(self._health_history[agent_id]) > self._history_limit:
                self._health_history[agent_id].pop(0)

            # 存储指标历史
            for metric in metrics:
                if metric.name not in self._metric_history:
                    self._metric_history[metric.name] = []
                self._metric_history[metric.name].append(metric)
                if len(self._metric_history[metric.name]) > self._history_limit:
                    self._metric_history[metric.name].pop(0)

            # 检查是否需要告警
            if status in [HealthStatus.CRITICAL, HealthStatus.WARNING]:
                await self._trigger_alert(agent_id, report)

            return report

        except Exception as e:
            logger.error(f"检查Agent健康异常 {agent_id}: {e}", exc_info=True)
            report = self._create_unknown_report(agent_id, str(e))
            self._health_reports[agent_id] = report
            return report

    async def _collect_agent_metrics(self, agent_id: str) -> List[HealthMetric]:
        """收集Agent指标"""
        metrics = []

        # 获取Agent实例
        agent_instance = await self.registry.get_agent_instance(agent_id)

        # 基础指标
        metrics.extend(await self._collect_basic_metrics(agent_id))

        # 自定义指标收集器
        for collector_name, collector_func in self._metric_collectors.items():
            try:
                collector_metrics = await collector_func(agent_id, agent_instance)
                if collector_metrics:
                    metrics.extend(collector_metrics)
            except Exception as e:
                logger.error(f"指标收集器异常 {collector_name} - {agent_id}: {e}")

        return metrics

    async def _collect_basic_metrics(self, agent_id: str) -> List[HealthMetric]:
        """收集基础指标"""
        metrics = []

        # Agent运行时间
        lifecycle_metrics = self.lifecycle.get_lifecycle_metrics(agent_id)
        if lifecycle_metrics:
            uptime = lifecycle_metrics.uptime_seconds
            metrics.append(HealthMetric(
                name="uptime_seconds",
                value=uptime,
                metric_type=MetricType.COUNTER,
                timestamp=datetime.now(),
                unit="seconds"
            ))

        # Agent最后活动时间
        agent_meta = await self.registry.get_agent(agent_id)
        if agent_meta and agent_meta.last_seen:
            time_since_last_seen = (datetime.now() - agent_meta.last_seen).total_seconds()
            metrics.append(HealthMetric(
                name="time_since_last_seen",
                value=time_since_last_seen,
                metric_type=MetricType.GAUGE,
                timestamp=datetime.now(),
                unit="seconds",
                threshold_warning=300.0,  # 5分钟
                threshold_critical=600.0  # 10分钟
            ))

        return metrics

    async def _basic_health_check(self, agent_id: str, metrics: List[HealthMetric]) -> Dict[str, Any]:
        """基础健康检查"""
        issues = []
        recommendations = []
        healthy = True

        # 检查运行时间
        uptime_metric = next((m for m in metrics if m.name == "uptime_seconds"), None)
        if uptime_metric and uptime_metric.value < 60:
            issues.append("Agent启动时间不足1分钟")
            healthy = False

        # 检查最后活动时间
        last_seen_metric = next((m for m in metrics if m.name == "time_since_last_seen"), None)
        if last_seen_metric:
            if last_seen_metric.value > last_seen_metric.threshold_critical:
                issues.append("Agent长时间未活动（超过10分钟）")
                recommendations.append("检查Agent是否正常运行")
                healthy = False
            elif last_seen_metric.value > last_seen_metric.threshold_warning:
                issues.append("Agent活动时间较长（超过5分钟）")
                recommendations.append("关注Agent活动状态")

        return {
            'healthy': healthy,
            'issues': issues,
            'recommendations': recommendations
        }

    async def _heartbeat_check(self, agent_id: str, metrics: List[HealthMetric]) -> Dict[str, Any]:
        """心跳检查"""
        issues = []
        recommendations = []
        healthy = True

        # 检查Agent是否在注册表中正常运行
        agent_meta = await self.registry.get_agent(agent_id)
        if not agent_meta:
            issues.append("Agent未注册")
            healthy = False
        elif agent_meta.status.value != "running":
            issues.append(f"Agent状态异常: {agent_meta.status.value}")
            healthy = False

        # 检查生命周期状态
        lifecycle_state = self.lifecycle.get_lifecycle_state(agent_id)
        if lifecycle_state and lifecycle_state.value != "running":
            issues.append(f"生命周期状态异常: {lifecycle_state.value}")
            healthy = False

        return {
            'healthy': healthy,
            'issues': issues,
            'recommendations': recommendations
        }

    async def _resource_usage_check(self, agent_id: str, metrics: List[HealthMetric]) -> Dict[str, Any]:
        """资源使用检查"""
        issues = []
        recommendations = []
        healthy = True

        # 这里可以添加更详细的资源使用检查
        # 例如检查Agent实例的CPU和内存使用

        return {
            'healthy': healthy,
            'issues': issues,
            'recommendations': recommendations
        }

    async def _dependency_check(self, agent_id: str, metrics: List[HealthMetric]) -> Dict[str, Any]:
        """依赖检查"""
        issues = []
        recommendations = []
        healthy = True

        # 检查Agent依赖
        agent_meta = await self.registry.get_agent(agent_id)
        if agent_meta and agent_meta.dependencies:
            for dep in agent_meta.dependencies:
                # 这里检查依赖是否满足
                pass

        return {
            'healthy': healthy,
            'issues': issues,
            'recommendations': recommendations
        }

    async def _collect_cpu_metric(self, agent_id: str, agent_instance: Any) -> List[HealthMetric]:
        """收集CPU指标"""
        return [HealthMetric(
            name="cpu_usage",
            value=psutil.cpu_percent(interval=1),
            metric_type=MetricType.GAUGE,
            timestamp=datetime.now(),
            unit="percent",
            threshold_warning=80.0,
            threshold_critical=95.0
        )]

    async def _collect_memory_metric(self, agent_id: str, agent_instance: Any) -> List[HealthMetric]:
        """收集内存指标"""
        memory = psutil.virtual_memory()
        return [HealthMetric(
            name="memory_usage",
            value=memory.percent,
            metric_type=MetricType.GAUGE,
            timestamp=datetime.now(),
            unit="percent",
            threshold_warning=85.0,
            threshold_critical=95.0
        )]

    async def _collect_disk_metric(self, agent_id: str, agent_instance: Any) -> List[HealthMetric]:
        """收集磁盘指标"""
        disk = psutil.disk_usage('/')
        return [HealthMetric(
            name="disk_usage",
            value=(disk.used / disk.total) * 100,
            metric_type=MetricType.GAUGE,
            timestamp=datetime.now(),
            unit="percent",
            threshold_warning=90.0,
            threshold_critical=95.0
        )]

    async def _collect_network_metric(self, agent_id: str, agent_instance: Any) -> List[HealthMetric]:
        """收集网络指标"""
        net_io = psutil.net_io_counters()
        return [HealthMetric(
            name="network_bytes_sent",
            value=net_io.bytes_sent,
            metric_type=MetricType.COUNTER,
            timestamp=datetime.now(),
            unit="bytes"
        )]

    async def _collect_custom_metrics(self, agent_id: str, agent_instance: Any) -> List[HealthMetric]:
        """收集自定义指标"""
        # 如果Agent实例有自定义指标收集方法
        if agent_instance and hasattr(agent_instance, 'collect_metrics'):
            try:
                custom_metrics = await agent_instance.collect_metrics()
                return [HealthMetric(
                    name=f"custom_{key}",
                    value=value,
                    metric_type=MetricType.GAUGE,
                    timestamp=datetime.now()
                ) for key, value in custom_metrics.items()]
            except Exception as e:
                logger.error(f"收集自定义指标异常 {agent_id}: {e}")

        return []

    async def _collect_system_metrics(self) -> SystemMetrics:
        """收集系统指标"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        net_io = psutil.net_io_counters()
        process_count = len(psutil.pids())

        return SystemMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used_mb=memory.used / 1024 / 1024,
            memory_total_mb=memory.total / 1024 / 1024,
            disk_usage_percent=(disk.used / disk.total) * 100,
            network_io_bytes={
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv
            },
            process_count=process_count,
            timestamp=datetime.now()
        )

    def _calculate_health_score(self, metrics: List[HealthMetric], issues: List[str]) -> float:
        """计算健康评分"""
        score = 100.0

        # 根据问题数量扣分
        score -= len(issues) * 10

        # 根据指标阈值扣分
        for metric in metrics:
            if metric.threshold_critical and metric.value > metric.threshold_critical:
                score -= 20
            elif metric.threshold_warning and metric.value > metric.threshold_warning:
                score -= 10

        return max(0.0, min(100.0, score))

    def _determine_health_status(self, score: float, issues: List[str]) -> HealthStatus:
        """确定健康状态"""
        if score >= 90:
            return HealthStatus.HEALTHY
        elif score >= 70:
            return HealthStatus.WARNING
        elif score >= 50:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.CRITICAL

    def _create_unknown_report(self, agent_id: str, reason: str) -> HealthReport:
        """创建未知状态报告"""
        return HealthReport(
            agent_id=agent_id,
            status=HealthStatus.UNKNOWN,
            score=0.0,
            timestamp=datetime.now(),
            issues=[reason],
            recommendations=["检查Agent配置和状态"]
        )

    async def _trigger_alert(self, agent_id: str, report: HealthReport):
        """触发告警"""
        for handler in self._alert_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(agent_id, report)
                else:
                    handler(agent_id, report)
            except Exception as e:
                logger.error(f"告警处理器异常: {e}", exc_info=True)

    def add_alert_handler(self, handler: Callable):
        """添加告警处理器"""
        self._alert_handlers.append(handler)

    def get_agent_health(self, agent_id: str) -> Optional[HealthReport]:
        """获取Agent健康报告"""
        return self._health_reports.get(agent_id)

    async def get_all_health_reports(self) -> Dict[str, HealthReport]:
        """获取所有Agent健康报告"""
        return self._health_reports.copy()

    def get_health_summary(self) -> Dict[str, Any]:
        """获取健康摘要"""
        reports = list(self._health_reports.values())

        summary = {
            'total_agents': len(reports),
            'healthy_count': len([r for r in reports if r.status == HealthStatus.HEALTHY]),
            'warning_count': len([r for r in reports if r.status == HealthStatus.WARNING]),
            'critical_count': len([r for r in reports if r.status == HealthStatus.CRITICAL]),
            'unknown_count': len([r for r in reports if r.status == HealthStatus.UNKNOWN]),
            'degraded_count': len([r for r in reports if r.status == HealthStatus.DEGRADED]),
            'average_score': sum(r.score for r in reports) / max(len(reports), 1),
            'timestamp': datetime.now().isoformat()
        }

        return summary

    def get_health_history(self, agent_id: str, limit: int = 10) -> List[HealthReport]:
        """获取Agent健康历史"""
        history = self._health_history.get(agent_id, [])
        return history[-limit:]

    def get_metric_history(self, metric_name: str, limit: int = 50) -> List[HealthMetric]:
        """获取指标历史"""
        history = self._metric_history.get(metric_name, [])
        return history[-limit:]

    async def export_health_data(self) -> Dict[str, Any]:
        """导出健康数据"""
        return {
            'reports': {aid: report.to_dict() for aid, report in self._health_reports.items()},
            'summary': self.get_health_summary(),
            'history': {
                aid: [h.to_dict() for h in history]
                for aid, history in self._health_history.items()
            },
            'exported_at': datetime.now().isoformat()
        }

# 全局健康监控器实例
_global_health_monitor: Optional[HealthMonitor] = None

def get_health_monitor() -> HealthMonitor:
    """获取全局健康监控器"""
    global _global_health_monitor
    if _global_health_monitor is None:
        _global_health_monitor = HealthMonitor()
    return _global_health_monitor

async def initialize_health_monitor():
    """初始化全局健康监控器"""
    monitor = get_health_monitor()
    await monitor.start()
    return monitor

# 使用示例
if __name__ == "__main__":
    async def test_health_monitor():
        """测试健康监控器"""
        print("🧪 测试健康监控器...")

        # 初始化
        registry = await initialize_agent_registry()
        lifecycle = await initialize_lifecycle_manager()
        monitor = await initialize_health_monitor()

        # 等待Agent发现
        await asyncio.sleep(2)

        # 检查所有Agent健康
        agents = await registry.list_agents()
        print(f"\n📋 检查 {len(agents)} 个Agent健康状态")

        for agent in agents:
            report = await monitor.check_agent_health(agent.id)
            print(f"\n🤖 {agent.name}:")
            print(f"  状态: {report.status.value}")
            print(f"  评分: {report.score:.1f}/100")
            print(f"  问题: {len(report.issues)} 个")
            print(f"  建议: {len(report.recommendations)} 条")

        # 显示摘要
        summary = monitor.get_health_summary()
        print(f"\n📊 健康摘要:")
        for key, value in summary.items():
            print(f"  {key}: {value}")

        # 关闭
        await monitor.stop()
        await lifecycle.shutdown()

        print("\n✅ 健康监控器测试完成")

    asyncio.run(test_health_monitor())
