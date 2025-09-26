"""
港股量化交易 AI Agent 系统 - 实时数据推送服务

实现WebSocket数据推送，确保仪表板实时更新。
扩展现有的WebSocket连接管理，提供低延迟的实时数据更新。
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Callable, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
from fastapi import WebSocket, WebSocketDisconnect

from ..core import SystemConfig
from ..core.message_queue import MessageQueue, Message
from ..agents.coordinator import AgentCoordinator
from ..models.agent_dashboard import (
    AgentDashboardData,
    StrategyInfo,
    PerformanceMetrics,
    DashboardSummary
)
from .agent_data_service import AgentDataService
from .strategy_data_service import StrategyDataService
from .performance_service import PerformanceService


@dataclass
class RealtimeConfig:
    """实时数据推送服务配置"""
    update_interval: int = 1  # 数据更新间隔（秒）
    max_connections: int = 100  # 最大WebSocket连接数
    heartbeat_interval: int = 30  # 心跳间隔（秒）
    connection_timeout: int = 60  # 连接超时时间（秒）
    enable_compression: bool = True  # 是否启用数据压缩


class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
        self.logger = logging.getLogger("hk_quant_system.connection_manager")
    
    async def connect(self, websocket: WebSocket, client_info: Dict[str, Any] = None):
        """接受新连接"""
        try:
            await websocket.accept()
            self.active_connections.append(websocket)
            
            # 存储连接元数据
            self.connection_metadata[websocket] = {
                "connected_at": datetime.utcnow(),
                "last_heartbeat": datetime.utcnow(),
                "client_info": client_info or {},
                "subscriptions": set()
            }
            
            self.logger.info(f"新WebSocket连接已建立，当前连接数: {len(self.active_connections)}")
            
        except Exception as e:
            self.logger.error(f"接受WebSocket连接失败: {e}")
            raise
    
    def disconnect(self, websocket: WebSocket):
        """断开连接"""
        try:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
            
            if websocket in self.connection_metadata:
                del self.connection_metadata[websocket]
            
            self.logger.info(f"WebSocket连接已断开，当前连接数: {len(self.active_connections)}")
            
        except Exception as e:
            self.logger.error(f"断开WebSocket连接失败: {e}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """发送个人消息"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            self.logger.error(f"发送个人消息失败: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: str, exclude: Optional[WebSocket] = None):
        """广播消息"""
        try:
            disconnected = []
            
            for connection in self.active_connections:
                if connection != exclude:
                    try:
                        await connection.send_text(message)
                    except Exception as e:
                        self.logger.error(f"广播消息失败: {e}")
                        disconnected.append(connection)
            
            # 清理断开的连接
            for connection in disconnected:
                self.disconnect(connection)
                
        except Exception as e:
            self.logger.error(f"广播消息失败: {e}")
    
    async def broadcast_to_subscribers(self, message: str, subscription_type: str):
        """向特定订阅者广播消息"""
        try:
            disconnected = []
            
            for connection in self.active_connections:
                if connection in self.connection_metadata:
                    subscriptions = self.connection_metadata[connection].get("subscriptions", set())
                    if subscription_type in subscriptions:
                        try:
                            await connection.send_text(message)
                        except Exception as e:
                            self.logger.error(f"向订阅者发送消息失败: {e}")
                            disconnected.append(connection)
            
            # 清理断开的连接
            for connection in disconnected:
                self.disconnect(connection)
                
        except Exception as e:
            self.logger.error(f"向订阅者广播消息失败: {e}")
    
    def subscribe(self, websocket: WebSocket, subscription_type: str):
        """订阅特定类型的数据"""
        try:
            if websocket in self.connection_metadata:
                self.connection_metadata[websocket]["subscriptions"].add(subscription_type)
                
        except Exception as e:
            self.logger.error(f"订阅失败: {e}")
    
    def unsubscribe(self, websocket: WebSocket, subscription_type: str):
        """取消订阅"""
        try:
            if websocket in self.connection_metadata:
                self.connection_metadata[websocket]["subscriptions"].discard(subscription_type)
                
        except Exception as e:
            self.logger.error(f"取消订阅失败: {e}")
    
    def get_connection_count(self) -> int:
        """获取连接数"""
        return len(self.active_connections)
    
    def get_connection_info(self) -> List[Dict[str, Any]]:
        """获取连接信息"""
        try:
            info_list = []
            for websocket, metadata in self.connection_metadata.items():
                info_list.append({
                    "connected_at": metadata["connected_at"].isoformat(),
                    "last_heartbeat": metadata["last_heartbeat"].isoformat(),
                    "subscriptions": list(metadata["subscriptions"]),
                    "client_info": metadata["client_info"]
                })
            return info_list
        except Exception as e:
            self.logger.error(f"获取连接信息失败: {e}")
            return []


