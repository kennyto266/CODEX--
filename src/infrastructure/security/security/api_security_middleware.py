"""
API安全中間件 - 提供全面的API防護機制
實現內容：
- 速率限制（用戶/IP/端點）
- 輸入驗證與消毒
- CORS安全配置
- 安全標頭
- 請求大小限制
- API版本安全
"""

import asyncio
import hashlib
import hmac
import json
import logging
import re
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from functools import wraps
from ipaddress import ip_address, ip_network
from typing import Dict, List, Optional, Set, Callable, Any
from urllib.parse import urlparse

import itsdangerous
from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import ValidationError as PydanticValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import PlainTextResponse

logger = logging.getLogger(__name__)


# =============================================================================
# 速率限制管理
# =============================================================================

class RateLimitStore:
    """內存存儲速率限制數據"""
    def __init__(self):
        self.requests: Dict[str, deque] = defaultdict(deque)
        self.blocked_ips: Dict[str, float] = {}
        self.whitelist: Set[str] = set()
        self.blacklist: Set[str] = set()
        self.failed_attempts: Dict[str, deque] = defaultdict(deque)

    def is_whitelisted(self, ip: str) -> bool:
        return ip in self.whitelist

    def is_blacklisted(self, ip: str) -> bool:
        return ip in self.blacklist or self._is_temp_blocked(ip)

    def _is_temp_blocked(self, ip: str) -> bool:
        if ip in self.blocked_ips:
            if time.time() < self.blocked_ips[ip]:
                return True
            else:
                del self.blocked_ips[ip]
        return False

    def add_to_blacklist(self, ip: str, duration: int = 3600):
        """添加IP到黑名單（臨時或永久）"""
        if duration > 0:
            self.blocked_ips[ip] = time.time() + duration
        else:
            self.blacklist.add(ip)

    def add_failed_attempt(self, ip: str):
        """記錄失敗嘗試"""
        now = time.time()
        self.failed_attempts[ip].append(now)
        # 清理超過1小時的舊記錄
        while self.failed_attempts[ip] and now - self.failed_attempts[ip][0] > 3600:
            self.failed_attempts[ip].popleft()

    def get_failed_attempts(self, ip: str) -> int:
        """獲取1小時內失敗嘗試次數"""
        now = time.time()
        attempts = 0
        while self.failed_attempts[ip] and now - self.failed_attempts[ip][0] <= 3600:
            attempts += 1
            self.failed_attempts[ip].popleft()
        return attempts


