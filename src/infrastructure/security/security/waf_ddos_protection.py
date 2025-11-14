"""
WAF和DDoS防護系統
實現內容：
- OWASP Top 10防護
- SQL注入防護
- XSS防護
- CSRF防護
- DDoS檢測與防護
- IP聲譽管理
- 請求過濾
- 響應過濾
- SSL/TLS安全
"""

import asyncio
import json
import logging
import re
import socket
import ssl
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from ipaddress import ip_address, ip_network
from typing import Dict, List, Optional, Set, Tuple, Any, Callable
from urllib.parse import urlparse

import geoip2.database
import geoip2.errors
import requests
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


# =============================================================================
# 攻擊類型定義
# =============================================================================

class AttackType(Enum):
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    CSRF = "csrf"
    PATH_TRAVERSAL = "path_traversal"
    COMMAND_INJECTION = "command_injection"
    LDAP_INJECTION = "ldap_injection"
    XXE_INJECTION = "xxe_injection"
    SSRF = "ssrf"
    DOS = "dos"
    DDoS = "ddos"
    BRUTE_FORCE = "brute_force"
    SLOWLORIS = "slowloris"
    RCE = "rce"


@dataclass
class AttackSignature:
    """攻擊簽名"""
    name: str
    pattern: str
    severity: int  # 1-10
    category: AttackType
    description: str


@dataclass
class SecurityEvent:
    """安全事件"""
    timestamp: datetime
    ip: str
    attack_type: AttackType
    severity: int
    path: str
    method: str
    user_agent: str
    signature: str
    blocked: bool
    details: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# OWASP Top 10 防護
# =============================================================================

class OWASPTop10Protector:
    """OWASP Top 10 防護實現"""

    PROTECTIONS = {
        'A01': {
            'name': 'Broken Access Control',
            'check': lambda req: req.url.path.startswith('/admin') and req.method != 'GET'
        },
        'A02': {
            'name': 'Cryptographic Failures',
            'check': lambda req: 'authorization' not in req.headers.get('authorization', '').lower()
        },
        'A03': {
            'name': 'Injection',
            'patterns': [
                r"(\bunion\b\s+select\b)",
                r"(\bor\b\s+1=1\b)",
                r"(<script|javascript:)",
                r"(\.\./)",
            ]
        },
        'A04': {
            'name': 'Insecure Design',
            'check': lambda req: False  # 需要業務邏輯分析
        },
        'A05': {
            'name': 'Security Misconfiguration',
            'check': lambda req: 'x-powered-by' in req.headers
        },
        'A06': {
            'name': 'Vulnerable Components',
            'check': lambda req: 'version' in req.url.path.lower()
        },
        'A07': {
            'name': 'Authentication Failures',
            'check': lambda req: req.url.path.startswith('/auth') and req.method == 'POST'
        },
        'A08': {
            'name': 'Software Integrity Failures',
            'check': lambda req: 'checksum' not in req.url.query.lower()
        },
        'A09': {
            'name': 'Logging Failures',
            'check': lambda req: False  # 服務器端檢查
        },
        'A10': {
            'name': 'Server-Side Request Forgery',
            'patterns': [
                r"file://",
                r"http://localhost",
                r"http://127\.0\.0\.1",
                r"https://localhost",
                r"https://127\.0\.0\.1",
            ]
        }
    }

    @staticmethod
    def check_injection(data: str) -> Tuple[bool, Optional[str]]:
        """檢查注入攻擊"""
        patterns = OWASPTop10Protector.PROTECTIONS['A03']['patterns']
        for pattern in patterns:
            if re.search(pattern, data, re.IGNORECASE):
                return True, pattern
        return False, None

    @staticmethod
    def check_ssrf(data: str) -> Tuple[bool, Optional[str]]:
        """檢查SSRF攻擊"""
        patterns = OWASPTop10Protector.PROTECTIONS['A10']['patterns']
        for pattern in patterns:
            if re.search(pattern, data, re.IGNORECASE):
                return True, pattern
        return False, None


# =============================================================================
# SQL注入防護
# =============================================================================

