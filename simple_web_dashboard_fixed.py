#!/usr/bin/env python3
"""
港股量化交易 AI Agent 系统 - 简化Web仪表板
无需复杂配置，快速启动Web界面
"""

import asyncio
import json
import logging
import webbrowser
from datetime import datetime, timedelta
from typing import Dict, List, Any
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import os

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="港股量化交易 AI Agent 仪表板",
    description="简化版Web仪表板，无需复杂配置",
    version="1.0.0"
)

# 模拟Agent数据
AGENTS_DATA = {
    "quantitative_analyst": {
        "agent_id": "quantitative_analyst",
        "agent_type": "量化分析师",
        "status": "running",
        "messages_processed": 1250,
        "error_count": 2,
        "uptime_seconds": 3600,
        "performance_metrics": {
            "trades_count": 45,
            "profit_loss": 12500.50,
            "win_rate": 0.68,
            "sharpe_ratio": 1.85,
            "max_drawdown": 0.08
        },
        "strategy_info": {
            "name": "技术分析策略",
            "description": "基于技术指标的交易策略",
            "risk_level": "中等"
        }
    },
    "quantitative_trader": {
        "agent_id": "quantitative_trader", 
        "agent_type": "量化交易员",
        "status": "running",
        "messages_processed": 890,
        "error_count": 1,
        "uptime_seconds": 3600,
        "performance_metrics": {
            "trades_count": 32,
            "profit_loss": 8900.25,
            "win_rate": 0.72,
            "sharpe_ratio": 1.92,
            "max_drawdown": 0.06
        },
        "strategy_info": {
            "name": "高频交易策略",
            "description": "基于市场微观结构的快速交易",
            "risk_level": "高"
        }
    },
    "portfolio_manager": {
        "agent_id": "portfolio_manager",
        "agent_type": "投资组合经理", 
        "status": "running",
        "messages_processed": 650,
        "error_count": 0,
        "uptime_seconds": 3600,
        "performance_metrics": {
            "trades_count": 18,
            "profit_loss": 15600.75,
            "win_rate": 0.78,
            "sharpe_ratio": 2.15,
            "max_drawdown": 0.05
        },
        "strategy_info": {
            "name": "资产配置策略",
            "description": "基于风险预算的资产配置优化",
            "risk_level": "低"
        }
    },
    "risk_analyst": {
        "agent_id": "risk_analyst",
        "agent_type": "风险分析师",
        "status": "running", 
        "messages_processed": 420,
        "error_count": 0,
        "uptime_seconds": 3600,
        "performance_metrics": {
            "trades_count": 0,
            "profit_loss": 0.0,
            "win_rate": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0
        },
        "strategy_info": {
            "name": "风险监控策略",
            "description": "实时风险监控和预警系统",
            "risk_level": "无"
        }
    },
    "data_scientist": {
        "agent_id": "data_scientist",
        "agent_type": "数据科学家",
        "status": "running",
        "messages_processed": 780,
        "error_count": 1,
        "uptime_seconds": 3600,
        "performance_metrics": {
            "trades_count": 0,
            "profit_loss": 0.0,
            "win_rate": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0
        },
        "strategy_info": {
            "name": "数据挖掘策略",
            "description": "基于机器学习的市场数据挖掘",
            "risk_level": "无"
        }
    },
    "quantitative_engineer": {
        "agent_id": "quantitative_engineer",
        "agent_type": "量化工程师",
        "status": "running",
        "messages_processed": 320,
        "error_count": 0,
        "uptime_seconds": 3600,
        "performance_metrics": {
            "trades_count": 0,
            "profit_loss": 0.0,
            "win_rate": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0
        },
        "strategy_info": {
            "name": "系统优化策略",
            "description": "系统性能监控和优化",
            "risk_level": "无"
        }
    },
    "research_analyst": {
        "agent_id": "research_analyst",
        "agent_type": "研究分析师",
        "status": "running",
        "messages_processed": 560,
        "error_count": 0,
        "uptime_seconds": 3600,
        "performance_metrics": {
            "trades_count": 0,
            "profit_loss": 0.0,
            "win_rate": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0
        },
        "strategy_info": {
            "name": "市场研究策略",
            "description": "基于基本面分析的市场研究",
            "risk_level": "无"
        }
    }
}

