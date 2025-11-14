"""
权限控制系统 - 细粒度权限管理、访问控制列表和角色权限管理
提供动态权限授予、权限验证和访问控制功能
"""

import sqlite3
import json
import logging
import hashlib
import secrets
from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import os

logger = logging.getLogger(__name__)


class PermissionType(Enum):
    """权限类型"""
    # 文件系统权限
    FILE_READ = "file:read"
    FILE_WRITE = "file:write"
    FILE_DELETE = "file:delete"
    FILE_EXECUTE = "file:execute"
    FILE_CREATE = "file:create"

    # 网络权限
    NETWORK_CONNECT = "network:connect"
    NETWORK_LISTEN = "network:listen"
    NETWORK_BROADCAST = "network:broadcast"

    # 系统权限
    SYSTEM_EXECUTE = "system:execute"
    SYSTEM_MODIFY = "system:modify"
    SYSTEM_ADMIN = "system:admin"

    # 代码执行权限
    CODE_EXECUTE = "code:execute"
    CODE_INJECT = "code:inject"
    CODE_DEBUG = "code:debug"

    # 数据权限
    DATA_READ = "data:read"
    DATA_WRITE = "data:write"
    DATA_DELETE = "data:delete"
    DATA_EXPORT = "data:export"

    # API权限
    API_ACCESS = "api:access"
    API_MODIFY = "api:modify"
    API_ADMIN = "api:admin"

    # 交易权限
    TRADE_EXECUTE = "trade:execute"
    TRADE_MODIFY = "trade:modify"
    TRADE_ADMIN = "trade:admin"

    # 策略权限
    STRATEGY_EXECUTE = "strategy:execute"
    STRATEGY_MODIFY = "strategy:modify"
    STRATEGY_CREATE = "strategy:create"

    # 用户管理权限
    USER_VIEW = "user:view"
    USER_MODIFY = "user:modify"
    USER_ADMIN = "user:admin"


class ResourceType(Enum):
    """资源类型"""
    FILE = "file"
    DIRECTORY = "directory"
    DATABASE = "database"
    API_ENDPOINT = "api_endpoint"
    NETWORK_HOST = "network_host"
    PROCESS = "process"
    PORT = "port"
    STRATEGY = "strategy"
    TRADE = "trade"
    USER = "user"


@dataclass
class User:
    """用户"""
    user_id: str
    username: str
    password_hash: str
    email: str
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True
    is_admin: bool = False
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class Role:
    """角色"""
    role_id: str
    name: str
    description: str
    permissions: Set[PermissionType]
    created_at: datetime
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class PermissionGrant:
    """权限授予"""
    grant_id: str
    user_id: str
    permission: PermissionType
    resource_type: ResourceType
    resource_id: Optional[str]
    granted_at: datetime
    expires_at: Optional[datetime] = None
    granted_by: str = "system"
    is_active: bool = True
    conditions: Dict[str, Any] = None

    def __post_init__(self):
        if self.conditions is None:
            self.conditions = {}

    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.expires_at:
            return datetime.now() > self.expires_at
        return False


@dataclass
class AccessLog:
    """访问日志"""
    log_id: str
    user_id: str
    action: str
    resource_type: ResourceType
    resource_id: Optional[str]
    permission: Optional[PermissionType]
    result: bool  # True=允许, False=拒绝
    timestamp: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Dict[str, Any] = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}


