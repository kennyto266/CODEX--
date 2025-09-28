"""
HTML生成器
生成Dashboard的HTML内容
"""

from typing import List, Dict, Any
from datetime import datetime

class HTMLGenerator:
    """HTML生成器"""
    
    def generate_dashboard_html(self, agent_results: List[Dict[str, Any]]) -> str:
        """
        生成Dashboard HTML
        
        Args:
            agent_results: 代理分析结果
            
        Returns:
            HTML字符串
        """
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>港股AI代理系统 Dashboard</title>
    <style>
        {self._get_css_styles()}
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <h1>🚀 港股AI代理系统 Dashboard</h1>
            <p class="subtitle">实时AI代理分析结果展示</p>
            <div class="status-bar">
                <span class="status-item">📊 总代理数: {len(agent_results)}</span>
                <span class="status-item">✅ 已完成: {len([r for r in agent_results if r.get('status', {}).get('status') == 'completed'])}</span>
                <span class="status-item">⏰ 更新时间: {datetime.now().strftime('%H:%M:%S')}</span>
            </div>
        </header>
        
        <main class="main-content">
            {self._generate_agents_section(agent_results)}
            {self._generate_summary_section(agent_results)}
        </main>
        
        <footer class="footer">
            <p>港股AI代理系统 v1.0 | 基于Cursor API | 实时更新</p>
        </footer>
    </div>
    
    <script>
        {self._get_javascript()}
    </script>