class TokenBucket:
    """令牌桶算法實現"""

    def __init__(self, capacity: float, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.timestamp = time.time()

    def consume(self, tokens: float = 1) -> bool:
        now = time.time()
        # 根據時間補充令牌
        delta = now - self.timestamp
        self.tokens = min(self.capacity, self.tokens + delta * self.refill_rate)
        self.timestamp = now

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False


class SlidingWindow:
    """滑動窗口算法實現"""

    def __init__(self, window_size: int, max_requests: int):
        self.window_size = window_size
        self.max_requests = max_requests
        self.requests: deque = deque()

    def is_allowed(self) -> bool:
        now = time.time()
        # 清理窗口外的請求
        while self.requests and now - self.requests[0] > self.window_size:
            self.requests.popleft()

        # 檢查是否超限
        if len(self.requests) >= self.max_requests:
            return False

        # 記錄當前請求
        self.requests.append(now)
        return True


# =============================================================================
# 輸入驗證與消毒
# =============================================================================

class InputValidator:
    """輸入驗證與消毒工具"""

    # 危險模式列表
    SQL_INJECTION_PATTERNS = [
        r"(\bunion\b\s+select\b)",
        r"(\bor\b\s+1=1\b)",
        r"(\bdrop\s+table\b)",
        r"(\binsert\s+into\b)",
        r"(\bdelete\s+from\b)",
        r"(\bupdate\b\s+\w+\s+set\b)",
        r"('|<|>|\|\||\*|%20)",
    ]

    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
        r"<link[^>]*>",
        r"<style[^>]*>",
        r"<img[^>]*src\s*=\s*['\"]?javascript:",
    ]

    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.\\",
        r"%2e%2e%2f",
        r"%2e%2e%5c",
    ]

    COMMAND_INJECTION_PATTERNS = [
        r"[;&|`$()]",
        r"\bcurl\b",
        r"\bwget\b",
        r"\bnc\b",
        r"\bnetcat\b",
        r"\bbash\b",
        r"\bsh\b",
        r"\bcmd\.exe\b",
        r"\bpowershell\b",
    ]

    @staticmethod
    def validate_sql_injection(input_str: str) -> bool:
        """檢查SQL注入"""
        if not input_str:
            return True
        return not any(re.search(pattern, input_str, re.IGNORECASE) for pattern in InputValidator.SQL_INJECTION_PATTERNS)

    @staticmethod
    def validate_xss(input_str: str) -> bool:
        """檢查XSS攻擊"""
        if not input_str:
            return True
        return not any(re.search(pattern, input_str, re.IGNORECASE) for pattern in InputValidator.XSS_PATTERNS)

    @staticmethod
    def validate_path_traversal(input_str: str) -> bool:
        """檢查路徑穿越攻擊"""
        if not input_str:
            return True
        return not any(re.search(pattern, input_str, re.IGNORECASE) for pattern in InputValidator.PATH_TRAVERSAL_PATTERNS)

    @staticmethod
    def validate_command_injection(input_str: str) -> bool:
        """檢查命令注入攻擊"""
        if not input_str:
            return True
        return not any(re.search(pattern, input_str, re.IGNORECASE) for pattern in InputValidator.COMMAND_INJECTION_PATTERNS)

    @staticmethod
    def sanitize_html(input_str: str) -> str:
        """HTML標籤消毒"""
        if not input_str:
            return ""
        # 移除危險標籤
        dangerous_tags = ['script', 'object', 'embed', 'link', 'style', 'iframe', 'frame', 'frameset']
        sanitized = input_str
        for tag in dangerous_tags:
            sanitized = re.sub(f'<{tag}[^>]*>.*?</{tag}>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
            sanitized = re.sub(f'<{tag}[^>]*/?>', '', sanitized, flags=re.IGNORECASE)
        return sanitized

    @staticmethod
    def validate_content_type(content_type: str, allowed_types: List[str]) -> bool:
        """驗證Content-Type"""
        if not content_type:
            return False
        return any(allowed in content_type.lower() for allowed in allowed_types)

    @staticmethod
    def validate_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
        """驗證文件擴展名"""
        if not filename:
            return False
        ext = filename.split('.')[-1].lower() if '.' in filename else ''
        return ext in allowed_extensions


# =============================================================================
# 安全標頭管理
# =============================================================================

class SecurityHeaders:
    """安全標頭配置"""

    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """獲取標準安全標頭"""
        return {
            # 防止MIME類型嗅探
            'X-Content-Type-Options': 'nosniff',
            # 防止頁面被嵌入iframe
            'X-Frame-Options': 'DENY',
            # XSS保護
            'X-XSS-Protection': '1; mode=block',
            # 嚴格傳輸安全（HTTPS強制）
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            # 內容安全策略
            'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none';",
            # 引薦策略
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            # 權限策略
            'Permissions-Policy': 'camera=(), microphone=(), geolocation=(), payment=()',
        }

    @staticmethod
    def add_cors_headers(headers: Dict[str, str], origin: str, methods: List[str], headers_list: List[str]) -> Dict[str, str]:
        """添加CORS標頭"""
        headers['Access-Control-Allow-Origin'] = origin
        headers['Access-Control-Allow-Methods'] = ', '.join(methods)
        headers['Access-Control-Allow-Headers'] = ', '.join(headers_list)
        headers['Access-Control-Allow-Credentials'] = 'true'
        headers['Access-Control-Max-Age'] = '86400'  # 24小時
        return headers


# =============================================================================
# API安全中間件
# =============================================================================

class APISecurityMiddleware(BaseHTTPMiddleware):
    """API安全中間件"""

    def __init__(
        self,
        app: FastAPI,
        rate_limit_per_minute: int = 60,
        rate_limit_per_hour: int = 1000,
        max_request_size: int = 10 * 1024 * 1024,  # 10MB
        allowed_origins: List[str] = None,
        allowed_methods: List[str] = None,
        allowed_headers: List[str] = None,
        enable_blocklist: bool = True,
        enable_waf: bool = True,
    ):
        super().__init__(app)
        self.rate_limit_store = RateLimitStore()
        self.validator = InputValidator()
        self.security_headers = SecurityHeaders()
        self.max_request_size = max_request_size

        # 配置
        self.allowed_origins = allowed_origins or [
            "http://localhost:3000",
            "http://localhost:8000",
            "http://localhost:8001",
            "https://your-domain.com"
        ]
        self.allowed_methods = allowed_methods or ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
        self.allowed_headers = allowed_headers or [
            "Authorization",
            "Content-Type",
            "X-Requested-With",
            "Accept",
            "Origin"
        ]
        self.enable_blocklist = enable_blocklist
        self.enable_waf = enable_waf

        # 速率限制器（每分鐘/每小時）
        self.minute_bucket = TokenBucket(capacity=60, refill_rate=1.0)  # 每秒1個令牌
        self.hour_bucket = TokenBucket(capacity=1000, refill_rate=1000/3600.0)  # 每秒約0.28個令牌

        # WAF規則
        self.waf_rules = self._load_waf_rules()

        logger.info("✅ API安全中間件已初始化")

    def _load_waf_rules(self) -> Dict[str, List[str]]:
        """載入WAF規則"""
        return {
            'sql_injection': self.validator.SQL_INJECTION_PATTERNS,
            'xss': self.validator.XSS_PATTERNS,
            'path_traversal': self.validator.PATH_TRAVERSAL_PATTERNS,
            'command_injection': self.validator.COMMAND_INJECTION_PATTERNS,
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        client_ip = self._get_client_ip(request)
        request_path = request.url.path
        request_method = request.method
        request_size = 0

        try:
            # 1. 檢查黑名單
            if self.enable_blocklist and self.rate_limit_store.is_blacklisted(client_ip):
                logger.warning(f"🚫 Blocked request from blacklisted IP: {client_ip}")
                return JSONResponse(
                    status_code=403,
                    content={"error": "Access denied", "message": "Your IP is blocked"},
                    headers=self.security_headers.get_security_headers()
                )

            # 2. 檢查請求大小
            if hasattr(request, '_body'):
                request_size = len(await request.body())
                if request_size > self.max_request_size:
                    logger.warning(f"⚠️ Request too large from {client_ip}: {request_size} bytes")
                    return JSONResponse(
                        status_code=413,
                        content={"error": "Payload too large", "message": "Request size exceeds limit"},
                        headers=self.security_headers.get_security_headers()
                    )

            # 3. 速率限制
            if not self._check_rate_limit(client_ip, request_path):
                logger.warning(f"⚠️ Rate limit exceeded for {client_ip}")
                return JSONResponse(
                    status_code=429,
                    content={"error": "Too many requests", "message": "Rate limit exceeded"},
                    headers={
                        **self.security_headers.get_security_headers(),
                        'X-RateLimit-Limit': '60',
                        'X-RateLimit-Remaining': '0',
                        'X-RateLimit-Reset': str(int(time.time()) + 60),
                    }
                )

            # 4. WAF檢查
            if self.enable_waf:
                waf_result = await self._check_waf(request)
                if not waf_result['allowed']:
                    logger.warning(f"🚫 WAF blocked request from {client_ip}: {waf_result['reason']}")
                    self.rate_limit_store.add_to_blacklist(client_ip, duration=3600)  # 封鎖1小時
                    return JSONResponse(
                        status_code=403,
                        content={"error": "Request blocked by security policy"},
                        headers=self.security_headers.get_security_headers()
                    )

            # 5. CORS預檢請求
            if request_method == "OPTIONS":
                return self._handle_cors_preflight(request)

            # 6. 輸入驗證
            validation_result = await self._validate_input(request)
            if not validation_result['valid']:
                logger.warning(f"⚠️ Input validation failed for {client_ip}: {validation_result['errors']}")
                return JSONResponse(
                    status_code=400,
                    content={"error": "Invalid input", "message": validation_result['errors']},
                    headers=self.security_headers.get_security_headers()
                )

            # 7. 處理請求
            response = await call_next(request)

            # 8. 添加安全標頭
            response.headers.update(self.security_headers.get_security_headers())

            # 9. 添加速率限制頭
            self._add_rate_limit_headers(response, client_ip)

            # 10. 記錄請求
            processing_time = time.time() - start_time
            logger.info(
                f"✅ Request processed: {client_ip} {request_method} {request_path} "
                f"- {response.status_code} ({processing_time:.3f}s)"
            )

            return response

        except Exception as e:
            logger.error(f"💥 Security middleware error for {client_ip}: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error"},
                headers=self.security_headers.get_security_headers()
            )

    def _get_client_ip(self, request: Request) -> str:
        """獲取客戶端IP地址"""
        # 檢查代理頭
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()

        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip

        return request.client.host if request.client else 'unknown'

    def _check_rate_limit(self, ip: str, path: str) -> bool:
        """檢查速率限制"""
        # 白名單不限制
        if self.rate_limit_store.is_whitelisted(ip):
            return True

        # 檢查每分鐘限制
        if not self.minute_bucket.consume():
            return False

        # 檢查每小時限制
        if not self.hour_bucket.consume():
            return False

        # 端點特定限制
        endpoint_key = f"{ip}:{path}"
        if not hasattr(self, '_endpoint_limits'):
            self._endpoint_limits = {}
        if endpoint_key not in self._endpoint_limits:
            self._endpoint_limits[endpoint_key] = SlidingWindow(window_size=60, max_requests=10)
        if not self._endpoint_limits[endpoint_key].is_allowed():
            return False

        return True

    async def _check_waf(self, request: Request) -> Dict[str, Any]:
        """WAF檢查"""
        try:
            body = await request.body()
            path = request.url.path
            query_params = str(request.query_params)
            headers = dict(request.headers)

            # 檢查路徑
            if not self.validator.validate_sql_injection(path):
                return {'allowed': False, 'reason': 'SQL injection pattern in path'}

            if not self.validator.validate_xss(path):
                return {'allowed': False, 'reason': 'XSS pattern in path'}

            if not self.validator.validate_path_traversal(path):
                return {'allowed': False, 'reason': 'Path traversal in path'}

            # 檢查查詢參數
            if query_params:
                if not self.validator.validate_sql_injection(query_params):
                    return {'allowed': False, 'reason': 'SQL injection in query params'}

                if not self.validator.validate_xss(query_params):
                    return {'allowed': False, 'reason': 'XSS in query params'}

            # 檢查請求體
            if body and request.method in ['POST', 'PUT', 'PATCH']:
                try:
                    body_str = body.decode('utf-8', errors='ignore')
                    if not self.validator.validate_sql_injection(body_str):
                        return {'allowed': False, 'reason': 'SQL injection in body'}
                    if not self.validator.validate_xss(body_str):
                        return {'allowed': False, 'reason': 'XSS in body'}
                    if not self.validator.validate_command_injection(body_str):
                        return {'allowed': False, 'reason': 'Command injection in body'}
                except Exception:
                    # 無法解碼的請求體可能包含攻擊
                    return {'allowed': False, 'reason': 'Undecodable body content'}

            # 檢查User-Agent
            user_agent = headers.get('User-Agent', '')
            if self._is_suspicious_user_agent(user_agent):
                return {'allowed': False, 'reason': 'Suspicious User-Agent'}

            return {'allowed': True, 'reason': 'Passed all checks'}

        except Exception as e:
            logger.error(f"WAF check error: {e}")
            return {'allowed': False, 'reason': 'WAF check error'}

    def _is_suspicious_user_agent(self, user_agent: str) -> bool:
        """檢查可疑的User-Agent"""
        if not user_agent:
            return True

        suspicious_patterns = [
            'sqlmap',
            'nikto',
            'nmap',
            'masscan',
            'zgrab',
            'bot',
            'crawler',
            'spider',
        ]

        return any(pattern in user_agent.lower() for pattern in suspicious_patterns)

    async def _validate_input(self, request: Request) -> Dict[str, Any]:
        """驗證輸入數據"""
        errors = []
        try:
            # 檢查Content-Type
            content_type = request.headers.get('content-type', '')
            if request.method in ['POST', 'PUT', 'PATCH']:
                if not self.validator.validate_content_type(
                    content_type,
                    ['application/json', 'application/x-www-form-urlencoded', 'multipart/form-data']
                ):
                    errors.append(f"Unsupported content type: {content_type}")

            # 驗證查詢參數
            for key, value in request.query_params.items():
                if isinstance(value, str):
                    if not self.validator.validate_sql_injection(value):
                        errors.append(f"SQL injection pattern in parameter: {key}")
                    if not self.validator.validate_xss(value):
                        errors.append(f"XSS pattern in parameter: {key}")

            # 驗證路徑參數
            path_parts = request.url.path.split('/')
            for part in path_parts:
                if part and not self.validator.validate_path_traversal(part):
                    errors.append(f"Path traversal in path: {part}")

            return {
                'valid': len(errors) == 0,
                'errors': errors
            }

        except Exception as e:
            logger.error(f"Input validation error: {e}")
            return {
                'valid': False,
                'errors': [f"Validation error: {str(e)}"]
            }

    def _handle_cors_preflight(self, request: Request) -> Response:
        """處理CORS預檢請求"""
        origin = request.headers.get('origin', '')

        # 檢查是否允許該來源
        allowed_origin = origin if origin in self.allowed_origins or '*' in self.allowed_origins else None

        headers = self.security_headers.get_security_headers()
        if allowed_origin:
            self.security_headers.add_cors_headers(
                headers,
                allowed_origin,
                self.allowed_methods,
                self.allowed_headers
            )

        return Response(status_code=200, headers=headers)

    def _add_rate_limit_headers(self, response: Response, ip: str):
        """添加速率限制頭"""
        # 計算剩餘請求數
        minute_remaining = int(self.minute_bucket.tokens)
        hour_remaining = int(self.hour_bucket.tokens)

        response.headers['X-RateLimit-Limit-Minute'] = '60'
        response.headers['X-RateLimit-Remaining-Minute'] = str(minute_remaining)
        response.headers['X-RateLimit-Limit-Hour'] = '1000'
        response.headers['X-RateLimit-Remaining-Hour'] = str(hour_remaining)
        response.headers['X-RateLimit-Reset'] = str(int(time.time()) + 60)


# =============================================================================
# 依賴注入
# =============================================================================

security_bearer = HTTPBearer(auto_error=False)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_bearer)):
    """獲取當前用戶（示例）"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    # 這裡應該驗證JWT token或其他認證機制
    return {"user_id": "example"}


def rate_limit(max_requests: int, window_seconds: int = 60):
    """速率限制裝飾器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 實現邏輯
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# =============================================================================
# WAF規則配置
# =============================================================================

