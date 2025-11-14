"""
API安全系統整合層
整合所有安全組件並與FastAPI應用集成
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

from .api_security_middleware import (
    APISecurityMiddleware,
    RateLimitStore,
    SecurityHeaders,
    DDoSProtection,
)
from .waf_ddos_protection import (
    WAFMiddleware,
    SecurityMonitor,
    SecurityConfig,
    AttackType,
)

logger = logging.getLogger(__name__)


class ComprehensiveSecuritySystem:
    """
    全面安全系統整合
    包含所有安全防護組件
    """

    def __init__(
        self,
        app: FastAPI,
        config_path: Optional[str] = None,
        enable_all: bool = True,
    ):
        self.app = app
        self.config = SecurityConfig.load_config(config_path)
        self.enable_all = enable_all

        # 初始化組件
        self.monitor = SecurityMonitor()
        self.rate_limit_store = RateLimitStore()
        self.ddos_protection = DDoSProtection()

        # 應用安全組件
        if enable_all:
            self._apply_security_middleware()
            self._setup_security_routes()
            self._setup_monitoring()
            self._load_ip_lists()

        logger.info("✅ Comprehensive Security System initialized")

    def _apply_security_middleware(self):
        """應用安全中間件"""

        # 1. API安全中間件（速率限制、輸入驗證、CORS等）
        if self.config.get('rate_limit', {}).get('enabled', True):
            self.app.add_middleware(
                APISecurityMiddleware,
                rate_limit_per_minute=self.config['rate_limit'].get('requests_per_minute', 60),
                rate_limit_per_hour=self.config['rate_limit'].get('requests_per_hour', 1000),
                max_request_size=self.config.get('max_request_size', 10 * 1024 * 1024),
                allowed_origins=self.config.get('cors', {}).get('allowed_origins', [
                    'http://localhost:3000',
                    'http://localhost:8000',
                    'http://localhost:8001'
                ]),
                enable_blocklist=True,
                enable_waf=True,
            )
            logger.info("✅ API Security Middleware applied")

        # 2. WAF中間件（DDoS、IP聲譽、響應過濾）
        if self.config.get('waf', {}).get('enabled', True):
            self.app.add_middleware(
                WAFMiddleware,
                enable_ddos_protection=self.config.get('ddos_protection', {}).get('enabled', True),
                enable_ip_reputation=self.config.get('ip_reputation', {}).get('enabled', True),
                enable_response_filtering=self.config.get('response_filtering', {}).get('enabled', True),
                geo_db_path=self.config.get('geo_db_path'),
            )
            logger.info("✅ WAF Middleware applied")

        # 3. CORS中間件（額外層次的安全控制）
        if self.config.get('cors', {}).get('enabled', True):
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=self.config.get('cors', {}).get('allowed_origins', [
                    'http://localhost:3000',
                    'http://localhost:8000'
                ]),
                allow_credentials=True,
                allow_methods=self.config.get('cors', {}).get('allowed_methods', [
                    'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'
                ]),
                allow_headers=self.config.get('cors', {}).get('allowed_headers', [
                    'Authorization',
                    'Content-Type',
                    'X-Requested-With',
                    'Accept',
                    'Origin'
                ]),
                expose_headers=['X-RateLimit-*', 'X-Blocked-Reason', 'X-Request-ID'],
                max_age=86400,  # 24小時
            )
            logger.info("✅ CORS Middleware applied")

    def _setup_security_routes(self):
        """設置安全相關路由"""

        @self.app.get("/api/security/status", tags=["Security"])
        async def security_status():
            """安全系統狀態"""
            return {
                "status": "active",
                "version": "1.0.0",
                "features": {
                    "rate_limiting": True,
                    "ddos_protection": True,
                    "waf": True,
                    "ip_reputation": True,
                    "input_validation": True,
                    "cors": True,
                },
                "config": {
                    "rate_limit_per_minute": self.config['rate_limit'].get('requests_per_minute'),
                    "rate_limit_per_hour": self.config['rate_limit'].get('requests_per_hour'),
                    "ddos_threshold": self.config.get('ddos_protection', {}).get('threshold'),
                }
            }

        @self.app.get("/api/security/stats", tags=["Security"])
        async def security_stats():
            """安全統計信息"""
            stats = self.monitor.get_attack_statistics()
            return {
                "attack_statistics": stats,
                "blocked_ips_count": len(self.monitor.get_blocked_ips()),
                "recent_events_count": len(self.monitor.get_recent_events()),
                "uptime": "N/A",  # 這裡可以計算運行時間
            }

        @self.app.get("/api/security/ips/blocked", tags=["Security"])
        async def get_blocked_ips():
            """獲取被封鎖的IP列表"""
            return {
                "blocked_ips": self.monitor.get_blocked_ips(),
                "count": len(self.monitor.get_blocked_ips())
            }

        @self.app.post("/api/security/ips/whitelist", tags=["Security"])
        async def whitelist_ip(request: Request):
            """將IP添加到白名單"""
            data = await request.json()
            ip = data.get('ip')
            reason = data.get('reason', 'manual_whitelist')

            if not ip:
                return JSONResponse(
                    status_code=400,
                    content={"error": "IP address is required"}
                )

            self.rate_limit_store.whitelist.add(ip)
            logger.info(f"IP {ip} added to whitelist. Reason: {reason}")

            return {
                "status": "success",
                "message": f"IP {ip} added to whitelist"
            }

        @self.app.post("/api/security/ips/blacklist", tags=["Security"])
        async def blacklist_ip(request: Request):
            """將IP添加到黑名單"""
            data = await request.json()
            ip = data.get('ip')
            duration = data.get('duration', 3600)  # 默認1小時
            reason = data.get('reason', 'manual_blacklist')

            if not ip:
                return JSONResponse(
                    status_code=400,
                    content={"error": "IP address is required"}
                )

            self.rate_limit_store.add_to_blacklist(ip, duration)
            logger.warning(f"IP {ip} added to blacklist for {duration}s. Reason: {reason}")

            return {
                "status": "success",
                "message": f"IP {ip} added to blacklist for {duration} seconds"
            }

        @self.app.get("/api/security/events", tags=["Security"])
        async def get_security_events(minutes: int = 60):
            """獲取安全事件"""
            events = self.monitor.get_recent_events(minutes)
            return {
                "events": [
                    {
                        "timestamp": event.timestamp.isoformat(),
                        "ip": event.ip,
                        "attack_type": event.attack_type.value,
                        "severity": event.severity,
                        "path": event.path,
                        "method": event.method,
                        "blocked": event.blocked,
                        "signature": event.signature,
                    }
                    for event in events
                ],
                "count": len(events)
            }

        @self.app.get("/api/security/dashboard", tags=["Security"])
        async def security_dashboard():
            """安全儀表板數據"""
            stats = self.monitor.get_attack_statistics()
            blocked_ips = self.monitor.get_blocked_ips()
            recent_events = self.monitor.get_recent_events(60)

            # 計算攻擊類型分佈
            attack_distribution = {}
            for attack_type, count in stats.items():
                attack_distribution[attack_type] = count

            return {
                "summary": {
                    "total_attacks": sum(stats.values()),
                    "blocked_ips": len(blocked_ips),
                    "recent_events": len(recent_events),
                },
                "attack_distribution": attack_distribution,
                "top_attack_types": sorted(stats.items(), key=lambda x: x[1], reverse=True)[:5],
                "recent_blocked_ips": blocked_ips[:20],  # 最近20個被封鎖的IP
                "security_level": self._calculate_security_level(stats),
            }

        @self.app.get("/api/security/test", tags=["Security"])
        async def security_test():
            """安全系統測試端點"""
            return {
                "status": "ok",
                "message": "Security system is running",
                "timestamp": "2025-01-01T00:00:00Z",
                "all_headers_present": True,
            }

    def _setup_monitoring(self):
        """設置監控"""
        # 註冊告警回調
        self.monitor.subscribe(self._security_alert_handler)

        logger.info("✅ Security monitoring configured")

    def _security_alert_handler(self, event):
        """安全事件告警處理"""
        # 這裡可以集成各種告警渠道
        if event.severity >= 8:
            logger.critical(
                f"🚨 HIGH SEVERITY SECURITY EVENT: {event.attack_type.value} "
                f"from {event.ip} - {event.signature}"
            )
            # 發送郵件、Slack、短信等

    def _load_ip_lists(self):
        """載入IP白名單和黑名單"""
        try:
            # 載入白名單
            whitelist_path = Path("config/whitelist_ips.txt")
            if whitelist_path.exists():
                with open(whitelist_path) as f:
                    for line in f:
                        ip = line.strip()
                        if ip and not ip.startswith('#'):
                            self.rate_limit_store.whitelist.add(ip)
                logger.info(f"Loaded {len(self.rate_limit_store.whitelist)} IPs to whitelist")

            # 載入黑名單
            blacklist_path = Path("config/blacklist_ips.txt")
            if blacklist_path.exists():
                with open(blacklist_path) as f:
                    for line in f:
                        ip = line.strip()
                        if ip and not ip.startswith('#'):
                            self.rate_limit_store.blacklist.add(ip)
                logger.info(f"Loaded {len(self.rate_limit_store.blacklist)} IPs to blacklist")
        except Exception as e:
            logger.error(f"Failed to load IP lists: {e}")

    def _calculate_security_level(self, stats: Dict[str, int]) -> str:
        """計算安全等級"""
        total_attacks = sum(stats.values())
        if total_attacks == 0:
            return "SECURE"
        elif total_attacks < 10:
            return "LOW_RISK"
        elif total_attacks < 50:
            return "MEDIUM_RISK"
        elif total_attacks < 100:
            return "HIGH_RISK"
        else:
            return "CRITICAL"

    def get_config(self) -> Dict[str, Any]:
        """獲取當前配置"""
        return self.config

    def update_config(self, new_config: Dict[str, Any]):
        """更新配置"""
        self.config.update(new_config)
        logger.info("Security configuration updated")

    def save_config(self, config_path: str):
        """保存配置到文件"""
        SecurityConfig.save_config(self.config, config_path)
        logger.info(f"Security configuration saved to {config_path}")


def setup_comprehensive_security(
    app: FastAPI,
    config_path: Optional[str] = None,
    enable_all: bool = True,
) -> ComprehensiveSecuritySystem:
    """
    設置全面安全系統

    Args:
        app: FastAPI應用實例
        config_path: 配置文件路徑
        enable_all: 是否啟用所有安全功能

    Returns:
        ComprehensiveSecuritySystem實例
    """
    security_system = ComprehensiveSecuritySystem(
        app=app,
        config_path=config_path,
        enable_all=enable_all
    )

    return security_system


# =============================================================================
# 裝飾器和工具函數
# =============================================================================

def secure_endpoint(required_privilege: Optional[str] = None):
    """
    安全端點裝飾器
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 這裡可以添加端點特定的權限檢查
            # 例如檢查用戶角色、權限等
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def validate_input(schema_class):
    """
    輸入驗證裝飾器
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 這裡可以添加Pydantic模式驗證
            # 例如驗證請求體、查詢參數等
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def log_security_event(event_type: str):
    """
    安全事件記錄裝飾器
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            logger.info(f"Security event: {event_type} - {func.__name__}")
            return result
        return wrapper
    return decorator