</body>
</html>
"""
        return html
    
    def _get_css_styles(self) -> str:
        """获取CSS样式"""
        return """
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
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            background: rgba(255, 255, 255, 0.95);
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            background: linear-gradient(45deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .subtitle {
            font-size: 1.2em;
            color: #666;
            margin-bottom: 20px;
        }
        
        .status-bar {
            display: flex;
            justify-content: center;
            gap: 30px;
            flex-wrap: wrap;
        }
        
        .status-item {
            background: #f8f9fa;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: 500;
            color: #495057;
        }
        
        .main-content {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }
        
        .agents-section {
            background: rgba(255, 255, 255, 0.95);
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }
        
        .agents-section h2 {
            margin-bottom: 20px;
            color: #495057;
            font-size: 1.5em;
        }
        
        .agents-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        
        .agent-card {
            background: #f8f9fa;
            border: 2px solid #e9ecef;
            border-radius: 10px;
            padding: 20px;
            transition: all 0.3s ease;
        }
        
        .agent-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
            border-color: #667eea;
        }
        
        .agent-header {
            display: flex;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .agent-icon {
            font-size: 2em;
            margin-right: 15px;
        }
        
        .agent-name {
            font-size: 1.2em;
            font-weight: 600;
            color: #495057;
        }
        
        .agent-status {
            margin-left: auto;
            padding: 4px 12px;
            border-radius: 15px;
            font-size: 0.9em;
            font-weight: 500;
        }
        
        .status-running {
            background: #d4edda;
            color: #155724;
        }
        
        .status-completed {
            background: #d1ecf1;
            color: #0c5460;
        }
        
        .status-error {
            background: #f8d7da;
            color: #721c24;
        }
        
        .agent-content {
            color: #6c757d;
            line-height: 1.6;
        }
        .content-box {
            white-space: pre-wrap;
            background: #ffffff;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 12px;
            max-height: 300px;
            overflow: auto;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
        }
        
        .summary-section {
            background: rgba(255, 255, 255, 0.95);
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }
        
        .summary-section h2 {
            margin-bottom: 20px;
            color: #495057;
            font-size: 1.5em;
        }
        
        .summary-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid #e9ecef;
        }
        
        .summary-item:last-child {
            border-bottom: none;
        }
        
        .summary-label {
            font-weight: 500;
            color: #495057;
        }
        
        .summary-value {
            font-weight: 600;
            color: #667eea;
        }
        
        .footer {
            text-align: center;
            color: rgba(255, 255, 255, 0.8);
            font-size: 0.9em;
        }
        
        .refresh-btn {
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 50px;
            padding: 15px 25px;
            font-size: 1em;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            transition: all 0.3s ease;
        }
        
        .refresh-btn:hover {
            background: #5a6fd8;
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        }
        
        @media (max-width: 768px) {
            .main-content {
                grid-template-columns: 1fr;
            }
            
            .status-bar {
                flex-direction: column;
                gap: 10px;
            }
            
            .agents-grid {
                grid-template-columns: 1fr;
            }
        }
        """
    
    def _generate_agents_section(self, agent_results: List[Dict[str, Any]]) -> str:
        """生成代理部分HTML"""
        if not agent_results:
            return """
            <div class="agents-section">
                <h2>🤖 AI代理分析结果</h2>
                <p>暂无代理分析结果，请等待代理完成分析...</p>
            </div>
            """
        
        agents_html = ""
        for result in agent_results:
            agent_name = result.get('agent_name', '未知代理')
            agent_icon = result.get('agent_icon', '🤖')
            agent_id = result.get('agent_id', 'N/A')
            status = result.get('status', {})
            conversation = result.get('conversation', {})
            
            status_text = status.get('status', 'unknown')
            status_class = f"status-{status_text.lower()}"
            
            # 获取对话内容：优先展示最新的assistant回复；若没有，则提示仍在分析并展示最近的用户指令摘要
            messages = conversation.get('messages', [])
            content = "暂无分析内容"
            if messages:
                # 找到最新的assistant消息
                assistant_text = None
                for msg in reversed(messages):
                    if isinstance(msg, dict) and msg.get('type') == 'assistant_message':
                        assistant_text = msg.get('text') or msg.get('content')
                        if assistant_text:
                            break
                if assistant_text:
                    content = assistant_text
                else:
                    # 没有assistant输出，展示用户最近一次指令的摘要，并提示正在分析
                    user_text = None
                    for msg in reversed(messages):
                        if isinstance(msg, dict) and msg.get('type') == 'user_message':
                            user_text = msg.get('text') or msg.get('content')
                            if user_text:
                                break
                    preview = (user_text or "(无)")
                    if len(preview) > 300:
                        preview = preview[:300] + "..."
                    content = "正在分析中，請稍後自動刷新查看AI回覆...\n\n最近一次指令:\n" + preview
            
            # 不截断内容，显示完整分析结果
            # if len(content) > 1200:
            #     content = content[:1200] + "\n... (内容过长，已截断)"
            
            agents_html += f"""
            <div class="agent-card">
                <div class="agent-header">
                    <span class="agent-icon">{agent_icon}</span>
                    <span class="agent-name">{agent_name}</span>
                    <span class="agent-status {status_class}">{status_text.upper()}</span>
                </div>
                <div class="agent-content">
                    <p><strong>代理ID:</strong> {agent_id}</p>
                    <p><strong>分析内容:</strong></p>
                    <pre class="content-box">{content}</pre>
                </div>
            </div>
            """
        
        return f"""
        <div class="agents-section">
            <h2>🤖 AI代理分析结果</h2>
            <div class="agents-grid">
                {agents_html}
            </div>
        </div>
        """
    
    def _generate_summary_section(self, agent_results: List[Dict[str, Any]]) -> str:
        """生成摘要部分HTML"""
        total_agents = len(agent_results)
        completed_agents = len([r for r in agent_results if str(r.get('status', {}).get('status', '')).lower() in ['completed', 'finished']])
        running_agents = len([r for r in agent_results if str(r.get('status', {}).get('status', '')).lower() in ['running', 'in_progress']])
        error_agents = total_agents - completed_agents - running_agents
        completion_rate = 0.0 if total_agents == 0 else (completed_agents/total_agents*100)
        
        return f"""
        <div class="summary-section">
            <h2>📊 系统摘要</h2>
            <div class="summary-item">
                <span class="summary-label">总代理数</span>
                <span class="summary-value">{total_agents}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">已完成</span>
                <span class="summary-value">{completed_agents}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">运行中</span>
                <span class="summary-value">{running_agents}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">错误</span>
                <span class="summary-value">{error_agents}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">完成率</span>
                <span class="summary-value">{completion_rate:.1f}%</span>
            </div>
        </div>
        """
    
    def _get_javascript(self) -> str:
        """获取JavaScript代码"""
        return """
        // 自动刷新功能
        function autoRefresh() {
            setTimeout(() => {
                location.reload();
            }, 30000); // 30秒刷新一次
        }
        
        // 手动刷新功能
        function manualRefresh() {
            location.reload();
        }
        
        // 添加刷新按钮
        function addRefreshButton() {
            const refreshBtn = document.createElement('button');
            refreshBtn.className = 'refresh-btn';
            refreshBtn.innerHTML = '🔄 刷新';
            refreshBtn.onclick = manualRefresh;
            document.body.appendChild(refreshBtn);
        }
        
        // 页面加载完成后执行
        document.addEventListener('DOMContentLoaded', function() {
            addRefreshButton();
            autoRefresh();
        });
        """