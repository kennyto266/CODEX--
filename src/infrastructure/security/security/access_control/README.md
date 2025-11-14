# 港股量化交易系統 - 訪問控制與權限管理

## 概述

本模塊提供了一套完整的訪問控制和權限管理系統，滿足T096-T100五個任務要求：

- **T096**: 基於角色的訪問控制 (RBAC)
- **T097**: 基於屬性的訪問控制 (ABAC)
- **T098**: 多因素認證 (MFA)
- **T099**: 會話管理
- **T100**: API訪問控制

系統採用分層安全架構，確保最小權限原則、防禦深度和故障安全默認設置。

## 架構圖

```
┌─────────────────────────────────────────────────────────┐
│                   前端應用 (Vue.js)                      │
└──────────┬──────────────┬──────────────┬────────────────┘
           │              │              │
┌──────────▼──────────┐  │  ┌──────────▼──────────┐
│  Vue Router Guards  │  │  │  HTTP Bearer Token  │
└──────────┬──────────┘  │  └──────────┬──────────┘
           │              │             │
           │              │             │
┌──────────▼──────────────────────────────────────────┐
│              FastAPI 應用服務器                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  Authentication│  │  Authorization│  │  API Access   │ │
│  │   Middleware  │  │   Middleware  │  │  Middleware   │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  MFA Support │  │   ABAC Engine│  │  Rate Limiter │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└──────────┬─────────────────────────────────────────────┘
           │
┌──────────▼─────────────────────────────────────────────┐
│              訪問控制管理器                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │  RBAC   │ │  ABAC   │ │   MFA   │ │  Session │  │
│  │ Manager │ │ Manager │ │ Manager │ │ Manager  │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
│  ┌──────────┐                                     │
│  │  API    │                                     │
│  │ Manager │                                     │
│  └──────────┘                                     │
└──────────┬─────────────────────────────────────────┘
           │
┌──────────▼─────────────────────────────────────────┐
│              數據存儲層                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │   RBAC   │ │   MFA   │ │ Session  │           │
│  │    DB    │ │   DB    │ │   DB     │           │
│  └──────────┘ └──────────┘ └──────────┘           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ ABAC     │ │  Audit   │ │ Redis    │           │
│  │ Policies │ │  Logs    │ │  Cache   │           │
│  └──────────┘ └──────────┘ └──────────┘           │
└─────────────────────────────────────────────────────┘
```

## 核心特性

### 1. 基於角色的訪問控制 (RBAC)

#### 角色層次結構

```
admin
├── trader
├── analyst
├── risk_manager
├── auditor
└── viewer
    └── guest
```

#### 預定義角色

| 角色 | 權限 | 描述 |
|------|------|------|
| admin | 所有權限 | 系統管理員 |
| trader | 交易執行、組合管理 | 交易員 |
| analyst | 數據分析、策略研究 | 分析師 |
| risk_manager | 風險控制、合規管理 | 風險管理員 |
| auditor | 審計、監控 | 審計員 |
| viewer | 僅查看權限 | 查看者 |
| guest | 公開數據 | 訪客 |

#### 使用示例

```python
from src.security.access_control import RBACManager

# 創建RBAC管理器
rbac = RBACManager("rbac.db")

# 獲取用戶角色
user_roles = rbac.get_user_roles("user_id_123")

# 檢查權限
has_permission = rbac.user_has_permission(
    "user_id_123",
    "trade:execute"
)

# 分配角色
admin_role = rbac.get_role_by_name("trader")
rbac.assign_role_to_user(
    user_id="user_id_123",
    role_id=admin_role.id,
    assigned_by="admin"
)
```

### 2. 基於屬性的訪問控制 (ABAC)

#### 屬性類型

- **用戶屬性**: 角色、部門、職級
- **資源屬性**: 分類、類型、所有者
- **環境屬性**: 時間、IP、地理位置
- **操作屬性**: 風險等級、併發數

#### 策略示例

