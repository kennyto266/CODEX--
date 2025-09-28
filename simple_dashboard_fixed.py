#!/usr/bin/env python3
"""
港股量化交易 AI Agent 系统 - 简化Web仪表板 (修复版)

这是一个简化的Web仪表板，可以直接启动而不需要复杂的依赖。
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

try:
    from fastapi import FastAPI, Request
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.staticfiles import StaticFiles
    import uvicorn
except ImportError:
    print("缺少FastAPI依赖，请安装:")
    print("pip install fastapi uvicorn")
    exit(1)


# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("simple_dashboard")

# 创建FastAPI应用
app = FastAPI(title="港股量化交易 AI Agent 仪表板", version="1.0.0")

# 模拟Agent数据
AGENTS_DATA = {
    "quant_analyst_001": {
        "agent_id": "quant_analyst_001",
        "agent_type": "量化分析师",
        "status": "running",
        "cpu_usage": 45.0,
        "memory_usage": 55.0,
        "messages_processed": 1500,
        "error_count": 2,
        "uptime_seconds": 7200,
        "version": "1.0.0",
        "configuration": {"param1": "value1"},
        "last_heartbeat": "2024-01-01T12:00:00Z",
        "last_updated": "2024-01-01T12:00:00Z",
        "performance_metrics": {
            "sharpe_ratio": 1.85,
            "total_return": 0.12,
            "max_drawdown": 0.05,
            "win_rate": 0.68,
            "trades_count": 45
        },
        "current_strategy": {
            "name": "动量策略",
            "parameters": {"lookback": 20, "threshold": 0.02},
            "description": "基于价格动量的交易策略"
        }
    },
    "quant_trader_001": {
        "agent_id": "quant_trader_001",
        "agent_type": "量化交易员",
        "status": "running",
        "cpu_usage": 38.0,
        "memory_usage": 42.0,
        "messages_processed": 2300,
        "error_count": 1,
        "uptime_seconds": 6800,
        "version": "1.0.0",
        "configuration": {"param2": "value2"},
        "last_heartbeat": "2024-01-01T12:00:00Z",
        "last_updated": "2024-01-01T12:00:00Z",
        "performance_metrics": {
            "sharpe_ratio": 2.1,
            "total_return": 0.15,
            "max_drawdown": 0.03,
            "win_rate": 0.72,
            "trades_count": 38
        },
        "current_strategy": {
            "name": "均值回归策略",
            "parameters": {"period": 14, "deviation": 2.0},
            "description": "基于统计套利的均值回归策略"
        }
    },
    "risk_analyst_001": {
        "agent_id": "risk_analyst_001",
        "agent_type": "风险分析师",
        "status": "running",
        "cpu_usage": 25.0,
        "memory_usage": 35.0,
        "messages_processed": 800,
        "error_count": 0,
        "uptime_seconds": 7500,
        "version": "1.0.0",
        "configuration": {"param3": "value3"},
        "last_heartbeat": "2024-01-01T12:00:00Z",
        "last_updated": "2024-01-01T12:00:00Z",
        "performance_metrics": {
            "sharpe_ratio": 1.2,
            "total_return": 0.08,
            "max_drawdown": 0.02,
            "win_rate": 0.65,
            "trades_count": 12
        },
        "current_strategy": {
            "name": "风险控制策略",
            "parameters": {"max_position": 0.1, "stop_loss": 0.05},
            "description": "专注于风险管理的保守策略"
        }
    }
}

# Agent ID 别名映射
AGENT_ID_ALIAS = {
    "qa": "quant_analyst_001",
    "qt": "quant_trader_001",
    "ra": "risk_analyst_001"
}


def get_dashboard_html():
    """生成仪表板HTML"""
    return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>港股量化交易 AI Agent 仪表板</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .header {
            background: rgba(255, 255, 255, 0.95);
            padding: 1rem 2rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
        }
        
        .header h1 {
            color: #2c3e50;
            font-size: 1.8rem;
            font-weight: 600;
        }
        
        .container {
            max-width: 1200px;
            margin: 2rem auto;
            padding: 0 1rem;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }
        
        .stat-card {
            background: rgba(255, 255, 255, 0.95);
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
            transition: transform 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
        }
        
        .stat-title {
            font-size: 0.9rem;
            color: #666;
            margin-bottom: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .stat-value {
            font-size: 2rem;
            font-weight: 700;
            color: #2c3e50;
        }
        
        .agents-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 1.5rem;
        }
        
        .agent-card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
            transition: transform 0.3s ease;
        }
        
        .agent-card:hover {
            transform: translateY(-5px);
        }
        
        .agent-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }
        
        .agent-title {
            font-size: 1.2rem;
            font-weight: 600;
            color: #2c3e50;
        }
        
        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 0.5rem;
        }
        
        .status-running { background-color: #27ae60; }
        .status-stopped { background-color: #e74c3c; }
        .status-error { background-color: #f39c12; }
        
        .agent-status {
            display: flex;
            align-items: center;
            font-size: 0.9rem;
            color: #666;
        }
        
        .agent-metrics {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.5rem;
            margin-bottom: 1rem;
        }
        
        .metric-item {
            display: flex;
            justify-content: space-between;
            padding: 0.5rem;
            background: rgba(0,0,0,0.05);
            border-radius: 6px;
        }
        
        .metric-label {
            font-size: 0.8rem;
            color: #666;
        }
        
        .metric-value {
            font-weight: 600;
            color: #2c3e50;
        }
        
        .loading {
            text-align: center;
            padding: 2rem;
            color: #666;
            font-size: 1.1rem;
        }
        
        .error {
            background: rgba(231, 76, 60, 0.1);
            color: #e74c3c;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
            text-align: center;
        }
        
        .btn {
            background: #3498db;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: background 0.3s ease;
        }
        
        .btn:hover {
            background: #2980b9;
        }
        
        .btn-danger {
            background: #e74c3c;
        }
        
        .btn-danger:hover {
            background: #c0392b;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>港股量化交易 AI Agent 仪表板</h1>
    </div>
    
    <div class="container">
        <div class="stats-grid" id="statsGrid">
            <div class="stat-card">
                <div class="stat-title">总Agent数</div>
                <div class="stat-value" id="totalAgents">-</div>
            </div>
            <div class="stat-card">
                <div class="stat-title">运行中</div>
                <div class="stat-value" id="runningAgents">-</div>
            </div>
            <div class="stat-card">
                <div class="stat-title">总交易数</div>
                <div class="stat-value" id="totalTrades">-</div>
            </div>
            <div class="stat-card">
                <div class="stat-title">平均夏普比率</div>
                <div class="stat-value" id="avgSharpe">-</div>
            </div>
        </div>
        
        <div class="agents-grid" id="agentsGrid">
            <div class="loading">
                <i class="fas fa-spinner fa-spin"></i> 加载Agent数据中...
            </div>
        </div>
    </div>
    
    <script>
        class SimpleDashboard {
            constructor() {
                this.init();
            }
            
            init() {
                this.loadAgentData();
                
                // 每30秒自动刷新
                setInterval(() => {
                    this.loadAgentData();
                }, 30000);
            }
            
            async loadAgentData() {
                try {
                    const response = await fetch('/api/agents');
                    const data = await response.json();
                    
                    this.renderAgents(data.agents);
                    this.updateSystemStats(data.agents);
                    
                } catch (error) {
                    console.error('加载数据失败:', error);
                    this.showError('加载数据失败，请刷新页面重试');
                }
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
                
                const performance = agentData.performance_metrics || {};
                const strategy = agentData.current_strategy || {};
                
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
                        
                        ${performance.sharpe_ratio ? `
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
                        ` : ''}
                        
                        ${strategy.name ? `
                        <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid rgba(0,0,0,0.1);">
                            <div style="font-size: 0.9rem; color: #666; margin-bottom: 0.5rem;">当前策略</div>
                            <div style="font-weight: 600; color: #2c3e50;">${strategy.name}</div>
                            <div style="font-size: 0.8rem; color: #666; margin-top: 0.25rem;">${strategy.description || ''}</div>
                        </div>
                        ` : ''}
                        
                        <div style="margin-top: 1rem; display: flex; gap: 0.5rem;">
                            <button class="btn" onclick="dashboard.showAgentDetails('${agentId}')">详情</button>
                            <button class="btn" onclick="dashboard.showStrategyDetails('${agentId}')">策略</button>
                            ${agentData.status === 'running' ? 
                                `<button class="btn btn-danger" onclick="dashboard.controlAgent('${agentId}', 'stop')">停止</button>` :
                                `<button class="btn" onclick="dashboard.controlAgent('${agentId}', 'start')">启动</button>`
                            }
                        </div>
                    </div>
                `;
            }
            
            updateSystemStats(agentsData) {
                const agents = Object.values(agentsData);
                const totalAgents = agents.length;
                const runningAgents = agents.filter(a => a.status === 'running').length;
                const totalTrades = agents.reduce((sum, a) => sum + (a.performance_metrics?.trades_count || 0), 0);
                const avgSharpe = agents.length > 0 ? 
                    agents.reduce((sum, a) => sum + (a.performance_metrics?.sharpe_ratio || 0), 0) / agents.length : 0;
                
                document.getElementById('totalAgents').textContent = totalAgents;
                document.getElementById('runningAgents').textContent = runningAgents;
                document.getElementById('totalTrades').textContent = totalTrades.toLocaleString();
                document.getElementById('avgSharpe').textContent = avgSharpe.toFixed(3);
            }
            
            getStatusText(status) {
                const statusMap = {
                    'running': '运行中',
                    'stopped': '已停止',
                    'error': '错误',
                    'starting': '启动中',
                    'stopping': '停止中'
                };
                return statusMap[status] || status;
            }
            
            getStatusColor(status) {
                const colorMap = {
                    'running': '#27ae60',
                    'stopped': '#e74c3c',
                    'error': '#f39c12',
                    'starting': '#3498db',
                    'stopping': '#9b59b6'
                };
                return colorMap[status] || '#95a5a6';
            }
            
            formatUptime(seconds) {
                const hours = Math.floor(seconds / 3600);
                const minutes = Math.floor((seconds % 3600) / 60);
                return `${hours}h ${minutes}m`;
            }
            
            showError(message) {
                const grid = document.getElementById('agentsGrid');
                grid.innerHTML = `<div class="error">${message}</div>`;
            }
            
            async showAgentDetails(agentId) {
                try {
                    const resp = await fetch(`/api/agents/${agentId}`);
                    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
                    const data = await resp.json();
                    const a = data.agent || {};
                    const info = [
                        `ID: ${a.agent_id || agentId}`,
                        `类型: ${a.agent_type || 'Unknown'}`,
                        `状态: ${a.status || 'Unknown'}`,
                        `版本: ${a.version || 'Unknown'}`,
                        `CPU: ${a.cpu_usage || 0}%`,
                        `内存: ${a.memory_usage || 0}%`,
                        `消息数: ${a.messages_processed || 0}`,
                        `错误数: ${a.error_count || 0}`,
                        `运行时间: ${this.formatUptime(a.uptime_seconds || 0)}`
                    ].join('\\n');
                    alert(info);
                } catch (e) {
                    alert('获取详情失败: ' + e.message);
                }
            }
            
            async showStrategyDetails(agentId) {
                try {
                    const resp = await fetch(`/api/agents/${agentId}`);
                    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
                    const data = await resp.json();
                    const s = (data.agent && data.agent.current_strategy) || {};
                    const perf = (data.agent && data.agent.performance_metrics) || {};
                    const info = [
                        `策略名称: ${s.name || 'Unknown'}`,
                        `描述: ${s.description || 'No description'}`,
                        `参数: ${JSON.stringify(s.parameters || {}, null, 2)}`,
                        `夏普比率: ${perf.sharpe_ratio || 0}`,
                        `总收益: ${((perf.total_return || 0) * 100).toFixed(2)}%`,
                        `最大回撤: ${((perf.max_drawdown || 0) * 100).toFixed(2)}%`,
                        `胜率: ${((perf.win_rate || 0) * 100).toFixed(1)}%`,
                        `交易次数: ${perf.trades_count || 0}`
                    ].join('\\n');
                    alert(info);
                } catch (e) {
                    alert('获取策略详情失败: ' + e.message);
                }
            }
            
            async controlAgent(agentId, action) {
                const actionText = {
                    'start': '启动',
                    'stop': '停止',
                    'restart': '重启'
                };
                try {
                    const resp = await fetch(`/api/agents/${agentId}/control/${action}`, { method: 'POST' });
                    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
                    const data = await resp.json();
                    alert(`${actionText[action]}成功\\nActionId: ${data.action_id || '(demo)'}`);
                    this.loadAgentData();
                } catch (e) {
                    alert(`${actionText[action]}失败: ${e}`);
                }
            }
        }
        
        // 初始化仪表板
        const dashboard = new SimpleDashboard();
    </script>
</body>
</html>
    """


