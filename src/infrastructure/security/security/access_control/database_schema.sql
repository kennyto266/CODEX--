-- 港股量化交易系統 - 訪問控制數據庫架構
-- 包含RBAC、ABAC、MFA、會話管理和API訪問控制所有表

-- ========================
-- RBAC 角色基於訪問控制
-- ========================

-- 角色表
CREATE TABLE roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    role_type TEXT NOT NULL, -- admin, trader, analyst, viewer, guest, auditor, risk_manager
    description TEXT,
    parent_role_id INTEGER,
    is_system_role BOOLEAN DEFAULT FALSE,
    permissions TEXT, -- JSON數組
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT, -- JSON
    FOREIGN KEY (parent_role_id) REFERENCES roles(id)
);

-- 權限表
CREATE TABLE permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    code TEXT UNIQUE NOT NULL, -- 權限代碼，如 "data:read"
    description TEXT,
    resource TEXT NOT NULL, -- 資源類型
    action TEXT NOT NULL, -- 操作類型
    scope TEXT NOT NULL, -- global, department, project, resource, own
    conditions TEXT, -- JSON條件
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用戶角色關聯表
CREATE TABLE user_roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL, -- 用戶ID（可以是UUID或username）
    role_id INTEGER NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by TEXT NOT NULL, -- 分配者ID
    expires_at TIMESTAMP, -- 過期時間
    is_active BOOLEAN DEFAULT TRUE,
    metadata TEXT, -- JSON
    FOREIGN KEY (role_id) REFERENCES roles(id),
    UNIQUE(user_id, role_id)
);

-- 角色權限關聯表
CREATE TABLE role_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    granted_by TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (role_id) REFERENCES roles(id),
    FOREIGN KEY (permission_id) REFERENCES permissions(id),
    UNIQUE(role_id, permission_id)
);

-- ========================
-- ABAC 屬性基於訪問控制
-- ========================

-- ABAC策略表
CREATE TABLE abac_policies (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    effect TEXT NOT NULL, -- permit, deny
    type TEXT NOT NULL, -- allow, deny, require, obligate
    conditions TEXT, -- JSON條件數組
    target_resources TEXT, -- JSON數組
    target_actions TEXT, -- JSON數組
    target_users TEXT, -- JSON數組
    target_environments TEXT, -- JSON數組
    is_active BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT -- JSON
);

-- ========================
-- MFA 多因素認證
-- ========================

-- MFA方法表
CREATE TABLE mfa_methods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    method_type TEXT NOT NULL, -- totp, sms, email, hardware, biometric, backup_code
    name TEXT NOT NULL, -- 設備名稱
    secret_key TEXT, -- 加密存儲
    phone_number TEXT,
    email TEXT,
    is_primary BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP,
    metadata TEXT -- JSON
);

-- 備份代碼表
CREATE TABLE backup_codes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    code_hash TEXT NOT NULL, -- SHA256哈希
    is_used BOOLEAN DEFAULT FALSE,
    used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 設備信息表
CREATE TABLE devices (
    device_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    device_name TEXT NOT NULL,
    device_type TEXT, -- mobile, desktop, tablet
    browser TEXT,
    os TEXT,
    ip_address TEXT,
    location TEXT,
    trust_level INTEGER DEFAULT 0, -- 0-4
    is_trusted BOOLEAN DEFAULT FALSE,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fingerprint TEXT
);

-- MFA驗證日誌表
CREATE TABLE mfa_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    method_type TEXT NOT NULL,
    success BOOLEAN NOT NULL,
    ip_address TEXT,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    failure_reason TEXT
);

-- ========================
-- 會話管理
-- ========================

-- 會話表
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE NOT NULL,
    user_id TEXT NOT NULL,
    ip_address TEXT,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    status TEXT DEFAULT 'active', -- active, expired, terminated, suspended
    device_id TEXT,
    device_name TEXT,
    location TEXT,
    metadata TEXT -- JSON
);

-- 令牌表
CREATE TABLE tokens (
    token_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    token_type TEXT NOT NULL, -- access, refresh, id
    token_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    is_revoked BOOLEAN DEFAULT FALSE,
    metadata TEXT -- JSON
);

-- 登錄嘗試表
CREATE TABLE login_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    ip_address TEXT NOT NULL,
    success BOOLEAN NOT NULL,
    failure_reason TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================
-- API訪問控制
-- ========================

-- API密鑰表
CREATE TABLE api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key_id TEXT UNIQUE NOT NULL, -- human-readable ID
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    key_hash TEXT NOT NULL, -- SHA256哈希
    key_prefix TEXT NOT NULL, -- 用於識別的前缀
    scopes TEXT NOT NULL, -- JSON數組
    rate_limit INTEGER DEFAULT 60, -- 每分鐘請求數
    status TEXT DEFAULT 'active', -- active, inactive, expired, revoked
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    last_used_at TIMESTAMP,
    usage_count INTEGER DEFAULT 0,
    metadata TEXT -- JSON
);

-- 端點權限表
CREATE TABLE endpoint_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    method TEXT NOT NULL, -- GET, POST, PUT, DELETE
    path_pattern TEXT NOT NULL, -- 正則表達式模式
    required_scopes TEXT, -- JSON數組
    required_roles TEXT, -- JSON數組
    rate_limit INTEGER, -- 端點級速率限制
    is_public BOOLEAN DEFAULT FALSE,
    metadata TEXT -- JSON
);

-- API使用統計表
CREATE TABLE api_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_key_id TEXT,
    user_id TEXT,
    endpoint TEXT NOT NULL,
    method TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    response_code INTEGER,
    response_time REAL, -- 秒
    ip_address TEXT,
    user_agent TEXT
);