class WAFFilter:
    """WAF過濾器"""

    OWASP_TOP_10 = {
        'A01': 'Broken Access Control',
        'A02': 'Cryptographic Failures',
        'A03': 'Injection',
        'A04': 'Insecure Design',
        'A05': 'Security Misconfiguration',
        'A06': 'Vulnerable Components',
        'A07': 'Authentication Failures',
        'A08': 'Software Integrity Failures',
        'A09': 'Logging Failures',
        'A10': 'Server-Side Request Forgery',
    }

    @staticmethod
    def check_injection_attempt(data: str) -> bool:
        """檢查注入攻擊"""
        injection_patterns = [
            r"(\bunion\b\s+\bselect\b)",
            r"(\bor\b\s+1=1)",
            r"('|<|>|\||;)",
            r"(#|--|/\*)",
        ]
        return any(re.search(pattern, data, re.IGNORECASE) for pattern in injection_patterns)

    @staticmethod
    def check_path_traversal(data: str) -> bool:
        """檢查路徑穿越"""
        patterns = [r"\.\./", r"\.\.\\", r"%2e%2e%2f"]
        return any(re.search(pattern, data, re.IGNORECASE) for pattern in patterns)

    @staticmethod
    def check_xss_attempt(data: str) -> bool:
        """檢查XSS攻擊"""
        patterns = [
            r"<script",
            r"javascript:",
            r"on\w+\s*=",
        ]
        return any(re.search(pattern, data, re.IGNORECASE) for pattern in patterns)


