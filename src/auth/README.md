# 企業級身份驗證與授權系統

## 概述

這是一個完整的企業級身份驗證與授權系統，實現了現代化的安全認證機制，包括JWT、OAuth 2.0、API密鑰管理、證書管理等功能。系統遵循OWASP、NIST等安全最佳實踐，提供銀行級別的安全保障。

## 核心功能

### ✅ T106: JWT 認證系統
- **訪問令牌**：短生命周期（15-30分鐘）
- **刷新令牌**：長生命周期（7-30天）
- **令牌輪換**：自動刷新機制
- **令牌黑名單**：登出時撤銷令牌
- **JTI追蹤**：唯一令牌標識
- **自定義聲明**：基於角色的訪問控制
- **多算法支持**：RS256、ES256、HS256、PS256

### ✅ T107: OAuth 2.0 / OpenID Connect
- **多身份提供者**：Google、Microsoft、GitHub、Facebook、Apple
- **授權碼流程**：標準OAuth 2.0流程
- **PKCE支持**：增強安全性
- **令牌管理**：自動刷新和撤銷
- **用戶信息映射**：自動創建/關聯用戶
- **Scope控制**：細粒度權限管理

### ✅ T108: 密碼安全
- **密碼策略**：12+字符、複雜度要求
- **密碼哈希**：Argon2id（推薦）、Bcrypt、Scrypt
- **密碼歷史**：防止重複使用
- **密碼到期**：可選90天到期
- **暴力破解防護**：賬戶鎖定機制
- **密碼強度檢查**：實時評估
- **密碼重置**：安全重置流程
- **MFA支持**：TOTP和備用碼

### ✅ T109: API密鑰管理
- **密鑰生成**：加密安全生成
- **密鑰版本控制**：支持多版本
- **密鑰輪換**：定期自動輪換
- **範圍管理**：細粒度權限控制
- **速率限制**：每小時/每天限制
- **IP白名單**：IP地址過濾
- **使用追蹤**：詳細使用記錄
- **密鑰撤銷**：即時撤銷機制

### ✅ T110: 證書管理（PKI）
- **CA證書**：自簽名CA或外部CA
- **SSL/TLS證書**：服務器和客戶端證書
- **CSR支持**：證書簽名請求
- **證書鏈驗證**：完整鏈驗證
- **證書撤銷**：CRL和OCSP
- **自動續期**：智能續期提醒
- **指紋驗證**：SHA256/SHA1指紋
- **多算法**：RSA、ECDSA、Ed25519

## 架構設計

```
┌─────────────────────────────────────────────────────────────┐
│                    認證系統架構                              │
├─────────────────────────────────────────────────────────────┤
│  API 層                                                    │
│  ├── /auth/login          - 用戶登錄                        │
│  ├── /auth/register       - 用戶註冊                        │
│  ├── /auth/token/*        - 令牌管理                        │
│  ├── /auth/api-keys/*     - API密鑰管理                     │
│  ├── /auth/oauth/*        - OAuth流程                       │
│  └── /auth/certificates/* - 證書管理                        │
├─────────────────────────────────────────────────────────────┤
│  中間件層                                                  │
│  ├── AuthenticationMiddleware  - 認證中間件                  │
│  ├── CORSMiddleware          - CORS處理                     │
│  └── SecurityHeaders         - 安全頭部                     │
├─────────────────────────────────────────────────────────────┤
│  業務邏輯層                                                │
│  ├── AuthService      - 認證服務                            │
│  ├── UserService      - 用戶服務                            │
│  └── TokenService     - 令牌服務                            │
├─────────────────────────────────────────────────────────────┤
│  管理器層                                                  │
│  ├── JWTManager       - JWT管理                            │
│  ├── PasswordManager  - 密碼管理                            │
│  ├── APIKeyManager    - API密鑰管理                         │
│  ├── OAuthManager     - OAuth管理                           │
│  └── CertificateManager - 證書管理                          │
├─────────────────────────────────────────────────────────────┤
│  核心層                                                    │
│  ├── SecurityManager  - 安全核心                            │
│  └── AuthConfig       - 配置管理                            │
├─────────────────────────────────────────────────────────────┤
│  數據層                                                    │
│  ├── 用戶模型          - User, UserSession                  │
│  ├── 令牌模型          - Token, TokenBlacklist              │
│  ├── OAuth模型         - OAuthToken, OAuthUser              │
│  ├── API密鑰模型       - APIKey, APIKeyUsage                │
│  ├── 證書模型          - Certificate, CertificateRequest    │
│  └── 安全事件模型      - SecurityEvent                      │
└─────────────────────────────────────────────────────────────┘
```

## 快速開始

### 1. 安裝依賴

```bash
# 安裝核心依賴
pip install -r requirements.txt

# 安裝額外的安全庫
pip install python-jose[cryptography] passlib[bcrypt] argon2-cffi
```

