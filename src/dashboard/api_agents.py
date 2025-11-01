"""
Agent 管理系統 API 路由

提供 Agent 監控、控制和日誌查詢的 REST 和 WebSocket 端點
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Query
from pydantic import BaseModel, Field

# 導入緩存管理器
try:
    from ..cache.cache_manager import cache_manager, cached
except ImportError:
    # 如果導入失敗，創建空的緩存管理器
    class DummyCache:
        def cache_result(self, *args, **kwargs):
            def decorator(func):
                return func
    cache_manager = DummyCache()
    cached = cache_manager.cache_result


# ==================== Data Models ====================

class AgentStatus(str, Enum):
    """Agent 狀態"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    FAILED = "failed"
    STOPPED = "stopped"


class AgentInfo(BaseModel):
    """Agent 信息"""
    agent_id: str = Field(..., description="Agent ID")
    name: str = Field(..., description="Agent 名稱")
    status: AgentStatus = Field(default=AgentStatus.IDLE)
    role: str = Field(..., description="Agent 角色")
    memory_usage_mb: float = Field(default=0, description="內存使用 (MB)")
    cpu_usage_pct: float = Field(default=0, description="CPU 使用率 (%)")
    processed_messages: int = Field(default=0, description="已處理消息數")
    last_activity: Optional[datetime] = Field(None, description="最後活動時間")


class AgentMetrics(BaseModel):
    """Agent 性能指標"""
    agent_id: str
    messages_processed: int
    errors_count: int
    average_response_time_ms: float
    uptime_seconds: int


class ControlAction(str, Enum):
    """控制操作"""
    START = "start"
    STOP = "stop"
    PAUSE = "pause"
    RESUME = "resume"
    RESTART = "restart"


class AgentControlRequest(BaseModel):
    """Agent 控制請求"""
    action: ControlAction = Field(..., description="控制操作")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="操作參數")


class AgentLogEntry(BaseModel):
    """Agent 日誌條目"""
    timestamp: datetime
    level: str  # DEBUG, INFO, WARNING, ERROR
    message: str
    source: str = Field(default="system")


# ==================== API Router ====================

