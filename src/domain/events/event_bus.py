#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
事件总线
"""

import asyncio
from typing import Dict, List, Type, Set
from collections import defaultdict
from .domain_event import DomainEvent
from .event_handler import EventHandler


class EventBus:
    """事件总线"""

    def __init__(self):
        self._handlers: Dict[Type[DomainEvent], List[EventHandler]] = defaultdict(list)
        self._wildcard_handlers: List[EventHandler] = []
        self._running = False
        self._event_queue = asyncio.Queue()
        self._worker_tasks: List[asyncio.Task] = []

    async def start(self):
        """启动事件总线"""
        if self._running:
            return

        self._running = True
        # 创建工作协程来处理事件
        for _ in range(5):  # 5个工作协程
            task = asyncio.create_task(self._event_worker())
            self._worker_tasks.append(task)

    async def stop(self):
        """停止事件总线"""
        self._running = False

        # 取消所有工作协程
        for task in self._worker_tasks:
            task.cancel()

        # 等待所有任务完成
        if self._worker_tasks:
            await asyncio.gather(*self._worker_tasks, return_exceptions=True)

        self._worker_tasks.clear()

    async def publish(self, event: DomainEvent):
        """发布事件"""
        await self._event_queue.put(event)

    async def publish_many(self, events: List[DomainEvent]):
        """批量发布事件"""
        for event in events:
            await self.publish(event)

    def subscribe(self, handler: EventHandler):
        """订阅事件处理器"""
        event_type = handler.subscribed_to

        # 检查是否为通配符处理器
        if event_type == DomainEvent:
            self._wildcard_handlers.append(handler)
        else:
            self._handlers[event_type].append(handler)

    def unsubscribe(self, handler: EventHandler):
        """取消订阅事件处理器"""
        event_type = handler.subscribed_to

        # 从通配符处理器中移除
        if event_type == DomainEvent:
            if handler in self._wildcard_handlers:
                self._wildcard_handlers.remove(handler)
        else:
            # 从特定事件处理器中移除
            if event_type in self._handlers and handler in self._handlers[event_type]:
                self._handlers[event_type].remove(handler)

    async def _event_worker(self):
        """事件处理工作协程"""
        while self._running:
            try:
                # 从队列获取事件
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)

                # 处理事件
                await self._dispatch_event(event)

                # 标记任务完成
                self._event_queue.task_done()

            except asyncio.TimeoutError:
                # 超时后继续循环
                continue
            except asyncio.CancelledError:
                # 任务被取消，退出
                break
            except Exception as e:
                # 处理异常，继续工作
                print(f"事件处理异常: {e}")

    async def _dispatch_event(self, event: DomainEvent):
        """分发事件给处理器"""
        # 首先获取事件类型及其所有父类
        event_type = type(event)
        handler_types = set()

        # 添加当前事件类型
        handler_types.add(event_type)

        # 添加所有父类
        for base in event_type.__mro__[1:]:
            if base != object:
                handler_types.add(base)

        # 找到匹配的事件处理器
        matched_handlers = []

        # 匹配特定事件类型
        for handler_type in handler_types:
            if handler_type in self._handlers:
                matched_handlers.extend(self._handlers[handler_type])

        # 匹配通配符处理器
        matched_handlers.extend(self._wildcard_handlers)

        # 并发处理事件
        if matched_handlers:
            tasks = [handler.handle(event) for handler in matched_handlers]
            await asyncio.gather(*tasks, return_exceptions=True)

    def get_subscribed_events(self) -> Dict[str, int]:
        """获取订阅的事件统计"""
        result = {}

        for event_type, handlers in self._handlers.items():
            result[event_type.__name__] = len(handlers)

        if self._wildcard_handlers:
            result["* (wildcard)"] = len(self._wildcard_handlers)

        return result