```python
from src.security.access_control import ABACManager, Context, PolicyEffect

abac = ABACManager("abac_policies.json")

# 創建上下文
context = Context(
    user_id="user_123",
    user_attributes={"role": "trader"},
    resource="/api/v1/portfolio",
    resource_attributes={"classification": "sensitive"},
    action="read",
    action_attributes={"risk_level": 2},
    environment="prod",
    environment_attributes={
        "hour": 14,  # 工作時間
        "ip": "192.168.1.100"
    },
    timestamp=datetime.now(),
    request_id="req_001"
)

# 評估訪問
result = await abac.evaluate_access(context)

if result == PolicyEffect.PERMIT:
    # 允許訪問
    pass
else:
    # 拒絕訪問
    raise HTTPException(403, "Access Denied")
```

### 3. 多因素認證 (MFA)

#### 支持的認證方法

- **TOTP**: Google Authenticator、Authy等
- **SMS**: 短信驗證碼
- **Email**: 郵件驗證碼
- **硬件令牌**: YubiKey等
- **生物識別**: 指紋、面部識別
- **備份代碼**: 一次性備份代碼

#### 使用示例

```python
from src.security.access_control import MFAManager, MFAMethodType

mfa = MFAManager("mfa.db")

# 設置TOTP
secret, qr_code = await mfa.setup_totp(
    "user_123",
    "user@example.com"
)

# 驗證TOTP令牌
is_valid = await mfa.verify_totp("user_123", "123456")

# 信任設備
mfa.trust_device("user_123", "device_001")
```

### 4. 會話管理

#### 特性

- 安全令牌生成 (JWT)
- 會話超時控制
- 並發會話限制
- 會話固定攻擊防護
- 會話劫持防護
- 單點登錄 (SSO)

#### 使用示例

```python
from src.security.access_control import SessionManager

session = SessionManager("sessions.db")

# 創建會話
session_obj, access_token, refresh_token, id_token = session.create_session(
    user_id="user_123",
    ip_address="192.168.1.1",
    user_agent="Mozilla/5.0",
    device_id="device_001",
    device_name="Workstation"
)

# 更新活動
session.update_activity(session_obj.session_id)

# 終止會話
session.terminate_session(session_obj.session_id)

# 獲取用戶所有會話
user_sessions = session.get_user_sessions("user_123")
```

### 5. API訪問控制

#### 功能

- API密鑰管理
- 權限範圍控制
- 速率限制
- 請求簽名 (HMAC)
- OAuth 2.0 / OpenID Connect
- API版本控制

#### 使用示例

```python
from src.security.access_control import APIAccessManager

api = APIAccessManager("api.db")

# 生成API密鑰
api_key, api_key_obj = api.generate_api_key(
    user_id="user_123",
    name="My API Key",
    scopes=["data:read", "portfolio:view"],
    rate_limit=100
)

# 驗證API密鑰
validated_key = api.validate_api_key(api_key)

# 檢查速率限制
is_limited, rate_info = api.check_rate_limit(
    validated_key,
    "/api/v1/data",
    "GET"
)
```

## 快速開始

### 1. 初始化訪問控制系統

```python
from src.security.access_control.middleware import AccessControlManager

# 創建訪問控制管理器
access_control = AccessControlManager(
    rbac_db_path="data/rbac.db",
    mfa_db_path="data/mfa.db",
    session_db_path="data/sessions.db",
    api_db_path="data/api.db",
    abac_policy_path="data/abac_policies.json"
)
```

### 2. 添加中間件到FastAPI

```python
from fastapi import FastAPI

app = FastAPI()

# 添加訪問控制中間件
for middleware in access_control.get_middleware():
    app.add_middleware(middleware)
```

### 3. 使用依賴注入