class PermissionDatabase:
    """权限数据库"""

    def __init__(self, db_path: str = "data/security/permissions.db"):
        self.db_path = db_path
        self.db_path = Path(self.db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()

    def init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # 创建用户表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_login TEXT,
                is_active INTEGER DEFAULT 1,
                is_admin INTEGER DEFAULT 0,
                metadata TEXT
            )
        """)

        # 创建角色表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS roles (
                role_id TEXT PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                permissions TEXT NOT NULL,
                created_at TEXT NOT NULL,
                metadata TEXT
            )
        """)

        # 创建用户角色关联表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_roles (
                user_id TEXT NOT NULL,
                role_id TEXT NOT NULL,
                assigned_at TEXT NOT NULL,
                PRIMARY KEY (user_id, role_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (role_id) REFERENCES roles(role_id)
            )
        """)

        # 创建权限授予表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS permission_grants (
                grant_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                permission TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                resource_id TEXT,
                granted_at TEXT NOT NULL,
                expires_at TEXT,
                granted_by TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                conditions TEXT
            )
        """)

        # 创建访问日志表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS access_logs (
                log_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                action TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                resource_id TEXT,
                permission TEXT,
                result INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                details TEXT
            )
        """)

        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_roles_user ON user_roles(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_permission_grants_user ON permission_grants(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_access_logs_user ON access_logs(user_id)")

        conn.commit()
        conn.close()

    def execute_query(self, query: str, params: tuple = ()) -> List[Tuple]:
        """执行查询"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.commit()
        conn.close()
        return results

    def get_user(self, user_id: str) -> Optional[Dict]:
        """获取用户"""
        results = self.execute_query(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,)
        )
        return dict(results[0]) if results else None

    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """通过用户名获取用户"""
        results = self.execute_query(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        )
        return dict(results[0]) if results else None

    def create_user(self, user: User) -> bool:
        """创建用户"""
        try:
            self.execute_query(
                """
                INSERT INTO users (
                    user_id, username, password_hash, email, created_at,
                    last_login, is_active, is_admin, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user.user_id, user.username, user.password_hash, user.email,
                    user.created_at.isoformat(), user.last_login.isoformat() if user.last_login else None,
                    user.is_active, user.is_admin, json.dumps(user.metadata)
                )
            )
            return True
        except sqlite3.IntegrityError as e:
            logger.error(f"Failed to create user: {e}")
            return False

    def get_user_roles(self, user_id: str) -> List[Dict]:
        """获取用户角色"""
        return [
            dict(row) for row in self.execute_query(
                """
                SELECT r.* FROM roles r
                JOIN user_roles ur ON r.role_id = ur.role_id
                WHERE ur.user_id = ?
                """,
                (user_id,)
            )
        ]

    def assign_role_to_user(self, user_id: str, role_id: str) -> bool:
        """分配角色给用户"""
        try:
            self.execute_query(
                "INSERT INTO user_roles (user_id, role_id, assigned_at) VALUES (?, ?, ?)",
                (user_id, role_id, datetime.now().isoformat())
            )
            return True
        except sqlite3.IntegrityError:
            return False

    def get_user_permissions(self, user_id: str) -> List[PermissionGrant]:
        """获取用户权限"""
        rows = self.execute_query(
            "SELECT * FROM permission_grants WHERE user_id = ? AND is_active = 1",
            (user_id,)
        )

        permissions = []
        for row in rows:
            permissions.append(PermissionGrant(
                grant_id=row['grant_id'],
                user_id=row['user_id'],
                permission=PermissionType(row['permission']),
                resource_type=ResourceType(row['resource_type']),
                resource_id=row['resource_id'],
                granted_at=datetime.fromisoformat(row['granted_at']),
                expires_at=datetime.fromisoformat(row['expires_at']) if row['expires_at'] else None,
                granted_by=row['granted_by'],
                is_active=bool(row['is_active']),
                conditions=json.loads(row['conditions']) if row['conditions'] else {}
            ))

        return permissions

    def grant_permission(self, grant: PermissionGrant) -> bool:
        """授予权限"""
        try:
            self.execute_query(
                """
                INSERT INTO permission_grants (
                    grant_id, user_id, permission, resource_type, resource_id,
                    granted_at, expires_at, granted_by, is_active, conditions
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    grant.grant_id, grant.user_id, grant.permission.value,
                    grant.resource_type.value, grant.resource_id,
                    grant.granted_at.isoformat(),
                    grant.expires_at.isoformat() if grant.expires_at else None,
                    grant.granted_by, grant.is_active,
                    json.dumps(grant.conditions)
                )
            )
            return True
        except Exception as e:
            logger.error(f"Failed to grant permission: {e}")
            return False

    def log_access(self, log: AccessLog):
        """记录访问日志"""
        # 处理JSON序列化中的datetime对象
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

        self.execute_query(
            """
            INSERT INTO access_logs (
                log_id, user_id, action, resource_type, resource_id,
                permission, result, timestamp, ip_address, user_agent, details
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                log.log_id, log.user_id, log.action,
                log.resource_type.value, log.resource_id,
                log.permission.value if log.permission else None,
                log.result, log.timestamp.isoformat(),
                log.ip_address, log.user_agent, json.dumps(log.details, default=json_serializer)
            )
        )

    def get_access_logs(self, user_id: str = None, limit: int = 100) -> List[Dict]:
        """获取访问日志"""
        if user_id:
            query = "SELECT * FROM access_logs WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?"
            params = (user_id, limit)
        else:
            query = "SELECT * FROM access_logs ORDER BY timestamp DESC LIMIT ?"
            params = (limit,)

        return [dict(row) for row in self.execute_query(query, params)]


class AccessControl:
    """访问控制器"""

    def __init__(self, db: PermissionDatabase):
        self.db = db
        self.role_permissions: Dict[str, Set[PermissionType]] = {}
        self._load_default_roles()

    def _load_default_roles(self):
        """加载默认角色"""
        # 管理员
        self.role_permissions['admin'] = set(PermissionType)

        # 开发者
        self.role_permissions['developer'] = {
            PermissionType.CODE_EXECUTE,
            PermissionType.CODE_DEBUG,
            PermissionType.DATA_READ,
            PermissionType.DATA_WRITE,
            PermissionType.STRATEGY_EXECUTE,
            PermissionType.STRATEGY_MODIFY,
            PermissionType.STRATEGY_CREATE,
        }

        # 交易员
        self.role_permissions['trader'] = {
            PermissionType.CODE_EXECUTE,
            PermissionType.DATA_READ,
            PermissionType.TRADE_EXECUTE,
            PermissionType.TRADE_MODIFY,
            PermissionType.STRATEGY_EXECUTE,
        }

        # 分析师
        self.role_permissions['analyst'] = {
            PermissionType.DATA_READ,
            PermissionType.DATA_EXPORT,
            PermissionType.STRATEGY_EXECUTE,
        }

        # 观察者
        self.role_permissions['observer'] = {
            PermissionType.DATA_READ,
        }

    def check_permission(
        self,
        user_id: str,
        permission: PermissionType,
        resource_type: ResourceType,
        resource_id: str = None,
        context: Dict[str, Any] = None
    ) -> bool:
        """检查权限"""
        # 获取用户
        user = self.db.get_user(user_id)
        if not user or not user['is_active']:
            self._log_access(user_id, "CHECK_PERMISSION", resource_type, resource_id, permission, False, context)
            return False

        # 管理员拥有所有权限
        if user['is_admin']:
            self._log_access(user_id, "CHECK_PERMISSION", resource_type, resource_id, permission, True, context)
            return True

        # 检查角色权限
        user_roles = self.db.get_user_roles(user_id)
        for role in user_roles:
            role_perms = json.loads(role['permissions'])
            if permission.value in role_perms:
                self._log_access(user_id, "CHECK_PERMISSION", resource_type, resource_id, permission, True, context)
                return True

        # 检查直接权限授予
        grants = self.db.get_user_permissions(user_id)
        for grant in grants:
            if grant.permission == permission and grant.resource_type == resource_type:
                if grant.resource_id is None or grant.resource_id == resource_id:
                    if not grant.is_expired() and grant.is_active:
                        self._log_access(user_id, "CHECK_PERMISSION", resource_type, resource_id, permission, True, context)
                        return True

        self._log_access(user_id, "CHECK_PERMISSION", resource_type, resource_id, permission, False, context)
        return False

    def grant_permission(
        self,
        granted_by: str,
        user_id: str,
        permission: PermissionType,
        resource_type: ResourceType,
        resource_id: str = None,
        expires_in_hours: int = 24
    ) -> bool:
        """授予权限"""
        # 检查授予者是否有权限
        if not self.check_permission(
            granted_by,
            PermissionType.USER_ADMIN,
            ResourceType.USER,
            user_id
        ):
            logger.error(f"User {granted_by} lacks permission to grant permissions")
            return False

        grant = PermissionGrant(
            grant_id=secrets.token_hex(16),
            user_id=user_id,
            permission=permission,
            resource_type=resource_type,
            resource_id=resource_id,
            granted_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=expires_in_hours),
            granted_by=granted_by
        )

        result = self.db.grant_permission(grant)
        if result:
            self._log_access(
                granted_by,
                "GRANT_PERMISSION",
                resource_type,
                resource_id,
                permission,
                True,
                {"target_user": user_id, "expires_at": grant.expires_at}
            )

        return result

    def revoke_permission(self, granted_by: str, grant_id: str) -> bool:
        """撤销权限"""
        if not self.check_permission(
            granted_by,
            PermissionType.USER_ADMIN,
            ResourceType.USER
        ):
            return False

        self.db.execute_query(
            "UPDATE permission_grants SET is_active = 0 WHERE grant_id = ?",
            (grant_id,)
        )

        self._log_access(
            granted_by,
            "REVOKE_PERMISSION",
            ResourceType.USER,
            None,
            None,
            True,
            {"grant_id": grant_id}
        )

        return True

    def _log_access(
        self,
        user_id: str,
        action: str,
        resource_type: ResourceType,
        resource_id: str,
        permission: Optional[PermissionType],
        result: bool,
        context: Dict[str, Any] = None
    ):
        """记录访问日志"""
        log = AccessLog(
            log_id=secrets.token_hex(16),
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            permission=permission,
            result=result,
            timestamp=datetime.now(),
            details=context or {}
        )
        self.db.log_access(log)

    def get_user_effective_permissions(self, user_id: str) -> Set[PermissionType]:
        """获取用户有效权限"""
        permissions = set()

        user = self.db.get_user(user_id)
        if user and user['is_admin']:
            return set(PermissionType)

        # 从角色获取权限
        user_roles = self.db.get_user_roles(user_id)
        for role in user_roles:
            role_perms = json.loads(role['permissions'])
            permissions.update(PermissionType(p) for p in role_perms)

        # 从直接授予获取权限
        grants = self.db.get_user_permissions(user_id)
        for grant in grants:
            if not grant.is_expired() and grant.is_active:
                permissions.add(grant.permission)

        return permissions


class PermissionManager:
    """权限管理器主类"""

    def __init__(self, db_path: str = "data/security/permissions.db"):
        self.db = PermissionDatabase(db_path)
        self.access_control = AccessControl(self.db)

    def authenticate(self, username: str, password: str) -> Optional[str]:
        """认证用户"""
        user = self.db.get_user_by_username(username)
        if not user or not user['is_active']:
            return None

        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if user['password_hash'] == password_hash:
            # 更新最后登录时间
            self.db.execute_query(
                "UPDATE users SET last_login = ? WHERE user_id = ?",
                (datetime.now().isoformat(), user['user_id'])
            )
            return user['user_id']

        return None

    def create_user(
        self,
        username: str,
        password: str,
        email: str,
        is_admin: bool = False
    ) -> Optional[str]:
        """创建用户"""
        user_id = secrets.token_hex(16)
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        user = User(
            user_id=user_id,
            username=username,
            password_hash=password_hash,
            email=email,
            created_at=datetime.now(),
            is_admin=is_admin
        )

        if self.db.create_user(user):
            logger.info(f"User {username} created with ID {user_id}")
            return user_id
        return None

    def assign_role(self, user_id: str, role_id: str) -> bool:
        """分配角色"""
        return self.db.assign_role_to_user(user_id, role_id)

    def check_permission(
        self,
        user_id: str,
        permission: PermissionType,
        resource_type: ResourceType,
        resource_id: str = None
    ) -> bool:
        """检查权限"""
        return self.access_control.check_permission(
            user_id, permission, resource_type, resource_id
        )

    def grant_permission(
        self,
        granted_by: str,
        user_id: str,
        permission: PermissionType,
        resource_type: ResourceType,
        resource_id: str = None,
        expires_in_hours: int = 24
    ) -> bool:
        """授予权限"""
        return self.access_control.grant_permission(
            granted_by, user_id, permission, resource_type, resource_id, expires_in_hours
        )

    def revoke_permission(self, granted_by: str, grant_id: str) -> bool:
        """撤销权限"""
        return self.access_control.revoke_permission(granted_by, grant_id)

    def get_user_permissions(self, user_id: str) -> Set[PermissionType]:
        """获取用户权限"""
        return self.access_control.get_user_effective_permissions(user_id)

    def get_access_logs(self, user_id: str = None, limit: int = 100) -> List[Dict]:
        """获取访问日志"""
        return self.db.get_access_logs(user_id, limit)

    def create_default_admin(self):
        """创建默认管理员"""
        admin = self.db.get_user_by_username("admin")
        if not admin:
            self.create_user("admin", "admin123", "admin@example.com", is_admin=True)
            logger.warning("Default admin user created: username=admin, password=admin123")

    def list_users(self) -> List[Dict]:
        """列出所有用户"""
        results = self.db.execute_query("SELECT user_id, username, email, is_active, is_admin, created_at FROM users")
        return [dict(row) for row in results]

    def deactivate_user(self, user_id: str) -> bool:
        """停用用户"""
        self.db.execute_query(
            "UPDATE users SET is_active = 0 WHERE user_id = ?",
            (user_id,)
        )
        return True

    def activate_user(self, user_id: str) -> bool:
        """激活用户"""
        self.db.execute_query(
            "UPDATE users SET is_active = 1 WHERE user_id = ?",
            (user_id,)
        )
        return True
