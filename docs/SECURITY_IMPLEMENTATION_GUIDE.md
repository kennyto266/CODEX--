# API安全防護系統實施指南

## Phase 5: Data Privacy & Security - API Security & Protection

### 📋 概述

本文檔詳細說明了港股量化交易系統的全面API安全防護機制實現。該系統遵循OWASP API Security Top 10標準，提供多層次的安全防護。

---

## 🛡️ 安全防護體系架構

```
┌─────────────────────────────────────────────────────────┐
│                    客戶端 (Client)                       │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  1. IP聲譽檢查 (IP Reputation)                           │
│     - 黑名單/白名單管理                                  │
│     - 地理位置過濾                                      │
│     - 代理/VPN檢測                                      │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  2. DDoS檢測 (DDoS Detection)                            │
│     - 請求頻率監控                                      │
│     - 帶寬使用分析                                      │
│     - 異常行為檢測                                      │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  3. 速率限制 (Rate Limiting)                             │
│     - 令牌桶算法                                        │
│     - 滑動窗口算法                                      │
│     - 端點特定限制                                      │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  4. WAF防火牆 (Web Application Firewall)                │
│     - SQL注入防護                                       │
│     - XSS防護                                           │
│     - 路徑穿越防護                                      │
│     - 命令注入防護                                      │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  5. 輸入驗證 (Input Validation)                          │
│     - SQL注入檢測                                       │
│     - XSS檢測                                           │
│     - 輸入消毒                                          │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  6. CORS安全配置 (CORS Security)                         │
│     - 來源驗證                                          │
│     - 方法限制                                          │
│     - 標頭控制                                          │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  7. 安全標頭 (Security Headers)                          │
│     - HSTS                                              │
│     - CSP                                               │
│     - X-Frame-Options                                  │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  8. 響應過濾 (Response Filtering)                        │
│     - 敏感信息脫敏                                      │
│     - 錯誤信息消毒                                      │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  業務邏輯 (Business Logic)               │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 核心組件

### 1. API安全中間件 (APISecurityMiddleware)

**功能特性：**
- ✅ 速率限制（用戶/IP/端點級）
- ✅ 輸入驗證與消毒
- ✅ CORS安全配置
- ✅ 安全標頭
- ✅ 請求大小限制
- ✅ API版本安全

**使用示例：**

```python
from src.security import APISecurityMiddleware

app.add_middleware(
    APISecurityMiddleware,
    rate_limit_per_minute=60,
    rate_limit_per_hour=1000,
    max_request_size=10 * 1024 * 1024,  # 10MB
    allowed_origins=["http://localhost:3000"],
    enable_blocklist=True,
    enable_waf=True,
)
```

**配置參數：**

| 參數 | 類型 | 默認值 | 說明 |
|------|------|--------|------|
| rate_limit_per_minute | int | 60 | 每分鐘最大請求數 |
| rate_limit_per_hour | int | 1000 | 每小時最大請求數 |
| max_request_size | int | 10MB | 最大請求大小 |
| allowed_origins | List[str] | localhost | 允許的CORS來源 |
| enable_blocklist | bool | True | 啟用IP黑名單 |
| enable_waf | bool | True | 啟用WAF |

### 2. WAF防火牆 (WAFMiddleware)

**功能特性：**
- ✅ OWASP Top 10防護
- ✅ SQL注入防護
- ✅ XSS防護
- ✅ CSRF防護
- ✅ 路徑穿越防護
- ✅ 命令注入防護
- ✅ SSRF防護

**使用示例：**

```python
from src.security import WAFMiddleware

app.add_middleware(
    WAFMiddleware,
    enable_ddos_protection=True,
    enable_ip_reputation=True,
    enable_response_filtering=True,
)
```

### 3. 速率限制系統 (RateLimitStore)

**支持的算法：**

1. **令牌桶算法 (TokenBucket)**
   - 適合處理突發流量
   - 精確控制平均速率

2. **滑動窗口算法 (SlidingWindow)**
   - 適合限制固定時間窗口內的請求數
   - 簡單易實現

**配置示例：**

```python
# 全局限制
rate_limit_per_minute = 60
rate_limit_per_hour = 1000