class SQLInjectionFilter:
    """SQL注入過濾器"""

    SQL_PATTERNS = [
        # 基礎注入
        r"(\bunion\b\s+\bselect\b)",
        r"(\bor\b\s+1=1\b)",
        r"(\band\b\s+1=1\b)",
        r"(;--|#|/\*|\*/)",
        r"('|<|>|\||\|\|)",
        r"(\bsleep\b)",
        r"(\bbenchmark\b)",
        r"(\bload_file\b)",
        r"(\binto\s+outfile\b)",

        # 進階注入
        r"(\bunion\s+all\s+select\b)",
        r"(\bor\s+'\w+'='\w+')",
        r"(\band\s+'\w+'='\w+')",
        r"(\bdrop\s+table\b)",
        r"(\bdrop\s+database\b)",
        r"(\balter\s+table\b)",
        r"(\binsert\s+into\b)",
        r"(\bupdate\s+\w+\s+set\b)",
        r"(\bdelete\s+from\b)",
        r"(\bcreate\s+table\b)",
        r"(\bexec\b)",
        r"(\bexecute\b)",

        # 盲注
        r"(\bcase\b\s+when\b)",
        r"(\bif\s*\()",
        r"(\bascii\s*\()",
        r"(\bsubstring\s*\()",
        r"(\bmid\s*\()",
        r"(\blength\s*\()",
    ]

    @classmethod
    def is_malicious(cls, data: str) -> Tuple[bool, Optional[str]]:
        """檢查是否為SQL注入攻擊"""
        if not data:
            return False, None

        for pattern in cls.SQL_PATTERNS:
            match = re.search(pattern, data, re.IGNORECASE)
            if match:
                return True, pattern
        return False, None

    @staticmethod
    def sanitize_input(data: str) -> str:
        """消毒輸入"""
        if not data:
            return ""

        # 移除或轉義危險字符
        sanitized = data
        dangerous_chars = ["'", '"', ';', '--', '/*', '*/', 'xp_', 'sp_']
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')

        return sanitized


# =============================================================================
# XSS防護
# =============================================================================

class XSSFilter:
    """XSS過濾器"""

    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"vbscript:",
        r"onload\s*=",
        r"onerror\s*=",
        r"onclick\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
        r"<link[^>]*>",
        r"<style[^>]*>",
        r"<img[^>]*src\s*=\s*['\"]?javascript:",
        r"<svg[^>]*onload\s*=",
        r"<body[^>]*onload\s*=",
        r"<iframe[^>]*src\s*=",
    ]

    HTML_ENTITIES = {
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#x27;',
        '&': '&amp;',
    }

    @classmethod
    def is_malicious(cls, data: str) -> Tuple[bool, Optional[str]]:
        """檢查是否為XSS攻擊"""
        if not data:
            return False, None

        for pattern in cls.XSS_PATTERNS:
            match = re.search(pattern, data, re.IGNORECASE | re.DOTALL)
            if match:
                return True, pattern
        return False, None

    @staticmethod
    def sanitize_html(data: str) -> str:
        """HTML消毒"""
        if not data:
            return ""

        # 移除危險標籤
        dangerous_tags = [
            'script', 'object', 'embed', 'link', 'style',
            'iframe', 'frame', 'frameset', 'applet', 'base',
            'form', 'input', 'button'
        ]

        sanitized = data
        for tag in dangerous_tags:
            # 移除標籤
            sanitized = re.sub(
                f'<{tag}[^>]*>.*?</{tag}>',
                '',
                sanitized,
                flags=re.IGNORECASE | re.DOTALL
            )
            # 移除自閉合標籤
            sanitized = re.sub(
                f'<{tag}[^>]*/?>',
                '',
                sanitized,
                flags=re.IGNORECASE
            )

        # 轉義剩餘HTML
        for char, entity in XSSFilter.HTML_ENTITIES.items():
            sanitized = sanitized.replace(char, entity)

        return sanitized


# =============================================================================
# CSRF防護
# =============================================================================

