"""
GOV 爬蟲系統 - 爬蟲監控 (Phase 1 新增)
實時監控爬蟲執行狀態、性能和數據新鮮度

功能：
- 執行狀態監控
- 性能指標收集
- 數據新鮮度檢查
- 故障告警
- 詳細的執行報告
"""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class CrawlerStatus(Enum):
    """爬蟲狀態"""
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class CrawlSession:
    """爬蟲會話記錄"""
    session_id: str
    start_time: str
    end_time: Optional[str] = None
    status: str = "running"
    category: str = ""
    total_records: int = 0
    failed_records: int = 0
    duration_seconds: float = 0
    error_message: str = ""
    resources_crawled: List[str] = None

    def __post_init__(self):
        if self.resources_crawled is None:
            self.resources_crawled = []


@dataclass
class PerformanceMetrics:
    """性能指標"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_data_size_mb: float = 0
    average_response_time_ms: float = 0
    requests_per_second: float = 0
    cache_hit_rate: float = 0


class CrawlerMonitor:
    """爬蟲監控系統"""

    def __init__(self, monitor_path: str = "data/monitoring"):
        """
        初始化爬蟲監控

        Args:
            monitor_path: 監控數據保存路徑
        """
        self.monitor_path = Path(monitor_path)
        self.monitor_path.mkdir(parents=True, exist_ok=True)

        self.current_session: Optional[CrawlSession] = None
        self.sessions: List[CrawlSession] = []
        self.metrics = PerformanceMetrics()
        self.data_freshness: Dict[str, datetime] = {}

        # 加載歷史記錄
        self._load_history()

        logger.info(f"✓ 爬蟲監控初始化成功")
        logger.info(f"  Monitor Path: {monitor_path}")

    def _load_history(self) -> None:
        """加載歷史爬蟲會話"""
        history_file = self.monitor_path / "session_history.json"
        if history_file.exists():
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.sessions = [
                        CrawlSession(
                            session_id=s['session_id'],
                            start_time=s['start_time'],
                            end_time=s.get('end_time'),
                            status=s.get('status', 'unknown'),
                            category=s.get('category', ''),
                            total_records=s.get('total_records', 0),
                            failed_records=s.get('failed_records', 0),
                            duration_seconds=s.get('duration_seconds', 0),
                            error_message=s.get('error_message', ''),
                            resources_crawled=s.get('resources_crawled', [])
                        )
                        for s in data.get('sessions', [])
                    ]
                logger.info(f"✓ 已加載 {len(self.sessions)} 個歷史會話")
            except Exception as e:
                logger.error(f"✗ 加載會話歷史失敗: {e}")

    def save_history(self) -> None:
        """保存會話歷史"""
        try:
            history_file = self.monitor_path / "session_history.json"
            history_data = {
                'last_updated': datetime.now().isoformat(),
                'sessions': [asdict(s) for s in self.sessions]
            }

            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"✗ 保存會話歷史失敗: {e}")

    def start_session(self, session_id: str, category: str) -> CrawlSession:
        """
        開始一個爬蟲會話

        Args:
            session_id: 會話 ID
            category: 爬蟲類別

        Returns:
            新的爬蟲會話
        """
        self.current_session = CrawlSession(
            session_id=session_id,
            start_time=datetime.now().isoformat(),
            category=category
        )

        logger.info("=" * 60)
        logger.info(f"開始爬蟲會話: {session_id}")
        logger.info(f"  類別: {category}")
        logger.info(f"  開始時間: {self.current_session.start_time}")
        logger.info("=" * 60)

        return self.current_session

    def end_session(self, status: str = "success", error_message: str = "") -> CrawlSession:
        """
        結束一個爬蟲會話

        Args:
            status: 結束狀態 (success/failed)
            error_message: 錯誤信息

        Returns:
            完成的爬蟲會話
        """
        if not self.current_session:
            logger.warning("⚠️ 沒有活動的爬蟲會話")
            return None

        self.current_session.end_time = datetime.now().isoformat()
        self.current_session.status = status
        self.current_session.error_message = error_message

        # 計算持續時間
        start = datetime.fromisoformat(self.current_session.start_time)
        end = datetime.fromisoformat(self.current_session.end_time)
        self.current_session.duration_seconds = (end - start).total_seconds()

        # 保存會話
        self.sessions.append(self.current_session)
        self.save_history()

        logger.info("=" * 60)
        logger.info(f"爬蟲會話結束: {self.current_session.session_id}")
        logger.info(f"  狀態: {status}")
        logger.info(f"  記錄數: {self.current_session.total_records}")
        logger.info(f"  失敗數: {self.current_session.failed_records}")
        logger.info(f"  持續時間: {self.current_session.duration_seconds:.2f}s")
        if error_message:
            logger.info(f"  錯誤: {error_message}")
        logger.info("=" * 60)

        session = self.current_session
        self.current_session = None
        return session

    def record_crawl_result(
        self,
        resource_name: str,
        total: int,
        failed: int = 0,
        data_size_mb: float = 0
    ) -> None:
        """
        記錄爬蟲結果

        Args:
            resource_name: 資源名稱
            total: 總記錄數
            failed: 失敗記錄數
            data_size_mb: 數據大小 (MB)
        """
        if not self.current_session:
            logger.warning("⚠️ 沒有活動的爬蟲會話")
            return

        self.current_session.total_records += total
        self.current_session.failed_records += failed
        self.current_session.resources_crawled.append(resource_name)

        # 更新性能指標
        self.metrics.total_requests += 1
        if failed == 0:
            self.metrics.successful_requests += 1
        else:
            self.metrics.failed_requests += 1
        self.metrics.total_data_size_mb += data_size_mb

        # 更新數據新鮮度
        self.data_freshness[resource_name] = datetime.now()

        logger.info(f"✓ 爬蟲結果: {resource_name}")
        logger.info(f"  記錄數: {total}")
        if failed > 0:
            logger.info(f"  失敗數: {failed}")
        if data_size_mb > 0:
            logger.info(f"  數據大小: {data_size_mb:.2f} MB")

    def check_data_freshness(self, max_age_hours: int = 24) -> Dict[str, Any]:
        """
        檢查數據新鮮度

        Args:
            max_age_hours: 最大年齡（小時）

        Returns:
            新鮮度檢查結果
        """
        now = datetime.now()
        freshness_status = {}
        stale_data = []

        for resource_name, last_update in self.data_freshness.items():
            age_hours = (now - last_update).total_seconds() / 3600
            is_fresh = age_hours <= max_age_hours

            freshness_status[resource_name] = {
                'last_update': last_update.isoformat(),
                'age_hours': age_hours,
                'is_fresh': is_fresh
            }

            if not is_fresh:
                stale_data.append({
                    'resource': resource_name,
                    'age_hours': age_hours
                })

        if stale_data:
            logger.warning(f"⚠️ 發現 {len(stale_data)} 個過期數據資源")
            for item in stale_data:
                logger.warning(f"  - {item['resource']}: {item['age_hours']:.1f} 小時未更新")

        return {
            'freshness_status': freshness_status,
            'stale_resources': stale_data,
            'check_time': now.isoformat()
        }

    def get_session_report(self, session: Optional[CrawlSession] = None) -> str:
        """
        生成爬蟲會話報告

        Args:
            session: 爬蟲會話（預設為最後一個）

        Returns:
            報告字符串
        """
        if session is None:
            if not self.sessions:
                return "沒有可用的爬蟲會話"
            session = self.sessions[-1]

        report = []
        report.append("=" * 60)
        report.append("爬蟲會話報告")
        report.append("=" * 60)
        report.append(f"會話 ID: {session.session_id}")
        report.append(f"類別: {session.category}")
        report.append(f"狀態: {session.status}")
        report.append(f"開始時間: {session.start_time}")
        report.append(f"結束時間: {session.end_time or 'N/A'}")
        report.append(f"持續時間: {session.duration_seconds:.2f}秒")
        report.append(f"記錄數: {session.total_records}")
        report.append(f"失敗數: {session.failed_records}")
        report.append(f"資源數: {len(session.resources_crawled)}")
        if session.resources_crawled:
            report.append("資源列表:")
            for res in session.resources_crawled:
                report.append(f"  - {res}")
        if session.error_message:
            report.append(f"錯誤信息: {session.error_message}")
        report.append("=" * 60)

        return "\n".join(report)

    def get_performance_report(self) -> str:
        """生成性能報告"""
        report = []
        report.append("=" * 60)
        report.append("爬蟲性能報告")
        report.append("=" * 60)
        report.append(f"總請求數: {self.metrics.total_requests}")
        report.append(f"成功請求: {self.metrics.successful_requests}")
        report.append(f"失敗請求: {self.metrics.failed_requests}")
        report.append(f"總數據大小: {self.metrics.total_data_size_mb:.2f} MB")
        report.append(f"平均響應時間: {self.metrics.average_response_time_ms:.2f} ms")
        report.append(f"請求速率: {self.metrics.requests_per_second:.2f} req/s")

        if self.metrics.total_requests > 0:
            success_rate = (self.metrics.successful_requests / self.metrics.total_requests) * 100
            report.append(f"成功率: {success_rate:.1f}%")

        report.append("=" * 60)
        return "\n".join(report)

    def get_monitoring_statistics(self) -> Dict[str, Any]:
        """獲取監控統計信息"""
        recent_sessions = self.sessions[-10:] if self.sessions else []
        success_count = sum(1 for s in recent_sessions if s.status == "success")

        return {
            'total_sessions': len(self.sessions),
            'recent_sessions': len(recent_sessions),
            'successful_sessions': success_count,
            'data_resources_tracked': len(self.data_freshness),
            'performance_metrics': asdict(self.metrics),
            'last_session': asdict(self.sessions[-1]) if self.sessions else None
        }

    def export_report(self, output_path: str = None) -> str:
        """
        導出監控報告

        Args:
            output_path: 導出路徑

        Returns:
            導出文件路徑
        """
        output_file = Path(output_path or self.monitor_path / "crawler_report.json")

        try:
            report_data = {
                'export_time': datetime.now().isoformat(),
                'statistics': self.get_monitoring_statistics(),
                'session_history': [asdict(s) for s in self.sessions],
                'data_freshness': {
                    k: v.isoformat() for k, v in self.data_freshness.items()
                }
            }

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)

            logger.info(f"✓ 已導出監控報告到 {output_file}")
            return str(output_file)

        except Exception as e:
            logger.error(f"✗ 導出報告失敗: {e}")
            return ""