```python
from fastapi import Depends

# 獲取當前用戶
async def get_current_user(user: dict = Depends(access_control.create_access_control_depends()['get_current_user'])):
    return user

# 權限依賴
require_permission = access_control.create_access_control_depends()['require_permission']

@app.get("/api/v1/protected")
async def protected_endpoint(
    current_user: dict = Depends(get_current_user),
    _: None = Depends(require_permission("data:read"))
):
    return {"message": "Protected data"}
```

### 4. 創建API密鑰

```python
# 為用戶創建API密鑰
api_key, key_obj = access_control.api_access_manager.generate_api_key(
    user_id="user_123",
    name="Production API Key",
    scopes=["data:read", "trade:execute"],
    rate_limit=60
)

# 在API請求中使用
headers = {
    "X-API-Key": api_key,
    "Authorization": f"Bearer {access_token}"
}
```

## 數據庫架構

### 主要表

1. **roles** - 角色表
2. **permissions** - 權限表
3. **user_roles** - 用戶角色關聯
4. **role_permissions** - 角色權限關聯
5. **abac_policies** - ABAC策略
6. **mfa_methods** - MFA方法
7. **backup_codes** - 備份代碼
8. **sessions** - 會話表
9. **api_keys** - API密鑰表
10. **audit_logs** - 審計日誌

完整的SQL架構請參考 `database_schema.sql` 文件。

## 配置

### 配置文件結構 (config.yaml)

```yaml
# 數據庫配置
database:
  rbac:
    path: "data/rbac.db"
  mfa:
    path: "data/mfa.db"
  session:
    path: "data/sessions.db"
  api:
    path: "data/api.db"

# 會話管理
session:
  idle_timeout: 1800  # 30分鐘
  absolute_timeout: 86400  # 24小時
  max_concurrent_sessions: 5

# MFA配置
mfa:
  enabled: true
  required_for_roles: ["admin", "trader", "risk_manager"]
  methods:
    totp:
      enabled: true
    sms:
      enabled: true
    backup_codes:
      enabled: true
      count: 10

# 速率限制
rate_limit:
  default_limit: 60
  default_window: 60
```

## 安全最佳實踐

### 1. 密碼策略

- 最小長度: 12個字符
- 必須包含: 大寫、小寫、數字、特殊字符
- 密碼過期: 90天
- 密碼歷史: 不能重複使用最近5個密碼
- 鎖定策略: 連續5次失敗後鎖定15分鐘

### 2. 會話安全

- 使用HTTPS傳輸所有認證令牌
- 設置適當的會話超時時間
- 限制並發會話數量
- 實現會話固定攻擊防護
- 記錄所有會話活動

### 3. API安全

- 要求所有API請求使用HTTPS
- 實施速率限制防止暴力攻擊
- 使用HMAC簽名驗證請求完整性
- 定期輪換API密鑰
- 監控API使用情況

### 4. 審計和監控

- 記錄所有認證和授權事件
- 監控異常登錄模式
- 設置可疑活動警報
- 定期審查訪問日誌
- 實施數據防泄露 (DLP)

## 測試

### 運行測試

```bash
# 運行所有測試
pytest tests/test_access_control.py -v

# 運行特定測試
pytest tests/test_access_control.py::TestRBAC -v
pytest tests/test_access_control.py::TestMFA -v
pytest tests/test_access_control.py::TestSession -v
```

### 測試覆蓋範圍

- ✅ RBAC角色管理
- ✅ ABAC策略評估
- ✅ MFA認證流程
- ✅ 會話管理
- ✅ API訪問控制
- ✅ 集成測試
- ✅ 端到端測試

## 部署

### 1. 環境準備

```bash
# 安裝依賴
pip install fastapi uvicorn redis PyJWT pyotp qrcode redis

# 創建數據目錄
mkdir -p data logs
```

### 2. 初始化數據庫

```python
# 運行初始化腳本
from src.security.access_control.example_usage import init_example_data

asyncio.run(init_example_data())
```

### 3. 啟動應用

```bash
# 啟動FastAPI服務
uvicorn example_usage:app --host 0.0.0.0 --port 8001 --reload
```

