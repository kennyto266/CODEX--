"""
Unified Agent System - Single Agent Framework for All 23 Implementations

Consolidates all agent variations (core, real, hk_prompt) into a single,
composable system using roles and plugins.

Features:
- Single UnifiedAgent class supporting all role types
- Composable role system (23 roles supported)
- Unified message handling and routing
- Common infrastructure (heartbeat, logging, error handling)
- Dynamic role loading and switching

Architecture:
- UnifiedAgent: Container for any role
- Role: Encapsulates agent behavior
- Tool: Provides domain-specific functionality
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable, Tuple
from enum import Enum

logger = logging.getLogger("hk_quant_system.unified_agent")


class AgentStatus(str, Enum):
    """Agent operational status"""
    IDLE = "idle"
    INITIALIZING = "initializing"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    MAINTENANCE = "maintenance"


@dataclass
class Message:
    """Unified message format for inter-agent communication"""
    message_type: str
    sender_id: str
    recipient_id: Optional[str] = None
    content: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    priority: int = 0  # 0=normal, 1=high, -1=low
    correlation_id: Optional[str] = None  # For request/response tracking

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            'type': self.message_type,
            'sender': self.sender_id,
            'recipient': self.recipient_id,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'priority': self.priority,
            'correlation_id': self.correlation_id,
        }


@dataclass
class AgentConfig:
    """Configuration for UnifiedAgent"""
    agent_id: str
    agent_name: str
    role_type: str  # 'coordinator', 'data_scientist', 'real_data_scientist', etc.
    config: Dict[str, Any] = field(default_factory=dict)
    heartbeat_interval: int = 30
    max_errors: int = 10
    restart_delay: int = 5
    enable_metrics: bool = True
    log_level: str = "INFO"


class BaseRole(ABC):
    """
    Abstract base class for all agent roles.

    Each role encapsulates specific agent behavior and capabilities.
    Roles are composable and can be swapped at runtime.
    """

    def __init__(self, role_name: str):
        self.role_name = role_name
        self.logger = logging.getLogger(f"hk_quant_system.role.{role_name}")
        self.state: Dict[str, Any] = {}
        self.tools: Dict[str, Callable] = {}

    @abstractmethod
    async def initialize(self, agent: 'UnifiedAgent') -> bool:
        """
        Initialize the role.

        Args:
            agent: The parent UnifiedAgent instance

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    async def process_message(self, message: Message, agent: 'UnifiedAgent') -> bool:
        """
        Process a message for this role.

        Args:
            message: The message to process
            agent: The parent UnifiedAgent instance

        Returns:
            True if successfully processed, False otherwise
        """
        pass

    @abstractmethod
    async def cleanup(self):
        """Cleanup role resources"""
        pass

    def get_tools(self) -> Dict[str, Callable]:
        """Return tools provided by this role"""
        return self.tools.copy()

    def get_state(self) -> Dict[str, Any]:
        """Return role state"""
        return self.state.copy()


