"""
安全監控儀表板
提供實時安全狀態可視化
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict, Counter

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

router = APIRouter()


class SecurityMetrics:
    """安全指標收集器"""

    def __init__(self):
        self.events = []
        self.attack_counts = Counter()
        self.blocked_ips = set()
        self.rate_limit_violations = 0
        self.ddos_attacks = 0
        self.waf_blocks = 0

    def add_event(self, event: Dict):
        """添加安全事件"""
        event['timestamp'] = datetime.now()
        self.events.append(event)
        self.attack_counts[event.get('type', 'unknown')] += 1

        if event.get('blocked'):
            self.blocked_ips.add(event.get('ip'))

    def get_metrics(self) -> Dict:
        """獲取指標"""
        now = datetime.now()
        last_24h = now - timedelta(hours=24)
        recent_events = [e for e in self.events if e['timestamp'] > last_24h]

        return {
            "total_events": len(self.events),
            "recent_events": len(recent_events),
            "attack_distribution": dict(self.attack_counts),
            "blocked_ips_count": len(self.blocked_ips),
            "rate_limit_violations": self.rate_limit_violations,
            "ddos_attacks": self.ddos_attacks,
            "waf_blocks": self.waf_blocks,
        }


# 全局指標實例
metrics = SecurityMetrics()


@router.get("/security/metrics", tags=["Security"])
async def get_security_metrics():
    """獲取安全指標"""
    return metrics.get_metrics()


@router.get("/security/dashboard", response_class=HTMLResponse, tags=["Security"])
async def security_dashboard():
    """安全監控儀表板HTML"""
    html = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>安全監控儀表板</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft JhengHei', sans-serif;
            background: #f5f7fa;
            color: #333;
            min-height: 100vh;
            padding: 20px;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .header h1 {
            font-size: 2em;
            margin-bottom: 10px;
        }
        .header p {
            opacity: 0.9;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .metric-card {
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid #667eea;
        }
        .metric-card h3 {
            color: #666;
            font-size: 0.9em;
            margin-bottom: 10px;
            text-transform: uppercase;
        }
        .metric-card .value {
            font-size: 2.5em;
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }
        .metric-card .change {
            font-size: 0.8em;
            color: #999;
        }
        .metric-card.danger { border-left-color: #e74c3c; }
        .metric-card.warning { border-left-color: #f39c12; }
        .metric-card.success { border-left-color: #27ae60; }
        .metric-card.info { border-left-color: #3498db; }

        .chart-container {
            background: white;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .chart-title {
            font-size: 1.2em;
            font-weight: bold;
            margin-bottom: 20px;
            color: #333;
        }
        .chart {
            height: 300px;
            display: flex;
            align-items: flex-end;
            gap: 10px;
        }
        .chart-bar {
            flex: 1;
            background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
            border-radius: 4px 4px 0 0;
            position: relative;
            transition: all 0.3s;
        }
        .chart-bar:hover {
            opacity: 0.8;
            transform: translateY(-5px);
        }
        .chart-bar-label {
            position: absolute;
            bottom: -25px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 0.8em;
            color: #666;
            white-space: nowrap;
        }
        .chart-bar-value {
            position: absolute;
            top: -25px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 0.9em;
            font-weight: bold;
            color: #333;
        }

        .events-table {
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .events-table table {
            width: 100%;
            border-collapse: collapse;
        }
        .events-table th {
            background: #667eea;
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }
        .events-table td {
            padding: 12px 15px;
            border-bottom: 1px solid #eee;
        }
        .events-table tr:hover {
            background: #f8f9fa;
        }
        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: 600;
        }
        .status-badge.blocked {
            background: #fee;
            color: #e74c3c;
        }
        .status-badge.allowed {
            background: #efe;
            color: #27ae60;
        }
        .severity-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: 600;
        }
        .severity-badge.critical { background: #fce4e4; color: #c0392b; }
        .severity-badge.high { background: #fde2e2; color: #e74c3c; }
        .severity-badge.medium { background: #fff4e5; color: #f39c12; }
        .severity-badge.low { background: #e8f4f8; color: #3498db; }

        .actions {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            font-size: 0.9em;
            cursor: pointer;
            transition: all 0.3s;
        }
        .btn-primary {
            background: #667eea;
            color: white;
        }
        .btn-primary:hover {
            background: #5568d3;
        }
        .btn-danger {
            background: #e74c3c;
            color: white;
        }
        .btn-danger:hover {
            background: #c0392b;
        }
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="header">
        <h1>🛡️ 安全監控儀表板</h1>
        <p>實時監控API安全狀態和威脅防護</p>
    </div>

    <div class="metrics-grid">
        <div class="metric-card danger">
            <h3>🚨 總攻擊次數</h3>
            <div class="value" id="total-attacks">0</div>
            <div class="change">過去24小時</div>
        </div>
        <div class="metric-card warning">
            <h3>🚫 被封鎖IP</h3>
            <div class="value" id="blocked-ips">0</div>
            <div class="change">正在封鎖</div>
        </div>
        <div class="metric-card info">
            <h3>⚡ 速率限制</h3>
            <div class="value" id="rate-limits">0</div>
            <div class="change">違規次數</div>
        </div>
        <div class="metric-card danger">
            <h3>🔥 DDoS攻擊</h3>
            <div class="value" id="ddos-attacks">0</div>
            <div class="change">檢測到</div>
        </div>
    </div>

    <div class="chart-container">
        <div class="chart-title">攻擊類型分佈</div>
        <canvas id="attackChart" width="400" height="200"></canvas>
    </div>

    <div class="events-table">
        <table>
            <thead>
                <tr>
                    <th>時間</th>
                    <th>IP地址</th>
                    <th>攻擊類型</th>
                    <th>路徑</th>
                    <th>嚴重程度</th>
                    <th>狀態</th>
                </tr>
            </thead>
            <tbody id="events-tbody">
                <tr>
                    <td colspan="6" style="text-align: center; color: #999;">正在加載...</td>
                </tr>
            </tbody>
        </table>
    </div>

    <script>
        // 初始化圖表
        const attackChart = new Chart(document.getElementById('attackChart'), {
            type: 'doughnut',
            data: {
                labels: ['SQL注入', 'XSS', 'DDoS', '路徑穿越', '其他'],
                datasets: [{
                    data: [0, 0, 0, 0, 0],
                    backgroundColor: [
                        '#e74c3c',
                        '#f39c12',
                        '#3498db',
                        '#9b59b6',
                        '#95a5a6'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                    }
                }
            }
        });

        // 定期更新數據
        async function updateDashboard() {
            try {
                const response = await fetch('/api/security/dashboard');
                const data = await response.json();

                // 更新指標
                document.getElementById('total-attacks').textContent = data.summary.total_attacks;
                document.getElementById('blocked-ips').textContent = data.blocked_ips_count;
                document.getElementById('rate-limits').textContent = data.rate_limit_violations || 0;
                document.getElementById('ddos-attacks').textContent = data.ddos_attacks || 0;

                // 更新圖表
                const attackData = data.attack_distribution;
                attackChart.data.datasets[0].data = [
                    attackData.sql_injection || 0,
                    attackData.xss || 0,
                    attackData.ddos || 0,
                    attackData.path_traversal || 0,
                    attackData.other || 0
                ];
                attackChart.update();

            } catch (error) {
                console.error('Failed to update dashboard:', error);
            }
        }

        // 初始加載
        updateDashboard();

        // 每30秒更新一次
        setInterval(updateDashboard, 30000);
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html)


@router.get("/security/events/recent", tags=["Security"])
async def get_recent_security_events(limit: int = 50):
    """獲取最近安全事件"""
    now = datetime.now()
    cutoff = now - timedelta(hours=24)
    recent = [e for e in metrics.events if e['timestamp'] > cutoff]

    # 轉換為可序列化的格式
    serializable_events = []
    for event in recent[-limit:]:
        serializable_events.append({
            'timestamp': event['timestamp'].isoformat(),
            'ip': event.get('ip', 'unknown'),
            'type': event.get('type', 'unknown'),
            'path': event.get('path', ''),
            'severity': event.get('severity', 0),
            'blocked': event.get('blocked', False),
        })

    return {
        "events": serializable_events,
        "count": len(serializable_events)
    }


@router.post("/security/test/attack", tags=["Security"])
async def simulate_attack(request: Request):
    """模擬攻擊用於測試"""
    data = await request.json()
    attack_type = data.get('type', 'sql_injection')

    # 創建模擬攻擊事件
    event = {
        'timestamp': datetime.now(),
        'ip': '192.168.1.100',
        'type': attack_type,
        'path': '/api/test',
        'severity': 8,
        'blocked': True,
        'signature': f'test_{attack_type}'
    }

    metrics.add_event(event)

    return {
        "status": "success",
        "message": f"Simulated {attack_type} attack",
        "event": event
    }


@router.get("/security/status", tags=["Security"])
async def get_security_status():
    """獲取安全系統狀態"""
    return {
        "status": "active",
        "uptime": "N/A",
        "version": "1.0.0",
        "components": {
            "api_security": "enabled",
            "waf": "enabled",
            "ddos_protection": "enabled",
            "ip_reputation": "enabled",
            "rate_limiting": "enabled",
            "input_validation": "enabled",
        },
        "last_update": datetime.now().isoformat()
    }
