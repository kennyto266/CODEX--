"""
港股量化交易 AI Agent 系统消息队列模块

基于Redis实现的消息队列系统，用于Agent间的异步通信。
支持发布/订阅模式、消息路由、可靠传递等功能。
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from datetime import datetime
import redis.asyncio as redis
from pydantic import BaseModel

from . import SystemConfig, SystemConstants


class Message(BaseModel):
    """消息数据模型"""
    
    id: str
    type: str
    sender: str
    receiver: Optional[str] = None
    content: Dict[str, Any]
    timestamp: datetime
    ttl: Optional[int] = None  # 消息生存时间（秒）
    priority: int = 0  # 消息优先级，数字越大优先级越高
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


@dataclass
class MessageHandler:
    """消息处理器"""
    handler: Callable
    message_type: str
    agent_id: str


class MessageQueue:
    """Redis消息队列管理器"""
    
    def __init__(self, config: SystemConfig = None):
        self.config = config or SystemConfig()
        self.redis_client: Optional[redis.Redis] = None
        self.handlers: Dict[str, List[MessageHandler]] = {}
        self.subscribers: Dict[str, asyncio.Task] = {}
        self.logger = logging.getLogger("hk_quant_system.message_queue")
        
        # 消息队列配置
        self.queue_prefix = "hk_quant:queue:"
        self.channel_prefix = "hk_quant:channel:"
        self.message_prefix = "hk_quant:message:"
        
    async def initialize(self):
        """初始化Redis连接"""
        try:
            self.redis_client = redis.Redis(
                host=self.config.redis_host,
                port=self.config.redis_port,
                password=self.config.redis_password or None,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            
            # 测试连接
            await self.redis_client.ping()
            self.logger.info("Redis连接成功建立")
            
        except Exception as e:
            self.logger.error(f"Redis连接失败: {e}")
            raise
    
    async def close(self):
        """关闭Redis连接"""
        if self.redis_client:
            await self.redis_client.close()
            self.logger.info("Redis连接已关闭")
    
    async def publish_message(
        self, 
        message_type: str, 
        content: Dict[str, Any], 
        sender: str,
        receiver: Optional[str] = None,
        priority: int = 0,
        ttl: Optional[int] = None
    ) -> str:
        """发布消息"""
        if not self.redis_client:
            raise RuntimeError("消息队列未初始化")
        
        # 创建消息
        message_id = f"{sender}_{datetime.now().timestamp()}"
        message = Message(
            id=message_id,
            type=message_type,
            sender=sender,
            receiver=receiver,
            content=content,
            timestamp=datetime.now(),
            ttl=ttl,
            priority=priority
        )
        
        # 序列化消息
        message_json = message.json()
        
        try:
            if receiver:
                # 点对点消息
                queue_name = f"{self.queue_prefix}{receiver}"
                await self.redis_client.lpush(queue_name, message_json)
                self.logger.debug(f"发送点对点消息到 {receiver}: {message_type}")
            else:
                # 广播消息
                channel_name = f"{self.channel_prefix}{message_type}"
                await self.redis_client.publish(channel_name, message_json)
                self.logger.debug(f"广播消息: {message_type}")
            
            # 设置消息TTL
            if ttl:
                message_key = f"{self.message_prefix}{message_id}"
                await self.redis_client.setex(message_key, ttl, message_json)
            
            return message_id
            
        except Exception as e:
            self.logger.error(f"发布消息失败: {e}")
            raise
    
    async def subscribe_to_channel(
        self, 
        channel_name: str, 
        agent_id: str,
        handler: Callable[[Message], None]
    ):
        """订阅频道"""
        if not self.redis_client:
            raise RuntimeError("消息队列未初始化")
        
        full_channel_name = f"{self.channel_prefix}{channel_name}"
        
        # 注册消息处理器
        if channel_name not in self.handlers:
            self.handlers[channel_name] = []
        
        self.handlers[channel_name].append(
            MessageHandler(handler=handler, message_type=channel_name, agent_id=agent_id)
        )
        
        # 创建订阅任务
        async def subscribe_task():
            pubsub = self.redis_client.pubsub()
            await pubsub.subscribe(full_channel_name)
            
            self.logger.info(f"Agent {agent_id} 开始订阅频道: {channel_name}")
            
            try:
                async for message in pubsub.listen():
                    if message['type'] == 'message':
                        try:
                            message_data = json.loads(message['data'])
                            msg = Message(**message_data)
                            
                            # 调用处理器
                            for handler_info in self.handlers.get(channel_name, []):
                                if handler_info.agent_id == agent_id:
                                    await handler_info.handler(msg)
                                    
                        except Exception as e:
                            self.logger.error(f"处理消息失败: {e}")
                            
            except asyncio.CancelledError:
                self.logger.info(f"Agent {agent_id} 取消订阅频道: {channel_name}")
            finally:
                await pubsub.unsubscribe(full_channel_name)
                await pubsub.close()
        
        # 启动订阅任务
        task = asyncio.create_task(subscribe_task())
        self.subscribers[f"{agent_id}:{channel_name}"] = task
        
        return task
    
    async def unsubscribe_from_channel(self, channel_name: str, agent_id: str):
        """取消订阅频道"""
        task_key = f"{agent_id}:{channel_name}"
        if task_key in self.subscribers:
            task = self.subscribers[task_key]
            task.cancel()
            del self.subscribers[task_key]
            self.logger.info(f"Agent {agent_id} 取消订阅频道: {channel_name}")
    
    async def receive_message(
        self, 
        agent_id: str, 
        timeout: Optional[float] = None
    ) -> Optional[Message]:
        """接收点对点消息"""
        if not self.redis_client:
            raise RuntimeError("消息队列未初始化")
        
        queue_name = f"{self.queue_prefix}{agent_id}"
        
        try:
            # 阻塞式接收消息
            result = await self.redis_client.brpop(queue_name, timeout=timeout or 0)
            if result:
                _, message_json = result
                message_data = json.loads(message_json)
                return Message(**message_data)
            return None
            
        except Exception as e:
            self.logger.error(f"接收消息失败: {e}")
            raise
    
    async def send_signal(
        self,
        signal_type: str,
        symbol: str,
        confidence: float,
        reasoning: str,
        target_price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        sender: str = "system"
    ) -> str:
        """发送交易信号"""
        signal_content = {
            "signal_type": signal_type,
            "symbol": symbol,
            "confidence": confidence,
            "reasoning": reasoning,
            "target_price": target_price,
            "stop_loss": stop_loss,
            "market_data": {
                "timestamp": datetime.now().isoformat()
            }
        }
        
        return await self.publish_message(
            message_type=SystemConstants.MESSAGE_TYPES["SIGNAL"],
            content=signal_content,
            sender=sender,
            priority=5  # 交易信号高优先级
        )
    
    async def send_market_data(
        self,
        symbol: str,
        data: Dict[str, Any],
        sender: str = "data_provider"
    ) -> str:
        """发送市场数据"""
        market_data = {
            "symbol": symbol,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        return await self.publish_message(
            message_type=SystemConstants.MESSAGE_TYPES["DATA"],
            content=market_data,
            sender=sender,
            priority=3
        )
    
    async def send_control_message(
        self,
        command: str,
        target_agent: str,
        parameters: Dict[str, Any] = None,
        sender: str = "coordinator"
    ) -> str:
        """发送控制消息"""
        control_content = {
            "command": command,
            "parameters": parameters or {},
            "timestamp": datetime.now().isoformat()
        }
        
        return await self.publish_message(
            message_type=SystemConstants.MESSAGE_TYPES["CONTROL"],
            content=control_content,
            sender=sender,
            receiver=target_agent,
            priority=7  # 控制消息最高优先级
        )
    
    async def send_heartbeat(self, agent_id: str, status: str = "alive") -> str:
        """发送心跳消息"""
        heartbeat_content = {
            "agent_id": agent_id,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "memory_usage": 0,  # 可以添加更多系统信息
            "cpu_usage": 0
        }
        
        return await self.publish_message(
            message_type=SystemConstants.MESSAGE_TYPES["HEARTBEAT"],
            content=heartbeat_content,
            sender=agent_id,
            receiver="coordinator",
            ttl=60  # 心跳消息1分钟后过期
        )
    
    async def get_queue_length(self, agent_id: str) -> int:
        """获取队列长度"""
        if not self.redis_client:
            return 0
        
        queue_name = f"{self.queue_prefix}{agent_id}"
        return await self.redis_client.llen(queue_name)
    
    async def clear_queue(self, agent_id: str):
        """清空队列"""
        if not self.redis_client:
            return
        
        queue_name = f"{self.queue_prefix}{agent_id}"
        await self.redis_client.delete(queue_name)
        self.logger.info(f"清空Agent {agent_id} 的消息队列")
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        if not self.redis_client:
            return {}
        
        stats = {
            "redis_info": await self.redis_client.info(),
            "active_subscribers": len(self.subscribers),
            "registered_handlers": sum(len(handlers) for handlers in self.handlers.values()),
            "queue_prefix": self.queue_prefix,
            "channel_prefix": self.channel_prefix
        }
        
        return stats


# 全局消息队列实例
message_queue = MessageQueue()

# 导出主要组件
__all__ = [
    "Message",
    "MessageHandler", 
    "MessageQueue",
    "message_queue"
]