class RealtimeService:
    """实时数据推送服务"""
    
    def __init__(
        self, 
        agent_data_service: AgentDataService,
        strategy_data_service: StrategyDataService,
        performance_service: PerformanceService,
        config: RealtimeConfig = None
    ):
        self.agent_data_service = agent_data_service
        self.strategy_data_service = strategy_data_service
        self.performance_service = performance_service
        self.config = config or RealtimeConfig()
        self.logger = logging.getLogger("hk_quant_system.realtime_service")
        
        # 连接管理
        self.connection_manager = ConnectionManager()
        
        # 数据缓存
        self._last_agent_data: Dict[str, AgentDashboardData] = {}
        self._last_strategy_data: Dict[str, StrategyInfo] = {}
        self._last_performance_data: Dict[str, PerformanceMetrics] = {}
        self._last_dashboard_summary: Optional[DashboardSummary] = None
        
        # 后台任务
        self._update_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def initialize(self) -> bool:
        """初始化服务"""
        try:
            self.logger.info("正在初始化实时数据推送服务...")
            
            # 注册数据更新回调
            self.agent_data_service.add_update_callback(self._on_agent_data_update)
            self.strategy_data_service.add_update_callback(self._on_strategy_data_update)
            self.performance_service.add_update_callback(self._on_performance_data_update)
            
            # 启动后台任务
            self._running = True
            self._update_task = asyncio.create_task(self._background_update_loop())
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            
            self.logger.info("实时数据推送服务初始化完成")
            return True
            
        except Exception as e:
            self.logger.error(f"实时数据推送服务初始化失败: {e}")
            return False
    
    async def _on_agent_data_update(self, agent_id: str, agent_data: AgentDashboardData):
        """Agent数据更新回调"""
        try:
            # 检查数据是否有变化
            if agent_id in self._last_agent_data:
                last_data = self._last_agent_data[agent_id]
                if self._is_agent_data_changed(last_data, agent_data):
                    self._last_agent_data[agent_id] = agent_data
                    await self._broadcast_agent_update(agent_id, agent_data)
            else:
                self._last_agent_data[agent_id] = agent_data
                await self._broadcast_agent_update(agent_id, agent_data)
                
        except Exception as e:
            self.logger.error(f"处理Agent数据更新失败 {agent_id}: {e}")
    
    async def _on_strategy_data_update(self, agent_id: str, strategy_info: StrategyInfo):
        """策略数据更新回调"""
        try:
            # 检查数据是否有变化
            if agent_id in self._last_strategy_data:
                last_data = self._last_strategy_data[agent_id]
                if self._is_strategy_data_changed(last_data, strategy_info):
                    self._last_strategy_data[agent_id] = strategy_info
                    await self._broadcast_strategy_update(agent_id, strategy_info)
            else:
                self._last_strategy_data[agent_id] = strategy_info
                await self._broadcast_strategy_update(agent_id, strategy_info)
                
        except Exception as e:
            self.logger.error(f"处理策略数据更新失败 {agent_id}: {e}")
    
    async def _on_performance_data_update(self, agent_id: str, performance: PerformanceMetrics):
        """绩效数据更新回调"""
        try:
            # 检查数据是否有变化
            if agent_id in self._last_performance_data:
                last_data = self._last_performance_data[agent_id]
                if self._is_performance_data_changed(last_data, performance):
                    self._last_performance_data[agent_id] = performance
                    await self._broadcast_performance_update(agent_id, performance)
            else:
                self._last_performance_data[agent_id] = performance
                await self._broadcast_performance_update(agent_id, performance)
                
        except Exception as e:
            self.logger.error(f"处理绩效数据更新失败 {agent_id}: {e}")
    
    def _is_agent_data_changed(self, old_data: AgentDashboardData, new_data: AgentDashboardData) -> bool:
        """检查Agent数据是否有变化"""
        try:
            # 比较关键字段
            return (
                old_data.status != new_data.status or
                old_data.last_heartbeat != new_data.last_heartbeat or
                old_data.messages_processed != new_data.messages_processed or
                old_data.error_count != new_data.error_count
            )
        except Exception:
            return True
    
    def _is_strategy_data_changed(self, old_data: StrategyInfo, new_data: StrategyInfo) -> bool:
        """检查策略数据是否有变化"""
        try:
            return (
                old_data.status != new_data.status or
                old_data.last_updated != new_data.last_updated or
                old_data.version != new_data.version
            )
        except Exception:
            return True
    
    def _is_performance_data_changed(self, old_data: PerformanceMetrics, new_data: PerformanceMetrics) -> bool:
        """检查绩效数据是否有变化"""
        try:
            return (
                abs(old_data.sharpe_ratio - new_data.sharpe_ratio) > 0.001 or
                abs(old_data.total_return - new_data.total_return) > 0.001 or
                abs(old_data.max_drawdown - new_data.max_drawdown) > 0.001
            )
        except Exception:
            return True
    
    async def _broadcast_agent_update(self, agent_id: str, agent_data: AgentDashboardData):
        """广播Agent更新"""
        try:
            message = {
                "type": "agent_update",
                "agent_id": agent_id,
                "data": agent_data.dict()
            }
            
            await self.connection_manager.broadcast_to_subscribers(
                json.dumps(message, default=str),
                "agent_updates"
            )
            
        except Exception as e:
            self.logger.error(f"广播Agent更新失败 {agent_id}: {e}")
    
    async def _broadcast_strategy_update(self, agent_id: str, strategy_info: StrategyInfo):
        """广播策略更新"""
        try:
            message = {
                "type": "strategy_update",
                "agent_id": agent_id,
                "data": strategy_info.dict()
            }
            
            await self.connection_manager.broadcast_to_subscribers(
                json.dumps(message, default=str),
                "strategy_updates"
            )
            
        except Exception as e:
            self.logger.error(f"广播策略更新失败 {agent_id}: {e}")
    
    async def _broadcast_performance_update(self, agent_id: str, performance: PerformanceMetrics):
        """广播绩效更新"""
        try:
            message = {
                "type": "performance_update",
                "agent_id": agent_id,
                "data": performance.dict()
            }
            
            await self.connection_manager.broadcast_to_subscribers(
                json.dumps(message, default=str),
                "performance_updates"
            )
            
        except Exception as e:
            self.logger.error(f"广播绩效更新失败 {agent_id}: {e}")
    
    async def _background_update_loop(self):
        """后台更新循环"""
        while self._running:
            try:
                # 定期广播仪表板总览
                await self._broadcast_dashboard_summary()
                
                # 等待下次更新
                await asyncio.sleep(self.config.update_interval)
                
            except Exception as e:
                self.logger.error(f"后台更新循环错误: {e}")
                await asyncio.sleep(self.config.update_interval)
    
    async def _broadcast_dashboard_summary(self):
        """广播仪表板总览"""
        try:
            # 获取仪表板总览
            summary = await self.agent_data_service.get_dashboard_summary()
            
            # 检查是否有变化
            if summary != self._last_dashboard_summary:
                self._last_dashboard_summary = summary
                
                message = {
                    "type": "dashboard_summary",
                    "data": summary.dict()
                }
                
                await self.connection_manager.broadcast_to_subscribers(
                    json.dumps(message, default=str),
                    "dashboard_summary"
                )
                
        except Exception as e:
            self.logger.error(f"广播仪表板总览失败: {e}")
    
    async def _heartbeat_loop(self):
        """心跳循环"""
        while self._running:
            try:
                # 发送心跳消息
                heartbeat_message = {
                    "type": "heartbeat",
                    "timestamp": datetime.utcnow().isoformat(),
                    "connection_count": self.connection_manager.get_connection_count()
                }
                
                await self.connection_manager.broadcast(
                    json.dumps(heartbeat_message)
                )
                
                # 等待下次心跳
                await asyncio.sleep(self.config.heartbeat_interval)
                
            except Exception as e:
                self.logger.error(f"心跳循环错误: {e}")
                await asyncio.sleep(self.config.heartbeat_interval)
    
    async def handle_websocket_connection(self, websocket: WebSocket, client_info: Dict[str, Any] = None):
        """处理WebSocket连接"""
        try:
            # 接受连接
            await self.connection_manager.connect(websocket, client_info)
            
            # 发送初始数据
            await self._send_initial_data(websocket)
            
            # 处理消息
            while True:
                try:
                    # 接收消息
                    message = await websocket.receive_text()
                    await self._handle_client_message(websocket, message)
                    
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    self.logger.error(f"处理WebSocket消息失败: {e}")
                    break
                    
        except Exception as e:
            self.logger.error(f"处理WebSocket连接失败: {e}")
        finally:
            # 断开连接
            self.connection_manager.disconnect(websocket)
    
    async def _send_initial_data(self, websocket: WebSocket):
        """发送初始数据"""
        try:
            # 发送所有Agent数据
            agents_data = await self.agent_data_service.get_all_agents_data()
            initial_message = {
                "type": "initial_data",
                "agents": {agent_id: agent_data.dict() for agent_id, agent_data in agents_data.items()},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.connection_manager.send_personal_message(
                json.dumps(initial_message, default=str),
                websocket
            )
            
            # 发送仪表板总览
            summary = await self.agent_data_service.get_dashboard_summary()
            summary_message = {
                "type": "dashboard_summary",
                "data": summary.dict()
            }
            
            await self.connection_manager.send_personal_message(
                json.dumps(summary_message, default=str),
                websocket
            )
            
        except Exception as e:
            self.logger.error(f"发送初始数据失败: {e}")
    
    async def _handle_client_message(self, websocket: WebSocket, message: str):
        """处理客户端消息"""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "subscribe":
                # 处理订阅请求
                subscription_type = data.get("subscription_type")
                if subscription_type:
                    self.connection_manager.subscribe(websocket, subscription_type)
                    
            elif message_type == "unsubscribe":
                # 处理取消订阅请求
                subscription_type = data.get("subscription_type")
                if subscription_type:
                    self.connection_manager.unsubscribe(websocket, subscription_type)
                    
            elif message_type == "ping":
                # 处理心跳
                pong_message = {
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                }
                await self.connection_manager.send_personal_message(
                    json.dumps(pong_message),
                    websocket
                )
                
        except json.JSONDecodeError:
            self.logger.error(f"无效的JSON消息: {message}")
        except Exception as e:
            self.logger.error(f"处理客户端消息失败: {e}")
    
    def get_connection_count(self) -> int:
        """获取连接数"""
        return self.connection_manager.get_connection_count()
    
    def get_connection_info(self) -> List[Dict[str, Any]]:
        """获取连接信息"""
        return self.connection_manager.get_connection_info()
    
    async def broadcast_custom_message(self, message_type: str, data: Any, subscription_type: Optional[str] = None):
        """广播自定义消息"""
        try:
            message = {
                "type": message_type,
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if subscription_type:
                await self.connection_manager.broadcast_to_subscribers(
                    json.dumps(message, default=str),
                    subscription_type
                )
            else:
                await self.connection_manager.broadcast(
                    json.dumps(message, default=str)
                )
                
        except Exception as e:
            self.logger.error(f"广播自定义消息失败: {e}")
    
    async def cleanup(self):
        """清理资源"""
        try:
            self.logger.info("正在清理实时数据推送服务...")
            
            self._running = False
            
            # 取消后台任务
            if self._update_task:
                self._update_task.cancel()
                try:
                    await self._update_task
                except asyncio.CancelledError:
                    pass
            
            if self._heartbeat_task:
                self._heartbeat_task.cancel()
                try:
                    await self._heartbeat_task
                except asyncio.CancelledError:
                    pass
            
            # 关闭所有连接
            for connection in self.connection_manager.active_connections.copy():
                self.connection_manager.disconnect(connection)
            
            # 清理数据缓存
            self._last_agent_data.clear()
            self._last_strategy_data.clear()
            self._last_performance_data.clear()
            self._last_dashboard_summary = None
            
            self.logger.info("实时数据推送服务清理完成")
            
        except Exception as e:
            self.logger.error(f"清理实时数据推送服务失败: {e}")


__all__ = [
    "RealtimeConfig",
    "ConnectionManager",
    "RealtimeService",
]
