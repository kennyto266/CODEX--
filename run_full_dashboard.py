#!/usr/bin/env python3
import asyncio
import logging

from unittest.mock import Mock, AsyncMock

import uvicorn

from src.core import SystemConfig
from src.dashboard.api_routes import DashboardAPI
from src.dashboard.dashboard_ui import DashboardUI


async def build_full_dashboard():
    logging.basicConfig(level=logging.INFO)

    # Create mocked coordinator and message_queue (same structure as start_dashboard.py)
    coordinator = Mock()
    coordinator.get_agent_status = AsyncMock(return_value={
        "agent_type": "QuantitativeAnalyst",
        "status": "running",
        "cpu_usage": 12.3,
        "memory_usage": 34.5,
        "messages_processed": 100,
        "error_count": 0,
        "uptime_seconds": 3600,
        "version": "1.0.0",
        "configuration": {},
    })
    coordinator.get_all_agent_statuses = AsyncMock(return_value={
        "quant_analyst_001": {"agent_type": "QuantitativeAnalyst", "status": "running"}
    })

    message_queue = Mock()
    message_queue.subscribe = AsyncMock()
    message_queue.unsubscribe = AsyncMock()
    message_queue.publish_message = AsyncMock()

    config = SystemConfig()

    # Build Dashboard API and UI
    dashboard_api = DashboardAPI(coordinator, message_queue, config)
    await dashboard_api.initialize()

    dashboard_ui = DashboardUI(dashboard_api, config)
    await dashboard_ui.start()

    return dashboard_ui


def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    dashboard_ui = loop.run_until_complete(build_full_dashboard())

    # Serve FastAPI app
    uvicorn.run(
        dashboard_ui.app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )


if __name__ == "__main__":
    main()