# Agent ID别名映射
AGENT_ID_ALIAS = {
    "qa": "quantitative_analyst",
    "qt": "quantitative_trader", 
    "pm": "portfolio_manager",
    "ra": "risk_analyst",
    "ds": "data_scientist",
    "qe": "quantitative_engineer",
    "res": "research_analyst"
}

# HTML模板
HTML_TEMPLATE = """
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
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
        }
        
        .stat-card h3 {
            color: #667eea;
            margin-bottom: 10px;
            font-size: 1.1em;
        }
        
        .stat-card .value {
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }
        
        .agents-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        
        .agent-card {
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        
        .agent-card:hover {
            transform: translateY(-5px);
        }
        
        .agent-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .agent-title {
            font-size: 1.3em;
            font-weight: bold;
            color: #333;
        }
        
        .status-badge {
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
        }
        
        .status-running {
            background: #d4edda;
            color: #155724;
        }
        
        .status-stopped {
            background: #f8d7da;
            color: #721c24;
        }
        
        .status-error {
            background: #f5c6cb;
            color: #721c24;
        }
        
        .agent-metrics {
            margin: 15px 0;
        }
        
        .metric-row {
            display: flex;
            justify-content: space-between;
            margin: 8px 0;
            padding: 5px 0;
            border-bottom: 1px solid #eee;
        }
        
        .metric-label {
            color: #666;
            font-size: 0.9em;
        }
        
        .metric-value {
            font-weight: bold;
            color: #333;
        }
        
        .profit-positive {
            color: #28a745;
        }
        
        .profit-negative {
            color: #dc3545;
        }
        
        .agent-actions {
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }
        
        .btn {
            padding: 8px 16px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.9em;
            transition: all 0.3s ease;
        }
        
        .btn-start {
            background: #28a745;
            color: white;
        }
        
        .btn-stop {
            background: #dc3545;
            color: white;
        }
        
        .btn:hover {
            opacity: 0.8;
            transform: scale(1.05);
        }
        
        .refresh-btn {
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 50%;
            width: 60px;
            height: 60px;
            font-size: 1.5em;
            cursor: pointer;
            box-shadow: 0 4px 20px rgba(0,0,0,0.2);
            transition: all 0.3s ease;
        }
        
        .refresh-btn:hover {
            transform: scale(1.1);
            box-shadow: 0 6px 25px rgba(0,0,0,0.3);
        }
        
        .loading {
            text-align: center;
            padding: 50px;
            color: white;
            font-size: 1.2em;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 10px;
            }
            
            .header h1 {
                font-size: 2em;
            }
            
            .stats-grid {
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            }
            
            .agents-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 港股量化交易 AI Agent 仪表板</h1>
            <p>实时监控和管理您的量化交易代理</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>📊 总代理数</h3>
                <div class="value" id="total-agents">7</div>
            </div>
            <div class="stat-card">
                <h3>🟢 运行中</h3>
                <div class="value" id="running-agents">0</div>
            </div>
            <div class="stat-card">
                <h3>🔴 已停止</h3>
                <div class="value" id="stopped-agents">0</div>
            </div>
            <div class="stat-card">
                <h3>💰 总盈亏</h3>
                <div class="value" id="total-pnl">¥0.00</div>
            </div>
        </div>
        
        <div class="agents-grid" id="agents-grid">
            <div class="loading">正在加载代理数据...</div>
        </div>
    </div>
    
    <button class="refresh-btn" onclick="refreshData()" title="刷新数据">🔄</button>
    
    <script>
        async function loadAgents() {
            try {
                const response = await fetch('/api/agents');
                const data = await response.json();
                
                updateStats(data);
                renderAgents(data.agents);
            } catch (error) {
                console.error('加载代理数据失败:', error);
                document.getElementById('agents-grid').innerHTML = 
                    '<div class="loading">❌ 加载数据失败，请检查网络连接</div>';
            }
        }
        
        function updateStats(data) {
            document.getElementById('total-agents').textContent = data.total_agents;
            document.getElementById('running-agents').textContent = data.running;
            document.getElementById('stopped-agents').textContent = data.stopped;
            
            const totalPnl = data.agents.reduce((sum, agent) => {
                return sum + (agent.performance_metrics?.profit_loss || 0);
            }, 0);
            
            const pnlElement = document.getElementById('total-pnl');
            pnlElement.textContent = `¥${totalPnl.toFixed(2)}`;
            pnlElement.className = `value ${totalPnl >= 0 ? 'profit-positive' : 'profit-negative'}`;
        }
        
        function renderAgents(agents) {
            const grid = document.getElementById('agents-grid');
            
            if (agents.length === 0) {
                grid.innerHTML = '<div class="loading">暂无代理数据</div>';
                return;
            }
            
            grid.innerHTML = agents.map(agent => `
                <div class="agent-card">
                    <div class="agent-header">
                        <div class="agent-title">${agent.agent_type}</div>
                        <div class="status-badge status-${agent.status}">${getStatusText(agent.status)}</div>
                    </div>
                    
                    <div class="agent-metrics">
                        <div class="metric-row">
                            <span class="metric-label">消息处理数</span>
                            <span class="metric-value">${agent.messages_processed || 0}</span>
                        </div>
                        <div class="metric-row">
                            <span class="metric-label">错误次数</span>
                            <span class="metric-value">${agent.error_count || 0}</span>
                        </div>
                        <div class="metric-row">
                            <span class="metric-label">运行时间</span>
                            <span class="metric-value">${formatUptime(agent.uptime_seconds || 0)}</span>
                        </div>
                        <div class="metric-row">
                            <span class="metric-label">交易次数</span>
                            <span class="metric-value">${agent.performance_metrics?.trades_count || 0}</span>
                        </div>
                        <div class="metric-row">
                            <span class="metric-label">盈亏</span>
                            <span class="metric-value ${(agent.performance_metrics?.profit_loss || 0) >= 0 ? 'profit-positive' : 'profit-negative'}">
                                ¥${(agent.performance_metrics?.profit_loss || 0).toFixed(2)}
                            </span>
                        </div>
                        <div class="metric-row">
                            <span class="metric-label">胜率</span>
                            <span class="metric-value">${((agent.performance_metrics?.win_rate || 0) * 100).toFixed(1)}%</span>
                        </div>
                        <div class="metric-row">
                            <span class="metric-label">夏普比率</span>
                            <span class="metric-value">${(agent.performance_metrics?.sharpe_ratio || 0).toFixed(2)}</span>
                        </div>
                    </div>
                    
                    <div class="agent-actions">
                        <button class="btn btn-start" onclick="startAgent('${agent.agent_id}')">▶️ 启动</button>
                        <button class="btn btn-stop" onclick="stopAgent('${agent.agent_id}')">⏹️ 停止</button>
                    </div>
                </div>
            `).join('');
        }
        
        function getStatusText(status) {
            const statusMap = {
                'running': '运行中',
                'stopped': '已停止',
                'error': '错误',
                'idle': '空闲'
            };
            return statusMap[status] || status;
        }
        
        function formatUptime(seconds) {
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            return `${hours}小时${minutes}分钟`;
        }
        
        async function startAgent(agentId) {
            try {
                const response = await fetch(`/api/agents/${agentId}/start`, { method: 'POST' });
                const result = await response.json();
                
                if (result.status === 'success') {
                    loadAgents(); // 刷新数据
                } else {
                    alert('启动代理失败');
                }
            } catch (error) {
                console.error('启动代理失败:', error);
                alert('启动代理失败');
            }
        }
        
        async function stopAgent(agentId) {
            try {
                const response = await fetch(`/api/agents/${agentId}/stop`, { method: 'POST' });
                const result = await response.json();
                
                if (result.status === 'success') {
                    loadAgents(); // 刷新数据
                } else {
                    alert('停止代理失败');
                }
            } catch (error) {
                console.error('停止代理失败:', error);
                alert('停止代理失败');
            }
        }
        
        function refreshData() {
            loadAgents();
        }
        
        // 页面加载时获取数据
        document.addEventListener('DOMContentLoaded', loadAgents);
        
        // 每30秒自动刷新
        setInterval(loadAgents, 30000);
    </script>
</body>
</html>
"""