def create_agents_router() -> APIRouter:
    """創建 Agent 管理 API 路由"""
    router = APIRouter(prefix="/api/agents", tags=["Agents"])
    logger = logging.getLogger("hk_quant_system.dashboard.api_agents")

    # 模擬的 Agent 列表和日誌存儲
    agents_store: Dict[str, Dict[str, Any]] = {
        "coordinator": {
            "agent_id": "coordinator",
            "name": "協調器",
            "status": AgentStatus.RUNNING,
            "role": "coordinator",
            "description": "協調所有 Agent 的工作流程",
            "memory_usage_mb": 128.5,
            "cpu_usage_pct": 25.3,
            "processed_messages": 1024,
            "last_activity": datetime.now(),
            "uptime_seconds": 3600
        },
        "data_scientist": {
            "agent_id": "data_scientist",
            "name": "數據科學家",
            "status": AgentStatus.RUNNING,
            "role": "data_scientist",
            "description": "進行數據分析和異常檢測",
            "memory_usage_mb": 256.2,
            "cpu_usage_pct": 18.7,
            "processed_messages": 512,
            "last_activity": datetime.now(),
            "uptime_seconds": 3600
        },
        "quantitative_analyst": {
            "agent_id": "quantitative_analyst",
            "name": "量化分析師",
            "status": AgentStatus.RUNNING,
            "role": "quantitative_analyst",
            "description": "進行量化分析和蒙特卡洛模擬",
            "memory_usage_mb": 512.8,
            "cpu_usage_pct": 42.1,
            "processed_messages": 256,
            "last_activity": datetime.now(),
            "uptime_seconds": 3600
        },
        "portfolio_manager": {
            "agent_id": "portfolio_manager",
            "name": "投資組合經理",
            "status": AgentStatus.RUNNING,
            "role": "portfolio_manager",
            "description": "進行投資組合管理和風險預算",
            "memory_usage_mb": 384.3,
            "cpu_usage_pct": 32.5,
            "processed_messages": 768,
            "last_activity": datetime.now(),
            "uptime_seconds": 3600
        },
        "risk_analyst": {
            "agent_id": "risk_analyst",
            "name": "風險分析師",
            "status": AgentStatus.RUNNING,
            "role": "risk_analyst",
            "description": "進行風險評估和對沖策略",
            "memory_usage_mb": 192.7,
            "cpu_usage_pct": 15.2,
            "processed_messages": 384,
            "last_activity": datetime.now(),
            "uptime_seconds": 3600
        },
        "research_analyst": {
            "agent_id": "research_analyst",
            "name": "研究分析師",
            "status": AgentStatus.RUNNING,
            "role": "research_analyst",
            "description": "進行策略研究和回測驗證",
            "memory_usage_mb": 320.1,
            "cpu_usage_pct": 28.9,
            "processed_messages": 640,
            "last_activity": datetime.now(),
            "uptime_seconds": 3600
        }
    }

    agent_logs: Dict[str, List[AgentLogEntry]] = {
        agent_id: [
            AgentLogEntry(
                timestamp=datetime.now(),
                level="INFO",
                message=f"{agent_data['name']} 已初始化",
                source="system"
            )
        ]
        for agent_id, agent_data in agents_store.items()
    }

    # ==================== GET: 獲取 Agent 列表 ====================

    @router.get("/list")
    @cached(ttl=60, key_prefix="agents")
    async def list_agents(
        status: Optional[str] = Query(None, description="按狀態過濾 (idle/running/paused/failed/stopped)"),
        role: Optional[str] = Query(None, description="按角色過濾"),
        sort_by: str = Query("last_activity", description="排序字段 (last_activity/cpu_usage/memory_usage)"),
        sort_order: str = Query("desc", description="排序方向 (asc/desc)"),
        page: int = Query(1, ge=1, description="頁碼"),
        size: int = Query(50, ge=1, le=100, description="每頁數量"),
        fields: Optional[str] = Query(None, description="返回字段，逗號分隔")
    ) -> Dict[str, Any]:
        """
        獲取 Agent 列表 - 帶緩存、分頁和過濾功能

        Returns:
            分頁的Agent列表，包含狀態、資源使用情況等
        """
        try:
            logger.info(f"獲取Agent列表: status={status}, role={role}, page={page}, size={size}")

            # 獲取所有Agent
            agents_list = []
            for agent_id, agent_data in agents_store.items():
                # 應用過濾器
                if status and agent_data["status"].value != status:
                    continue
                if role and agent_data["role"] != role:
                    continue

                # 轉換數據
                agent_dict = {
                    "agent_id": agent_data["agent_id"],
                    "name": agent_data["name"],
                    "status": agent_data["status"].value,
                    "role": agent_data["role"],
                    "description": agent_data.get("description", ""),
                    "memory_usage_mb": agent_data["memory_usage_mb"],
                    "cpu_usage_pct": agent_data["cpu_usage_pct"],
                    "processed_messages": agent_data["processed_messages"],
                    "last_activity": agent_data["last_activity"].isoformat() if agent_data["last_activity"] else None,
                    "uptime_seconds": agent_data["uptime_seconds"]
                }
                agents_list.append(agent_dict)

            # 應用排序
            reverse = sort_order.lower() == "desc"
            if sort_by in ["last_activity", "cpu_usage", "memory_usage"]:
                # 特殊處理last_activity排序
                if sort_by == "last_activity":
                    agents_list.sort(
                        key=lambda x: x["last_activity"] or "",
                        reverse=reverse
                    )
                elif sort_by == "cpu_usage":
                    agents_list.sort(
                        key=lambda x: x["cpu_usage_pct"],
                        reverse=reverse
                    )
                elif sort_by == "memory_usage":
                    agents_list.sort(
                        key=lambda x: x["memory_usage_mb"],
                        reverse=reverse
                    )

            # 計算總數和分頁
            total = len(agents_list)
            start = (page - 1) * size
            end = start + size
            paginated_agents = agents_list[start:end]

            # 字段過濾
            if fields:
                requested_fields = [f.strip() for f in fields.split(",")]
                filtered_agents = []
                for agent in paginated_agents:
                    filtered_agent = {k: v for k, v in agent.items() if k in requested_fields}
                    filtered_agents.append(filtered_agent)
                paginated_agents = filtered_agents

            # 計算頁數
            pages = (total + size - 1) // size if total > 0 else 0

            logger.info(f"返回 {len(paginated_agents)} 個Agent (總數: {total})")

            return {
                "success": True,
                "data": paginated_agents,
                "pagination": {
                    "total": total,
                    "page": page,
                    "size": size,
                    "pages": pages,
                    "has_next": page < pages,
                    "has_prev": page > 1,
                    "next_page": page + 1 if page < pages else None,
                    "prev_page": page - 1 if page > 1 else None
                },
                "filters": {
                    "status": status,
                    "role": role,
                    "sort_by": sort_by,
                    "sort_order": sort_order
                },
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"獲取 Agent 列表失敗: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ==================== GET: 獲取單個 Agent 狀態 ====================

    @router.get("/{agent_id}/status")
    @cached(ttl=30, key_prefix="agent_status")
    async def get_agent_status(agent_id: str) -> Dict[str, Any]:
        """
        獲取特定 Agent 的詳細狀態 - 帶緩存

        - **agent_id**: Agent ID

        Returns:
            Agent 詳細狀態信息
        """
        logger.debug(f"獲取Agent狀態: {agent_id}")

        if agent_id not in agents_store:
            raise HTTPException(status_code=404, detail=f"Agent 不存在: {agent_id}")

        agent = agents_store[agent_id]
        return {
            "success": True,
            "data": {
                "agent_id": agent["agent_id"],
                "name": agent["name"],
                "status": agent["status"].value,
                "role": agent["role"],
                "memory_usage_mb": agent["memory_usage_mb"],
                "cpu_usage_pct": agent["cpu_usage_pct"],
                "processed_messages": agent["processed_messages"],
                "last_activity": agent["last_activity"].isoformat() if agent["last_activity"] else None,
                "uptime_seconds": agent["uptime_seconds"],
                "health": "healthy" if agent["status"] == AgentStatus.RUNNING else "unhealthy"
            }
        }

    # ==================== GET: 獲取 Agent 日誌 ====================

    @router.get("/{agent_id}/logs", response_model=List[Dict[str, Any]])
    async def get_agent_logs(
        agent_id: str,
        limit: int = 50,
        level: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        獲取 Agent 的日誌記錄

        - **agent_id**: Agent ID
        - **limit**: 返回的日誌條數限制
        - **level**: 日誌級別過濾 (DEBUG, INFO, WARNING, ERROR)

        Returns:
            日誌條目列表
        """
        if agent_id not in agent_logs:
            raise HTTPException(status_code=404, detail=f"Agent 不存在: {agent_id}")

        logs = agent_logs[agent_id]

        # 過濾日誌級別
        if level:
            logs = [log for log in logs if log.level == level.upper()]

        # 返回最近的日誌
        return [
            {
                "timestamp": log.timestamp.isoformat(),
                "level": log.level,
                "message": log.message,
                "source": log.source
            }
            for log in logs[-limit:]
        ]

    # ==================== GET: 獲取 Agent 性能指標 ====================

    @router.get("/{agent_id}/metrics", response_model=Dict[str, Any])
    async def get_agent_metrics(agent_id: str) -> Dict[str, Any]:
        """
        獲取 Agent 的性能指標

        - **agent_id**: Agent ID

        Returns:
            性能指標
        """
        if agent_id not in agents_store:
            raise HTTPException(status_code=404, detail=f"Agent 不存在: {agent_id}")

        agent = agents_store[agent_id]
        return {
            "agent_id": agent_id,
            "messages_processed": agent["processed_messages"],
            "errors_count": 0,
            "average_response_time_ms": 150.5,
            "uptime_seconds": agent["uptime_seconds"],
            "memory_mb": agent["memory_usage_mb"],
            "cpu_pct": agent["cpu_usage_pct"]
        }

    # ==================== POST: 控制 Agent ====================

    @router.post("/{agent_id}/start", response_model=Dict[str, str])
    async def start_agent(agent_id: str) -> Dict[str, str]:
        """啟動 Agent"""
        if agent_id not in agents_store:
            raise HTTPException(status_code=404, detail=f"Agent 不存在: {agent_id}")

        agent = agents_store[agent_id]
        agent["status"] = AgentStatus.RUNNING
        agent["last_activity"] = datetime.now()

        # 添加日誌
        if agent_id not in agent_logs:
            agent_logs[agent_id] = []
        agent_logs[agent_id].append(
            AgentLogEntry(
                timestamp=datetime.now(),
                level="INFO",
                message=f"Agent {agent['name']} 已啟動",
                source="control"
            )
        )

        logger.info(f"Agent 已啟動: {agent_id}")
        return {"status": "success", "message": f"Agent {agent_id} 已啟動"}

    @router.post("/{agent_id}/stop", response_model=Dict[str, str])
    async def stop_agent(agent_id: str) -> Dict[str, str]:
        """停止 Agent"""
        if agent_id not in agents_store:
            raise HTTPException(status_code=404, detail=f"Agent 不存在: {agent_id}")

        agent = agents_store[agent_id]
        agent["status"] = AgentStatus.STOPPED
        agent["last_activity"] = datetime.now()

        if agent_id not in agent_logs:
            agent_logs[agent_id] = []
        agent_logs[agent_id].append(
            AgentLogEntry(
                timestamp=datetime.now(),
                level="INFO",
                message=f"Agent {agent['name']} 已停止",
                source="control"
            )
        )

        logger.info(f"Agent 已停止: {agent_id}")
        return {"status": "success", "message": f"Agent {agent_id} 已停止"}

    @router.post("/{agent_id}/pause", response_model=Dict[str, str])
    async def pause_agent(agent_id: str) -> Dict[str, str]:
        """暫停 Agent"""
        if agent_id not in agents_store:
            raise HTTPException(status_code=404, detail=f"Agent 不存在: {agent_id}")

        agent = agents_store[agent_id]
        agent["status"] = AgentStatus.PAUSED
        agent["last_activity"] = datetime.now()

        return {"status": "success", "message": f"Agent {agent_id} 已暫停"}

    @router.post("/{agent_id}/restart", response_model=Dict[str, str])
    async def restart_agent(agent_id: str) -> Dict[str, str]:
        """重啟 Agent"""
        if agent_id not in agents_store:
            raise HTTPException(status_code=404, detail=f"Agent 不存在: {agent_id}")

        agent = agents_store[agent_id]
        agent["status"] = AgentStatus.RUNNING
        agent["last_activity"] = datetime.now()
        agent["processed_messages"] = 0

        return {"status": "success", "message": f"Agent {agent_id} 已重啟"}

    return router
