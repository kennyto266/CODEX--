#!/usr/bin/env python3
"""
WebSocket API - Story 3.1.1 Implementation
完整的WebSocket實時數據推送系統
支持HIBOR、經濟數據、物業數據的實時廣播
實現心跳檢測、連接管理、消息隊列等功能
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from .websocket_manager import manager, message_handler, broadcaster
from .models.api_response import APIResponse

logger = logging.getLogger(__name__)

# Pydantic Models

class SubscriptionRequest(BaseModel):
    """訂閱請求模型"""
    topics: List[str]
    client_id: Optional[str] = None


class DataRequest(BaseModel):
    """數據請求模型"""
    data_type: str
    params: Dict[str, Any] = {}


class ConnectionInfo(BaseModel):
    """連接信息模型"""
    client_id: str
    connected_at: str
    subscriptions: List[str]
    message_count: int
    last_message: Optional[str] = None


class BroadcastMessage(BaseModel):
    """廣播消息模型"""
    type: str
    data: Dict[str, Any]
    topic: Optional[str] = None


# WebSocket端點

async def websocket_endpoint(websocket: WebSocket):
    """WebSocket連接端點"""
    client_id = await manager.connect(websocket)

    try:
        # 啟動消息處理循環
        while True:
            # 接收客戶端消息
            data = await websocket.receive_text()
            message = json.loads(data)

            # 處理消息
            await message_handler.handle_message(client_id, message)

    except WebSocketDisconnect:
        logger.info(f"WebSocket客戶端斷開連接: {client_id}")
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket錯誤: {client_id}, {str(e)}")
        manager.disconnect(client_id)


# FastAPI Router
router = APIRouter(prefix="/api/v2/websocket", tags=["websocket"])

# 連接統計端點

@router.get("/stats", response_model=APIResponse)
async def get_websocket_stats():
    """獲取WebSocket連接統計"""
    try:
        stats = manager.get_connection_stats()

        return APIResponse(
            success=True,
            data=stats,
            message=f"WebSocket統計查詢成功 (當前{stats['total_connections']}個連接)"
        )

    except Exception as e:
        logger.error(f"獲取WebSocket統計失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/connections", response_model=APIResponse)
async def get_active_connections():
    """獲取所有活動連接"""
    try:
        connections = manager.get_connection_stats()["connection_details"]

        return APIResponse(
            success=True,
            data={
                "connections": connections,
                "total": len(connections)
            },
            message=f"活動連接查詢成功 (共{len(connections)}個)"
        )

    except Exception as e:
        logger.error(f"獲取連接列表失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# 控制端點

@router.post("/broadcast", response_model=APIResponse)
async def broadcast_message(
    message: BroadcastMessage,
    topic: Optional[str] = Query(None, description="指定主題廣播")
):
    """廣播消息到所有連接"""
    try:
        if topic:
            # 發送給特定主題的訂閱者
            results = await manager.broadcast(
                message.dict(),
                topic=topic
            )
        else:
            # 發送給所有連接
            results = await manager.broadcast(message.dict())

        success_count = sum(1 for _, result in results if result)

        return APIResponse(
            success=True,
            data={
                "total_targets": len(results),
                "success_count": success_count,
                "failure_count": len(results) - success_count
            },
            message=f"消息廣播完成 (成功: {success_count}/{len(results)})"
        )

    except Exception as e:
        logger.error(f"廣播消息失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/broadcast/hibor", response_model=APIResponse)
async def broadcast_hibor_update(
    rates: Dict[str, float],
    topic: str = Query("hibor", description="主題")
):
    """廣播HIBOR利率更新"""
    try:
        message = {
            "type": "hibor_update",
            "data": {
                "rates": rates,
                "timestamp": datetime.now().isoformat()
            }
        }

        results = await manager.broadcast(message, topic=topic)
        success_count = sum(1 for _, result in results if result)

        return APIResponse(
            success=True,
            data={
                "topic": topic,
                "success_count": success_count,
                "total_targets": len(results)
            },
            message=f"HIBOR更新廣播完成 (成功: {success_count}/{len(results)})"
        )

    except Exception as e:
        logger.error(f"廣播HIBOR更新失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/broadcast/economic", response_model=APIResponse)
async def broadcast_economic_update(
    indicator: str,
    value: float,
    change: Optional[float] = None,
    topic: str = Query("economic", description="主題")
):
    """廣播經濟數據更新"""
    try:
        message = {
            "type": "economic_update",
            "data": {
                "indicator": indicator,
                "value": value,
                "change": change,
                "timestamp": datetime.now().isoformat()
            }
        }

        results = await manager.broadcast(message, topic=topic)
        success_count = sum(1 for _, result in results if result)

        return APIResponse(
            success=True,
            data={
                "indicator": indicator,
                "value": value,
                "topic": topic,
                "success_count": success_count
            },
            message=f"{indicator}數據廣播完成"
        )

    except Exception as e:
        logger.error(f"廣播經濟數據失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/broadcast/alert", response_model=APIResponse)
async def broadcast_alert(
    alert_type: str,
    message: str,
    severity: str = Query("info", description="告警級別"),
    topic: str = Query("alerts", description="主題")
):
    """廣播告警信息"""
    try:
        alert_message = {
            "type": "alert",
            "data": {
                "alert_type": alert_type,
                "message": message,
                "severity": severity,
                "timestamp": datetime.now().isoformat()
            }
        }

        results = await manager.broadcast(alert_message, topic=topic)
        success_count = sum(1 for _, result in results if result)

        return APIResponse(
            success=True,
            data={
                "alert_type": alert_type,
                "severity": severity,
                "topic": topic,
                "success_count": success_count
            },
            message=f"告警廣播完成: {message}"
        )

    except Exception as e:
        logger.error(f"廣播告警失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# 測試端點

@router.post("/test/ping", response_model=APIResponse)
async def test_ping_all():
    """測試ping所有連接"""
    try:
        test_message = {
            "type": "test_ping",
            "data": {
                "message": "測試消息",
                "timestamp": datetime.now().isoformat()
            }
        }

        results = await manager.broadcast(test_message)
        success_count = sum(1 for _, result in results if result)

        return APIResponse(
            success=True,
            data={
                "success_count": success_count,
                "total_targets": len(results)
            },
            message=f"Ping測試完成 (成功: {success_count}/{len(results)})"
        )

    except Exception as e:
        logger.error(f"Ping測試失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test/burst", response_model=APIResponse)
async def test_burst_messages(
    count: int = Query(10, ge=1, le=100, description="消息數量")
):
    """測試突發消息"""
    try:
        success_count = 0

        for i in range(count):
            message = {
                "type": "test_burst",
                "data": {
                    "sequence": i,
                    "message": f"突發消息 {i+1}/{count}",
                    "timestamp": datetime.now().isoformat()
                }
            }

            results = await manager.broadcast(message)
            success_count += sum(1 for _, result in results if result)

            # 避免發送過快
            await asyncio.sleep(0.1)

        return APIResponse(
            success=True,
            data={
                "total_messages": count,
                "total_success": success_count
            },
            message=f"突發測試完成"
        )

    except Exception as e:
        logger.error(f"突發測試失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# 管理端點

@router.delete("/cleanup", response_model=APIResponse)
async def cleanup_inactive_connections():
    """清理非活動連接"""
    try:
        cleaned_count = await manager.cleanup_inactive_connections()

        return APIResponse(
            success=True,
            data={
                "cleaned_count": cleaned_count
            },
            message=f"清理完成 (清理了{cleaned_count}個非活動連接)"
        )

    except Exception as e:
        logger.error(f"清理失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start-broadcaster", response_model=APIResponse)
async def start_broadcaster():
    """啟動實時數據廣播器"""
    try:
        if not broadcaster.is_running:
            await broadcaster.start()
            return APIResponse(
                success=True,
                data={"status": "started"},
                message="實時數據廣播器已啟動"
            )
        else:
            return APIResponse(
                success=True,
                data={"status": "already_running"},
                message="廣播器已在運行中"
            )

    except Exception as e:
        logger.error(f"啟動廣播器失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop-broadcaster", response_model=APIResponse)
async def stop_broadcaster():
    """停止實時數據廣播器"""
    try:
        if broadcaster.is_running:
            await broadcaster.stop()
            return APIResponse(
                success=True,
                data={"status": "stopped"},
                message="實時數據廣播器已停止"
            )
        else:
            return APIResponse(
                success=True,
                data={"status": "already_stopped"},
                message="廣播器已停止"
            )

    except Exception as e:
        logger.error(f"停止廣播器失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# 健康檢查端點

@router.get("/health", response_model=APIResponse)
async def websocket_health_check():
    """WebSocket健康檢查"""
    try:
        stats = manager.get_connection_stats()
        broadcaster_status = "running" if broadcaster.is_running else "stopped"

        health_status = "healthy"
        if stats["total_connections"] >= stats["max_connections"]:
            health_status = "warning"
        if stats["total_connections"] > stats["max_connections"]:
            health_status = "critical"

        return APIResponse(
            success=True,
            data={
                "status": health_status,
                "broadcaster_status": broadcaster_status,
                "connections": stats["total_connections"],
                "max_connections": stats["max_connections"],
                "subscription_topics": stats["subscription_topics"],
                "version": "3.1.1"
            },
            message=f"WebSocket健康檢查完成: {health_status}"
        )

    except Exception as e:
        logger.error(f"健康檢查失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket客戶端HTML頁面

@router.get("/test-client", response_class=HTMLResponse)
async def websocket_test_client():
    """WebSocket測試客戶端頁面"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>WebSocket Test Client</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            #log { border: 1px solid #ccc; height: 300px; overflow-y: scroll; padding: 10px; }
            .message { margin: 5px 0; padding: 5px; }
            .sent { background-color: #e3f2fd; }
            .received { background-color: #f1f8e9; }
            .error { background-color: #ffebee; color: red; }
            button { margin: 5px; padding: 10px; }
        </style>
    </head>
    <body>
        <h1>WebSocket 測試客戶端</h1>

        <div>
            <button onclick="connect()">連接</button>
            <button onclick="disconnect()">斷開</button>
            <span id="status">未連接</span>
        </div>

        <div>
            <button onclick="sendPing()">發送Ping</button>
            <button onclick="subscribeHibor()">訂閱HIBOR</button>
            <button onclick="subscribeEconomic()">訂閱經濟數據</button>
            <button onclick="subscribeAlerts()">訂閱告警</button>
        </div>

        <div id="log"></div>

        <script>
            let ws = null;
            let reconnectInterval = null;

            function log(message, type = 'received') {
                const logDiv = document.getElementById('log');
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${type}`;
                messageDiv.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
                logDiv.appendChild(messageDiv);
                logDiv.scrollTop = logDiv.scrollHeight;
            }

            function connect() {
                if (ws && ws.readyState === WebSocket.OPEN) {
                    log('已連接', 'error');
                    return;
                }

                ws = new WebSocket(`ws://${window.location.host}/api/v2/websocket/ws`);

                ws.onopen = function(event) {
                    document.getElementById('status').textContent = '已連接';
                    log('WebSocket連接已建立');
                };

                ws.onmessage = function(event) {
                    try {
                        const data = JSON.parse(event.data);
                        log(`收到: ${JSON.stringify(data, null, 2)}`, 'received');
                    } catch (e) {
                        log(`收到: ${event.data}`, 'received');
                    }
                };

                ws.onerror = function(error) {
                    log('WebSocket錯誤', 'error');
                };

                ws.onclose = function(event) {
                    document.getElementById('status').textContent = '已斷開';
                    log('WebSocket連接已關閉', 'error');

                    // 自動重連
                    if (!reconnectInterval) {
                        reconnectInterval = setInterval(() => {
                            log('嘗試重連...');
                            connect();
                        }, 3000);
                    }
                };
            }

            function disconnect() {
                if (ws) {
                    ws.close();
                    if (reconnectInterval) {
                        clearInterval(reconnectInterval);
                        reconnectInterval = null;
                    }
                }
            }

            function sendPing() {
                if (ws && ws.readyState === WebSocket.OPEN) {
                    const message = { type: 'ping' };
                    ws.send(JSON.stringify(message));
                    log(`發送: ${JSON.stringify(message)}`, 'sent');
                } else {
                    log('未連接', 'error');
                }
            }

            function subscribeHibor() {
                if (ws && ws.readyState === WebSocket.OPEN) {
                    const message = {
                        type: 'subscribe',
                        topics: ['hibor']
                    };
                    ws.send(JSON.stringify(message));
                    log(`發送: ${JSON.stringify(message)}`, 'sent');
                } else {
                    log('未連接', 'error');
                }
            }

            function subscribeEconomic() {
                if (ws && ws.readyState === WebSocket.OPEN) {
                    const message = {
                        type: 'subscribe',
                        topics: ['economic']
                    };
                    ws.send(JSON.stringify(message));
                    log(`發送: ${JSON.stringify(message)}`, 'sent');
                } else {
                    log('未連接', 'error');
                }
            }

            function subscribeAlerts() {
                if (ws && ws.readyState === WebSocket.OPEN) {
                    const message = {
                        type: 'subscribe',
                        topics: ['alerts']
                    };
                    ws.send(JSON.stringify(message));
                    log(`發送: ${JSON.stringify(message)}`, 'sent');
                } else {
                    log('未連接', 'error');
                }
            }

            // 頁面加載時自動連接
            window.onload = function() {
                connect();
            };
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


__all__ = ['router', 'websocket_endpoint']