# 端點特定限制
endpoint_limits = {
    "/api/auth/login": 5,      # 登錄端點更嚴格
    "/api/auth/register": 3,
    "/api/data/search": 30,
}
```

### 4. 輸入驗證與消毒 (InputValidator)

**檢測的攻擊類型：**

1. **SQL注入**
   - 聯合查詢：`UNION SELECT`
   - 布爾盲注：`OR 1=1`
   - 時延攻擊：`SLEEP()`

2. **XSS攻擊**
   - 反射型XSS：`<script>alert('xss')</script>`
   - 存儲型XSS：HTML標籤注入
   - DOM型XSS：`javascript:` 協議

3. **路徑穿越**
   - 目錄遍歷：`../../../etc/passwd`
   - URL編碼：`%2e%2e%2f`

4. **命令注入**
   - 系統命令執行：`; curl http://evil.com`
   - 管道操作：`|`、`&`、`$()`

**使用示例：**

```python
from src.security import InputValidator

validator = InputValidator()

# 檢查SQL注入
if not validator.validate_sql_injection(user_input):
    raise HTTPException(400, "Potential SQL injection detected")

# 檢查XSS
if not validator.validate_xss(user_input):
    raise HTTPException(400, "Potential XSS attack detected")

# 消毒HTML
safe_input = validator.sanitize_html(user_input)
```

### 5. IP聲譽管理 (IPReputationManager)

**功能特性：**
- 📊 IP聲譽評分系統（0-100）
- 🌍 地理位置過濾
- 🔒 自動黑名單/白名單管理
- 🔍 代理/VPN/TOR檢測
- 📈 動態分數調整

**使用示例：**

```python
from src.security import IPReputationManager

# 初始化聲譽管理器
reputation_manager = IPReputationManager(db_path="/path/to/GeoLite2.mmdb")

# 檢查IP
result = reputation_manager.check_ip("192.168.1.1")
if result['blocked']:
    raise HTTPException(403, "IP is blocked")

# 添加到白名單
reputation_manager.add_to_whitelist("127.0.0.1", "localhost")

# 添加到黑名單
reputation_manager.add_to_blacklist("192.168.1.100", "malicious_activity")
```

### 6. DDoS防護 (DDoSDetector)

**檢測機制：**
1. **請求頻率檢測**
   - 5分鐘內 > 200 請求

2. **請求間隔檢測**
   - 平均間隔 < 50ms

3. **帶寬使用檢測**
   - 5分鐘內 > 100MB

4. **大請求檢測**
   - 單個請求 > 50MB

**配置示例：**

```python
ddos_config = {
    "enabled": True,
    "threshold": 200,           # 5分鐘內最大請求數
    "block_duration": 3600,     # 封鎖1小時
    "auto_unblock": True,
}
```

### 7. CSRF防護 (CSRFProtection)

**防護措施：**
- 🔑 CSRF Token生成與驗證
- 🌐 Origin標頭檢查
- 📋 Referer標頭驗證

**使用示例：**

```python
from src.security import CSRFProtection

csrf_protection = CSRFProtection(secret_key="your-secret-key")

# 生成Token
token = csrf_protection.generate_token(session_id="user123")

# 驗證Token
if not csrf_protection.validate_token(token, session_id="user123"):
    raise HTTPException(403, "Invalid CSRF token")
```

### 8. 安全標頭 (SecurityHeaders)

**實現的安全標頭：**

| 標頭 | 值 | 說明 |
|------|-----|------|
| X-Content-Type-Options | nosniff | 防止MIME類型嗅探 |
| X-Frame-Options | DENY | 防止頁面被嵌入iframe |
| X-XSS-Protection | 1; mode=block | XSS保護 |
| Strict-Transport-Security | max-age=31536000 | 強制HTTPS |
| Content-Security-Policy | default-src 'self' | 內容安全策略 |
| Referrer-Policy | strict-origin-when-cross-origin | 引薦策略 |
| Permissions-Policy | camera=(), microphone=() | 權限策略 |