### 4. Docker部署

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

EXPOSE 8001
CMD ["uvicorn", "example_usage:app", "--host", "0.0.0.0", "--port", "8001"]
```

## 監控和指標

### 關鍵指標

- 活躍會話數
- 每日/每小時登錄嘗試
- API請求量和錯誤率
- 權限拒絕次數
- MFA驗證成功率
- 異常活動檢測

### 告警

- 連續登錄失敗
- 異常地理位置登錄
- 會話異常增加
- API密鑰濫用
- 權限提升嘗試

## 合規性

### 支持的合規框架

- **GDPR**: 數據保護和隱私權
- **SOX**: 金融報告控制
- **ISO 27001**: 信息安全管理
- **PCI DSS**: 支付卡行業數據安全

### 數據保護

- 個人數據加密存儲
- 數據保留策略
- 數據最小化原則
- 刪除權 (Right to be Forgotten)
- 數據可攜權 (Data Portability)

## 故障排除

### 常見問題

#### 1. 會話過期過快

**問題**: 會話在空閒超時前被終止

**解決方案**:
- 檢查會話更新頻率
- 調整 idle_timeout 設置
- 檢查Redis連接（如果使用）

```python
session = SessionManager(
    idle_timeout=3600,  # 調整為1小時
    absolute_timeout=86400
)
```

#### 2. MFA驗證失敗

**問題**: TOTP令牌無效

**解決方案**:
- 檢查設備時間同步
- 重新設置TOTP
- 使用備份代碼

```python
# 重新設置TOTP
secret, qr_code = await mfa.setup_totp("user_id", "email@example.com")
```

#### 3. API密鑰無效

**問題**: API密鑰被拒絕

**解決方案**:
- 檢查密鑰格式 (prefix_key)
- 確認密鑰未過期/撤銷
- 驗證IP白名單

```python
# 重新生成API密鑰
api_key, key_obj = api.generate_api_key(
    user_id="user_id",
    name="New Key"
)
```

### 日誌分析

```bash
# 查看審計日誌
tail -f logs/audit.log

# 查找登錄失敗
grep "login_failed" logs/audit.log

# 查找權限拒絕
grep "permission_denied" logs/audit.log
```

## 性能優化

### 1. 緩存

- 使用Redis緩存會話
- 緩存權限檢查結果
- 緩存ABAC策略評估

### 2. 數據庫優化

- 為常用查詢添加索引
- 定期清理過期會話
- 歸檔舊審計日誌

### 3. 並發處理

- 使用連接池
- 實施異步處理
- 分散式鎖定

## 擴展

### 添加自定義MFA方法

```python
class CustomMFAProvider:
    async def send_challenge(self, user_id: str, challenge: str) -> bool:
        # 自定義挑戰發送邏輯
        pass

    async def verify_challenge(self, user_id: str, response: str) -> bool:
        # 自定義挑戰驗證邏輯
        pass
```

### 添加自定義ABAC策略

```python
def custom_policyEvaluator(context: Context) -> PolicyEffect:
    # 實現自定義策略邏輯
    if context.environment_attributes.get("maintenance_mode"):
        return PolicyEffect.DENY
    return PolicyEffect.PERMIT
```

## 支持

如有問題或需要支持，請聯繫：

- 郵箱: security@quant-system.com
- 問題追蹤: [GitHub Issues](https://github.com/quant-system/security/issues)
- 文檔: [完整文檔](https://docs.quant-system.com/access-control)

## 版本歷史

| 版本 | 日期 | 更新內容 |
|------|------|----------|
| 1.0.0 | 2025-11-09 | 初始版本 - 完整訪問控制系統 |
| 1.1.0 | 2025-11-10 | (計劃) 添加生物識別支持 |
| 1.2.0 | 2025-11-15 | (計劃) 支持OAuth 2.1 |

## 許可證

本項目採用 MIT 許可證。詳見 LICENSE 文件。