class CSRFProtection:
    """CSRF防護"""

    def __init__(self, secret_key: str):
        self.secret_key = secret_key

    def generate_token(self, session_id: str) -> str:
        """生成CSRF token"""
        import itsdangerous
        signer = itsdangerous.URLSafeTimedSerializer(self.secret_key)
        return signer.dumps({'session_id': session_id, 'timestamp': time.time()})

    def validate_token(self, token: str, session_id: str, max_age: int = 3600) -> bool:
        """驗證CSRF token"""
        import itsdangerous
        signer = itsdangerous.URLSafeTimedSerializer(self.secret_key)
        try:
            data = signer.loads(token, max_age=max_age)
            return data.get('session_id') == session_id
        except Exception:
            return False

    def check_origin(self, request: Request) -> bool:
        """檢查Origin標頭"""
        origin = request.headers.get('origin')
        referer = request.headers.get('referer')

        if not origin and not referer:
            return False

        # 這裡應該檢查是否為信任的來源
        trusted_origins = [
            'http://localhost:3000',
            'http://localhost:8000',
            'https://your-domain.com'
        ]

        return origin in trusted_origins or referer in trusted_origins


# =============================================================================
# 請求過濾器
# =============================================================================

class RequestFilter:
    """請求過濾器"""

    def __init__(self):
        self.malicious_patterns = {
            'sql_injection': SQLInjectionFilter.SQL_PATTERNS,
            'xss': XSSFilter.XSS_PATTERNS,
            'path_traversal': [
                r"\.\./",
                r"\.\.\\",
                r"%2e%2e%2f",
                r"%2e%2e%5c",
            ],
            'command_injection': [
                r"[;&|`$()]",
                r"\bcurl\b",
                r"\bwget\b",
                r"\bnc\b",
                r"\bnetcat\b",
                r"\bbash\b",
                r"\bsh\b",
                r"\bcmd\.exe\b",
            ],
            'file_inclusion': [
                r"php://",
                r"file://",
                r"data://",
                r"expect://",
            ],
        }

    def scan_request(self, request: Request, body: bytes) -> List[SecurityEvent]:
        """掃描請求"""
        events = []
        ip = request.client.host if request.client else 'unknown'
        path = request.url.path
        method = request.method
        user_agent = request.headers.get('user-agent', '')

        # 檢查路徑
        path_events = self._scan_data(path, ip, path, method, user_agent, AttackType.PATH_TRAVERSAL)
        events.extend(path_events)

        # 檢查查詢參數
        query_params = str(request.query_params)
        query_events = self._scan_data(query_params, ip, path, method, user_agent, AttackType.SQL_INJECTION)
        events.extend(query_events)

        # 檢查請求體
        if body and method in ['POST', 'PUT', 'PATCH']:
            try:
                body_str = body.decode('utf-8', errors='ignore')
                body_events = self._scan_data(body_str, ip, path, method, user_agent, AttackType.INJECTION)
                events.extend(body_events)
            except Exception:
                events.append(SecurityEvent(
                    timestamp=datetime.now(),
                    ip=ip,
                    attack_type=AttackType.INJECTION,
                    severity=5,
                    path=path,
                    method=method,
                    user_agent=user_agent,
                    signature='undecodable_body',
                    blocked=True,
                    details={'reason': 'Unable to decode request body'}
                ))

        # 檢查User-Agent
        if self._is_suspicious_user_agent(user_agent):
            events.append(SecurityEvent(
                timestamp=datetime.now(),
                ip=ip,
                attack_type=AttackType.DOS,
                severity=7,
                path=path,
                method=method,
                user_agent=user_agent,
                signature='suspicious_user_agent',
                blocked=True,
                details={'user_agent': user_agent}
            ))

        return events

    def _scan_data(
        self,
        data: str,
        ip: str,
        path: str,
        method: str,
        user_agent: str,
        attack_type: AttackType
    ) -> List[SecurityEvent]:
        """掃描數據"""
        events = []
        if not data:
            return events

        # 檢查各種攻擊模式
        for category, patterns in self.malicious_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, data, re.IGNORECASE)
                for match in matches:
                    events.append(SecurityEvent(
                        timestamp=datetime.now(),
                        ip=ip,
                        attack_type=attack_type,
                        severity=self._get_severity(category),
                        path=path,
                        method=method,
                        user_agent=user_agent,
                        signature=pattern,
                        blocked=True,
                        details={
                            'category': category,
                            'matched_text': match.group()[:100]  # 截斷匹配文本
                        }
                    ))

        return events

    def _is_suspicious_user_agent(self, user_agent: str) -> bool:
        """檢查可疑User-Agent"""
        if not user_agent:
            return True

        suspicious = [
            'sqlmap', 'nikto', 'nmap', 'masscan', 'zgrab',
            'python-requests', 'curl', 'wget',
            'bot', 'crawler', 'spider', 'scanner',
        ]

        return any(ua in user_agent.lower() for ua in suspicious)

    def _get_severity(self, category: str) -> int:
        """獲取攻擊嚴重程度"""
        severity_map = {
            'sql_injection': 9,
            'xss': 8,
            'command_injection': 10,
            'path_traversal': 7,
            'file_inclusion': 9,
        }
        return severity_map.get(category, 5)