class UnifiedAgent:
    """
    Unified Agent Framework - Single class for all 23 agent implementations.

    Supports all agent types through a composable role system:
    - 8 Core agents (Coordinator, DataScientist, etc.)
    - 8 Real agents (with ML integration)
    - 7 HK Prompt agents

    Example:
        >>> config = AgentConfig(
        ...     agent_id="agent_001",
        ...     agent_name="Data Science Agent",
        ...     role_type="data_scientist"
        ... )
        >>> agent = UnifiedAgent(config)
        >>> await agent.start()
        >>> await agent.process_message(message)
    """

    def __init__(self, config: AgentConfig, message_queue: Optional['MessageQueue'] = None):
        """
        Initialize UnifiedAgent.

        Args:
            config: Agent configuration
            message_queue: Optional external message queue
        """
        self.config = config
        self.agent_id = config.agent_id
        self.agent_name = config.agent_name
        self.logger = logging.getLogger(f"hk_quant_system.agent.{config.agent_id}")

        # Core state
        self.status = AgentStatus.IDLE
        self.role: Optional[BaseRole] = None
        self.message_queue = message_queue or SimpleMessageQueue()

        # Execution state
        self.running = False
        self.start_time: Optional[datetime] = None
        self.tasks: List[asyncio.Task] = []

        # Error tracking
        self.error_count = 0
        self.last_error: Optional[str] = None
        self.error_history: List[Tuple[datetime, str]] = []

        # Message tracking
        self.messages_processed = 0
        self.messages_sent = 0

        # Performance metrics
        self.metrics = {
            'messages_received': 0,
            'messages_processed': 0,
            'messages_failed': 0,
            'errors': 0,
            'uptime_seconds': 0,
            'avg_processing_time_ms': 0.0,
        }

    async def start(self) -> bool:
        """
        Start the agent.

        Returns:
            True if successfully started, False otherwise
        """
        try:
            self.logger.info(f"Starting agent: {self.agent_id} ({self.agent_name})")
            self.status = AgentStatus.INITIALIZING

            # Load and initialize role
            if not await self._initialize_role():
                self.logger.error(f"Failed to initialize role for agent {self.agent_id}")
                self.status = AgentStatus.ERROR
                return False

            # Mark as running
            self.status = AgentStatus.RUNNING
            self.running = True
            self.start_time = datetime.now()

            # Start background tasks
            await self._start_background_tasks()

            self.logger.info(f"Agent started successfully: {self.agent_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to start agent {self.agent_id}: {e}")
            self.status = AgentStatus.ERROR
            return False

    async def stop(self):
        """Stop the agent and cleanup resources"""
        try:
            self.logger.info(f"Stopping agent: {self.agent_id}")
            self.running = False
            self.status = AgentStatus.STOPPING

            # Cancel all tasks
            for task in self.tasks:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            # Cleanup role
            if self.role:
                await self.role.cleanup()

            self.status = AgentStatus.STOPPED
            self.logger.info(f"Agent stopped: {self.agent_id}")

        except Exception as e:
            self.logger.error(f"Error stopping agent {self.agent_id}: {e}")
            self.status = AgentStatus.ERROR

    async def process_message(self, message: Message) -> bool:
        """
        Process an incoming message.

        Args:
            message: The message to process

        Returns:
            True if processed successfully, False otherwise
        """
        self.metrics['messages_received'] += 1

        try:
            if not self.running:
                self.logger.warning(f"Agent {self.agent_id} not running, ignoring message")
                self.metrics['messages_failed'] += 1
                return False

            # Delegate to role
            if not self.role:
                self.logger.error("No role initialized")
                self.metrics['messages_failed'] += 1
                return False

            start_time = datetime.now()
            success = await self.role.process_message(message, self)
            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

            if success:
                self.metrics['messages_processed'] += 1
            else:
                self.metrics['messages_failed'] += 1

            # Update average processing time
            total_processed = self.metrics['messages_processed'] + self.metrics['messages_failed']
            if total_processed > 0:
                current_avg = self.metrics['avg_processing_time_ms']
                self.metrics['avg_processing_time_ms'] = (
                    (current_avg * (total_processed - 1) + elapsed_ms) / total_processed
                )

            return success

        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            self.error_history.append((datetime.now(), str(e)))
            self.metrics['messages_failed'] += 1
            self.metrics['errors'] += 1
            self.logger.error(f"Error processing message: {e}")

            # Check if error limit exceeded
            if self.error_count >= self.config.max_errors:
                self.logger.error(f"Error limit exceeded for agent {self.agent_id}")
                self.status = AgentStatus.ERROR
                await self.stop()
                return False

            return False

    async def _initialize_role(self) -> bool:
        """
        Load and initialize the role for this agent.

        Returns:
            True if successful, False otherwise
        """
        try:
            from .role_provider import RoleProvider

            provider = RoleProvider()
            self.role = provider.create_role(self.config.role_type)

            if not self.role:
                self.logger.error(f"Unknown role type: {self.config.role_type}")
                return False

            # Initialize role
            success = await self.role.initialize(self)
            return success

        except Exception as e:
            self.logger.error(f"Failed to initialize role: {e}")
            return False

    async def _start_background_tasks(self):
        """Start background tasks (heartbeat, metrics)"""
        try:
            # Heartbeat task
            heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            self.tasks.append(heartbeat_task)

            # Metrics update task (every 60 seconds)
            metrics_task = asyncio.create_task(self._metrics_loop())
            self.tasks.append(metrics_task)

        except Exception as e:
            self.logger.error(f"Failed to start background tasks: {e}")

    async def _heartbeat_loop(self):
        """Periodic heartbeat task"""
        while self.running:
            try:
                await asyncio.sleep(self.config.heartbeat_interval)

                if self.running:
                    # Send heartbeat message
                    heartbeat_msg = Message(
                        message_type='HEARTBEAT',
                        sender_id=self.agent_id,
                        content={
                            'agent_name': self.agent_name,
                            'status': self.status.value,
                            'messages_processed': self.metrics['messages_processed'],
                            'error_count': self.error_count,
                        }
                    )
                    await self.message_queue.put(heartbeat_msg)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Heartbeat error: {e}")

    async def _metrics_loop(self):
        """Periodic metrics update task"""
        while self.running:
            try:
                await asyncio.sleep(60)  # Update every 60 seconds

                if self.start_time and self.running:
                    uptime = (datetime.now() - self.start_time).total_seconds()
                    self.metrics['uptime_seconds'] = int(uptime)

                    self.logger.debug(
                        f"Metrics - Processed: {self.metrics['messages_processed']}, "
                        f"Failed: {self.metrics['messages_failed']}, "
                        f"Uptime: {uptime:.1f}s"
                    )

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Metrics error: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            'agent_id': self.agent_id,
            'agent_name': self.agent_name,
            'role_type': self.config.role_type,
            'status': self.status.value,
            'running': self.running,
            'error_count': self.error_count,
            'last_error': self.last_error,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'metrics': self.metrics.copy(),
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return self.metrics.copy()

    async def send_message(self, target_id: str, message_type: str, content: Dict[str, Any]):
        """Send a message to another agent"""
        message = Message(
            message_type=message_type,
            sender_id=self.agent_id,
            recipient_id=target_id,
            content=content,
        )
        await self.message_queue.put(message)
        self.messages_sent += 1


class SimpleMessageQueue:
    """Simple in-memory message queue for agent communication"""

    def __init__(self):
        self.queue: asyncio.Queue = asyncio.Queue()

    async def put(self, message: Message):
        """Put a message in the queue"""
        await self.queue.put(message)

    async def get(self, timeout: Optional[float] = None) -> Optional[Message]:
        """Get a message from the queue"""
        try:
            return await asyncio.wait_for(self.queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None

    def empty(self) -> bool:
        """Check if queue is empty"""
        return self.queue.empty()

    def size(self) -> int:
        """Get queue size"""
        return self.queue.qsize()


__all__ = [
    'UnifiedAgent',
    'BaseRole',
    'Message',
    'AgentConfig',
    'AgentStatus',
    'SimpleMessageQueue',
]