# =============================================================================
# DDoS防護
# =============================================================================

class DDoSProtection:
    """DDoS防護機制"""

    def __init__(self):
        self.connection_tracker: Dict[str, deque] = defaultdict(deque)
        self.request_patterns: Dict[str, List[float]] = defaultdict(list)
        self.suspicious_ips: Set[str] = set()
        self.blocked_ips: Dict[str, float] = {}

    def track_request(self, ip: str):
        """追蹤請求"""
        now = time.time()
        self.connection_tracker[ip].append(now)

        # 清理舊記錄（1分鐘窗口）
        window_start = now - 60
        while self.connection_tracker[ip] and self.connection_tracker[ip][0] < window_start:
            self.connection_tracker[ip].popleft()

    def detect_ddos(self, ip: str) -> bool:
        """檢測DDoS攻擊"""
        now = time.time()
        request_count = len(self.connection_tracker[ip])

        # 超過100請求/分鐘視為可疑
        if request_count > 100:
            self.suspicious_ips.add(ip)
            return True

        # 檢查連接頻率
        if len(self.connection_tracker[ip]) > 0:
            intervals = []
            for i in range(1, len(self.connection_tracker[ip])):
                intervals.append(self.connection_tracker[ip][i] - self.connection_tracker[ip][i-1])

            # 平均間隔小於100ms視為機器人
            if intervals and sum(intervals) / len(intervals) < 0.1:
                self.suspicious_ips.add(ip)
                return True

        return False

    def block_ip(self, ip: str, duration: int = 3600):
        """封鎖IP"""
        self.blocked_ips[ip] = time.time() + duration
        logger.warning(f"🚫 IP {ip} blocked for {duration} seconds")

    def is_blocked(self, ip: str) -> bool:
        """檢查IP是否被封鎖"""
        if ip in self.blocked_ips:
            if time.time() < self.blocked_ips[ip]:
                return True
            else:
                del self.blocked_ips[ip]
        return False