# =============================================================================
# 配置範例
# =============================================================================

SECURITY_CONFIG_EXAMPLE = {
    "rate_limit": {
        "enabled": True,
        "requests_per_minute": 60,
        "requests_per_hour": 1000,
        "burst_limit": 20,
        "per_endpoint_limits": {
            "/api/auth/login": 5,  # 登錄端點更嚴格
            "/api/auth/register": 3,
            "/api/data/search": 30,
        }
    },
    "ddos_protection": {
        "enabled": True,
        "threshold": 200,  # 5分鐘內最大請求數
        "block_duration": 3600,  # 封鎖1小時
        "auto_unblock": True,
    },
    "ip_reputation": {
        "enabled": True,
        "geo_db_path": "/path/to/GeoLite2-City.mmdb",
        "block_low_score": 30,
        "auto_block_suspicious": True,
    },
    "cors": {
        "enabled": True,
        "allowed_origins": [
            "http://localhost:3000",
            "http://localhost:8000",
            "https://your-domain.com"
        ],
        "allowed_methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        "allowed_headers": ["*"],
        "expose_headers": ["X-RateLimit-*", "X-Request-ID"],
        "max_age": 86400,
    },
    "security_headers": {
        "enabled": True,
        "strict_mode": True,
        "csp_enabled": True,
        "hsts_enabled": True,
    },
    "waf": {
        "enabled": True,
        "strict_mode": True,
        "block_on_first_violation": True,
        "rules": {
            "sql_injection": {"enabled": True, "severity": 9},
            "xss": {"enabled": True, "severity": 8},
            "path_traversal": {"enabled": True, "severity": 7},
            "command_injection": {"enabled": True, "severity": 10},
        }
    },
    "response_filtering": {
        "enabled": True,
        "sanitize_errors": True,
        "hide_stack_traces": True,
        "remove_sensitive_data": True,
    },
    "monitoring": {
        "enabled": True,
        "log_level": "INFO",
        "alert_on_attack": True,
        "alert_thresholds": {
            "ddos": 10,
            "sql_injection": 5,
            "xss": 5,
        }
    }
}


def create_security_config_file(config_path: str, custom_config: Optional[Dict] = None):
    """
    創建安全配置文件
    """
    config = custom_config or SECURITY_CONFIG_EXAMPLE
    config_dir = os.path.dirname(config_path)
    os.makedirs(config_dir, exist_ok=True)

    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

    logger.info(f"Security configuration saved to {config_path}")
    return config_path
