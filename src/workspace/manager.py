"""
個人工作區管理器
管理用戶的個人化設定、投資組合和交易歷史
"""

import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import os
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class WorkspaceSettings:
    """工作區設定"""
    user_id: str
    name: str
    theme: str = "dark"  # dark, light, auto
    language: str = "zh-TW"
    timezone: str = "Asia/Hong_Kong"
    dashboard_layout: Dict[str, Any] = None  # 儀表板布局配置
    default_symbols: List[str] = None  # 默認關注股票
    refresh_interval: int = 60  # 刷新間隔(秒)
    notifications_enabled: bool = True
    auto_save: bool = True

    def __post_init__(self):
        if self.dashboard_layout is None:
            self.dashboard_layout = {}
        if self.default_symbols is None:
            self.default_symbols = ['0700.HK', '0388.HK', '1398.HK']


@dataclass
class UserPreferences:
    """用戶偏好"""
    strategy_type: str = "technical"  # 技術面、基本面、宏觀
    risk_tolerance: str = "medium"  # low, medium, high
    investment_style: str = "growth"  # growth, value, income, momentum
    preferred_timeframe: str = "1D"  # 1D, 1W, 1M
    technical_indicators: List[str] = None  # 偏好的技術指標
    color_scheme: str = "blue"  # blue, green, purple, red

    def __post_init__(self):
        if self.technical_indicators is None:
            self.technical_indicators = ['sma', 'rsi', 'macd']


@dataclass
class Workspace:
    """完整工作區"""
    settings: WorkspaceSettings
    preferences: UserPreferences
    created_at: str
    updated_at: str

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            'settings': asdict(self.settings),
            'preferences': asdict(self.preferences),
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Workspace':
        """從字典創建"""
        settings = WorkspaceSettings(**data['settings'])
        preferences = UserPreferences(**data['preferences'])
        return cls(
            settings=settings,
            preferences=preferences,
            created_at=data['created_at'],
            updated_at=data['updated_at'],
        )


class WorkspaceManager:
    """工作區管理器"""

    def __init__(self, workspace_dir: str = "workspace_data"):
        self.workspace_dir = workspace_dir
        self.workspaces: Dict[str, Workspace] = {}
        self._ensure_workspace_dir()

    def _ensure_workspace_dir(self):
        """確保工作區目錄存在"""
        if not os.path.exists(self.workspace_dir):
            os.makedirs(self.workspace_dir)

    def create_workspace(
        self,
        user_id: str,
        name: str,
        theme: str = "dark",
        language: str = "zh-TW"
    ) -> Workspace:
        """
        創建新工作區

        Args:
            user_id: 用戶ID
            name: 工作區名稱
            theme: 主題
            language: 語言

        Returns:
            新創建的工作區
        """
        now = datetime.now().isoformat()

        settings = WorkspaceSettings(
            user_id=user_id,
            name=name,
            theme=theme,
            language=language
        )

        preferences = UserPreferences()

        workspace = Workspace(
            settings=settings,
            preferences=preferences,
            created_at=now,
            updated_at=now
        )

        self.workspaces[user_id] = workspace
        self._save_workspace(user_id, workspace)

        logger.info(f"Created workspace for user {user_id}")
        return workspace

    def get_workspace(self, user_id: str) -> Optional[Workspace]:
        """
        獲取工作區

        Args:
            user_id: 用戶ID

        Returns:
            工作區或None
        """
        if user_id in self.workspaces:
            return self.workspaces[user_id]

        # 嘗試從文件加載
        workspace = self._load_workspace(user_id)
        if workspace:
            self.workspaces[user_id] = workspace
            return workspace

        return None

    def update_workspace(
        self,
        user_id: str,
        **kwargs
    ) -> Optional[Workspace]:
        """
        更新工作區

        Args:
            user_id: 用戶ID
            **kwargs: 更新字段

        Returns:
            更新後的工作區
        """
        workspace = self.get_workspace(user_id)
        if not workspace:
            return None

        # 更新設定
        if 'name' in kwargs:
            workspace.settings.name = kwargs['name']
        if 'theme' in kwargs:
            workspace.settings.theme = kwargs['theme']
        if 'language' in kwargs:
            workspace.settings.language = kwargs['language']
        if 'timezone' in kwargs:
            workspace.settings.timezone = kwargs['timezone']
        if 'default_symbols' in kwargs:
            workspace.settings.default_symbols = kwargs['default_symbols']
        if 'refresh_interval' in kwargs:
            workspace.settings.refresh_interval = kwargs['refresh_interval']
        if 'notifications_enabled' in kwargs:
            workspace.settings.notifications_enabled = kwargs['notifications_enabled']
        if 'auto_save' in kwargs:
            workspace.settings.auto_save = kwargs['auto_save']

        # 更新偏好
        if 'strategy_type' in kwargs:
            workspace.preferences.strategy_type = kwargs['strategy_type']
        if 'risk_tolerance' in kwargs:
            workspace.preferences.risk_tolerance = kwargs['risk_tolerance']
        if 'investment_style' in kwargs:
            workspace.preferences.investment_style = kwargs['investment_style']
        if 'preferred_timeframe' in kwargs:
            workspace.preferences.preferred_timeframe = kwargs['preferred_timeframe']
        if 'technical_indicators' in kwargs:
            workspace.preferences.technical_indicators = kwargs['technical_indicators']
        if 'color_scheme' in kwargs:
            workspace.preferences.color_scheme = kwargs['color_scheme']

        workspace.updated_at = datetime.now().isoformat()
        self.workspaces[user_id] = workspace

        if workspace.settings.auto_save:
            self._save_workspace(user_id, workspace)

        logger.info(f"Updated workspace for user {user_id}")
        return workspace

    def delete_workspace(self, user_id: str) -> bool:
        """
        刪除工作區

        Args:
            user_id: 用戶ID

        Returns:
            是否成功刪除
        """
        if user_id not in self.workspaces:
            return False

        del self.workspaces[user_id]

        # 刪除文件
        file_path = os.path.join(self.workspace_dir, f"{user_id}.json")
        if os.path.exists(file_path):
            os.remove(file_path)

        logger.info(f"Deleted workspace for user {user_id}")
        return True

    def _save_workspace(self, user_id: str, workspace: Workspace):
        """保存工作區到文件"""
        file_path = os.path.join(self.workspace_dir, f"{user_id}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(workspace.to_dict(), f, indent=2, ensure_ascii=False)

    def _load_workspace(self, user_id: str) -> Optional[Workspace]:
        """從文件加載工作區"""
        file_path = os.path.join(self.workspace_dir, f"{user_id}.json")
        if not os.path.exists(file_path):
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return Workspace.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load workspace for {user_id}: {e}")
            return None

    def list_workspaces(self) -> List[str]:
        """列出所有工作區用戶ID"""
        return list(self.workspaces.keys())

    def export_workspace(self, user_id: str) -> str:
        """導出工作區為JSON"""
        workspace = self.get_workspace(user_id)
        if not workspace:
            raise ValueError(f"Workspace for user {user_id} not found")

        return json.dumps(workspace.to_dict(), indent=2, ensure_ascii=False)

    def import_workspace(self, workspace_json: str) -> Workspace:
        """從JSON導入工作區"""
        data = json.loads(workspace_json)
        workspace = Workspace.from_dict(data)
        self.workspaces[workspace.settings.user_id] = workspace
        self._save_workspace(workspace.settings.user_id, workspace)
        return workspace


# 導出
__all__ = [
    'WorkspaceManager',
    'Workspace',
    'WorkspaceSettings',
    'UserPreferences',
]