### 2. 配置環境變量

創建 `.env` 文件：

```env
# JWT配置
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=RS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
JWT_ISSUER=hk-quant-system
JWT_AUDIENCE=hk-quant-system-users

# OAuth配置
OAUTH_GOOGLE_CLIENT_ID=your-google-client-id
OAUTH_GOOGLE_CLIENT_SECRET=your-google-client-secret
OAUTH_REDIRECT_URI=http://localhost:8001/auth/callback

# 密碼安全
PASSWORD_MIN_LENGTH=12
PASSWORD_HASH_ALGORITHM=argon2id
PASSWORD_EXPIRATION_DAYS=90
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=30

# API密鑰
API_KEY_PREFIX=hkqs
API_KEY_DEFAULT_EXPIRATION_DAYS=90
API_KEY_DEFAULT_RATE_LIMIT=1000

# 證書管理
CERT_VALIDITY_DAYS=365
CERT_RENEWAL_THRESHOLD_DAYS=30
```

### 3. 初始化數據庫

```python
from src.auth.models import Base
from src.database import engine

# 創建所有表
Base.metadata.create_all(bind=engine)
```

### 4. 集成到FastAPI

```python
from fastapi import FastAPI
from src.auth.core.config import AuthConfig
from src.auth.core.security import SecurityManager
from src.auth.routes import router, initialize_auth_components
from src.database import SessionLocal

app = FastAPI(title="HK Quant System")

# 初始化認證組件
config = AuthConfig()
security = SecurityManager(config)
db = SessionLocal()

initialize_auth_components(config, security, db)

# 添加認證路由
app.include_router(router)

# 添加認證中間件
from src.auth.middleware.auth import AuthenticationMiddleware
app.add_middleware(AuthenticationMiddleware, config=config, security=security, db_session=db)
```

## API使用示例

### 用戶認證

#### 1. 用戶註冊

```bash
curl -X POST "http://localhost:8001/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "testuser",
    "password": "TestPassword123!",
    "password_confirm": "TestPassword123!",
    "full_name": "Test User"
  }'
```

#### 2. 用戶登錄

```bash
curl -X POST "http://localhost:8001/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "TestPassword123!"
  }'
```

響應：
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 900,
  "expires_at": "2024-01-01T12:15:00"
}
```

#### 3. 刷新令牌

```bash
curl -X POST "http://localhost:8001/auth/token/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }'
```

#### 4. 登出

```bash
curl -X POST "http://localhost:8001/auth/logout" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### API密鑰管理

#### 1. 創建API密鑰

```bash
curl -X POST "http://localhost:8001/auth/api-keys" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Trading API Key",
    "description": "Key for trading operations",
    "scopes": ["read:data", "write:trades"],
    "expiration_days": 90,
    "rate_limit_per_hour": 1000
  }'
```

響應：
```json
{
  "id": 1,
  "key_id": "hkqs_1234567890_abcdef",
  "secret_key": "hkqs_1234567890_abcdef.secret123",
  "name": "Trading API Key",
  "scopes": ["read:data", "write:trades"],
  "expires_at": "2024-04-01T00:00:00",
  "created_at": "2024-01-01T00:00:00"
}
```

#### 2. 使用API密鑰

```bash
curl -X GET "http://localhost:8001/api/trades" \
  -H "X-API-Key: hkqs_1234567890_abcdef.secret123"
```

#### 3. 查看API密鑰列表

```bash
curl -X GET "http://localhost:8001/auth/api-keys" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### 4. 查看API密鑰使用統計

```bash
curl -X GET "http://localhost:8001/auth/api-keys/hkqs_1234567890_abcdef/statistics" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### OAuth 2.0

#### 1. 開始OAuth流程

```bash
curl -X GET "http://localhost:8001/auth/oauth/google/authorize" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -G -d "state=RANDOM_STATE"
```

響應：
```json
{
  "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?...",
  "state": "RANDOM_STATE"
}
```

#### 2. OAuth回調處理

```bash
curl -X POST "http://localhost:8001/auth/oauth/google/callback" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "AUTH_CODE",
    "state": "RANDOM_STATE"
  }'
```

### 證書管理

#### 1. 創建證書

```bash
curl -X POST "http://localhost:8001/auth/certificates" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Server Certificate",
    "subject_cn": "server.example.com",
    "subject_o": "HK Quant System",
    "subject_c": "HK",
    "san_dns_names": ["server.example.com", "api.example.com"],
    "algorithm": "RSA",
    "key_size": 2048,
    "validity_days": 365
  }'
```

#### 2. 驗證證書

```bash
curl -X POST "http://localhost:8001/auth/certificates/verify" \
  -H "Content-Type: application/json" \
  -d '{
    "certificate_pem": "-----BEGIN CERTIFICATE-----\n..."
  }'
```

