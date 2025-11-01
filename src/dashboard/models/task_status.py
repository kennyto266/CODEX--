"""
任務狀態枚舉定義
用於港股量化交易系統的項目管理
"""

from enum import Enum


class TaskStatus(str, Enum):
    """任務狀態枚舉"""
    TODO = "待開始"  # 任務已創建，等待開始
    IN_PROGRESS = "進行中"  # 任務正在執行中
    REVIEW = "待驗收"  # 任務完成，等待審查驗收
    DONE = "已完成"  # 任務已完成並通過驗收
    BLOCKED = "已阻塞"  # 任務被阻塞，無法繼續

    def can_transition_to(self, target_status: 'TaskStatus') -> bool:
        """
        檢查是否可以從當前狀態轉換到目標狀態

        Args:
            target_status: 目標狀態

        Returns:
            bool: 是否可以轉換

        狀態轉換規則:
        TODO -> IN_PROGRESS, BLOCKED
        IN_PROGRESS -> REVIEW, BLOCKED, TODO
        REVIEW -> DONE, IN_PROGRESS
        BLOCKED -> TODO, IN_PROGRESS
        DONE -> (無效轉換，終止狀態)
        """
        valid_transitions = {
            TaskStatus.TODO: [TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED],
            TaskStatus.IN_PROGRESS: [TaskStatus.REVIEW, TaskStatus.BLOCKED, TaskStatus.TODO],
            TaskStatus.REVIEW: [TaskStatus.DONE, TaskStatus.IN_PROGRESS],
            TaskStatus.BLOCKED: [TaskStatus.TODO, TaskStatus.IN_PROGRESS],
            TaskStatus.DONE: []  # 已完成任務不能轉換
        }

        return target_status in valid_transitions.get(self, [])


class Priority(str, Enum):
    """任務優先級枚舉"""
    P0 = "P0"  # 關鍵路徑任務，最高優先級
    P1 = "P1"  # 重要任務
    P2 = "P2"  # 一般任務

    @property
    def level(self) -> int:
        """獲取優先級數值，等級越高優先級越高"""
        return {"P0": 3, "P1": 2, "P2": 1}[self.value]


class SprintStatus(str, Enum):
    """Sprint狀態枚舉"""
    PLANNING = "計劃中"  # Sprint規劃階段
    ACTIVE = "進行中"  # Sprint執行中
    COMPLETED = "已完成"  # Sprint已完成
    CANCELLED = "已取消"  # Sprint被取消

    def can_transition_to(self, target_status: 'SprintStatus') -> bool:
        """檢查Sprint狀態轉換是否合法"""
        valid_transitions = {
            SprintStatus.PLANNING: [SprintStatus.ACTIVE, SprintStatus.CANCELLED],
            SprintStatus.ACTIVE: [SprintStatus.COMPLETED, SprintStatus.CANCELLED],
            SprintStatus.COMPLETED: [],  # 終止狀態
            SprintStatus.CANCELLED: []  # 終止狀態
        }
        return target_status in valid_transitions.get(self, [])