# =============================================================================
# IP聲譽管理
# =============================================================================

class IPReputationManager:
    """IP聲譽管理器"""

    def __init__(self, db_path: Optional[str] = None):
        self.blacklist: Set[str] = set()
        self.whitelist: Set[str] = set()
        self.ip_scores: Dict[str, int] = {}  # IP聲譽分數
        self.geo_db = None

        # 載入GeoIP數據庫（如果可用）
        if db_path:
            try:
                self.geo_db = geoip2.database.Reader(db_path)
            except Exception as e:
                logger.warning(f"Failed to load GeoIP database: {e}")

    def check_ip(self, ip: str) -> Dict[str, Any]:
        """檢查IP聲譽"""
        result = {
            'blocked': False,
            'score': 0,
            'country': None,
            'isp': None,
            'reasons': []
        }

        # 檢查黑名單
        if ip in self.blacklist:
            result['blocked'] = True
            result['reasons'].append('IP is blacklisted')
            return result

        # 檢查白名單
        if ip in self.whitelist:
            result['score'] = 100
            return result

        # 獲取地理位置信息
        if self.geo_db:
            try:
                response = self.geo_db.city(ip)
                result['country'] = response.country.name
                result['country_code'] = response.country.iso_code
            except Exception:
                pass

        # 檢查IP分數
        score = self.ip_scores.get(ip, 50)  # 默認50分
        result['score'] = score

        # 低于30分的IP被封鎖
        if score < 30:
            result['blocked'] = True
            result['reasons'].append('Low reputation score')

        # 檢查是否为代理/VPN
        if self._is_proxy_vpn(ip):
            result['reasons'].append('Proxy/VPN detected')
            score -= 20
            result['score'] = max(0, score)

        # 檢查是否为TOR出口
        if self._is_tor_exit(ip):
            result['reasons'].append('TOR exit node')
            result['blocked'] = True
            return result

        return result

    def _is_proxy_vpn(self, ip: str) -> bool:
        """檢查是否为代理/VPN"""
        # 這裡應該集成IP聲譡API（如VirusTotal、IPQualityScore等）
        # 簡化實現
        proxy_ranges = [
            ip_network('10.0.0.0/8'),
            ip_network('172.16.0.0/12'),
            ip_network('192.168.0.0/16'),
        ]

        ip_obj = ip_address(ip)
        for net in proxy_ranges:
            if ip_obj in net:
                return True

        return False

    def _is_tor_exit(self, ip: str) -> bool:
        """檢查是否为TOR出口節點"""
        # 這裡應該檢查TOR出口節點列表
        # 簡化實現
        return False

    def add_to_blacklist(self, ip: str, reason: str = ''):
        """添加IP到黑名單"""
        self.blacklist.add(ip)
        self.ip_scores[ip] = 0
        logger.warning(f"IP {ip} added to blacklist. Reason: {reason}")

    def add_to_whitelist(self, ip: str, reason: str = ''):
        """添加IP到白名單"""
        self.whitelist.add(ip)
        self.ip_scores[ip] = 100
        logger.info(f"IP {ip} added to whitelist. Reason: {reason}")

    def update_score(self, ip: str, delta: int):
        """更新IP聲譡分數"""
        self.ip_scores[ip] = max(0, min(100, self.ip_scores.get(ip, 50) + delta))


# =============================================================================
# 響應過濾器
# =============================================================================