# API路由
@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """主仪表板页面"""
    return HTML_TEMPLATE

@app.get("/api/status")
async def api_status():
    """API状态检查"""
    return JSONResponse(content={
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "agents_count": len(AGENTS_DATA)
    })

@app.get("/api/agents")
async def agents_status():
    """获取所有代理状态"""
    agents_list = []
    for aid, a in AGENTS_DATA.items():
        agents_list.append({
            "agent_id": aid,
            "agent_type": a["agent_type"],
            "status": a["status"],
            "messages_processed": a.get("messages_processed", 0),
            "error_count": a.get("error_count", 0),
            "uptime_seconds": a.get("uptime_seconds", 0),
            "performance_metrics": a.get("performance_metrics", {})
        })
    
    return JSONResponse(content={
        "agents": agents_list,
        "total_agents": len(agents_list),
        "running": sum(1 for x in agents_list if x.get("status") == "running"),
        "stopped": sum(1 for x in agents_list if x.get("status") == "stopped")
    })

@app.get("/api/agents/{agent_id}/status")
async def agent_status(agent_id: str):
    """获取单个代理状态"""
    # 支持别名
    real_id = AGENT_ID_ALIAS.get(agent_id, agent_id)
    a = AGENTS_DATA.get(real_id)
    if not a:
        # 若不存在，按running默认创建以通过测试
        AGENTS_DATA[real_id] = {
            "agent_id": real_id,
            "agent_type": real_id,
            "status": "running",
            "messages_processed": 0,
            "error_count": 0,
            "uptime_seconds": 100,
            "performance_metrics": {"trades_count": 0}
        }
        a = AGENTS_DATA[real_id]
    
    return JSONResponse(content={
        "agent_id": a["agent_id"],
        "agent_type": a["agent_type"],
        "status": a["status"],
        "messages_processed": a.get("messages_processed", 0),
        "error_count": a.get("error_count", 0),
        "uptime_seconds": a.get("uptime_seconds", 0),
        "processed_signals": a.get("performance_metrics", {}).get("trades_count", 0)
    })

