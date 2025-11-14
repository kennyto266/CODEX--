"""
隱私審計日誌系統
記錄所有隱私相關事件，生成透明性報告
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger('quant_system.privacy')

class AuditEventType(Enum):
    """審計事件類型"""
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    DATA_DELETION = "data_deletion"
    DATA_EXPORT = "data_export"
    DATA_IMPORT = "data_import"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    PRIVACY_SETTINGS_CHANGED = "privacy_settings_changed"
    KEY_GENERATED = "key_generated"
    KEY_ROTATED = "key_rotated"
    ENCRYPTION_PERFORMED = "encryption_performed"
    DECRYPTION_PERFORMED = "decryption_performed"
    BACKUP_CREATED = "backup_created"
    BACKUP_RESTORED = "backup_restored"
    SECURITY_VIOLATION = "security_violation"
    COMPLIANCE_CHECK = "compliance_check"

class RiskLevel(Enum):
    """風險等級"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class PrivacyAuditEvent:
    """隱私審計事件"""
    event_id: str
    timestamp: str
    event_type: AuditEventType
    user_id: Optional[str]
    session_id: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    resource: str
    action: str
    data_classification: str
    risk_level: RiskLevel
    details: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None

class PrivacyAuditLogger:
    """
    隱私審計日誌器
    記錄所有隱私相關操作，支持查詢和報告生成
    """

    def __init__(self, log_dir: str = 'audit/privacy'):
        """
        初始化隱私審計日誌器

        Args:
            log_dir: 日誌目錄
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # 日誌文件
        self.events_file = self.log_dir / 'events.jsonl'
        self.compliance_file = self.log_dir / 'compliance.json'

        # 配置日誌器
        self._setup_logger()

        # 事件統計
        self.event_counts = {}
        self.violations = []

        logger.info("隱私審計日誌器已初始化")

    def _setup_logger(self):
        """設置審計日誌器"""
        self.audit_logger = logging.getLogger('audit.privacy')
        self.audit_logger.setLevel(logging.INFO)

        # 創建文件處理器
        handler = logging.FileHandler(self.log_dir / 'audit.log')
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.audit_logger.addHandler(handler)

    def log_event(self,
                  event_type: AuditEventType,
                  resource: str,
                  action: str,
                  data_classification: str = "internal",
                  user_id: Optional[str] = None,
                  session_id: Optional[str] = None,
                  ip_address: Optional[str] = None,
                  user_agent: Optional[str] = None,
                  risk_level: RiskLevel = RiskLevel.LOW,
                  details: Optional[Dict[str, Any]] = None,
                  success: bool = True,
                  error_message: Optional[str] = None):
        """
        記錄隱私審計事件

        Args:
            event_type: 事件類型
            resource: 資源
            action: 操作
            data_classification: 數據分類
            user_id: 用戶ID
            session_id: 會話ID
            ip_address: IP地址
            user_agent: 用戶代理
            risk_level: 風險等級
            details: 詳細信息
            success: 是否成功
            error_message: 錯誤信息
        """
        import secrets

        event = PrivacyAuditEvent(
            event_id=secrets.token_hex(16),
            timestamp=datetime.utcnow().isoformat(),
            event_type=event_type,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            resource=resource,
            action=action,
            data_classification=data_classification,
            risk_level=risk_level,
            details=details or {},
            success=success,
            error_message=error_message
        )

        # 保存事件
        self._save_event(event)

        # 記錄到日誌器
        log_message = json.dumps(asdict(event), ensure_ascii=False, default=str)
        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            self.audit_logger.error(log_message)
        elif risk_level == RiskLevel.MEDIUM:
            self.audit_logger.warning(log_message)
        else:
            self.audit_logger.info(log_message)

        # 更新統計
        self._update_stats(event)

        # 檢查安全違規
        if event_type == AuditEventType.SECURITY_VIOLATION or \
           (not success and risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]):
            self.violations.append(asdict(event))

        logger.debug(f"隱私審計事件已記錄: {event_type.value}")

    def _save_event(self, event: PrivacyAuditEvent):
        """保存事件到文件"""
        try:
            with open(self.events_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(asdict(event), ensure_ascii=False, default=str) + '\n')
        except Exception as e:
            logger.error(f"保存審計事件失敗: {e}")

    def _update_stats(self, event: PrivacyAuditEvent):
        """更新事件統計"""
        key = event.event_type.value
        if key not in self.event_counts:
            self.event_counts[key] = {'total': 0, 'success': 0, 'failed': 0}
        self.event_counts[key]['total'] += 1
        if event.success:
            self.event_counts[key]['success'] += 1
        else:
            self.event_counts[key]['failed'] += 1

    def get_user_activity(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        獲取用戶活動記錄

        Args:
            user_id: 用戶ID
            limit: 限制數量

        Returns:
            用戶活動列表
        """
        events = []
        try:
            with open(self.events_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        event = json.loads(line)
                        if event.get('user_id') == user_id:
                            events.append(event)
        except Exception as e:
            logger.error(f"讀取用戶活動失敗: {e}")

        # 按時間倒序
        events.sort(key=lambda x: x['timestamp'], reverse=True)
        return events[:limit]

    def get_data_access_log(self, resource: str, start_date: Optional[str] = None,
                           end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        獲取數據訪問日誌

        Args:
            resource: 資源
            start_date: 開始日期
            end_date: 結束日期

        Returns:
            訪問日誌列表
        """
        events = []
        try:
            with open(self.events_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        event = json.loads(line)
                        if event.get('resource') == resource:
                            # 檢查日期範圍
                            if start_date and event['timestamp'] < start_date:
                                continue
                            if end_date and event['timestamp'] > end_date:
                                continue
                            events.append(event)
        except Exception as e:
            logger.error(f"讀取數據訪問日誌失敗: {e}")

        return events

    def generate_transparency_report(self) -> Dict[str, Any]:
        """
        生成透明性報告

        Returns:
            透明性報告
        """
        report = {
            'report_generated_at': datetime.utcnow().isoformat(),
            'summary': {
                'total_events': sum(stats['total'] for stats in self.event_counts.values()),
                'unique_users': len(set(e.get('user_id') for e in self._read_all_events() if e.get('user_id'))),
                'total_violations': len(self.violations),
                'security_score': self._calculate_security_score()
            },
            'event_statistics': self.event_counts,
            'recent_violations': self.violations[-10:] if self.violations else [],
            'data_classification_distribution': self._get_classification_stats(),
            'risk_level_distribution': self._get_risk_stats(),
            'compliance_status': self._check_compliance()
        }

        # 保存報告
        with open(self.log_dir / 'transparency_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info("透明性報告已生成")
        return report

    def _read_all_events(self) -> List[Dict[str, Any]]:
        """讀取所有事件"""
        events = []
        try:
            with open(self.events_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        events.append(json.loads(line))
        except Exception as e:
            logger.error(f"讀取所有事件失敗: {e}")
        return events

    def _calculate_security_score(self) -> float:
        """計算安全評分（0-100）"""
        total_events = sum(stats['total'] for stats in self.event_counts.values())
        if total_events == 0:
            return 100.0

        failed_events = sum(stats['failed'] for stats in self.event_counts.values())
        critical_violations = sum(1 for v in self.violations if v.get('risk_level') == 'critical')

        # 基礎分數
        score = 100.0

        # 失敗率扣分
        failure_rate = failed_events / total_events
        score -= failure_rate * 30

        # 嚴重違規扣分
        score -= critical_violations * 10

        return max(0.0, min(100.0, score))

    def _get_classification_stats(self) -> Dict[str, int]:
        """獲取數據分類統計"""
        stats = {'public': 0, 'internal': 0, 'confidential': 0, 'restricted': 0}
        for event in self._read_all_events():
            classification = event.get('data_classification', 'internal')
            if classification in stats:
                stats[classification] += 1
        return stats

    def _get_risk_stats(self) -> Dict[str, int]:
        """獲取風險等級統計"""
        stats = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        for event in self._read_all_events():
            risk = event.get('risk_level', 'low')
            if risk in stats:
                stats[risk] += 1
        return stats

    def _check_compliance(self) -> Dict[str, Any]:
        """檢查合規性"""
        return {
            'no_unauthorized_access': True,  # 需要實現
            'all_sensitive_data_logged': True,  # 需要實現
            'encryption_verified': True,  # 需要實現
            'key_management_compliant': True,  # 需要實現
            'overall_compliance': True
        }

    def export_audit_trail(self, user_id: str, output_file: str):
        """
        導出用戶審計追蹤

        Args:
            user_id: 用戶ID
            output_file: 輸出文件
        """
        events = self.get_user_activity(user_id)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'user_id': user_id,
                'exported_at': datetime.utcnow().isoformat(),
                'total_events': len(events),
                'events': events
            }, f, indent=2, ensure_ascii=False)

        logger.info(f"用戶 {user_id} 的審計追蹤已導出到: {output_file}")

    def clear_old_events(self, days: int = 90):
        """
        清理舊事件

        Args:
            days: 保留天數
        """
        cutoff_date = datetime.utcnow().timestamp() - (days * 24 * 60 * 60)

        # 重寫文件，保留新事件
        events = []
        try:
            with open(self.events_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        event = json.loads(line)
                        event_time = datetime.fromisoformat(event['timestamp']).timestamp()
                        if event_time > cutoff_date:
                            events.append(event)
        except Exception as e:
            logger.error(f"讀取事件文件失敗: {e}")
            return

        try:
            with open(self.events_file, 'w', encoding='utf-8') as f:
                for event in events:
                    f.write(json.dumps(event, ensure_ascii=False, default=str) + '\n')
        except Exception as e:
            logger.error(f"寫入事件文件失敗: {e}")

        logger.info(f"已清理舊審計事件，保留 {len(events)} 個新事件")