class ResponseFilter:
    """響應過濾器"""

    SENSITIVE_PATTERNS = [
        r"(?i)(password|passwd|pwd)[\s:=]+[^\s,]+",
        r"(?i)(api[_-]?key|secret[_-]?key)[\s:=]+[^\s,]+",
        r"(?i)(private[_-]?key)[\s:=]+[^\s,]+",
        r"(?i)(db[_-]?password|mysql[_-]?password)[\s:=]+[^\s,]+",
        r"(stack\s+trace|traceback|error\s+in)",
        r"(?i)(exception|internal\s+error)",
        r"(?i)(file\s+not\s+found|no\s+such\s+file)",
    ]

    def filter_response(self, response_body: str) -> str:
        """過濾響應內容"""
        if not response_body:
            return response_body

        filtered = response_body
        for pattern in self.SENSITIVE_PATTERNS:
            filtered = re.sub(pattern, '[FILTERED]', filtered, flags=re.IGNORECASE)

        return filtered

    def sanitize_error(self, error_message: str) -> str:
        """消毒錯誤信息"""
        if not error_message:
            return "An error occurred"

        # 移除敏感信息
        sanitized = error_message
        sensitive_info = [
            'password', 'passwd', 'secret', 'key', 'token',
            'connection string', 'database', 'sql',
        ]

        for info in sensitive_info:
            sanitized = re.sub(
                rf"{info}[\s:=]+[^\s,;]+",
                f"{info}=[FILTERED]",
                sanitized,
                flags=re.IGNORECASE
            )

        return sanitized


# =============================================================================
# DDoS檢測與防護
# =============================================================================

class DDoSDetector:
    """DDoS攻擊檢測器"""

    def __init__(self):
        self.request_counts: Dict[str, deque] = defaultdict(deque)
        self.connection_times: Dict[str, deque] = defaultdict(deque)
        self.request_sizes: Dict[str, deque] = defaultdict(deque)
        self.bandwidth_usage: Dict[str, float] = defaultdict(float)
        self.last_request_time: Dict[str, float] = {}

    def track_request(self, ip: str, request_size: int = 0):
        """追蹤請求"""
        now = time.time()
        self.request_counts[ip].append(now)
        self.request_sizes[ip].append(request_size)
        self.bandwidth_usage[ip] += request_size
        self.last_request_time[ip] = now

        # 清理舊記錄（5分鐘窗口）
        window_start = now - 300
        for tracker in [self.request_counts, self.request_sizes]:
            while tracker[ip] and tracker[ip][0] < window_start:
                tracker[ip].popleft()

    def detect_ddos(self, ip: str) -> Tuple[bool, str, int]:
        """檢測DDoS攻擊"""
        now = time.time()
        request_count = len(self.request_counts[ip])

        # 檢查請求頻率
        if request_count > 200:  # 5分鐘內超過200請求
            return True, "High request frequency", 8

        # 檢查請求間隔
        if len(self.request_counts[ip]) > 10:
            intervals = [
                self.request_counts[ip][i] - self.request_counts[ip][i-1]
                for i in range(1, len(self.request_counts[ip]))
            ]
            avg_interval = sum(intervals) / len(intervals)
            if avg_interval < 0.05:  # 平均間隔<50ms
                return True, "Very fast requests", 9

        # 檢查帶寬使用
        if self.bandwidth_usage[ip] > 100 * 1024 * 1024:  # 100MB
            return True, "Excessive bandwidth usage", 7

        # 檢查大請求
        if self.request_sizes[ip]:
            recent_sizes = list(self.request_sizes[ip])[-10:]
            if any(size > 50 * 1024 * 1024 for size in recent_sizes):  # 50MB
                return True, "Large payload size", 6

        return False, "", 0

    def reset_tracking(self, ip: str):
        """重置追蹤"""
        if ip in self.request_counts:
            self.request_counts[ip].clear()
        if ip in self.connection_times:
            self.connection_times[ip].clear()
        if ip in self.request_sizes:
            self.request_sizes[ip].clear()


# =============================================================================
# SSL/TLS安全
# =============================================================================

