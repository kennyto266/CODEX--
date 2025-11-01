#!/usr/bin/env python3
"""
價格警報管理模組
支持設置價格警報、監控和通知
"""

import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class AlertType(Enum):
    """警報類型"""
    ABOVE = "above"      # 高於某個價格
    BELOW = "below"      # 低於某個價格
    CHANGE_UP = "change_up"    # 漲幅超過百分比
    CHANGE_DOWN = "change_down"  # 跌幅超過百分比

class AlertStatus(Enum):
    """警報狀態"""
    ACTIVE = "active"
    TRIGGERED = "triggered"
    DISABLED = "disabled"

@dataclass
class PriceAlert:
    """價格警報"""
    id: str
    user_id: int
    chat_id: int
    stock_code: str
    alert_type: AlertType
    threshold: float
    created_at: datetime
    last_checked: Optional[datetime] = None
    status: AlertStatus = AlertStatus.ACTIVE
    cooldown_until: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        data = asdict(self)
        data['alert_type'] = self.alert_type.value
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        if self.last_checked:
            data['last_checked'] = self.last_checked.isoformat()
        if self.cooldown_until:
            data['cooldown_until'] = self.cooldown_until.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PriceAlert':
        """從字典創建"""
        data['alert_type'] = AlertType(data['alert_type'])
        data['status'] = AlertStatus(data['status'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data.get('last_checked'):
            data['last_checked'] = datetime.fromisoformat(data['last_checked'])
        if data.get('cooldown_until'):
            data['cooldown_until'] = datetime.fromisoformat(data['cooldown_until'])
        return cls(**data)

class AlertManager:
    """警報管理器"""

    def __init__(self):
        self.alerts: Dict[str, PriceAlert] = {}
        self.data_file = "data/price_alerts.json"
        self.monitoring_active = False
        self.monitor_task: Optional[asyncio.Task] = None
        self.check_interval = 60  # 60秒檢查一次
        self.cooldown_period = 1800  # 30分鐘冷卻期
        self.load_alerts()

    def load_alerts(self) -> None:
        """從文件載入警報"""
        try:
            if os.path.exists(self.data_file):
                os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.alerts = {
                        alert_id: PriceAlert.from_dict(alert_data)
                        for alert_id, alert_data in data.items()
                    }
                logger.info(f"載入警報: {len(self.alerts)}個")
            else:
                self.alerts = {}
        except Exception as e:
            logger.error(f"載入警報失敗: {e}")
            self.alerts = {}

    def save_alerts(self) -> bool:
        """保存警報到文件"""
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump({
                    alert_id: alert.to_dict()
                    for alert_id, alert in self.alerts.items()
                }, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"保存警報失敗: {e}")
            return False

    def generate_alert_id(self) -> str:
        """生成警報ID"""
        import uuid
        return str(uuid.uuid4())[:8]

    def create_alert(
        self,
        user_id: int,
        chat_id: int,
        stock_code: str,
        alert_type: AlertType,
        threshold: float
    ) -> tuple[bool, str, Optional[str]]:
        """
        創建警報
        返回: (是否成功, 消息, 警報ID)
        """
        try:
            # 驗證輸入
            if not stock_code or not stock_code.endswith('.HK'):
                return False, "股票代碼格式無效，應以.HK結尾", None

            if threshold <= 0:
                return False, "閾值必須大於0", None

            # 檢查警報限制（每個用戶最多10個警報）
            user_alerts = [a for a in self.alerts.values() if a.user_id == user_id]
            if len(user_alerts) >= 10:
                return False, "警報數量已達上限（10個），請刪除一些警報後再添加", None

            # 創建警報
            alert_id = self.generate_alert_id()
            alert = PriceAlert(
                id=alert_id,
                user_id=user_id,
                chat_id=chat_id,
                stock_code=stock_code.upper(),
                alert_type=alert_type,
                threshold=threshold,
                created_at=datetime.now()
            )

            self.alerts[alert_id] = alert
            self.save_alerts()

            return True, f"警報創建成功", alert_id

        except Exception as e:
            logger.error(f"創建警報失敗: {e}")
            return False, f"創建警報失敗: {str(e)}", None

    def list_alerts(self, user_id: int) -> List[PriceAlert]:
        """列出用戶的所有警報"""
        return [
            alert for alert in self.alerts.values()
            if alert.user_id == user_id and alert.status != AlertStatus.DISABLED
        ]

    def delete_alert(self, user_id: int, alert_id: str) -> tuple[bool, str]:
        """刪除警報"""
        try:
            if alert_id not in self.alerts:
                return False, f"警報 {alert_id} 不存在"

            alert = self.alerts[alert_id]
            if alert.user_id != user_id:
                return False, "無權刪除此警報"

            del self.alerts[alert_id]
            self.save_alerts()

            return True, f"警報 {alert_id} 已刪除"

        except Exception as e:
            logger.error(f"刪除警報失敗: {e}")
            return False, f"刪除警報失敗: {str(e)}"

    def delete_all_alerts(self, user_id: int) -> tuple[bool, str]:
        """刪除用戶所有警報"""
        try:
            user_alerts = list(self.alerts.values())
            deleted_count = 0
            for alert in user_alerts:
                if alert.user_id == user_id:
                    del self.alerts[alert.id]
                    deleted_count += 1

            if deleted_count > 0:
                self.save_alerts()
                return True, f"已刪除 {deleted_count} 個警報"
            else:
                return False, "沒有找到警報"

        except Exception as e:
            logger.error(f"刪除所有警報失敗: {e}")
            return False, f"刪除失敗: {str(e)}"

    async def check_alerts(self, get_price_func: Callable) -> List[PriceAlert]:
        """檢查所有警報"""
        triggered_alerts = []

        for alert_id, alert in self.alerts.items():
            # 跳過非活躍警報
            if alert.status != AlertStatus.ACTIVE:
                continue

            # 跳過冷卻期內的警報
            if alert.cooldown_until and datetime.now() < alert.cooldown_until:
                continue

            try:
                # 獲取當前價格
                current_price = await get_price_func(alert.stock_code)

                if not current_price:
                    continue

                # 檢查是否觸發警報
                is_triggered = False

                if alert.alert_type == AlertType.ABOVE:
                    is_triggered = current_price >= alert.threshold
                elif alert.alert_type == AlertType.BELOW:
                    is_triggered = current_price <= alert.threshold
                elif alert.alert_type == AlertType.CHANGE_UP:
                    # 這裡需要計算漲幅百分比，暫時簡化
                    is_triggered = False
                elif alert.alert_type == AlertType.CHANGE_DOWN:
                    # 這裡需要計算跌幅百分比，暫時簡化
                    is_triggered = False

                if is_triggered:
                    alert.status = AlertStatus.TRIGGERED
                    alert.cooldown_until = datetime.now() + timedelta(seconds=self.cooldown_period)
                    triggered_alerts.append(alert)
                    logger.info(f"警報觸發: {alert_id} - {alert.stock_code} {alert.alert_type.value} {alert.threshold}")

                alert.last_checked = datetime.now()

            except Exception as e:
                logger.error(f"檢查警報 {alert_id} 失敗: {e}")

        # 保存更新
        if triggered_alerts:
            self.save_alerts()

        return triggered_alerts

    async def start_monitoring(self, get_price_func: Callable):
        """開始監控"""
        if self.monitoring_active:
            logger.warning("監控已在運行中")
            return

        self.monitoring_active = True
        logger.info("開始價格警報監控")

        async def monitor_loop():
            while self.monitoring_active:
                try:
                    triggered_alerts = await self.check_alerts(get_price_func)

                    if triggered_alerts:
                        logger.info(f"檢查到 {len(triggered_alerts)} 個警報觸發")

                    # 等待下一次檢查
                    await asyncio.sleep(self.check_interval)

                except Exception as e:
                    logger.error(f"監控循環錯誤: {e}")
                    await asyncio.sleep(self.check_interval)

        self.monitor_task = asyncio.create_task(monitor_loop())

    def stop_monitoring(self):
        """停止監控"""
        if not self.monitoring_active:
            return

        self.monitoring_active = False

        if self.monitor_task:
            self.monitor_task.cancel()
            self.monitor_task = None

        logger.info("停止價格警報監控")

    def format_alert_list(self, alerts: List[PriceAlert]) -> str:
        """格式化警報列表"""
        if not alerts:
            return "📊 沒有設置警報\n\n使用 /alert add <代碼> <類型> <閾值> 添加警報\n\n警報類型：\n- above <價格>  - 高於某價格\n- below <價格>  - 低於某價格"

        lines = ["📊 價格警報列表", "=" * 40]

        for i, alert in enumerate(alerts, 1):
            status_emoji = {
                AlertStatus.ACTIVE: "🟢",
                AlertStatus.TRIGGERED: "🟡",
                AlertStatus.DISABLED: "🔴"
            }

            type_text = {
                AlertType.ABOVE: f"高於 {alert.threshold}",
                AlertType.BELOW: f"低於 {alert.threshold}",
                AlertType.CHANGE_UP: f"漲幅超 {alert.threshold}%",
                AlertType.CHANGE_DOWN: f"跌幅超 {alert.threshold}%"
            }

            lines.append(
                f"{i}. {status_emoji[alert.status]} {alert.id}\n"
                f"   股票: {alert.stock_code}\n"
                f"   條件: {type_text[alert.alert_type]}\n"
                f"   創建: {alert.created_at.strftime('%m-%d %H:%M')}"
            )

            if alert.status == AlertStatus.TRIGGERED and alert.cooldown_until:
                remaining = int((alert.cooldown_until - datetime.now()).total_seconds())
                if remaining > 0:
                    lines.append(f"   冷卻: {remaining//60}分鐘後可再次觸發")

        lines.append("\n💡 提示:")
        lines.append("• 使用 /alert delete <ID> 刪除警報")
        lines.append("• 警報觸發後會進入30分鐘冷卻期")

        return "\n".join(lines)

    def format_alert_message(self, alert: PriceAlert, current_price: float) -> str:
        """格式化警報觸發消息"""
        type_emoji = {
            AlertType.ABOVE: "📈",
            AlertType.BELOW: "📉",
            AlertType.CHANGE_UP: "🚀",
            AlertType.CHANGE_DOWN: "⚠️"
        }

        type_text = {
            AlertType.ABOVE: "高於",
            AlertType.BELOW: "低於",
            AlertType.CHANGE_UP: "漲幅超過",
            AlertType.CHANGE_DOWN: "跌幅超過"
        }

        message = (
            f"{type_emoji[alert.alert_type]} 價格警報觸發！\n"
            "=" * 30 + "\n"
            f"股票: {alert.stock_code}\n"
            f"條件: {type_text[alert.alert_type]} {alert.threshold}\n"
            f"當前價格: {current_price:.2f}\n"
            f"警報ID: {alert.id}\n"
            "=" * 30 + "\n"
            f"🕐 觸發時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        return message

# 創建全局實例
alert_manager = AlertManager()