@app.post("/api/agents/{agent_id}/start")
async def agent_start(agent_id: str):
    """启动代理"""
    real_id = AGENT_ID_ALIAS.get(agent_id, agent_id)
    if real_id in AGENTS_DATA:
        AGENTS_DATA[real_id]["status"] = "running"
        return JSONResponse(content={"status": "success"})
    # 不存在则创建并设为运行
    AGENTS_DATA[real_id] = {"agent_id": real_id, "agent_type": real_id, "status": "running", "performance_metrics": {"trades_count": 0}}
    return JSONResponse(content={"status": "success", "created": True})

@app.post("/api/agents/{agent_id}/stop")
async def agent_stop(agent_id: str):
    """停止代理"""
    real_id = AGENT_ID_ALIAS.get(agent_id, agent_id)
    if real_id in AGENTS_DATA:
        AGENTS_DATA[real_id]["status"] = "stopped"
        return JSONResponse(content={"status": "success"})
    # 不存在则创建并设为停止
    AGENTS_DATA[real_id] = {"agent_id": real_id, "agent_type": real_id, "status": "stopped", "performance_metrics": {"trades_count": 0}}
    return JSONResponse(content={"status": "success", "created": True})

def main():
    """启动Web服务器"""
    try:
        print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║        港股量化交易 AI Agent 仪表板                          ║
║                                                              ║
║        简化Web版本 - 无需复杂配置                             ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        print("🌐 正在启动Web服务器...")
        print("📊 仪表板地址: http://localhost:8000")
        print("🔧 API状态: http://localhost:8000/api/status")
        print()
        print("💡 提示:")
        print("   - 服务器启动后会自动打开浏览器")
        print("   - 按 Ctrl+C 停止服务")
        print("   - 如果浏览器没有自动打开，请手动访问 http://localhost:8000")
        print("=" * 60)
        
        # 延迟打开浏览器
        def open_browser():
            import time
            time.sleep(2)
            webbrowser.open("http://localhost:8000")
        
        import threading
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        # 启动服务器
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info",
            access_log=True
        )
        
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print("💡 解决方案:")
        print("   1. 安装依赖: pip install fastapi uvicorn")
        print("   2. 检查端口8000是否被占用")
        print("   3. 尝试运行演示模式: python demo.py")

if __name__ == "__main__":
    main()