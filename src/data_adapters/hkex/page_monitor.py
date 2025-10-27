#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HKEX 页面变化监控模块

监控网页内容变化，触发数据更新，支持阈值配置和变更通知。

主要功能:
- 检测页面结构变化
- 监控数据更新时间
- 支持阈值配置
- 提供变更通知
- 防抖机制避免频繁触发

作者: Claude Code
创建日期: 2025-10-27
"""

import asyncio
import hashlib
import json
import logging
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import difflib

logger = logging.getLogger("hk_quant_system.hkex_page_monitor")


class ChangeType(Enum):
    """变化类型枚举"""
    CONTENT = "content"  # 内容变化
    STRUCTURE = "structure"  # 结构变化
    ATTRIBUTE = "attribute"  # 属性变化
    NEW_ELEMENT = "new_element"  # 新元素
    REMOVED_ELEMENT = "removed_element"  # 元素移除
    TIMESTAMP = "timestamp"  # 时间戳变化


@dataclass
class PageChange:
    """页面变化记录"""
    page_id: str
    url: str
    change_type: ChangeType
    timestamp: datetime
    selector: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    change_ratio: float = 0.0
    severity: str = "medium"  # low, medium, high, critical
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MonitoringConfig:
    """监控配置"""
    page_id: str
    url: str
    selectors: List[str]
    check_interval: int = 60  # 检查间隔（秒）
    debounce_ms: int = 5000  # 防抖时间（毫秒）
    change_threshold: float = 0.01  # 变化阈值（1%）
    min_change_interval: int = 300  # 最小变化间隔（秒）
    enable_notifications: bool = True
    max_history: int = 100  # 最大历史记录数


class PageMonitor:
    """页面监控器

    监控页面内容变化，检测数据更新。
    """

    def __init__(self):
        """初始化监控器"""
        self.monitoring_tasks = {}
        self.change_history = {}
        self.callbacks = {}
        self.page_snapshots = {}
        self.running_monitors = set()
        self.lock = asyncio.Lock()

        logger.info("✓ PageMonitor 初始化完成")

    async def start_monitoring(
        self,
        config: MonitoringConfig,
        callback: Optional[Callable[[PageChange], None]] = None
    ) -> str:
        """启动页面监控

        Args:
            config: 监控配置
            callback: 变化回调函数

        Returns:
            监控任务 ID

        Raises:
            Exception: 启动监控失败
        """
        try:
            monitor_id = f"monitor_{config.page_id}_{int(datetime.now().timestamp())}"

            # 注册回调
            if callback:
                self.callbacks[monitor_id] = callback

            # 创建监控任务
            task = asyncio.create_task(
                self._monitor_loop(config, monitor_id)
            )

            async with self.lock:
                self.monitoring_tasks[monitor_id] = {
                    "task": task,
                    "config": config,
                    "start_time": datetime.now(),
                    "status": "running"
                }
                self.running_monitors.add(monitor_id)

            logger.info(f"✓ 启动页面监控: {monitor_id} ({config.url})")
            return monitor_id

        except Exception as e:
            logger.error(f"✗ 启动页面监控失败: {e}")
            raise

    async def _monitor_loop(
        self,
        config: MonitoringConfig,
        monitor_id: str
    ):
        """监控循环"""
        try:
            logger.info(f"开始监控循环: {monitor_id}")

            while monitor_id in self.running_monitors:
                try:
                    # 检查页面变化
                    change = await self._check_page_changes(config)

                    if change:
                        # 触发回调
                        await self._trigger_callback(monitor_id, change)

                        # 记录变化
                        await self._record_change(monitor_id, change)

                        # 防抖延迟
                        await asyncio.sleep(config.debounce_ms / 1000)

                    # 等待下次检查
                    await asyncio.sleep(config.check_interval)

                except asyncio.CancelledError:
                    logger.info(f"监控任务取消: {monitor_id}")
                    break
                except Exception as e:
                    logger.error(f"监控循环错误 {monitor_id}: {e}")
                    await asyncio.sleep(60)  # 错误后等待1分钟

            logger.info(f"监控循环结束: {monitor_id}")

        except Exception as e:
            logger.error(f"✗ 监控循环异常: {e}")

    async def _check_page_changes(
        self,
        config: MonitoringConfig
    ) -> Optional[PageChange]:
        """检查页面变化

        Args:
            config: 监控配置

        Returns:
            页面变化记录
        """
        try:
            # 生成页面快照
            current_snapshot = await self._capture_page_snapshot(config)

            # 与上次快照比较
            if config.page_id in self.page_snapshots:
                last_snapshot = self.page_snapshots[config.page_id]

                # 比较变化
                change = await self._compare_snapshots(
                    config, last_snapshot, current_snapshot
                )

                if change:
                    # 更新快照
                    self.page_snapshots[config.page_id] = current_snapshot
                    return change

            # 首次监控，保存快照
            self.page_snapshots[config.page_id] = current_snapshot
            return None

        except Exception as e:
            logger.error(f"检查页面变化失败: {e}")
            return None

    async def _capture_page_snapshot(
        self,
        config: MonitoringConfig
    ) -> Dict[str, Any]:
        """捕获页面快照

        Args:
            config: 监控配置

        Returns:
            页面快照数据
        """
        try:
            # 这里需要实际调用 Chrome MCP
            # 暂时返回模拟数据
            snapshot = {
                "page_id": config.page_id,
                "url": config.url,
                "timestamp": datetime.now().isoformat(),
                "selectors": {},
                "content_hash": hashlib.md5(
                    json.dumps(config.selectors, sort_keys=True).encode()
                ).hexdigest()
            }

            # 为每个监控的选择器捕获内容
            for selector in config.selectors:
                snapshot["selectors"][selector] = {
                    "found": True,
                    "content": f"content for {selector}",
                    "attributes": {},
                    "element_count": 1
                }

            return snapshot

        except Exception as e:
            logger.error(f"捕获页面快照失败: {e}")
            raise

    async def _compare_snapshots(
        self,
        config: MonitoringConfig,
        last_snapshot: Dict[str, Any],
        current_snapshot: Dict[str, Any]
    ) -> Optional[PageChange]:
        """比较快照并检测变化

        Args:
            config: 监控配置
            last_snapshot: 上次快照
            current_snapshot: 当前快照

        Returns:
            页面变化记录
        """
        try:
            # 检查时间戳变化
            if last_snapshot["timestamp"] != current_snapshot["timestamp"]:
                # 计算变化比例
                change_ratio = self._calculate_change_ratio(
                    last_snapshot, current_snapshot
                )

                if change_ratio >= config.change_threshold:
                    change_type = self._determine_change_type(
                        last_snapshot, current_snapshot
                    )

                    change = PageChange(
                        page_id=config.page_id,
                        url=config.url,
                        change_type=change_type,
                        timestamp=datetime.now(),
                        change_ratio=change_ratio,
                        severity=self._calculate_severity(change_ratio),
                        description=f"页面内容发生变化 (变化率: {change_ratio:.2%})"
                    )

                    logger.info(
                        f"检测到页面变化: {config.page_id} "
                        f"(类型: {change_type.value}, 变化率: {change_ratio:.2%})"
                    )
                    return change

            return None

        except Exception as e:
            logger.error(f"比较快照失败: {e}")
            return None

    def _calculate_change_ratio(
        self,
        snapshot1: Dict[str, Any],
        snapshot2: Dict[str, Any]
    ) -> float:
        """计算变化比例

        Args:
            snapshot1: 快照1
            snapshot2: 快照2

        Returns:
            变化比例 (0.0 - 1.0)
        """
        try:
            # 比较选择器内容
            selectors1 = snapshot1.get("selectors", {})
            selectors2 = snapshot2.get("selectors", {})

            all_selectors = set(selectors1.keys()) | set(selectors2.keys())
            if not all_selectors:
                return 0.0

            changed_count = 0
            for selector in all_selectors:
                content1 = selectors1.get(selector, {}).get("content", "")
                content2 = selectors2.get(selector, {}).get("content", "")

                if content1 != content2:
                    changed_count += 1

            return changed_count / len(all_selectors)

        except Exception as e:
            logger.error(f"计算变化比例失败: {e}")
            return 0.0

    def _determine_change_type(
        self,
        snapshot1: Dict[str, Any],
        snapshot2: Dict[str, Any]
    ) -> ChangeType:
        """确定变化类型

        Args:
            snapshot1: 快照1
            snapshot2: 快照2

        Returns:
            变化类型
        """
        try:
            # 简单实现：基于内容哈希变化
            if snapshot1["content_hash"] != snapshot2["content_hash"]:
                return ChangeType.CONTENT

            return ChangeType.CONTENT

        except Exception as e:
            logger.error(f"确定变化类型失败: {e}")
            return ChangeType.CONTENT

    def _calculate_severity(self, change_ratio: float) -> str:
        """计算变化严重程度

        Args:
            change_ratio: 变化比例

        Returns:
            严重程度
        """
        if change_ratio >= 0.5:
            return "critical"
        elif change_ratio >= 0.3:
            return "high"
        elif change_ratio >= 0.1:
            return "medium"
        else:
            return "low"

    async def _trigger_callback(
        self,
        monitor_id: str,
        change: PageChange
    ):
        """触发回调函数

        Args:
            monitor_id: 监控 ID
            change: 页面变化
        """
        try:
            if monitor_id in self.callbacks:
                callback = self.callbacks[monitor_id]
                if asyncio.iscoroutinefunction(callback):
                    await callback(change)
                else:
                    callback(change)

        except Exception as e:
            logger.error(f"触发回调失败: {e}")

    async def _record_change(
        self,
        monitor_id: str,
        change: PageChange
    ):
        """记录变化

        Args:
            monitor_id: 监控 ID
            change: 页面变化
        """
        try:
            if monitor_id not in self.change_history:
                self.change_history[monitor_id] = []

            # 添加到历史
            self.change_history[monitor_id].append(change)

            # 限制历史记录数量
            config = self.monitoring_tasks[monitor_id]["config"]
            if len(self.change_history[monitor_id]) > config.max_history:
                self.change_history[monitor_id] = (
                    self.change_history[monitor_id][-config.max_history:]
                )

            logger.debug(f"记录变化: {monitor_id} -> {change.change_type.value}")

        except Exception as e:
            logger.error(f"记录变化失败: {e}")

    async def stop_monitoring(self, monitor_id: str) -> bool:
        """停止页面监控

        Args:
            monitor_id: 监控 ID

        Returns:
            是否成功
        """
        try:
            async with self.lock:
                if monitor_id not in self.monitoring_tasks:
                    logger.warning(f"监控不存在: {monitor_id}")
                    return False

                # 从运行集合中移除
                self.running_monitors.discard(monitor_id)

                # 取消任务
                task_info = self.monitoring_tasks[monitor_id]
                task = task_info["task"]
                if not task.done():
                    task.cancel()

                # 等待任务完成
                try:
                    await task
                except asyncio.CancelledError:
                    pass

                # 清理资源
                del self.monitoring_tasks[monitor_id]
                if monitor_id in self.callbacks:
                    del self.callbacks[monitor_id]

            logger.info(f"✓ 停止页面监控: {monitor_id}")
            return True

        except Exception as e:
            logger.error(f"✗ 停止页面监控失败: {e}")
            return False

    async def stop_all_monitoring(self) -> int:
        """停止所有监控

        Returns:
            停止的监控数量
        """
        try:
            monitor_ids = list(self.monitoring_tasks.keys())
            stopped_count = 0

            for monitor_id in monitor_ids:
                await self.stop_monitoring(monitor_id)
                stopped_count += 1

            logger.info(f"✓ 停止所有监控: {stopped_count} 个")
            return stopped_count

        except Exception as e:
            logger.error(f"✗ 停止所有监控失败: {e}")
            return 0

    async def get_monitoring_status(self, monitor_id: str) -> Optional[Dict[str, Any]]:
        """获取监控状态

        Args:
            monitor_id: 监控 ID

        Returns:
            监控状态字典
        """
        try:
            if monitor_id not in self.monitoring_tasks:
                return None

            task_info = self.monitoring_tasks[monitor_id]
            config = task_info["config"]
            changes = self.change_history.get(monitor_id, [])

            # 计算统计信息
            now = datetime.now()
            last_change = changes[-1] if changes else None
            uptime = now - task_info["start_time"]

            return {
                "monitor_id": monitor_id,
                "status": "running" if monitor_id in self.running_monitors else "stopped",
                "url": config.url,
                "start_time": task_info["start_time"].isoformat(),
                "uptime_seconds": uptime.total_seconds(),
                "last_change": last_change.timestamp.isoformat() if last_change else None,
                "change_count": len(changes),
                "check_interval": config.check_interval,
                "selectors": config.selectors,
                "recent_changes": [
                    {
                        "timestamp": c.timestamp.isoformat(),
                        "type": c.change_type.value,
                        "severity": c.severity,
                        "description": c.description
                    }
                    for c in changes[-5:]  # 最近5次变化
                ]
            }

        except Exception as e:
            logger.error(f"获取监控状态失败: {e}")
            return None

    def list_active_monitors(self) -> List[str]:
        """列出所有活动监控

        Returns:
            监控 ID 列表
        """
        return list(self.running_monitors)

    def get_change_history(
        self,
        monitor_id: str,
        limit: int = 50
    ) -> List[PageChange]:
        """获取变化历史

        Args:
            monitor_id: 监控 ID
            limit: 返回数量限制

        Returns:
            变化历史列表
        """
        try:
            changes = self.change_history.get(monitor_id, [])
            return changes[-limit:] if limit > 0 else changes

        except Exception as e:
            logger.error(f"获取变化历史失败: {e}")
            return []


# 变化通知回调示例
async def change_notification_callback(change: PageChange):
    """变化通知回调示例

    Args:
        change: 页面变化
    """
    print(f"\n🔔 页面变化通知:")
    print(f"  页面: {change.page_id}")
    print(f"  类型: {change.change_type.value}")
    print(f"  严重程度: {change.severity}")
    print(f"  变化率: {change.change_ratio:.2%}")
    print(f"  描述: {change.description}")
    print(f"  时间: {change.timestamp}\n")


# 使用示例
async def main():
    """演示页面监控功能"""

    print("\n" + "="*70)
    print("HKEX 页面变化监控演示")
    print("="*70 + "\n")

    # 创建监控器
    monitor = PageMonitor()

    # 创建监控配置
    config = MonitoringConfig(
        page_id="hkex_main",
        url="https://www.hkex.com.hk/?sc_lang=zh-HK",
        selectors=[
            "table[role='table']",
            ".market-data",
            ".index-value"
        ],
        check_interval=60,  # 每分钟检查一次
        debounce_ms=5000,  # 5秒防抖
        change_threshold=0.01,  # 1% 变化阈值
        max_history=100
    )

    # 启动监控
    monitor_id = await monitor.start_monitoring(
        config,
        callback=change_notification_callback
    )

    print(f"✓ 启动监控: {monitor_id}\n")

    # 运行一段时间
    print("运行监控 10 秒...")
    await asyncio.sleep(10)

    # 获取监控状态
    status = await monitor.get_monitoring_status(monitor_id)
    if status:
        print(f"\n监控状态:")
        print(f"  状态: {status['status']}")
        print(f"  URL: {status['url']}")
        print(f"  运行时长: {status['uptime_seconds']:.0f} 秒")
        print(f"  变化次数: {status['change_count']}")

    # 停止监控
    await monitor.stop_monitoring(monitor_id)
    print(f"\n✓ 监控已停止")

    print("\n" + "="*70)
    print("演示完成")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