#### 3. 創建CSR

```bash
curl -X POST "http://localhost:8001/auth/csr" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Client Certificate",
    "subject_cn": "client@example.com",
    "subject_o": "HK Quant System",
    "algorithm": "RSA",
    "key_size": 2048
  }'
```

## 安全功能

### 1. 密碼策略

系統強制執行強密碼策略：
- 最少12個字符
- 包含大小寫字母
- 包含數字
- 包含特殊字符
- 檢查常見密碼
- 防止模式匹配

### 2. 賬戶安全

- 登錄失敗鎖定（5次失敗後鎖定30分鐘）
- 密碼到期提醒
- 暴力破解檢測
- 可疑登錄檢測
- 設備指紋追蹤

### 3. 令牌安全

- 短生命周期訪問令牌（15分鐘）
- 長生命周期刷新令牌（7天）
- 令牌輪換
- 令牌黑名單
- JTI追蹤
- 多算法支持

### 4. API密鑰安全

- 加密安全生成
- IP白名單
- 速率限制
- 使用追蹤
- 自動輪換
- 範圍控制

### 5. 證書安全

- CA證書管理
- 證書鏈驗證
- 證書撤銷
- 自動續期
- 指紋驗證
- 多算法支持

## 數據模型

### 用戶模型

```python
class User(Base):
    id: int
    email: str
    username: str
    full_name: str
    hashed_password: str
    role: str
    is_active: bool
    is_verified: bool
    mfa_enabled: bool
    last_login: datetime
    password_expires_at: datetime
    # ...更多字段
```

### 令牌模型

```python
class Token(Base):
    jti: str  # JWT ID
    token_type: str  # access, refresh
    user_id: int
    subject: str
    audience: str
    issuer: str
    issued_at: datetime
    expires_at: datetime
    revoked_at: datetime
    # ...更多字段
```

### API密鑰模型

```python
class APIKey(Base):
    key_id: str
    hashed_key: str
    name: str
    scopes: List[APIKeyScope]
    expires_at: datetime
    rate_limit_per_hour: int
    ip_whitelist: List[str]
    usage_count: int
    # ...更多字段
```

### 證書模型

```python
class Certificate(Base):
    serial_number: str
    type: CertificateType
    certificate_pem: str
    private_key_pem: str
    subject_cn: str
    issuer_cn: str
    not_before: datetime
    not_after: datetime
    sha256_fingerprint: str
    # ...更多字段
```

## 安全事件追蹤

系統記錄所有安全相關事件：

- 登錄成功/失敗
- 令牌創建/撤銷
- 密碼更改/重置
- 賬戶鎖定/解鎖
- API密鑰使用
- OAuth登錄
- 證書操作
- 可疑活動

查看安全日誌：

```bash
# 查看安全事件
tail -f security.log | grep "Security Event"

# 查詢特定用戶的安全事件
grep "user_id=12345" security.log
```

## 測試

### 運行測試

```bash
# 運行所有認證測試
pytest tests/test_auth/ -v

# 運行特定測試
pytest tests/test_auth/test_jwt.py -v

# 運行測試並生成覆蓋率報告
pytest tests/test_auth/ --cov=src.auth --cov-report=html
```

### 測試用例

測試套件包括：

1. **JWT測試**
   - 令牌生成和驗證
   - 令牌撤銷
   - 令牌輪換
   - 令牌黑名單

2. **密碼管理測試**
   - 密碼哈希和驗證
   - 密碼強度檢查
   - 密碼歷史
   - 密碼重置

3. **API密鑰測試**
   - 密鑰生成
   - 密鑰驗證
   - 範圍檢查
   - 速率限制

4. **OAuth測試**
   - OAuth流程
   - 用戶信息映射
   - 令牌管理

5. **證書測試**
   - 證書生成
   - 證書驗證
   - CSR處理

## 最佳實踐

### 1. 密碼安全

- 使用Argon2id進行密碼哈希
- 強制執行強密碼策略
- 定期檢查密碼強度
- 啟用密碼到期（90天）
- 監控密碼重置請求

### 2. 令牌安全

- 使用RS256或ES256算法
- 設置短生命周期訪問令牌
- 實施令牌黑名單
- 監控令牌使用
- 定期輪換刷新令牌

### 3. API密鑰安全

- 使用加密安全隨機數生成器
- 設置適當的過期時間
- 實施IP白名單
- 監控API使用
- 定期輪換密鑰

### 4. 證書安全

- 使用強加密算法（RSA 2048+或ECDSA）
- 定期更新證書
- 監控證書到期
- 實施證書撤銷
- 驗證證書鏈

### 5. 監控和審計

- 啟用安全日誌
- 監控異常登錄
- 審計API使用
- 追蹤密鑰使用
- 定期審查安全事件