# API路由
@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """主仪表板页面"""
    return HTMLResponse(content=get_dashboard_html())


@app.get("/api/agents")
async def get_agents():
    """获取所有Agent数据（以列表形式返回，便于统计）"""
    agents_list = []
    for aid, a in AGENTS_DATA.items():
        item = a.copy()
        item["agent_id"] = aid
        agents_list.append(item)
    return JSONResponse(content={"agents": agents_list, "total": len(agents_list)})


@app.get("/api/agents/{agent_id}")
async def get_agent(agent_id: str):
    """获取特定Agent数据"""
    if agent_id not in AGENTS_DATA:
        return JSONResponse(content={"error": "Agent not found"}, status_code=404)
    
    return JSONResponse(content={"agent": AGENTS_DATA[agent_id]})


@app.post("/api/agents/{agent_id}/control/{action}")
async def control_agent(agent_id: str, action: str):
    """控制Agent操作"""
    if agent_id not in AGENTS_DATA:
        return JSONResponse(content={"error": "Agent not found"}, status_code=404)
    
    if action == "start":
        AGENTS_DATA[agent_id]["status"] = "running"
    elif action == "stop":
        AGENTS_DATA[agent_id]["status"] = "stopped"
    elif action == "restart":
        AGENTS_DATA[agent_id]["status"] = "running"
        AGENTS_DATA[agent_id]["uptime_seconds"] = 0
    else:
        return JSONResponse(content={"error": "Invalid action"}, status_code=400)
    
    return JSONResponse(content={"status": "success", "action_id": f"demo_{action}_{agent_id}"})


@app.get("/api/status")
async def system_status():
    """系统状态"""
    return JSONResponse(content={
        "system_name": "HK Quant",
        "version": "1.0.0",
        "environment": "local",
        "status": "running",
        "start_time": datetime.now().isoformat(),
        "uptime": 1234,
        "components": {"total": len(AGENTS_DATA), "running": len(AGENTS_DATA), "stopped": 0, "error": 0}
    })


def main():
    """启动Web服务器"""
    try:
        print("HK Quant AI Agent Dashboard")
        print("Web Server Starting...")
        print("Dashboard: http://localhost:8000")
        print("API Status: http://localhost:8000/api/status")
        print("Performance: http://localhost:8000/api/performance")
        print("Press Ctrl+C to stop")
        print("=" * 60)
    except UnicodeEncodeError:
        print("HK Quant AI Agent Dashboard")
        print("Web Server Starting...")
        print("Dashboard: http://localhost:8000")
        print("API Status: http://localhost:8000/api/status")
        print("Performance: http://localhost:8000/api/performance")
        print("Press Ctrl+C to stop")
        print("=" * 60)
    
    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n服务已停止")
    except Exception as e:
        print(f"启动失败: {e}")


if __name__ == "__main__":
    main()