-- ========================
-- 審計日誌
-- ========================

-- 訪問日誌表
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    session_id TEXT,
    action TEXT NOT NULL, -- login, logout, access, modify, delete
    resource TEXT,
    resource_id TEXT,
    success BOOLEAN NOT NULL,
    ip_address TEXT,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    details TEXT, -- JSON
    old_values TEXT, -- JSON
    new_values TEXT -- JSON
);

-- ========================
-- 索引
-- ========================

-- RBAC索引
CREATE INDEX idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX idx_user_roles_role_id ON user_roles(role_id);
CREATE INDEX idx_user_roles_active ON user_roles(user_id, is_active);
CREATE INDEX idx_role_permissions_role_id ON role_permissions(role_id);
CREATE INDEX idx_role_permissions_permission_id ON role_permissions(permission_id);

-- ABAC索引
CREATE INDEX idx_abac_policies_active ON abac_policies(is_active);
CREATE INDEX idx_abac_policies_priority ON abac_policies(priority);

-- MFA索引
CREATE INDEX idx_mfa_methods_user_id ON mfa_methods(user_id);
CREATE INDEX idx_mfa_methods_type ON mfa_methods(method_type);
CREATE INDEX idx_mfa_methods_active ON mfa_methods(is_active);
CREATE INDEX idx_backup_codes_user_id ON backup_codes(user_id);
CREATE INDEX idx_backup_codes_used ON backup_codes(is_used);
CREATE INDEX idx_devices_user_id ON devices(user_id);
CREATE INDEX idx_devices_trusted ON devices(is_trusted);
CREATE INDEX idx_mfa_logs_user_id ON mfa_logs(user_id);
CREATE INDEX idx_mfa_logs_timestamp ON mfa_logs(timestamp);

-- 會話索引
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_session_id ON sessions(session_id);
CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_sessions_expires ON sessions(expires_at);
CREATE INDEX idx_tokens_user_id ON tokens(user_id);
CREATE INDEX idx_tokens_type ON tokens(token_type);
CREATE INDEX idx_tokens_revoked ON tokens(is_revoked);
CREATE INDEX idx_login_attempts_ip ON login_attempts(ip_address);
CREATE INDEX idx_login_attempts_user ON login_attempts(user_id);
CREATE INDEX idx_login_attempts_timestamp ON login_attempts(timestamp);

-- API索引
CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX idx_api_keys_status ON api_keys(status);
CREATE INDEX idx_api_keys_active ON api_keys(status);
CREATE INDEX idx_api_usage_api_key ON api_usage(api_key_id);
CREATE INDEX idx_api_usage_timestamp ON api_usage(timestamp);
CREATE INDEX idx_api_usage_endpoint ON api_usage(endpoint);
CREATE INDEX idx_api_usage_response_code ON api_usage(response_code);

-- 審計索引
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_session_id ON audit_logs(session_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);

-- ========================
-- 視圖
-- ========================

-- 用戶權限視圖
CREATE VIEW user_permissions AS
SELECT
    ur.user_id,
    r.name as role_name,
    r.role_type,
    p.code as permission_code,
    p.resource,
    p.action,
    r.is_system_role
FROM user_roles ur
JOIN roles r ON ur.role_id = r.id
JOIN role_permissions rp ON r.id = rp.role_id
JOIN permissions p ON rp.permission_id = p.id
WHERE ur.is_active = TRUE
AND rp.is_active = TRUE;

-- 活躍會話視圖
CREATE VIEW active_sessions AS
SELECT
    s.session_id,
    s.user_id,
    s.ip_address,
    s.device_name,
    s.created_at,
    s.last_activity,
    s.expires_at,
    ROUND((julianday(s.expires_at) - julianday('now')) * 24 * 60) as minutes_to_expiry
FROM sessions s
WHERE s.status = 'active'
AND s.expires_at > datetime('now');

-- API使用統計視圖
CREATE VIEW api_usage_stats AS
SELECT
    api_key_id,
    DATE(timestamp) as usage_date,
    COUNT(*) as total_requests,
    AVG(response_time) as avg_response_time,
    COUNT(CASE WHEN response_code >= 400 THEN 1 END) as error_count,
    MIN(response_time) as min_response_time,
    MAX(response_time) as max_response_time
FROM api_usage
GROUP BY api_key_id, DATE(timestamp);

-- ========================
-- 觸發器
-- ========================

-- 自動更新 updated_at
CREATE TRIGGER update_roles_updated_at
    AFTER UPDATE ON roles
    FOR EACH ROW
    BEGIN
        UPDATE roles SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER update_abac_policies_updated_at
    AFTER UPDATE ON abac_policies
    FOR EACH ROW
    BEGIN
        UPDATE abac_policies SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

-- 記錄會話過期
CREATE TRIGGER session_expiry_check
    AFTER UPDATE ON sessions
    FOR EACH ROW
    WHEN NEW.status = 'expired' AND OLD.status = 'active'
    BEGIN
        INSERT INTO audit_logs (user_id, session_id, action, resource, success)
        VALUES (NEW.user_id, NEW.session_id, 'session_expired', 'session', TRUE);
    END;

-- 記錄權限變更
CREATE TRIGGER log_permission_changes
    AFTER UPDATE ON role_permissions
    FOR EACH ROW
    WHEN NEW.is_active != OLD.is_active
    BEGIN
        INSERT INTO audit_logs (user_id, action, resource, success)
        VALUES (
            'system',
            CASE WHEN NEW.is_active = 1 THEN 'grant_permission' ELSE 'revoke_permission' END,
            'role:' || NEW.role_id || ':permission:' || NEW.permission_id,
            TRUE
        );
    END;