## 常見問題

### Q: 如何重置管理員密碼？

A: 使用密碼重置功能或直接操作數據庫：

```python
from src.auth.password.manager import PasswordManager
from src.auth.models.user import User

# 獲取用戶
user = db.query(User).filter_by(email="admin@example.com").first()

# 重置密碼
password_manager = PasswordManager(config, security)
hashed = password_manager.hash_password("NewAdmin123!")
user.hashed_password = hashed
db.commit()
```

### Q: 如何撤銷所有用戶令牌？

A: 使用JWT管理器的撤銷功能：

```python
from src.auth.jwt.manager import JWTManager

jwt_manager = JWTManager(config, security, db)
count = jwt_manager.revoke_all_user_tokens(user_id, reason="Security incident")
print(f"Revoked {count} tokens")
```

### Q: 如何監控API密鑰使用？

A: 查詢API使用統計：

```python
from src.auth.api_keys.manager import APIKeyManager

api_key_manager = APIKeyManager(config, security, db)
stats = api_key_manager.get_api_key_statistics(key_id)
print(stats)
```

### Q: 如何啟用MFA？

A: 生成MFA密鑰：

```python
from src.auth.password.manager import PasswordManager

password_manager = PasswordManager(config, security)
secret = password_manager.generate_mfa_secret()
backup_codes = password_manager.generate_backup_codes(10)

# 配置用戶
user.mfa_secret = secret
user.mfa_backup_codes = json.dumps(backup_codes)
db.commit()
```

### Q: 如何查看安全事件？

A: 查詢安全事件表：

```python
from src.auth.models.security_event import SecurityEvent
from sqlalchemy import desc

events = db.query(SecurityEvent).filter_by(
    user_id=user_id
).order_by(desc(SecurityEvent.timestamp)).limit(100).all()

for event in events:
    print(f"{event.timestamp}: {event.event_type} - {event.description}")
```

## 性能優化

### 1. 令牌緩存

啟用令牌緩存以減少數據庫查詢：

```python
# 在配置中啟用
TOKEN_CACHE_ENABLED=True
TOKEN_CACHE_EXPIRE_SECONDS=300
```

### 2. 速率限制

使用Redis進行高效的速率限制：

```python
# 實現基於Redis的速率限制
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def check_rate_limit(api_key_id, limit=100, window=3600):
    key = f"rate_limit:{api_key_id}"
    current = redis_client.get(key)
    if current and int(current) >= limit:
        return False
    redis_client.incr(key)
    redis_client.expire(key, window)
    return True
```

### 3. 數據庫優化

- 為常用查詢字段添加索引
- 使用連接池
- 實施查詢緩存
- 定期清理過期數據

## 部署指南

### 1. 生產環境配置

```env
# 生產環境配置示例
ENVIRONMENT=production

# JWT配置（使用強密鑰）
JWT_SECRET_KEY=<64-byte-random-key>
JWT_ALGORITHM=RS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# 密碼安全
PASSWORD_HASH_ALGORITHM=argon2id
PASSWORD_HASH_MEMORY_KB=65536
PASSWORD_HASH_TIME_COST=3
PASSWORD_HASH_PARALLELISM=1
PASSWORD_EXPIRATION_DAYS=90

# API密鑰
API_KEY_PREFIX=hkqs_prod
API_KEY_DEFAULT_EXPIRATION_DAYS=90
API_KEY_DEFAULT_RATE_LIMIT=1000

# 證書
CERT_VALIDITY_DAYS=365
CERT_RENEWAL_THRESHOLD_DAYS=30
```

### 2. 安全檢查清單

- [ ] 使用強JWT密鑰（64字節隨機）
- [ ] 配置HTTPS
- [ ] 設置安全頭部
- [ ] 啟用CORS
- [ ] 配置防火牆
- [ ] 啟用審計日誌
- [ ] 配置監控告警
- [ ] 測試密碼策略
- [ ] 驗證令牌安全
- [ ] 檢查API密鑰權限
- [ ] 測試證書管理

### 3. 監控指標

監控以下關鍵指標：

1. **認證指標**
   - 登錄成功率
   - 登錄失敗率
   - 令牌生成量
   - 令牌驗證成功率

2. **安全指標**
   - 暴力破解嘗試
   - 異常登錄
   - 密碼重置請求
   - 賬戶鎖定次數

3. **性能指標**
   - API響應時間
   - 數據庫查詢時間
   - 令牌驗證延遲
   - 緩存命中率

## 許可證

MIT License

## 支持

如有問題，請聯繫開發團隊或查看文檔。

## 更新日誌

### v5.0.0 (2024-11-09)
- 初始版本
- 實現JWT認證
- 實現OAuth 2.0
- 實現密碼安全
- 實現API密鑰管理
- 實現證書管理
- 完整測試套件
