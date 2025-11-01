#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent注册表 (AgentRegistry)
统一管理所有Agent的注册、发现和生命周期
"""

import os
import sys
import logging
import asyncio
import importlib
import inspect
from typing import Dict, List, Optional, Type, Any, Set
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import uuid
from datetime import datetime

# 添加项目根目录
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from infrastructure.logging.context_logger import get_context_logger

logger = get_context_logger("agent.registry")

class AgentStatus(Enum):
    """Agent状态枚举"""
    UNREGISTERED = "unregistered"
    REGISTERED = "registered"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    DEGRADED = "degraded"

class AgentType(Enum):
    """Agent类型枚举"""
    COORDINATOR = "coordinator"
    DATA_SCIENTIST = "data_scientist"
    QUANTITATIVE_ANALYST = "quantitative_analyst"
    QUANTITATIVE_ENGINEER = "quantitative_engineer"
    PORTFOLIO_MANAGER = "portfolio_manager"
    RESEARCH_ANALYST = "research_analyst"
    RISK_ANALYST = "risk_analyst"
    CUSTOM = "custom"

@dataclass
class AgentMetadata:
    """Agent元数据"""
    id: str
    name: str
    type: AgentType
    description: str
    version: str
    author: str
    dependencies: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    config_schema: Optional[Dict[str, Any]] = None
    status: AgentStatus = AgentStatus.UNREGISTERED
    created_at: datetime = field(default_factory=datetime.now)
    last_seen: Optional[datetime] = None
    health_score: float = 0.0
    metrics: Dict[str, Any] = field(default_factory=dict)
    tags: Set[str] = field(default_factory=set)

    def update_last_seen(self):
        """更新最后活动时间"""
        self.last_seen = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type.value,
            'description': self.description,
            'version': self.version,
            'author': self.author,
            'dependencies': self.dependencies,
            'capabilities': self.capabilities,
            'config_schema': self.config_schema,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'health_score': self.health_score,
            'metrics': self.metrics,
            'tags': list(self.tags)
        }

class AgentRegistry:
    """Agent注册表 - 统一管理所有Agent"""

    def __init__(self):
        self._agents: Dict[str, AgentMetadata] = {}
        self._agent_classes: Dict[str, Type] = {}
        self._agent_instances: Dict[str, Any] = {}
        self._capability_index: Dict[str, Set[str]] = {}  # capability -> set of agent IDs
        self._type_index: Dict[AgentType, Set[str]] = {}  # type -> set of agent IDs
        self._lock = asyncio.Lock()
        self._auto_discover_enabled = True
        self._discovery_paths = [
            project_root / "src" / "agents",
            project_root / "src" / "agents" / "real_agents"
        ]
        self._loaded_modules: Set[str] = set()

    async def initialize(self):
        """初始化注册表"""
        logger.info("初始化Agent注册表...")

        # 启用自动发现
        if self._auto_discover_enabled:
            await self.auto_discover_agents()

        logger.info(f"Agent注册表初始化完成，已注册 {len(self._agents)} 个Agent")

    async def auto_discover_agents(self):
        """自动发现Agent类"""
        logger.info("开始自动发现Agent...")

        for path in self._discovery_paths:
            if not path.exists():
                logger.warning(f"Agent发现路径不存在: {path}")
                continue

            # 遍历所有Python文件
            for py_file in path.rglob("*.py"):
                if py_file.name.startswith("_"):
                    continue

                module_path = str(py_file.relative_to(project_root)).replace("/", ".").replace(".py", "")

                try:
                    await self._load_agent_module(module_path)
                except Exception as e:
                    logger.error(f"加载Agent模块失败 {module_path}: {e}", exc_info=True)
                    continue

        logger.info(f"自动发现完成，发现 {len(self._agent_classes)} 个Agent类")

    async def _load_agent_module(self, module_path: str):
        """加载Agent模块"""
        if module_path in self._loaded_modules:
            return

        try:
            module = importlib.import_module(module_path)

            # 扫描模块中的Agent类
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if hasattr(obj, '_is_agent') and obj._is_agent:
                    agent_class = obj

                    # 生成Agent ID
                    agent_id = getattr(agent_class, 'AGENT_ID', f"{name.lower()}_{uuid.uuid4().hex[:8]}")

                    # 创建元数据
                    metadata = AgentMetadata(
                        id=agent_id,
                        name=getattr(agent_class, 'AGENT_NAME', name),
                        type=AgentType(getattr(agent_class, 'AGENT_TYPE', 'custom')),
                        description=getattr(agent_class, '__doc__', ''),
                        version=getattr(agent_class, 'VERSION', '1.0.0'),
                        author=getattr(agent_class, 'AUTHOR', 'Unknown'),
                        dependencies=getattr(agent_class, 'DEPENDENCIES', []),
                        capabilities=getattr(agent_class, 'CAPABILITIES', [])
                    )

                    # 注册Agent
                    await self.register_agent(agent_id, agent_class, metadata)

            self._loaded_modules.add(module_path)

        except Exception as e:
            logger.error(f"加载Agent模块失败 {module_path}: {e}")
            raise

    async def register_agent(self, agent_id: str, agent_class: Type, metadata: Optional[AgentMetadata] = None):
        """注册Agent"""
        async with self._lock:
            if agent_id in self._agents:
                logger.warning(f"Agent {agent_id} 已存在，将更新元数据")

            if metadata is None:
                metadata = AgentMetadata(
                    id=agent_id,
                    name=agent_class.__name__,
                    type=AgentType.CUSTOM,
                    description=agent_class.__doc__ or '',
                    version='1.0.0'
                )

            # 更新状态
            metadata.status = AgentStatus.REGISTERED
            metadata.update_last_seen()

            # 存储
            self._agents[agent_id] = metadata
            self._agent_classes[agent_id] = agent_class

            # 更新索引
            self._capability_index.setdefault(metadata.type.value, set()).add(agent_id)
            for capability in metadata.capabilities:
                self._capability_index.setdefault(capability, set()).add(agent_id)

            self._type_index.setdefault(metadata.type, set()).add(agent_id)

            logger.info(f"注册Agent成功: {metadata.name} ({agent_id})")

    async def unregister_agent(self, agent_id: str):
        """注销Agent"""
        async with self._lock:
            if agent_id not in self._agents:
                logger.warning(f"尝试注销不存在的Agent: {agent_id}")
                return

            metadata = self._agents[agent_id]

            # 停止实例（如果存在）
            if agent_id in self._agent_instances:
                await self.stop_agent(agent_id)

            # 从索引中移除
            self._capability_index.get(metadata.type.value, set()).discard(agent_id)
            for capability in metadata.capabilities:
                self._capability_index.get(capability, set()).discard(agent_id)
            self._type_index.get(metadata.type, set()).discard(agent_id)

            # 删除
            del self._agents[agent_id]
            self._agent_classes.pop(agent_id, None)
            self._agent_instances.pop(agent_id, None)

            logger.info(f"注销Agent成功: {agent_id}")

    async def get_agent(self, agent_id: str) -> Optional[AgentMetadata]:
        """获取Agent元数据"""
        return self._agents.get(agent_id)

    async def get_agent_class(self, agent_id: str) -> Optional[Type]:
        """获取Agent类"""
        return self._agent_classes.get(agent_id)

    async def get_agent_instance(self, agent_id: str) -> Optional[Any]:
        """获取Agent实例"""
        return self._agent_instances.get(agent_id)

    async def list_agents(self, agent_type: Optional[AgentType] = None,
                         status: Optional[AgentStatus] = None) -> List[AgentMetadata]:
        """列出Agent"""
        agents = list(self._agents.values())

        if agent_type:
            agents = [a for a in agents if a.type == agent_type]

        if status:
            agents = [a for a in agents if a.status == status]

        return agents

    async def find_agents_by_capability(self, capability: str) -> List[AgentMetadata]:
        """根据能力查找Agent"""
        agent_ids = self._capability_index.get(capability, set())
        return [self._agents[aid] for aid in agent_ids if aid in self._agents]

    async def find_agents_by_type(self, agent_type: AgentType) -> List[AgentMetadata]:
        """根据类型查找Agent"""
        agent_ids = self._type_index.get(agent_type, set())
        return [self._agents[aid] for aid in agent_ids if aid in self._agents]

    async def start_agent(self, agent_id: str, config: Optional[Dict[str, Any]] = None) -> bool:
        """启动Agent实例"""
        try:
            agent_class = await self.get_agent_class(agent_id)
            if not agent_class:
                logger.error(f"未找到Agent类: {agent_id}")
                return False

            # 检查是否已运行
            if agent_id in self._agent_instances:
                logger.warning(f"Agent {agent_id} 已运行")
                return True

            # 创建实例
            instance = agent_class(agent_id)

            # 应用配置
            if config:
                instance.config = config

            # 更新状态
            metadata = self._agents[agent_id]
            metadata.status = AgentStatus.INITIALIZING
            metadata.update_last_seen()

            # 启动
            success = await instance.initialize()

            if success:
                self._agent_instances[agent_id] = instance
                metadata.status = AgentStatus.RUNNING
                logger.info(f"启动Agent成功: {agent_id}")
            else:
                metadata.status = AgentStatus.ERROR
                logger.error(f"启动Agent失败: {agent_id}")

            return success

        except Exception as e:
            logger.error(f"启动Agent异常 {agent_id}: {e}", exc_info=True)
            metadata = self._agents.get(agent_id)
            if metadata:
                metadata.status = AgentStatus.ERROR
            return False

    async def stop_agent(self, agent_id: str) -> bool:
        """停止Agent实例"""
        try:
            instance = self._agent_instances.get(agent_id)
            if not instance:
                logger.warning(f"Agent {agent_id} 未运行")
                return True

            # 更新状态
            metadata = self._agents[agent_id]
            metadata.status = AgentStatus.STOPPING
            metadata.update_last_seen()

            # 停止
            await instance.cleanup()

            # 移除实例
            self._agent_instances.pop(agent_id, None)
            metadata.status = AgentStatus.STOPPED

            logger.info(f"停止Agent成功: {agent_id}")
            return True

        except Exception as e:
            logger.error(f"停止Agent异常 {agent_id}: {e}", exc_info=True)
            metadata = self._agents.get(agent_id)
            if metadata:
                metadata.status = AgentStatus.ERROR
            return False

    async def restart_agent(self, agent_id: str, config: Optional[Dict[str, Any]] = None) -> bool:
        """重启Agent"""
        logger.info(f"重启Agent: {agent_id}")

        # 先停止
        await self.stop_agent(agent_id)

        # 再启动
        return await self.start_agent(agent_id, config)

    async def pause_agent(self, agent_id: str) -> bool:
        """暂停Agent"""
        try:
            instance = self._agent_instances.get(agent_id)
            if not instance:
                logger.warning(f"Agent {agent_id} 未运行")
                return False

            metadata = self._agents[agent_id]
            metadata.status = AgentStatus.PAUSED
            metadata.update_last_seen()

            if hasattr(instance, 'pause'):
                await instance.pause()

            logger.info(f"暂停Agent成功: {agent_id}")
            return True

        except Exception as e:
            logger.error(f"暂停Agent异常 {agent_id}: {e}", exc_info=True)
            return False

    async def resume_agent(self, agent_id: str) -> bool:
        """恢复Agent"""
        try:
            instance = self._agent_instances.get(agent_id)
            if not instance:
                logger.warning(f"Agent {agent_id} 未运行")
                return False

            metadata = self._agents[agent_id]
            metadata.status = AgentStatus.RUNNING
            metadata.update_last_seen()

            if hasattr(instance, 'resume'):
                await instance.resume()

            logger.info(f"恢复Agent成功: {agent_id}")
            return True

        except Exception as e:
            logger.error(f"恢复Agent异常 {agent_id}: {e}", exc_info=True)
            return False

    async def update_agent_status(self, agent_id: str, status: AgentStatus, health_score: float = 0.0):
        """更新Agent状态"""
        if agent_id in self._agents:
            self._agents[agent_id].status = status
            self._agents[agent_id].health_score = health_score
            self._agents[agent_id].update_last_seen()

    async def get_registry_stats(self) -> Dict[str, Any]:
        """获取注册表统计信息"""
        stats = {
            'total_agents': len(self._agents),
            'running_agents': len([a for a in self._agents.values() if a.status == AgentStatus.RUNNING]),
            'stopped_agents': len([a for a in self._agents.values() if a.status == AgentStatus.STOPPED]),
            'error_agents': len([a for a in self._agents.values() if a.status == AgentStatus.ERROR]),
            'agents_by_type': {},
            'agents_by_capability': {},
            'auto_discovery_enabled': self._auto_discover_enabled,
            'discovery_paths': [str(p) for p in self._discovery_paths]
        }

        # 按类型统计
        for agent_type in AgentType:
            count = len(await self.find_agents_by_type(agent_type))
            if count > 0:
                stats['agents_by_type'][agent_type.value] = count

        # 按能力统计
        for capability, agent_ids in self._capability_index.items():
            if capability != 'custom':  # 跳过自定义类型
                count = len(agent_ids)
                if count > 0:
                    stats['agents_by_capability'][capability] = count

        return stats

    async def export_registry(self) -> Dict[str, Any]:
        """导出注册表"""
        return {
            'agents': {aid: metadata.to_dict() for aid, metadata in self._agents.items()},
            'stats': await self.get_registry_stats(),
            'exported_at': datetime.now().isoformat()
        }

    async def import_registry(self, data: Dict[str, Any]):
        """导入注册表"""
        logger.info("导入Agent注册表...")

        for agent_id, agent_data in data.get('agents', {}).items():
            try:
                # 重建元数据
                metadata = AgentMetadata(
                    id=agent_data['id'],
                    name=agent_data['name'],
                    type=AgentType(agent_data['type']),
                    description=agent_data['description'],
                    version=agent_data['version'],
                    author=agent_data['author'],
                    dependencies=agent_data.get('dependencies', []),
                    capabilities=agent_data.get('capabilities', []),
                    status=AgentStatus(agent_data['status'])
                )

                # 注册（不包含类，只包含元数据）
                self._agents[agent_id] = metadata

            except Exception as e:
                logger.error(f"导入Agent失败 {agent_id}: {e}")
                continue

        logger.info(f"导入完成，共导入 {len(data.get('agents', {}))} 个Agent")

# 全局注册表实例
_global_registry: Optional[AgentRegistry] = None

def get_agent_registry() -> AgentRegistry:
    """获取全局Agent注册表"""
    global _global_registry
    if _global_registry is None:
        _global_registry = AgentRegistry()
    return _global_registry

async def initialize_agent_registry():
    """初始化全局Agent注册表"""
    registry = get_agent_registry()
    await registry.initialize()
    return registry

# 装饰器：标记Agent类
def agent_component(name: str, agent_type: AgentType = AgentType.CUSTOM,
                   version: str = "1.0.0", author: str = "Unknown"):
    """Agent组件装饰器"""
    def decorator(cls):
        cls._is_agent = True
        cls.AGENT_NAME = name
        cls.AGENT_TYPE = agent_type.value
        cls.VERSION = version
        cls.AUTHOR = author
        return cls
    return decorator

# 使用示例
if __name__ == "__main__":
    async def test_registry():
        """测试注册表功能"""
        print("🧪 测试Agent注册表...")

        # 初始化注册表
        registry = await initialize_agent_registry()

        # 显示统计信息
        stats = await registry.get_registry_stats()
        print(f"\n📊 注册表统计:")
        for key, value in stats.items():
            print(f"  {key}: {value}")

        # 列出所有Agent
        agents = await registry.list_agents()
        print(f"\n🤖 已注册Agent列表:")
        for agent in agents:
            print(f"  - {agent.name} ({agent.type.value}): {agent.status.value}")

        # 按能力查找
        if agents:
            first_agent = agents[0]
            if first_agent.capabilities:
                capability = first_agent.capabilities[0]
                found = await registry.find_agents_by_capability(capability)
                print(f"\n🔍 具有能力 '{capability}' 的Agent:")
                for agent in found:
                    print(f"  - {agent.name}")

        print("\n✅ Agent注册表测试完成")

    asyncio.run(test_registry())
