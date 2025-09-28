"""
Web服务器模块
提供Dashboard的Web服务
"""

import asyncio
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import threading

logger = logging.getLogger(__name__)

class DashboardHandler(BaseHTTPRequestHandler):
    """Dashboard HTTP处理器"""
    
    def __init__(self, *args, dashboard_server=None, **kwargs):
        self.dashboard_server = dashboard_server
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """处理GET请求"""
        if self.path == '/' or self.path == '/index.html':
            self._serve_dashboard()
        elif self.path == '/api/agents':
            self._serve_agents_api()
        elif self.path == '/api/status':
            self._serve_status_api()
        elif self.path == '/favicon.ico':
            # 返回一个空的favicon，避免404导致的浏览器重复请求
            try:
                self.send_response(204)
                self.send_header('Content-Length', '0')
                self.end_headers()
            except Exception:
                pass
        elif self.path.startswith('/static/'):
            self._serve_static()
        else:
            self._serve_404()

    def do_POST(self):
        """处理POST请求 - 用于外部更新Dashboard数据"""
        if self.path == '/api/update':
            self._handle_update_api()
        else:
            self._serve_404()
    
    def _serve_dashboard(self):
        """提供Dashboard页面"""
        try:
            html_content = self.dashboard_server.generate_html()
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            try:
                self.wfile.write(html_content.encode('utf-8'))
            except Exception:
                # 客户端中止连接时忽略
                pass
            
        except Exception as e:
            logger.error(f"提供Dashboard页面失败: {e}")
            self._serve_500()
    
    def _serve_agents_api(self):
        """提供代理数据API"""
        try:
            agents_data = self.dashboard_server.get_agents_data()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response_data = {
                "status": "success",
                "data": agents_data,
                "timestamp": datetime.now().isoformat()
            }
            
            try:
                self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
            except Exception:
                pass
            
        except Exception as e:
            logger.error(f"提供代理数据API失败: {e}")
            self._serve_500()
    
    def _serve_status_api(self):
        """提供状态API"""
        try:
            status_data = self.dashboard_server.get_status()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response_data = {
                "status": "success",
                "data": status_data,
                "timestamp": datetime.now().isoformat()
            }
            
            try:
                self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
            except Exception:
                pass
            
        except Exception as e:
            logger.error(f"提供状态API失败: {e}")
            self._serve_500()

    def _handle_update_api(self):
        """接收外部推送的代理结果并更新到Dashboard"""
        try:
            content_length = int(self.headers.get('Content-Length', '0'))
            raw_body = self.rfile.read(content_length) if content_length > 0 else b''
            payload = json.loads(raw_body.decode('utf-8') or '{}')
            data = payload.get('data') or payload.get('agent_results') or []
            if isinstance(data, dict):
                data = [data]
            if not isinstance(data, list):
                data = []
            self.dashboard_server.update_agent_results(data)
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            try:
                self.wfile.write(json.dumps({"status":"ok","updated":len(data)}).encode('utf-8'))
            except Exception:
                pass
        except Exception as e:
            logger.error(f"更新Dashboard失败: {e}")
            self._serve_500()
    
    def _serve_static(self):
        """提供静态资源"""
        self._serve_404()  # 简化实现，不提供静态资源
    
    def _serve_404(self):
        """提供404页面"""
        self.send_response(404)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        try:
            self.wfile.write(b'<h1>404 Not Found</h1>')
        except Exception:
            pass
    
    def _serve_500(self):
        """提供500页面"""
        self.send_response(500)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        try:
            self.wfile.write(b'<h1>500 Internal Server Error</h1>')
        except Exception:
            pass
    
    def log_message(self, format, *args):
        """自定义日志格式"""
        logger.info(f"{self.address_string()} - {format % args}")

class DashboardServer:
    """Dashboard服务器"""
    
    def __init__(self, port: int = 8080):
        self.port = port
        self.agent_results: List[Dict[str, Any]] = []
        self.server: Optional[HTTPServer] = None
        self.server_thread: Optional[threading.Thread] = None
        self.is_running = False
    
    def start(self, agent_results: List[Dict[str, Any]]):
        """
        启动Dashboard服务器
        
        Args:
            agent_results: 代理分析结果
        """
        self.agent_results = agent_results
        
        if self.is_running:
            logger.warning("Dashboard服务器已在运行")
            return
        
        try:
            # 创建HTTP服务器
            handler = lambda *args, **kwargs: DashboardHandler(*args, dashboard_server=self, **kwargs)
            self.server = HTTPServer(('localhost', self.port), handler)
            
            # 在单独线程中启动服务器
            self.server_thread = threading.Thread(target=self._run_server, daemon=True)
            self.server_thread.start()
            
            self.is_running = True
            logger.info(f"Dashboard服务器启动成功: http://localhost:{self.port}")
            
        except Exception as e:
            logger.error(f"启动Dashboard服务器失败: {e}")
            raise
    
    def _run_server(self):
        """运行服务器"""
        try:
            self.server.serve_forever()
        except Exception as e:
            logger.error(f"服务器运行出错: {e}")
    
    def stop(self):
        """停止Dashboard服务器"""
        if self.server and self.is_running:
            self.server.shutdown()
            self.is_running = False
            logger.info("Dashboard服务器已停止")
    
    def update_agent_results(self, agent_results: List[Dict[str, Any]]):
        """更新代理结果"""
        self.agent_results = agent_results
    
    def get_agents_data(self) -> List[Dict[str, Any]]:
        """获取代理数据"""
        return self.agent_results
    
    def get_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            "is_running": self.is_running,
            "port": self.port,
            "total_agents": len(self.agent_results),
            "successful_agents": len([r for r in self.agent_results if r.get('status', {}).get('status') == 'completed']),
            "last_updated": datetime.now().isoformat()
        }
    
    def generate_html(self) -> str:
        """生成HTML内容"""
        from .html_generator import HTMLGenerator
        generator = HTMLGenerator()
        return generator.generate_dashboard_html(self.agent_results)