**使用示例：**

```python
from src.security import SecurityHeaders

headers = SecurityHeaders()
security_headers = headers.get_security_headers()

# 添加CORS標頭
headers.add_cors_headers(
    security_headers,
    origin="http://localhost:3000",
    methods=["GET", "POST"],
    headers=["Authorization", "Content-Type"]
)
```

---

## 🔌 快速開始

### 1. 安裝依賴

```bash
pip install fastapi uvicorn geoip2 itsdangerous
```

### 2. 創建安全配置

```python
from src.security import create_security_config_file

config_path = "config/security_config.json"
create_security_config_file(config_path)
```

### 3. 應用安全系統

```python
from fastapi import FastAPI
from src.security import setup_comprehensive_security

app = FastAPI()

# 應用全面安全系統
security_system = setup_comprehensive_security(
    app=app,
    config_path="config/security_config.json",
    enable_all=True
)
```

### 4. 啟動服務

```bash
python secure_complete_system.py
```

---

## ⚙️ 配置選項

### 完整配置示例

```json
{
  "rate_limit": {
    "enabled": true,
    "requests_per_minute": 60,
    "requests_per_hour": 1000,
    "burst_limit": 20,
    "per_endpoint_limits": {
      "/api/auth/login": 5,
      "/api/auth/register": 3,
      "/api/data/search": 30
    }
  },
  "ddos_protection": {
    "enabled": true,
    "threshold": 200,
    "block_duration": 3600,
    "auto_unblock": true
  },
  "ip_reputation": {
    "enabled": true,
    "geo_db_path": "/path/to/GeoLite2-City.mmdb",
    "block_low_score": 30,
    "auto_block_suspicious": true
  },
  "cors": {
    "enabled": true,
    "allowed_origins": [
      "http://localhost:3000",
      "http://localhost:8000"
    ],
    "allowed_methods": ["GET", "POST", "PUT", "DELETE", "PATCH"],
    "allowed_headers": ["*"],
    "expose_headers": ["X-RateLimit-*", "X-Request-ID"],
    "max_age": 86400
  },
  "security_headers": {
    "enabled": true,
    "strict_mode": true,
    "csp_enabled": true,
    "hsts_enabled": true
  },
  "waf": {
    "enabled": true,
    "strict_mode": true,
    "block_on_first_violation": true,
    "rules": {
      "sql_injection": {"enabled": true, "severity": 9},
      "xss": {"enabled": true, "severity": 8},
      "path_traversal": {"enabled": true, "severity": 7},
      "command_injection": {"enabled": true, "severity": 10}
    }
  },
  "response_filtering": {
    "enabled": true,
    "sanitize_errors": true,
    "hide_stack_traces": true,
    "remove_sensitive_data": true
  }
}
```

---

## 📊 監控與告警

### 安全事件API

**1. 獲取安全狀態**
```bash
GET /api/security/status
```

響應示例：
```json
{
  "status": "active",
  "version": "1.0.0",
  "features": {
    "rate_limiting": true,
    "ddos_protection": true,
    "waf": true,
    "ip_reputation": true,
    "input_validation": true,
    "cors": true
  }
}
```

**2. 獲取安全統計**
```bash
GET /api/security/stats
```

響應示例：
```json
{
  "attack_statistics": {
    "sql_injection": 15,
    "xss": 8,
    "ddos": 3
  },
  "blocked_ips_count": 12,
  "recent_events_count": 26
}
```

**3. 獲取安全事件**
```bash
GET /api/security/events?minutes=60
```

響應示例：
```json
{
  "events": [
    {
      "timestamp": "2025-01-01T12:00:00",
      "ip": "192.168.1.100",
      "attack_type": "sql_injection",
      "severity": 9,
      "path": "/api/test",
      "method": "POST",
      "blocked": true,
      "signature": "union_select"
    }
  ],
  "count": 1
}
```

**4. 安全儀表板**
```bash
GET /api/security/dashboard
```

