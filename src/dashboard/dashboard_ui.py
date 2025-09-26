"""
港股量化交易 AI Agent 系统 - 仪表板前端界面

实现完整的仪表板HTML界面，集成所有组件和实时更新功能。
提供用户友好的仪表板界面，支持响应式设计和实时数据更新。
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ..core import SystemConfig
from .api_routes import DashboardAPI


class DashboardUI:
    """仪表板前端界面"""
    
    def __init__(self, dashboard_api: DashboardAPI, config: SystemConfig = None):
        self.dashboard_api = dashboard_api
        self.config = config or SystemConfig()
        self.logger = logging.getLogger("hk_quant_system.dashboard_ui")
        
        # 创建FastAPI应用
        self.app = FastAPI(
            title="港股量化交易 AI Agent 仪表板",
            description="实时监控和管理7个AI Agent的量化交易系统",
            version="1.0.0"
        )
        
        # 设置模板和静态文件
        self.templates = Jinja2Templates(directory="src/dashboard/templates")
        
        # 设置路由
        self._setup_routes()
        
        # WebSocket连接管理
        self.active_connections: List[WebSocket] = []
        
        # 数据缓存
        self._cached_data: Dict[str, Any] = {}
        self._last_update: Dict[str, datetime] = {}
        
        # 后台任务
        self._update_task: Optional[asyncio.Task] = None
        self._running = False
    
    def _setup_routes(self):
        """设置前端路由"""
        
        # 主仪表板页面
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard_home(request: Request):
            """仪表板主页"""
            return HTMLResponse(content=self._get_dashboard_html())
        
        # Agent详情页面
        @self.app.get("/agent/{agent_id}", response_class=HTMLResponse)
        async def agent_detail(request: Request, agent_id: str):
            """Agent详情页面"""
            return HTMLResponse(content=self._get_agent_detail_html(agent_id))
        
        # 策略详情页面
        @self.app.get("/agent/{agent_id}/strategy", response_class=HTMLResponse)
        async def strategy_detail(request: Request, agent_id: str):
            """策略详情页面"""
            return HTMLResponse(content=self._get_strategy_detail_html(agent_id))
        
        # 绩效分析页面
        @self.app.get("/performance", response_class=HTMLResponse)
        async def performance_analysis(request: Request):
            """绩效分析页面"""
            return HTMLResponse(content=self._get_performance_html())
        
        # 系统状态页面
        @self.app.get("/system", response_class=HTMLResponse)
        async def system_status(request: Request):
            """系统状态页面"""
            return HTMLResponse(content=self._get_system_status_html())
        
        # API代理端点
        @self.app.get("/api/{path:path}")
        async def api_proxy(path: str, request: Request):
            """API代理"""
            # 这里可以添加API代理逻辑
            pass
        
        # WebSocket端点
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket实时连接"""
            await self._handle_websocket(websocket)
    
    def _get_dashboard_html(self) -> str:
        """获取主仪表板HTML"""
        return """
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>港股量化交易 AI Agent 仪表板</title>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
            <style>
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }
                
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    color: #333;
                }
                
                .dashboard-container {
                    max-width: 1400px;
                    margin: 0 auto;
                    padding: 20px;
                }
                
                .dashboard-header {
                    background: rgba(255, 255, 255, 0.95);
                    backdrop-filter: blur(10px);
                    border-radius: 15px;
                    padding: 30px;
                    margin-bottom: 30px;
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                }
                
                .dashboard-title {
                    font-size: 2.5rem;
                    font-weight: 700;
                    color: #2c3e50;
                    margin-bottom: 10px;
                    text-align: center;
                }
                
                .dashboard-subtitle {
                    font-size: 1.2rem;
                    color: #7f8c8d;
                    text-align: center;
                    margin-bottom: 30px;
                }
                
                .system-stats {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }
                
                .stat-card {
                    background: rgba(255, 255, 255, 0.9);
                    border-radius: 12px;
                    padding: 20px;
                    text-align: center;
                    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
                    transition: transform 0.3s ease;
                }
                
                .stat-card:hover {
                    transform: translateY(-5px);
                }
                
                .stat-value {
                    font-size: 2rem;
                    font-weight: bold;
                    color: #3498db;
                    margin-bottom: 5px;
                }
                
                .stat-label {
                    font-size: 0.9rem;
                    color: #7f8c8d;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }
                
                .agents-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
                    gap: 25px;
                    margin-bottom: 30px;
                }
                
                .agent-card {
                    background: rgba(255, 255, 255, 0.95);
                    border-radius: 15px;
                    padding: 25px;
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                    transition: all 0.3s ease;
                    border-left: 5px solid #3498db;
                }
                
                .agent-card:hover {
                    transform: translateY(-5px);
                    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
                }
                
                .agent-card.running {
                    border-left-color: #27ae60;
                }
                
                .agent-card.error {
                    border-left-color: #e74c3c;
                }
                
                .agent-card.stopped {
                    border-left-color: #95a5a6;
                }
                
                .agent-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 20px;
                }
                
                .agent-title {
                    font-size: 1.4rem;
                    font-weight: 600;
                    color: #2c3e50;
                }
                
                .agent-status {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }
                
                .status-indicator {
                    width: 12px;
                    height: 12px;
                    border-radius: 50%;
                    animation: pulse 2s infinite;
                }
                
                .status-indicator.running {
                    background: #27ae60;
                }
                
                .status-indicator.error {
                    background: #e74c3c;
                }
                
                .status-indicator.stopped {
                    background: #95a5a6;
                }
                
                @keyframes pulse {
                    0% { opacity: 1; }
                    50% { opacity: 0.5; }
                    100% { opacity: 1; }
                }
                
                .status-text {
                    font-size: 0.9rem;
                    font-weight: 500;
                    color: #7f8c8d;
                }
                
                .agent-metrics {
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 15px;
                    margin-bottom: 20px;
                }
                
                .metric-item {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 10px;
                    background: rgba(52, 152, 219, 0.1);
                    border-radius: 8px;
                }
                
                .metric-label {
                    font-size: 0.9rem;
                    color: #7f8c8d;
                }
                
                .metric-value {
                    font-weight: 600;
                    color: #2c3e50;
                }
                
                .metric-value.sharpe {
                    color: #27ae60;
                }
                
                .metric-value.return {
                    color: #3498db;
                }
                
                .metric-value.drawdown {
                    color: #e74c3c;
                }
                
                .agent-actions {
                    display: flex;
                    gap: 10px;
                    flex-wrap: wrap;
                }
                
                .btn {
                    padding: 8px 16px;
                    border: none;
                    border-radius: 6px;
                    font-size: 0.9rem;
                    font-weight: 500;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    display: flex;
                    align-items: center;
                    gap: 5px;
                }
                
                .btn-success {
                    background: #27ae60;
                    color: white;
                }
                
                .btn-danger {
                    background: #e74c3c;
                    color: white;
                }
                
                .btn-warning {
                    background: #f39c12;
                    color: white;
                }
                
                .btn-info {
                    background: #3498db;
                    color: white;
                }
                
                .btn:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
                }
                
                .performance-overview {
                    background: rgba(255, 255, 255, 0.95);
                    border-radius: 15px;
                    padding: 30px;
                    margin-bottom: 30px;
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                }
                
                .performance-title {
                    font-size: 1.8rem;
                    font-weight: 600;
                    color: #2c3e50;
                    margin-bottom: 20px;
                    text-align: center;
                }
                
                .performance-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                }
                
                .performance-card {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border-radius: 12px;
                    padding: 20px;
                    text-align: center;
                }
                
                .performance-value {
                    font-size: 2.2rem;
                    font-weight: bold;
                    margin-bottom: 5px;
                }
                
                .performance-label {
                    font-size: 0.9rem;
                    opacity: 0.9;
                }
                
                .navigation {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    display: flex;
                    gap: 10px;
                }
                
                .nav-btn {
                    background: rgba(255, 255, 255, 0.9);
                    border: none;
                    border-radius: 8px;
                    padding: 10px 15px;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    text-decoration: none;
                    color: #2c3e50;
                    font-weight: 500;
                }
                
                .nav-btn:hover {
                    background: white;
                    transform: translateY(-2px);
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
                }
                
                .loading {
                    text-align: center;
                    padding: 40px;
                    color: #7f8c8d;
                }
                
                .error {
                    background: #e74c3c;
                    color: white;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 20px 0;
                    text-align: center;
                }
                
                @media (max-width: 768px) {
                    .dashboard-container {
                        padding: 10px;
                    }
                    
                    .agents-grid {
                        grid-template-columns: 1fr;
                    }
                    
                    .agent-metrics {
                        grid-template-columns: 1fr;
                    }
                    
                    .system-stats {
                        grid-template-columns: repeat(2, 1fr);
                    }
                }
            </style>
        </head>
        <body>
            <div class="dashboard-container">
                <div class="navigation">
                    <a href="/" class="nav-btn">首页</a>
                    <a href="/performance" class="nav-btn">绩效分析</a>
                    <a href="/system" class="nav-btn">系统状态</a>
                </div>
                
                <div class="dashboard-header">
                    <h1 class="dashboard-title">港股量化交易 AI Agent 仪表板</h1>
                    <p class="dashboard-subtitle">实时监控和管理7个AI Agent的量化交易系统</p>
                    
                    <div class="system-stats" id="systemStats">
                        <div class="stat-card">
                            <div class="stat-value" id="activeAgents">-</div>
                            <div class="stat-label">活跃Agent</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value" id="totalSharpe">-</div>
                            <div class="stat-label">平均夏普比率</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value" id="totalReturn">-</div>
                            <div class="stat-label">总收益率</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value" id="activeAlerts">-</div>
                            <div class="stat-label">活跃告警</div>
                        </div>
                    </div>
                </div>
                
                <div class="performance-overview">
                    <h2 class="performance-title">系统绩效总览</h2>
                    <div class="performance-grid">
                        <div class="performance-card">
                            <div class="performance-value" id="avgSharpe">-</div>
                            <div class="performance-label">平均夏普比率</div>
                        </div>
                        <div class="performance-card">
                            <div class="performance-value" id="avgReturn">-</div>
                            <div class="performance-label">平均收益率</div>
                        </div>
                        <div class="performance-card">
                            <div class="performance-value" id="avgDrawdown">-</div>
                            <div class="performance-label">平均回撤</div>
                        </div>
                        <div class="performance-card">
                            <div class="performance-value" id="totalTrades">-</div>
                            <div class="performance-label">总交易次数</div>
                        </div>
                    </div>
                </div>
                
                <div class="agents-grid" id="agentsGrid">
                    <div class="loading">
                        <i class="fas fa-spinner fa-spin"></i> 加载Agent数据中...
                    </div>
                </div>
            </div>
            
            <script>
                class DashboardApp {
                    constructor() {
                        this.ws = null;
                        this.reconnectInterval = null;
                        this.init();
                    }
                    
                    init() {
                        this.connectWebSocket();
                        this.loadInitialData();
                        this.setupEventListeners();
                        
                        // 定期刷新数据
                        setInterval(() => {
                            this.loadInitialData();
                        }, 30000);
                    }
                    
                    connectWebSocket() {
                        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                        const wsUrl = `${protocol}//${window.location.host}/ws`;
                        
                        this.ws = new WebSocket(wsUrl);
                        
                        this.ws.onopen = () => {
                            console.log('WebSocket连接已建立');
                            this.ws.send(JSON.stringify({
                                type: 'subscribe',
                                subscription_type: 'agent_updates'
                            }));
                        };
                        
                        this.ws.onmessage = (event) => {
                            const data = JSON.parse(event.data);
                            this.handleWebSocketMessage(data);
                        };
                        
                        this.ws.onclose = () => {
                            console.log('WebSocket连接已断开，尝试重连...');
                            this.scheduleReconnect();
                        };
                        
                        this.ws.onerror = (error) => {
                            console.error('WebSocket错误:', error);
                        };
                    }
                    
                    scheduleReconnect() {
                        if (this.reconnectInterval) return;
                        
                        this.reconnectInterval = setInterval(() => {
                            this.connectWebSocket();
                            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                                clearInterval(this.reconnectInterval);
                                this.reconnectInterval = null;
                            }
                        }, 5000);
                    }
                    
                    handleWebSocketMessage(data) {
                        switch (data.type) {
                            case 'agent_update':
                                this.updateAgentCard(data.agent_id, data.data);
                                break;
                            case 'dashboard_summary':
                                this.updateDashboardSummary(data.data);
                                break;
                            case 'heartbeat':
                                // 心跳消息，不需要处理
                                break;
                        }
                    }
                    
                    async loadInitialData() {
                        try {
                            // 加载系统统计
                            const statsResponse = await fetch('/api/dashboard/status');
                            const statsData = await statsResponse.json();
                            this.updateSystemStats(statsData);
                            
                            // 加载所有Agent数据
                            const agentsResponse = await fetch('/api/dashboard/agents');
                            const agentsData = await agentsResponse.json();
                            this.renderAgents(agentsData.agents);
                            
                            // 加载绩效数据
                            const performanceResponse = await fetch('/api/dashboard/performance');
                            const performanceData = await performanceResponse.json();
                            this.updatePerformanceOverview(performanceData.performance);
                            
                        } catch (error) {
                            console.error('加载数据失败:', error);
                            this.showError('加载数据失败，请刷新页面重试');
                        }
                    }
                    
                    updateSystemStats(statsData) {
                        document.getElementById('activeAgents').textContent = statsData.active_agents || 0;
                        document.getElementById('activeAlerts').textContent = statsData.total_alerts || 0;
                    }
                    
                    renderAgents(agentsData) {
                        const grid = document.getElementById('agentsGrid');
                        
                        if (!agentsData || Object.keys(agentsData).length === 0) {
                            grid.innerHTML = '<div class="loading">暂无Agent数据</div>';
                            return;
                        }
                        
                        let html = '';
                        for (const [agentId, agentData] of Object.entries(agentsData)) {
                            html += this.createAgentCard(agentId, agentData);
                        }
                        
                        grid.innerHTML = html;
                    }
                    
                    createAgentCard(agentId, agentData) {
                        const statusClass = agentData.status.toLowerCase();
                        const statusText = this.getStatusText(agentData.status);
                        const statusColor = this.getStatusColor(agentData.status);
                        
                        return `
                            <div class="agent-card ${statusClass}" data-agent-id="${agentId}">
                                <div class="agent-header">
                                    <div class="agent-title">${agentData.agent_type}</div>
                                    <div class="agent-status">
                                        <div class="status-indicator ${statusClass}" style="background-color: ${statusColor};"></div>
                                        <span class="status-text">${statusText}</span>
                                    </div>
                                </div>
                                
                                <div class="agent-metrics">
                                    <div class="metric-item">
                                        <span class="metric-label">运行时间</span>
                                        <span class="metric-value">${this.formatUptime(agentData.uptime_seconds)}</span>
                                    </div>
                                    <div class="metric-item">
                                        <span class="metric-label">处理消息</span>
                                        <span class="metric-value">${agentData.messages_processed.toLocaleString()}</span>
                                    </div>
                                    <div class="metric-item">
                                        <span class="metric-label">错误计数</span>
                                        <span class="metric-value">${agentData.error_count}</span>
                                    </div>
                                    <div class="metric-item">
                                        <span class="metric-label">CPU使用率</span>
                                        <span class="metric-value">${agentData.cpu_usage.toFixed(1)}%</span>
                                    </div>
                                </div>
                                
                                ${agentData.performance_metrics ? this.createPerformanceMetrics(agentData.performance_metrics) : ''}
                                
                                <div class="agent-actions">
                                    <button class="btn btn-info" onclick="dashboardApp.showAgentDetails('${agentId}')">
                                        <i class="fas fa-info-circle"></i> 详情
                                    </button>
                                    <button class="btn btn-info" onclick="dashboardApp.showStrategyDetails('${agentId}')">
                                        <i class="fas fa-chart-line"></i> 策略
                                    </button>
                                    ${this.createControlButtons(agentId, agentData.status)}
                                </div>
                            </div>
                        `;
                    }
                    
                    createPerformanceMetrics(performance) {
                        return `
                            <div class="agent-metrics">
                                <div class="metric-item">
                                    <span class="metric-label">夏普比率</span>
                                    <span class="metric-value sharpe">${performance.sharpe_ratio.toFixed(3)}</span>
                                </div>
                                <div class="metric-item">
                                    <span class="metric-label">总收益率</span>
                                    <span class="metric-value return">${(performance.total_return * 100).toFixed(2)}%</span>
                                </div>
                                <div class="metric-item">
                                    <span class="metric-label">最大回撤</span>
                                    <span class="metric-value drawdown">${(performance.max_drawdown * 100).toFixed(2)}%</span>
                                </div>
                                <div class="metric-item">
                                    <span class="metric-label">胜率</span>
                                    <span class="metric-value">${(performance.win_rate * 100).toFixed(1)}%</span>
                                </div>
                            </div>
                        `;
                    }
                    
                    createControlButtons(agentId, status) {
                        let buttons = '';
                        
                        if (status !== 'running') {
                            buttons += `<button class="btn btn-success" onclick="dashboardApp.controlAgent('${agentId}', 'start')">
                                <i class="fas fa-play"></i> 启动
                            </button>`;
                        }
                        
                        if (status === 'running') {
                            buttons += `<button class="btn btn-warning" onclick="dashboardApp.controlAgent('${agentId}', 'pause')">
                                <i class="fas fa-pause"></i> 暂停
                            </button>`;
                            buttons += `<button class="btn btn-danger" onclick="dashboardApp.controlAgent('${agentId}', 'stop')">
                                <i class="fas fa-stop"></i> 停止
                            </button>`;
                        }
                        
                        buttons += `<button class="btn btn-info" onclick="dashboardApp.controlAgent('${agentId}', 'restart')">
                            <i class="fas fa-redo"></i> 重启
                        </button>`;
                        
                        return buttons;
                    }
                    
                    updateAgentCard(agentId, agentData) {
                        const card = document.querySelector(`[data-agent-id="${agentId}"]`);
                        if (card) {
                            // 更新Agent卡片数据
                            const newCard = this.createAgentCard(agentId, agentData);
                            card.outerHTML = newCard;
                        }
                    }
                    
                    updateDashboardSummary(summary) {
                        // 更新仪表板总览数据
                        if (summary.system_metrics) {
                            document.getElementById('totalSharpe').textContent = summary.system_metrics.avg_sharpe_ratio.toFixed(3);
                            document.getElementById('totalReturn').textContent = (summary.system_metrics.total_return * 100).toFixed(2) + '%';
                        }
                    }
                    
                    updatePerformanceOverview(performanceData) {
                        if (!performanceData || Object.keys(performanceData).length === 0) return;
                        
                        let totalSharpe = 0, totalReturn = 0, totalDrawdown = 0, totalTrades = 0;
                        let count = 0;
                        
                        for (const perf of Object.values(performanceData)) {
                            totalSharpe += perf.sharpe_ratio;
                            totalReturn += perf.total_return;
                            totalDrawdown += perf.max_drawdown;
                            totalTrades += perf.trades_count;
                            count++;
                        }
                        
                        if (count > 0) {
                            document.getElementById('avgSharpe').textContent = (totalSharpe / count).toFixed(3);
                            document.getElementById('avgReturn').textContent = (totalReturn / count * 100).toFixed(2) + '%';
                            document.getElementById('avgDrawdown').textContent = (totalDrawdown / count * 100).toFixed(2) + '%';
                            document.getElementById('totalTrades').textContent = totalTrades.toLocaleString();
                        }
                    }
                    
                    async controlAgent(agentId, action) {
                        try {
                            const response = await fetch(`/api/dashboard/agents/${agentId}/control/${action}`, {
                                method: 'POST'
                            });
                            
                            if (response.ok) {
                                const result = await response.json();
                                this.showSuccess(`Agent ${agentId} ${action} 操作已启动`);
                            } else {
                                this.showError(`控制Agent失败: ${response.statusText}`);
                            }
                        } catch (error) {
                            console.error('控制Agent失败:', error);
                            this.showError('控制Agent失败，请重试');
                        }
                    }
                    
                    showAgentDetails(agentId) {
                        window.open(`/agent/${agentId}`, '_blank');
                    }
                    
                    showStrategyDetails(agentId) {
                        window.open(`/agent/${agentId}/strategy`, '_blank');
                    }
                    
                    setupEventListeners() {
                        // 添加全局事件监听器
                        window.addEventListener('beforeunload', () => {
                            if (this.ws) {
                                this.ws.close();
                            }
                        });
                    }
                    
                    getStatusText(status) {
                        const statusMap = {
                            'running': '运行中',
                            'idle': '空闲',
                            'error': '错误',
                            'stopped': '已停止'
                        };
                        return statusMap[status.toLowerCase()] || status;
                    }
                    
                    getStatusColor(status) {
                        const colorMap = {
                            'running': '#27ae60',
                            'idle': '#f39c12',
                            'error': '#e74c3c',
                            'stopped': '#95a5a6'
                        };
                        return colorMap[status.toLowerCase()] || '#95a5a6';
                    }
                    
                    formatUptime(seconds) {
                        if (seconds < 60) return `${seconds.toFixed(0)}秒`;
                        if (seconds < 3600) return `${(seconds / 60).toFixed(0)}分钟`;
                        if (seconds < 86400) return `${(seconds / 3600).toFixed(1)}小时`;
                        return `${(seconds / 86400).toFixed(1)}天`;
                    }
                    
                    showSuccess(message) {
                        this.showNotification(message, 'success');
                    }
                    
                    showError(message) {
                        this.showNotification(message, 'error');
                    }
                    
                    showNotification(message, type) {
                        // 简单的通知实现
                        const notification = document.createElement('div');
                        notification.style.cssText = `
                            position: fixed;
                            top: 20px;
                            right: 20px;
                            padding: 15px 20px;
                            border-radius: 8px;
                            color: white;
                            font-weight: 500;
                            z-index: 1000;
                            background: ${type === 'success' ? '#27ae60' : '#e74c3c'};
                            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
                        `;
                        notification.textContent = message;
                        
                        document.body.appendChild(notification);
                        
                        setTimeout(() => {
                            notification.remove();
                        }, 3000);
                    }
                }
                
                // 初始化应用
                const dashboardApp = new DashboardApp();
            </script>
        </body>
        </html>
        """
    
    def _get_agent_detail_html(self, agent_id: str) -> str:
        """获取Agent详情页面HTML"""
        return f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Agent {agent_id} 详情</title>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
            <style>
                /* 复用主仪表板的样式 */
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    color: #333;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: rgba(255, 255, 255, 0.95);
                    backdrop-filter: blur(10px);
                    border-radius: 15px;
                    padding: 30px;
                    margin-bottom: 30px;
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                }}
                .back-btn {{
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                    padding: 10px 20px;
                    background: #3498db;
                    color: white;
                    text-decoration: none;
                    border-radius: 8px;
                    margin-bottom: 20px;
                    transition: all 0.3s ease;
                }}
                .back-btn:hover {{
                    background: #2980b9;
                    transform: translateY(-2px);
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <a href="/" class="back-btn">
                        <i class="fas fa-arrow-left"></i> 返回仪表板
                    </a>
                    <h1>Agent {agent_id} 详情页面</h1>
                    <p>详细的Agent信息和控制面板</p>
                </div>
                <div id="agentDetailContent">
                    <div class="loading">
                        <i class="fas fa-spinner fa-spin"></i> 加载Agent详情中...
                    </div>
                </div>
            </div>
            
            <script>
                async function loadAgentDetail() {{
                    try {{
                        const response = await fetch('/api/dashboard/agents/{agent_id}');
                        const data = await response.json();
                        
                        document.getElementById('agentDetailContent').innerHTML = `
                            <div class="agent-detail">
                                <h2>${{data.agent.agent_type}}</h2>
                                <p>状态: ${{data.agent.status}}</p>
                                <p>运行时间: ${{formatUptime(data.agent.uptime_seconds)}}</p>
                                <p>处理消息: ${{data.agent.messages_processed}}</p>
                                <p>错误计数: ${{data.agent.error_count}}</p>
                            </div>
                        `;
                    }} catch (error) {{
                        document.getElementById('agentDetailContent').innerHTML = `
                            <div class="error">
                                加载Agent详情失败: ${{error.message}}
                            </div>
                        `;
                    }}
                }}
                
                function formatUptime(seconds) {{
                    if (seconds < 60) return `${{seconds.toFixed(0)}}秒`;
                    if (seconds < 3600) return `${{(seconds / 60).toFixed(0)}}分钟`;
                    if (seconds < 86400) return `${{(seconds / 3600).toFixed(1)}}小时`;
                    return `${{(seconds / 86400).toFixed(1)}}天`;
                }}
                
                loadAgentDetail();
            </script>
        </body>
        </html>
        """
    
    def _get_strategy_detail_html(self, agent_id: str) -> str:
        """获取策略详情页面HTML"""
        return f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Agent {agent_id} 策略详情</title>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <a href="/" class="back-btn">
                        <i class="fas fa-arrow-left"></i> 返回仪表板
                    </a>
                    <h1>Agent {agent_id} 策略详情</h1>
                    <p>策略参数、回测结果和实时表现</p>
                </div>
                <div id="strategyDetailContent">
                    <div class="loading">
                        <i class="fas fa-spinner fa-spin"></i> 加载策略详情中...
                    </div>
                </div>
            </div>
            
            <script>
                async function loadStrategyDetail() {{
                    try {{
                        const response = await fetch('/api/dashboard/agents/{agent_id}/strategy');
                        const data = await response.json();
                        
                        document.getElementById('strategyDetailContent').innerHTML = `
                            <div class="strategy-detail">
                                <h2>${{data.strategy.strategy_name}}</h2>
                                <p>策略类型: ${{data.strategy.strategy_type}}</p>
                                <p>状态: ${{data.strategy.status}}</p>
                                <p>版本: ${{data.strategy.version}}</p>
                                <p>风险等级: ${{data.strategy.risk_level}}</p>
                            </div>
                        `;
                    }} catch (error) {{
                        document.getElementById('strategyDetailContent').innerHTML = `
                            <div class="error">
                                加载策略详情失败: ${{error.message}}
                            </div>
                        `;
                    }}
                }}
                
                loadStrategyDetail();
            </script>
        </body>
        </html>
        """
    
    def _get_performance_html(self) -> str:
        """获取绩效分析页面HTML"""
        return """
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>绩效分析</title>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <a href="/" class="back-btn">
                        <i class="fas fa-arrow-left"></i> 返回仪表板
                    </a>
                    <h1>绩效分析</h1>
                    <p>详细的绩效指标和图表分析</p>
                </div>
                <div id="performanceContent">
                    <div class="loading">
                        <i class="fas fa-spinner fa-spin"></i> 加载绩效数据中...
                    </div>
                </div>
            </div>
            
            <script>
                async function loadPerformanceData() {
                    try {
                        const response = await fetch('/api/dashboard/performance');
                        const data = await response.json();
                        
                        // 渲染绩效数据
                        renderPerformanceData(data.performance);
                    } catch (error) {
                        document.getElementById('performanceContent').innerHTML = `
                            <div class="error">
                                加载绩效数据失败: ${error.message}
                            </div>
                        `;
                    }
                }
                
                function renderPerformanceData(performanceData) {
                    // 实现绩效数据渲染逻辑
                    document.getElementById('performanceContent').innerHTML = `
                        <div class="performance-analysis">
                            <h2>绩效分析数据</h2>
                            <pre>${JSON.stringify(performanceData, null, 2)}</pre>
                        </div>
                    `;
                }
                
                loadPerformanceData();
            </script>
        </body>
        </html>
        """
    
    def _get_system_status_html(self) -> str:
        """获取系统状态页面HTML"""
        return """
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>系统状态</title>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <a href="/" class="back-btn">
                        <i class="fas fa-arrow-left"></i> 返回仪表板
                    </a>
                    <h1>系统状态</h1>
                    <p>系统运行状态和监控信息</p>
                </div>
                <div id="systemStatusContent">
                    <div class="loading">
                        <i class="fas fa-spinner fa-spin"></i> 加载系统状态中...
                    </div>
                </div>
            </div>
            
            <script>
                async function loadSystemStatus() {
                    try {
                        const response = await fetch('/api/dashboard/status');
                        const data = await response.json();
                        
                        document.getElementById('systemStatusContent').innerHTML = `
                            <div class="system-status">
                                <h2>系统运行状态</h2>
                                <p>状态: ${data.status}</p>
                                <p>活跃连接: ${data.active_connections}</p>
                                <p>总告警: ${data.total_alerts}</p>
                                <p>活跃Agent: ${data.active_agents}</p>
                                <p>最后更新: ${data.timestamp}</p>
                            </div>
                        `;
                    } catch (error) {
                        document.getElementById('systemStatusContent').innerHTML = `
                            <div class="error">
                                加载系统状态失败: ${error.message}
                            </div>
                        `;
                    }
                }
                
                loadSystemStatus();
            </script>
        </body>
        </html>
        """
    
    async def _handle_websocket(self, websocket: WebSocket):
        """处理WebSocket连接"""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        try:
            while True:
                # 保持连接活跃
                await websocket.receive_text()
        except WebSocketDisconnect:
            self.active_connections.remove(websocket)
    
    async def start(self):
        """启动前端界面"""
        try:
            self.logger.info("正在启动仪表板前端界面...")
            
            # 集成API路由
            self.app.include_router(self.dashboard_api.router)
            
            self.logger.info("仪表板前端界面启动完成")
            
        except Exception as e:
            self.logger.error(f"启动仪表板前端界面失败: {e}")
            raise
    
    async def cleanup(self):
        """清理资源"""
        try:
            self.logger.info("正在清理仪表板前端界面...")
            
            # 关闭所有WebSocket连接
            for connection in self.active_connections:
                await connection.close()
            
            self.active_connections.clear()
            self._cached_data.clear()
            self._last_update.clear()
            
            self.logger.info("仪表板前端界面清理完成")
            
        except Exception as e:
            self.logger.error(f"清理仪表板前端界面失败: {e}")


__all__ = [
    "DashboardUI",
]