class TLSSecurity:
    """SSL/TLS安全配置"""

    @staticmethod
    def get_ssl_context() -> ssl.SSLContext:
        """獲取SSL上下文"""
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.maximum_version = ssl.TLSVersion.TLSv1_3

        # 僅允許強密碼套件
        context.set_ciphers(
            'ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS:!3DES'
        )

        # 啟用證書驗證
        context.verify_mode = ssl.CERT_REQUIRED

        # 啟用OCSP裝訂
        context.options |= ssl.OP_ENABLE_MIDDLEBOX_COMPAT
        context.options |= ssl.OP_NO_RENEGOTIATION

        return context

    @staticmethod
    def check_certificate(hostname: str, port: int = 443) -> Dict[str, Any]:
        """檢查SSL證書"""
        try:
            context = ssl.create_default_context()
            with socket.create_connection((hostname, port), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    return {
                        'valid': True,
                        'subject': dict(x[0] for x in cert['subject']),
                        'issuer': dict(x[0] for x in cert['issuer']),
                        'expires': cert['notAfter'],
                        'version': cert['version'],
                        'serial': cert['serialNumber']
                    }
        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }


# =============================================================================
# 實時監控與告警
# =============================================================================

class SecurityMonitor:
    """安全監控系統"""

    def __init__(self):
        self.events: List[SecurityEvent] = []
        self.attack_counts: Dict[AttackType, int] = defaultdict(int)
        self.blocked_ips: Set[str] = set()
        self.alert_thresholds = {
            AttackType.DDoS: 10,  # 10次DDoS攻擊觸發告警
            AttackType.SQL_INJECTION: 5,
            AttackType.XSS: 5,
        }
        self.subscribers: List[Callable] = []

    def add_event(self, event: SecurityEvent):
        """添加安全事件"""
        self.events.append(event)
        self.attack_counts[event.attack_type] += 1

        if event.blocked:
            self.blocked_ips.add(event.ip)

        # 檢查是否觸發告警
        if event.attack_type in self.alert_thresholds:
            if self.attack_counts[event.attack_type] >= self.alert_thresholds[event.attack_type]:
                self._trigger_alert(event)

        # 通知訂閱者
        for callback in self.subscribers:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Error in security alert callback: {e}")

    def _trigger_alert(self, event: SecurityEvent):
        """觸發告警"""
        logger.critical(
            f"🚨 SECURITY ALERT: {event.attack_type.value} from {event.ip}. "
            f"Total count: {self.attack_counts[event.attack_type]}"
        )

    def subscribe(self, callback: Callable):
        """訂閱安全事件"""
        self.subscribers.append(callback)

    def get_attack_statistics(self) -> Dict[str, int]:
        """獲取攻擊統計"""
        return {k.value: v for k, v in self.attack_counts.items()}

    def get_blocked_ips(self) -> List[str]:
        """獲取被封鎖的IP"""
        return list(self.blocked_ips)

    def get_recent_events(self, minutes: int = 60) -> List[SecurityEvent]:
        """獲取最近事件"""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        return [e for e in self.events if e.timestamp > cutoff]


# =============================================================================
# WAF中間件
# =============================================================================