響應示例：
```json
{
  "summary": {
    "total_attacks": 26,
    "blocked_ips": 12,
    "recent_events": 5
  },
  "attack_distribution": {
    "sql_injection": 15,
    "xss": 8,
    "ddos": 3
  },
  "top_attack_types": [
    ["sql_injection", 15],
    ["xss", 8],
    ["ddos", 3]
  ],
  "security_level": "MEDIUM_RISK"
}
```

**5. IP白名單管理**
```bash
POST /api/security/ips/whitelist
{
  "ip": "192.168.1.100",
  "reason": "trusted_partner"
}
```

**6. IP黑名單管理**
```bash
POST /api/security/ips/blacklist
{
  "ip": "192.168.1.200",
  "duration": 3600,
  "reason": "multiple_attacks"
}
```

**7. 獲取被封鎖IP**
```bash
GET /api/security/ips/blocked
```

響應示例：
```json
{
  "blocked_ips": [
    "192.168.1.200",
    "10.0.0.50"
  ],
  "count": 2
}
```

---

## 🧪 測試

### 運行安全測試

```bash
# 運行所有安全測試
pytest tests/security/test_api_security.py -v

# 運行特定測試
pytest tests/security/test_api_security.py::TestInputValidation::test_sql_injection_detection -v

# 生成覆蓋率報告
pytest tests/security/test_api_security.py --cov=src.security --cov-report=html
```

### 手動測試

**1. 測試SQL注入防護**
```bash
curl "http://localhost:8001/api/test?param='; DROP TABLE users; --"
# 期望響應: 400 Bad Request
```

**2. 測試XSS防護**
```bash
curl "http://localhost:8001/api/test?param=<script>alert('xss')</script>"
# 期望響應: 400 Bad Request
```

**3. 測試速率限制**
```bash
for i in {1..70}; do
  curl http://localhost:8001/api/test
done
# 期望響應: 429 Too Many Requests (在第60次之後)
```

**4. 測試CORS**
```bash
curl -H "Origin: http://evil.com" -H "Access-Control-Request-Method: POST" -X OPTIONS http://localhost:8001/api/test
# 期望響應: 沒有Access-Control-Allow-Origin頭
```

---

## 📈 性能優化

### 1. 緩存優化

**IP聲譽緩存**
```python
from functools import lru_cache

@lru_cache(maxsize=10000)
def get_cached_ip_reputation(ip: str) -> Dict:
    """緩存IP聲譽檢查結果"""
    return reputation_manager.check_ip(ip)
```

**WAF規則緩存**
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def check_malicious_pattern(pattern_type: str, data: str) -> bool:
    """緩存模式匹配結果"""
    return request_filter.check_pattern(pattern_type, data)
```

### 2. 異步處理

**非阻塞安全檢查**
```python
async def process_request_with_security(request: Request):
    # 並行執行安全檢查
    tasks = [
        check_rate_limit(request),
        check_ip_reputation(request),
        validate_input(request),
    ]
    results = await asyncio.gather(*tasks)

    if not all(results):
        raise HTTPException(403, "Security check failed")
```

### 3. 批處理

**批量IP檢查**
```python
async def batch_check_ip_reputation(ips: List[str]) -> Dict[str, Dict]:
    """批量檢查IP聲譽"""
    tasks = [check_ip_reputation(ip) for ip in ips]
    results = await asyncio.gather(*tasks)
    return dict(zip(ips, results))
```

---

## 🔒 最佳實踐

### 1. 密鑰管理

- **環境變量**：使用環境變量存儲敏感密鑰
- **密鑰輪換**：定期輪換JWT、CSRF等密鑰
- **最小權限**：只授予必要的權限
- **加密存儲**：使用加密算法存儲密鑰

**示例：**
```python
import os
from cryptography.fernet import Fernet

# 生成密鑰
secret_key = os.environ.get("SECRET_KEY")
if not secret_key:
    secret_key = Fernet.generate_key()

# 加密存儲
cipher = Fernet(secret_key)
encrypted_data = cipher.encrypt(b"secret_value")
```

### 2. 日誌管理

**結構化日誌**
```python
import structlog

