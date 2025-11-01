"""
自動化工作流配置
定義任務自動化規則、觸發條件和操作
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)


class TriggerType(Enum):
    """觸發類型"""
    GIT_COMMIT = "git_commit"
    SCHEDULE = "schedule"
    MANUAL = "manual"
    WEBHOOK = "webhook"
    STATUS_CHANGE = "status_change"


class ActionType(Enum):
    """操作類型"""
    UPDATE_STATUS = "update_status"
    ASSIGN_TASK = "assign_task"
    ADD_COMMENT = "add_comment"
    BLOCK_TASK = "block_task"
    UNBLOCK_TASK = "unblock_task"
    NOTIFY = "notify"
    GENERATE_REPORT = "generate_report"
    CREATE_SUBTASK = "create_subtask"


@dataclass
class TriggerCondition:
    """觸發條件"""
    pattern: str  # 正則表達式模式
    match_type: str  # "commit_message", "branch", "file_path"
    value: str  # 匹配值


@dataclass
class AutomationRule:
    """自動化規則"""
    name: str
    description: str
    trigger_type: TriggerType
    conditions: List[TriggerCondition]
    actions: List[Dict[str, any]]
    enabled: bool = True
    priority: int = 0  # 優先級，數字越大優先級越高
    metadata: Dict[str, any] = field(default_factory=dict)


class AutomationConfig:
    """自動化配置管理器"""

    # 默認規則
    DEFAULT_RULES = [
        # 規則1: 完成任務
        AutomationRule(
            name="complete_task_on_close",
            description="當提交信息包含關閉關鍵字時自動完成任務",
            trigger_type=TriggerType.GIT_COMMIT,
            conditions=[
                TriggerCondition(
                    pattern=r"(close[sd]?|fix(e[sd])?|resolve[sd]?|complete[sd]?)",
                    match_type="commit_message",
                    value="close,fix,resolve,complete"
                )
            ],
            actions=[
                {
                    "type": ActionType.UPDATE_STATUS.value,
                    "params": {
                        "status": "已完成",
                        "comment": "由Git提交自動完成"
                    }
                }
            ],
            priority=100
        ),

        # 規則2: 開始任務
        AutomationRule(
            name="start_task_on_begin",
            description="當提交信息包含開始關鍵字時自動開始任務",
            trigger_type=TriggerType.GIT_COMMIT,
            conditions=[
                TriggerCondition(
                    pattern=r"(start|begin|init|work on|tackle)",
                    match_type="commit_message",
                    value="start,begin,init,work on,tackle"
                )
            ],
            actions=[
                {
                    "type": ActionType.UPDATE_STATUS.value,
                    "params": {
                        "status": "進行中",
                        "comment": "由Git提交自動開始"
                    }
                }
            ],
            priority=90
        ),

        # 規則3: 標記進度
        AutomationRule(
            name="update_progress_on_wip",
            description="當提交標記為WIP時更新任務進度",
            trigger_type=TriggerType.GIT_COMMIT,
            conditions=[
                TriggerCondition(
                    pattern=r"(wip|progress|update)",
                    match_type="commit_message",
                    value="wip,progress,update"
                )
            ],
            actions=[
                {
                    "type": ActionType.ADD_COMMENT.value,
                    "params": {
                        "comment": "收到進度更新"
                    }
                }
            ],
            priority=50
        ),

        # 規則4: 文檔任務自動完成
        AutomationRule(
            name="complete_docs_task",
            description="文檔相關的提交自動完成文檔任務",
            trigger_type=TriggerType.GIT_COMMIT,
            conditions=[
                TriggerCondition(
                    pattern=r"^(docs|doc|documentation)\s*:",
                    match_type="commit_message",
                    value="docs:"
                )
            ],
            actions=[
                {
                    "type": ActionType.UPDATE_STATUS.value,
                    "params": {
                        "status": "已完成",
                        "comment": "文檔更新完成"
                    }
                }
            ],
            priority=80
        ),

        # 規則5: 測試任務自動完成
        AutomationRule(
            name="complete_test_task",
            description="測試相關的提交自動完成測試任務",
            trigger_type=TriggerType.GIT_COMMIT,
            conditions=[
                TriggerCondition(
                    pattern=r"^(test|testing)\s*:",
                    match_type="commit_message",
                    value="test:"
                )
            ],
            actions=[
                {
                    "type": ActionType.UPDATE_STATUS.value,
                    "params": {
                        "status": "已完成",
                        "comment": "測試完成"
                    }
                }
            ],
            priority=80
        ),

        # 規則6: 自動分配任務
        AutomationRule(
            name="assign_by_author",
            description="根據提交者自動分配任務",
            trigger_type=TriggerType.GIT_COMMIT,
            conditions=[
                TriggerCondition(
                    pattern=r".*",
                    match_type="author",
                    value="*"
                )
            ],
            actions=[
                {
                    "type": ActionType.ASSIGN_TASK.value,
                    "params": {
                        "assignee": "${commit.author}",
                        "comment": "自動分配給提交者"
                    }
                }
            ],
            priority=10,
            metadata={
                "assign_to_author": True
            }
        ),

        # 規則7: 檢查依賴任務
        AutomationRule(
            name="check_dependencies",
            description="當任務狀態變更時檢查依賴",
            trigger_type=TriggerType.STATUS_CHANGE,
            conditions=[],
            actions=[
                {
                    "type": ActionType.BLOCK_TASK.value,
                    "params": {
                        "block_if_deps_unsatisfied": True
                    }
                },
                {
                    "type": ActionType.UNBLOCK_TASK.value,
                    "params": {
                        "unblock_if_deps_satisfied": True
                    }
                }
            ],
            priority=95
        ),

        # 規則8: 僵屍任務檢測
        AutomationRule(
            name="stale_task_detection",
            description="每週檢測僵屍任務並發送通知",
            trigger_type=TriggerType.SCHEDULE,
            conditions=[
                TriggerCondition(
                    pattern=r"0 9 * * 1",  # 每週一上午9點
                    match_type="cron",
                    value="weekly"
                )
            ],
            actions=[
                {
                    "type": ActionType.NOTIFY.value,
                    "params": {
                        "message": "僵屍任務檢測報告",
                        "channel": "alerts"
                    }
                }
            ],
            priority=20
        ),

        # 規則9: 自動生成報告
        AutomationRule(
            name="daily_status_report",
            description="每日生成任務狀態報告",
            trigger_type=TriggerType.SCHEDULE,
            conditions=[
                TriggerCondition(
                    pattern=r"0 18 * * *",  # 每天下午6點
                    match_type="cron",
                    value="daily"
                )
            ],
            actions=[
                {
                    "type": ActionType.GENERATE_REPORT.value,
                    "params": {
                        "report_type": "daily_status",
                        "channels": ["email", "dashboard"]
                    }
                }
            ],
            priority=15
        ),

        # 規則10: 創建子任務
        AutomationRule(
            name="create_subtasks_for_large_task",
            description="大任務自動拆分子任務",
            trigger_type=TriggerType.GIT_COMMIT,
            conditions=[
                TriggerCondition(
                    pattern=r"(split|break down|refactor)",
                    match_type="commit_message",
                    value="split,break down,refactor"
                )
            ],
            actions=[
                {
                    "type": ActionType.CREATE_SUBTASK.value,
                    "params": {
                        "count": 3,
                        "template": "${task.title} - 子任務 ${index}"
                    }
                }
            ],
            priority=30
        )
    ]

    def __init__(self, config_path: Optional[str] = None):
        """初始化配置

        Args:
            config_path: 配置文件路徑
        """
        self.config_path = config_path
        self.rules: List[AutomationRule] = []
        self.load_config()

    def load_config(self):
        """載入配置"""
        try:
            if self.config_path and os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    self.rules = self._parse_config(config_data)
                logger.info(f"從 {self.config_path} 載入配置")
            else:
                # 使用默認配置
                self.rules = self.DEFAULT_RULES.copy()
                logger.info("使用默認配置")

        except Exception as e:
            logger.error(f"載入配置失敗: {e}")
            # 失敗時使用默認配置
            self.rules = self.DEFAULT_RULES.copy()

    def save_config(self):
        """保存配置到文件"""
        if not self.config_path:
            logger.warning("未指定配置文件路徑，無法保存")
            return

        try:
            config_data = self._serialize_config(self.rules)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            logger.info(f"配置已保存到 {self.config_path}")

        except Exception as e:
            logger.error(f"保存配置失敗: {e}")

    def _parse_config(self, config_data: Dict) -> List[AutomationRule]:
        """解析配置數據

        Args:
            config_data: 配置字典

        Returns:
            規則列表
        """
        rules = []

        # TODO: 實現配置解析邏輯
        # 目前返回默認配置
        return self.DEFAULT_RULES

    def _serialize_config(self, rules: List[AutomationRule]) -> Dict:
        """序列化配置

        Args:
            rules: 規則列表

        Returns:
            配置字典
        """
        # TODO: 實現配置序列化邏輯
        return {
            "rules": [
                {
                    "name": rule.name,
                    "description": rule.description,
                    "trigger_type": rule.trigger_type.value,
                    "enabled": rule.enabled,
                    "priority": rule.priority
                }
                for rule in rules
            ]
        }

    def get_matching_rules(
        self,
        trigger_type: TriggerType,
        context: Dict[str, Any]
    ) -> List[AutomationRule]:
        """獲取匹配的規則

        Args:
            trigger_type: 觸發類型
            context: 上下文信息

        Returns:
            匹配的規則列表（按優先級排序）
        """
        matching_rules = []

        for rule in self.rules:
            if not rule.enabled:
                continue

            if rule.trigger_type != trigger_type:
                continue

            # 檢查條件是否滿足
            if self._check_conditions(rule, context):
                matching_rules.append(rule)

        # 按優先級排序
        matching_rules.sort(key=lambda r: r.priority, reverse=True)

        return matching_rules

    def _check_conditions(
        self,
        rule: AutomationRule,
        context: Dict[str, Any]
    ) -> bool:
        """檢查條件是否滿足

        Args:
            rule: 規則
            context: 上下文

        Returns:
            是否滿足
        """
        if not rule.conditions:
            return True

        for condition in rule.conditions:
            if not self._check_single_condition(condition, context):
                return False

        return True

    def _check_single_condition(
        self,
        condition: TriggerCondition,
        context: Dict[str, Any]
    ) -> bool:
        """檢查單個條件

        Args:
            condition: 條件
            context: 上下文

        Returns:
            是否滿足
        """
        # 根據匹配類型獲取值
        if condition.match_type == "commit_message":
            value = context.get("message", "")
        elif condition.match_type == "branch":
            value = context.get("branch", "")
        elif condition.match_type == "file_path":
            value = ",".join(context.get("files", []))
        elif condition.match_type == "author":
            value = context.get("author", "")
        else:
            return False

        # 使用正則匹配
        import re
        pattern = re.compile(condition.pattern, re.IGNORECASE)
        return pattern.search(value) is not None

    def add_rule(self, rule: AutomationRule):
        """添加規則

        Args:
            rule: 規則
        """
        self.rules.append(rule)
        self.rules.sort(key=lambda r: r.priority, reverse=True)
        logger.info(f"已添加規則: {rule.name}")

    def remove_rule(self, rule_name: str) -> bool:
        """移除規則

        Args:
            rule_name: 規則名稱

        Returns:
            是否成功移除
        """
        for i, rule in enumerate(self.rules):
            if rule.name == rule_name:
                del self.rules[i]
                logger.info(f"已移除規則: {rule_name}")
                return True

        return False

    def enable_rule(self, rule_name: str):
        """啟用規則

        Args:
            rule_name: 規則名稱
        """
        for rule in self.rules:
            if rule.name == rule_name:
                rule.enabled = True
                logger.info(f"已啟用規則: {rule_name}")
                break

    def disable_rule(self, rule_name: str):
        """禁用規則

        Args:
            rule_name: 規則名稱
        """
        for rule in self.rules:
            if rule.name == rule_name:
                rule.enabled = False
                logger.info(f"已禁用規則: {rule_name}")
                break

    def list_rules(self) -> List[Dict[str, Any]]:
        """列出所有規則

        Returns:
            規則列表
        """
        return [
            {
                "name": rule.name,
                "description": rule.description,
                "trigger_type": rule.trigger_type.value,
                "enabled": rule.enabled,
                "priority": rule.priority,
                "conditions": len(rule.conditions),
                "actions": len(rule.actions)
            }
            for rule in self.rules
        ]

    def get_rule_by_name(self, name: str) -> Optional[AutomationRule]:
        """根據名稱獲取規則

        Args:
            name: 規則名稱

        Returns:
            規則對象
        """
        for rule in self.rules:
            if rule.name == name:
                return rule
        return None


# 預定義規則模板
RULE_TEMPLATES = {
    "commit_status_update": AutomationRule(
        name="template_commit_status_update",
        description="根據提交信息更新任務狀態",
        trigger_type=TriggerType.GIT_COMMIT,
        conditions=[
            TriggerCondition(
                pattern=r"TASK-(\d{3})",
                match_type="commit_message",
                value="task reference"
            )
        ],
        actions=[
            {
                "type": ActionType.UPDATE_STATUS.value,
                "params": {
                    "status": "進行中",
                    "comment": "收到提交更新"
                }
            }
        ],
        priority=80
    ),

    "auto_assignment": AutomationRule(
        name="template_auto_assignment",
        description="根據規則自動分配任務",
        trigger_type=TriggerType.GIT_COMMIT,
        conditions=[
            TriggerCondition(
                pattern=r".*",
                match_type="author",
                value="*"
            )
        ],
        actions=[
            {
                "type": ActionType.ASSIGN_TASK.value,
                "params": {
                    "assignee": "${commit.author}",
                    "auto": True
                }
            }
        ],
        priority=10
    )
}