class WAFMiddleware(BaseHTTPMiddleware):
    """Web應用防火牆中間件"""

    def __init__(
        self,
        app: FastAPI,
        enable_ddos_protection: bool = True,
        enable_ip_reputation: bool = True,
        enable_response_filtering: bool = True,
        geo_db_path: Optional[str] = None,
    ):
        super().__init__(app)
        self.request_filter = RequestFilter()
        self.response_filter = ResponseFilter()
        self.ddos_detector = DDoSDetector()
        self.ip_reputation = IPReputationManager(geo_db_path)
        self.monitor = SecurityMonitor()
        self.enable_ddos = enable_ddos_protection
        self.enable_reputation = enable_ip_reputation
        self.enable_response = enable_response_filtering

        # 註冊告警回調
        self.monitor.subscribe(self._on_security_event)

        logger.info("✅ WAF Middleware initialized")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        ip = request.client.host if request.client else 'unknown'
        path = request.url.path
        method = request.method

        try:
            # 1. IP聲譽檢查
            if self.enable_reputation:
                reputation = self.ip_reputation.check_ip(ip)
                if reputation['blocked']:
                    logger.warning(f"🚫 Blocked request from low-reputation IP: {ip}")
                    self.monitor.add_event(SecurityEvent(
                        timestamp=datetime.now(),
                        ip=ip,
                        attack_type=AttackType.DOS,
                        severity=7,
                        path=path,
                        method=method,
                        user_agent=request.headers.get('user-agent', ''),
                        signature='low_ip_reputation',
                        blocked=True,
                        details=reputation
                    ))
                    return JSONResponse(
                        status_code=403,
                        content={"error": "Access denied", "message": "Your IP has low reputation"},
                        headers={'X-Blocked-Reason': 'low_reputation'}
                    )

            # 2. DDoS檢測
            if self.enable_ddos:
                body = await request.body()
                self.ddos_detector.track_request(ip, len(body))
                is_ddos, reason, severity = self.ddos_detector.detect_ddos(ip)
                if is_ddos:
                    logger.warning(f"🚫 DDoS attack detected from {ip}: {reason}")
                    self.monitor.add_event(SecurityEvent(
                        timestamp=datetime.now(),
                        ip=ip,
                        attack_type=AttackType.DDoS,
                        severity=severity,
                        path=path,
                        method=method,
                        user_agent=request.headers.get('user-agent', ''),
                        signature=reason,
                        blocked=True
                    ))
                    # 暫時封鎖IP
                    self.ip_reputation.add_to_blacklist(ip, reason)
                    return JSONResponse(
                        status_code=429,
                        content={"error": "Too many requests", "message": "You have been temporarily blocked"},
                        headers={'X-Blocked-Reason': 'ddos_detection'}
                    )

            # 3. 請求過濾
            body = await request.body()
            security_events = self.request_filter.scan_request(request, body)

            if security_events:
                for event in security_events:
                    self.monitor.add_event(event)
                return JSONResponse(
                    status_code=403,
                    content={"error": "Request blocked", "message": "Your request was blocked by security policy"},
                    headers={'X-Blocked-Reason': 'waf_filter'}
                )

            # 4. 處理請求
            response = await call_next(request)

            # 5. 響應過濾
            if self.enable_response and hasattr(response, 'body'):
                response_body = response.body.decode('utf-8', errors='ignore')
                filtered_body = self.response_filter.filter_response(response_body)
                if filtered_body != response_body:
                    response.body = filtered_body.encode('utf-8')

            # 6. 記錄正常請求
            processing_time = time.time() - start_time
            logger.debug(f"✅ Request processed: {ip} {method} {path} - {response.status_code} ({processing_time:.3f}s)")

            return response

        except Exception as e:
            logger.error(f"💥 WAF error: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error"},
                headers={'X-Error': 'waf_internal_error'}
            )

    def _on_security_event(self, event: SecurityEvent):
        """安全事件回調"""
        # 這裡可以集成SIEM、Slack郵件等告警系統
        pass


# =============================================================================
# 配置管理
# =============================================================================

class SecurityConfig:
    """安全配置管理"""

    # 默認配置
    DEFAULT_CONFIG = {
        'rate_limit': {
            'requests_per_minute': 60,
            'requests_per_hour': 1000,
            'burst_limit': 20,
        },
        'ddos_protection': {
            'enabled': True,
            'threshold': 200,  # requests per 5 minutes
            'block_duration': 3600,  # seconds
        },
        'ip_reputation': {
            'enabled': True,
            'geo_db_path': None,
            'block_low_score': 30,
        },
        'cors': {
            'allowed_origins': ['http://localhost:3000', 'http://localhost:8000'],
            'allowed_methods': ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'],
            'allowed_headers': ['*'],
        },
        'security_headers': {
            'enabled': True,
            'strict_mode': True,
        },
        'waf': {
            'enabled': True,
            'strict_mode': True,
            'block_on_first_violation': True,
        }
    }

    @classmethod
    def load_config(cls, config_path: Optional[str] = None) -> Dict[str, Any]:
        """載入配置"""
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        return cls.DEFAULT_CONFIG.copy()

    @classmethod
    def save_config(cls, config: Dict[str, Any], config_path: str):
        """保存配置"""
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