logger = structlog.get_logger()

# 記錄安全事件
logger.info(
    "security_event",
    event_type="sql_injection_attempt",
    ip="192.168.1.100",
    path="/api/test",
    severity="high",
    blocked=True
)
```

**敏感數據脫敏**
```python
def sanitize_log_data(data: Dict) -> Dict:
    """日誌數據脫敏"""
    sensitive_fields = ["password", "token", "key", "secret"]
    sanitized = data.copy()

    for field in sensitive_fields:
        if field in sanitized:
            sanitized[field] = "[FILTERED]"

    return sanitized
```

### 3. 錯誤處理

**安全錯誤響應**
```python
def handle_security_error(error_type: str, details: str) -> JSONResponse:
    """處理安全錯誤"""
    # 記錄詳細錯誤
    logger.error(
        f"Security error: {error_type}",
        details=details,
        exc_info=True
    )

    # 返回通用錯誤信息
    return JSONResponse(
        status_code=400 if "validation" in error_type else 403,
        content={
            "error": "Request blocked by security policy",
            "code": "SECURITY_BLOCK",
            "timestamp": datetime.now().isoformat()
        }
    )
```

### 4. 配置管理

**環境特定配置**
```python
import os

ENV = os.environ.get("ENVIRONMENT", "development")

if ENV == "production":
    RATE_LIMIT = 30
    BLOCK_SUSPICIOUS_IPS = True
    STRICT_CORS = True
else:
    RATE_LIMIT = 100
    BLOCK_SUSPICIOUS_IPS = False
    STRICT_CORS = False
```

---

## 🚨 故障排除

### 常見問題

**1. 速率限制過於嚴格**
```
問題: 正常用戶被誤封
解決: 調整rate_limit參數，增加白名單
```

**2. WAF誤報**
```
問題: 正常請求被阻擋
解決: 檢查waf_rules配置，添加例外規則
```

**3. CORS錯誤**
```
問題: 前端無法訪問API
解決: 檢查allowed_origins配置
```

**4. 性能下降**
```
問題: 安全檢查導致延遲
解決: 啟用緩存，優化異步處理
```

### 日誌分析

**查看安全日誌**
```bash
tail -f logs/security.log | grep "SECURITY"
```

**分析攻擊模式**
```bash
grep "sql_injection" logs/security.log | awk '{print $5}' | sort | uniq -c | sort -nr
```

**統計被封鎖IP**
```bash
grep "blocked" logs/security.log | awk '{print $6}' | sort | uniq -c | sort -nr
```

---

## 📚 參考資源

### OWASP資源
- [OWASP API Security Top 10](https://owasp.org/API-Security/)
- [OWASP Top 10 Web App Security Risks](https://owasp.org/Top10/)
- [OWASP Secure Coding Practices](https://owasp.org/www-project-secure-coding-practices-quick-reference-guide/)

### 技術文檔
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Web Application Firewall (WAF)](https://en.wikipedia.org/wiki/Web_application_firewall)
- [Rate Limiting Algorithms](https://cloud.google.com/architecture/rate-limiting-strategies-techniques)

### 安全工具
- [SQLMap](https://sqlmap.org/) - 自動SQL注入檢測
- [OWASP ZAP](https://www.zaproxy.org/) - 滲透測試
- [Bandit](https://bandit.readthedocs.io/) - Python安全分析

---

## 📝 更新日誌

| 日期 | 版本 | 變更 |
|------|------|------|
| 2025-01-01 | 1.0.0 | 初始版本發布 |
| | | |
| | | |

---

## 📄 許可證

MIT License

---

## 🤝 貢獻

歡迎提交Issue和Pull Request來改進安全系統。

---

## 📧 聯繫方式

- 作者: Claude Code
- 郵箱: security@quant-system.com
- 項目: 港股量化交易系統

---

**⚠️ 安全提醒：**
本系統提供多層次安全防護，但安全是一個持續的過程。請定期更新安全規則、監控日誌、並根據新的威脅調整配置。
