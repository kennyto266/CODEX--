"""
报告归档和版本管理模块

实现报告归档功能，支持：
- 自动归档旧报告
- 版本控制
- 存储空间管理
- 压缩和清理
- 快速检索
- 备份策略
- 保留期管理
"""

import os
import shutil
import zipfile
import gzip
import json
import time
import hashlib
from typing import Dict, List, Optional, Any, Tuple, Union
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from .params import ReportParams, get_params_manager

logger = logging.getLogger(__name__)


class ArchiveStatus(Enum):
    """归档状态"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    COMPRESSED = "compressed"
    DELETED = "deleted"
    BACKED_UP = "backed_up"


class ArchiveFormat(Enum):
    """归档格式"""
    ZIP = "zip"
    GZ = "gz"
    TAR = "tar"
    TAR_GZ = "tar.gz"


@dataclass
class ArchivedReport:
    """归档报告记录"""
    report_id: str
    original_path: str
    archive_path: str
    version: str
    format: ArchiveFormat
    size: int
    compressed_size: int
    checksum: str
    created_at: str
    archived_at: str
    status: ArchiveStatus
    retention_days: int
    metadata: Dict[str, Any]
    backup_count: int = 0
    access_count: int = 0
    last_accessed: Optional[str] = None


class ArchiveManager:
    """归档管理器"""

    def __init__(
        self,
        archive_dir: str = "archive/reports",
        temp_dir: str = "archive/temp",
        max_size_gb: float = 10.0,
        default_retention_days: int = 365
    ):
        self.archive_dir = Path(archive_dir)
        self.temp_dir = Path(temp_dir)
        self.max_size_bytes = int(max_size_gb * 1024 * 1024 * 1024)
        self.default_retention_days = default_retention_days

        # 创建目录
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        # 归档记录存储
        self.archive_db_path = self.archive_dir / "archive_db.json"
        self.archived_reports: Dict[str, List[ArchivedReport]] = {}
        self.executor = ThreadPoolExecutor(max_workers=4)

        # 加载归档记录
        self._load_archive_db()

    def _load_archive_db(self):
        """加载归档数据库"""
        if self.archive_db_path.exists():
            try:
                with open(self.archive_db_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                    for report_id, reports in data.items():
                        self.archived_reports[report_id] = []
                        for report_data in reports:
                            report_data['format'] = ArchiveFormat(report_data['format'])
                            report_data['status'] = ArchiveStatus(report_data['status'])
                            self.archived_reports[report_id].append(
                                ArchivedReport(**report_data)
                            )

                logger.info(f"已加载 {len(self.archived_reports)} 个报告的归档记录")
            except Exception as e:
                logger.error(f"加载归档数据库失败: {e}")

    def _save_archive_db(self):
        """保存归档数据库"""
        try:
            data = {}
            for report_id, reports in self.archived_reports.items():
                data[report_id] = [asdict(report) for report in reports]

            with open(self.archive_db_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)

        except Exception as e:
            logger.error(f"保存归档数据库失败: {e}")

    def archive_report(
        self,
        report_path: str,
        report_id: str,
        version: Optional[str] = None,
        format: ArchiveFormat = ArchiveFormat.ZIP,
        retention_days: Optional[int] = None,
        compress: bool = True
    ) -> Optional[ArchivedReport]:
        """归档报告"""
        try:
            report_path = Path(report_path)
            if not report_path.exists():
                logger.error(f"报告文件不存在: {report_path}")
                return None

            # 确定版本号
            if version is None:
                version = self._generate_version(report_id)

            # 确定保留期
            if retention_days is None:
                retention_days = self.default_retention_days

            # 创建归档记录
            archived_report = ArchivedReport(
                report_id=report_id,
                original_path=str(report_path),
                archive_path="",  # 稍后设置
                version=version,
                format=format,
                size=report_path.stat().st_size,
                compressed_size=0,
                checksum=self._calculate_checksum(report_path),
                created_at=datetime.fromtimestamp(report_path.stat().st_ctime).isoformat(),
                archived_at=datetime.now().isoformat(),
                status=ArchiveStatus.ARCHIVED,
                retention_days=retention_days,
                metadata={}
            )

            # 执行归档
            if compress:
                archive_path = self._compress_archive(report_path, report_id, version, format)
            else:
                archive_path = self._copy_archive(report_path, report_id, version)

            archived_report.archive_path = str(archive_path)
            archived_report.compressed_size = archive_path.stat().st_size

            # 保存到数据库
            if report_id not in self.archived_reports:
                self.archived_reports[report_id] = []

            # 检查是否已存在相同版本
            existing = next(
                (r for r in self.archived_reports[report_id] if r.version == version),
                None
            )

            if existing:
                # 更新现有记录
                for key, value in asdict(archived_report).items():
                    setattr(existing, key, value)
            else:
                # 添加新记录
                self.archived_reports[report_id].append(archived_report)

            # 保存数据库
            self._save_archive_db()

            # 清理原始文件
            if report_path.exists():
                report_path.unlink()

            logger.info(f"已归档报告: {report_id} v{version}, 路径: {archive_path}")
            return archived_report

        except Exception as e:
            logger.error(f"归档报告失败: {e}")
            return None

    def restore_report(
        self,
        report_id: str,
        version: str,
        restore_path: Optional[str] = None
    ) -> Optional[Path]:
        """恢复报告"""
        try:
            archived_report = self._find_archived_report(report_id, version)
            if not archived_report:
                logger.error(f"未找到归档报告: {report_id} v{version}")
                return None

            archive_path = Path(archived_report.archive_path)
            if not archive_path.exists():
                logger.error(f"归档文件不存在: {archive_path}")
                return None

            # 确定恢复路径
            if restore_path is None:
                restore_dir = Path("reports/restored")
                restore_dir.mkdir(parents=True, exist_ok=True)
                restore_path = restore_dir / f"{report_id}_{version}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            else:
                restore_path = Path(restore_path)

            # 解压缩
            if archived_report.format == ArchiveFormat.ZIP:
                self._extract_zip(archive_path, restore_path)
            elif archived_report.format == ArchiveFormat.GZ:
                self._extract_gz(archive_path, restore_path)
            else:
                shutil.copy2(archive_path, restore_path)

            # 更新访问记录
            archived_report.last_accessed = datetime.now().isoformat()
            archived_report.access_count += 1
            self._save_archive_db()

            logger.info(f"已恢复报告: {report_id} v{version} -> {restore_path}")
            return restore_path

        except Exception as e:
            logger.error(f"恢复报告失败: {e}")
            return None

    def list_archived_reports(
        self,
        report_id: Optional[str] = None,
        status: Optional[ArchiveStatus] = None
    ) -> List[ArchivedReport]:
        """列出归档报告"""
        reports = []

        if report_id:
            reports = self.archived_reports.get(report_id, [])
        else:
            for reports_list in self.archived_reports.values():
                reports.extend(reports_list)

        # 过滤状态
        if status:
            reports = [r for r in reports if r.status == status]

        # 按归档时间排序
        reports.sort(key=lambda x: x.archived_at, reverse=True)

        return reports

    def delete_archived_report(self, report_id: str, version: str) -> bool:
        """删除归档报告"""
        try:
            archived_report = self._find_archived_report(report_id, version)
            if not archived_report:
                logger.error(f"未找到归档报告: {report_id} v{version}")
                return False

            archive_path = Path(archived_report.archive_path)

            # 删除归档文件
            if archive_path.exists():
                archive_path.unlink()

            # 更新状态
            archived_report.status = ArchiveStatus.DELETED
            archived_report.archive_path = ""

            # 从数据库中移除
            self.archived_reports[report_id] = [
                r for r in self.archived_reports[report_id] if r.version != version
            ]

            self._save_archive_db()

            logger.info(f"已删除归档报告: {report_id} v{version}")
            return True

        except Exception as e:
            logger.error(f"删除归档报告失败: {e}")
            return False

    def cleanup_expired_reports(self) -> int:
        """清理过期报告"""
        cleaned_count = 0
        current_time = datetime.now()

        for report_id, reports in self.archived_reports.items():
            for report in reports[:]:  # 使用切片避免修改时出错
                # 计算是否过期
                archived_date = datetime.fromisoformat(report.archived_at)
                days_old = (current_time - archived_date).days

                if days_old > report.retention_days:
                    # 删除归档文件
                    archive_path = Path(report.archive_path)
                    if archive_path.exists():
                        archive_path.unlink()

                    # 标记为已删除
                    report.status = ArchiveStatus.DELETED
                    report.archive_path = ""
                    cleaned_count += 1

                    logger.info(f"已清理过期报告: {report_id} v{report.version}")

        # 清理空记录
        self.archived_reports = {
            rid: reports for rid, reports in self.archived_reports.items()
            if reports
        }

        self._save_archive_db()
        return cleaned_count

    def check_storage_limit(self) -> Dict[str, Any]:
        """检查存储空间使用情况"""
        total_size = 0
        total_files = 0

        for report_id, reports in self.archived_reports.items():
            for report in reports:
                if report.status in [ArchiveStatus.ARCHIVED, ArchiveStatus.COMPRESSED]:
                    archive_path = Path(report.archive_path)
                    if archive_path.exists():
                        total_size += archive_path.stat().st_size
                        total_files += 1

        usage_percent = (total_size / self.max_size_bytes) * 100

        return {
            "total_size_bytes": total_size,
            "total_size_gb": round(total_size / (1024**3), 2),
            "max_size_gb": round(self.max_size_bytes / (1024**3), 2),
            "usage_percent": round(usage_percent, 2),
            "total_files": total_files,
            "limit_reached": total_size >= self.max_size_bytes
        }

    def compress_old_reports(self, days_threshold: int = 30) -> int:
        """压缩旧报告"""
        compressed_count = 0
        current_time = datetime.now()

        for report_id, reports in self.archived_reports.items():
            for report in reports:
                if report.status == ArchiveStatus.ARCHIVED:
                    archived_date = datetime.fromisoformat(report.archived_at)
                    if (current_time - archived_date).days >= days_threshold:
                        # 压缩报告
                        archive_path = Path(report.archive_path)
                        if archive_path.exists() and not str(archive_path).endswith(('.gz', '.zip')):
                            self._recompress_report(report)
                            compressed_count += 1

        self._save_archive_db()
        return compressed_count

    def create_backup(
        self,
        report_id: str,
        version: str,
        backup_location: str,
        format: ArchiveFormat = ArchiveFormat.ZIP
    ) -> bool:
        """创建备份"""
        try:
            archived_report = self._find_archived_report(report_id, version)
            if not archived_report:
                logger.error(f"未找到归档报告: {report_id} v{version}")
                return False

            source_path = Path(archived_report.archive_path)
            if not source_path.exists():
                logger.error(f"归档文件不存在: {source_path}")
                return False

            backup_path = Path(backup_location) / f"{report_id}_{version}_backup.zip"

            # 创建备份
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                zf.write(source_path, source_path.name)

            # 更新备份计数
            archived_report.backup_count += 1

            logger.info(f"已创建备份: {report_id} v{version} -> {backup_path}")
            return True

        except Exception as e:
            logger.error(f"创建备份失败: {e}")
            return False

    def search_reports(self, keyword: str) -> List[ArchivedReport]:
        """搜索报告"""
        results = []
        pattern = re.compile(keyword, re.IGNORECASE)

        for reports in self.archived_reports.values():
            for report in reports:
                # 在报告ID和路径中搜索
                if pattern.search(report.report_id) or pattern.search(report.original_path):
                    results.append(report)

        return results

    def get_statistics(self) -> Dict[str, Any]:
        """获取归档统计信息"""
        total_reports = sum(len(reports) for reports in self.archived_reports.values())
        active_reports = sum(
            1 for reports in self.archived_reports.values()
            for report in reports if report.status == ArchiveStatus.ARCHIVED
        )
        compressed_reports = sum(
            1 for reports in self.archived_reports.values()
            for report in reports if report.status == ArchiveStatus.COMPRESSED
        )

        total_size = sum(
            report.compressed_size
            for reports in self.archived_reports.values()
            for report in reports
            if report.status in [ArchiveStatus.ARCHIVED, ArchiveStatus.COMPRESSED]
        )

        storage_info = self.check_storage_limit()

        return {
            "total_archived_reports": total_reports,
            "active_reports": active_reports,
            "compressed_reports": compressed_reports,
            "total_size_gb": round(total_size / (1024**3), 2),
            "storage_usage": storage_info,
            "unique_report_ids": len(self.archived_reports)
        }

    def _generate_version(self, report_id: str) -> str:
        """生成版本号"""
        reports = self.archived_reports.get(report_id, [])

        if not reports:
            return "v1.0.0"

        # 解析现有版本号
        versions = []
        for report in reports:
            version = report.version
            # 提取版本号格式: v1.0.0 或 1.0.0
            match = re.search(r'v?(\d+)\.(\d+)\.(\d+)', version)
            if match:
                major, minor, patch = map(int, match.groups())
                versions.append((major, minor, patch))

        if not versions:
            return "v1.0.0"

        # 增加补丁版本号
        major, minor, patch = max(versions)
        return f"v{major}.{minor}.{patch + 1}"

    def _calculate_checksum(self, file_path: Path) -> str:
        """计算文件校验和"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    def _compress_archive(
        self,
        report_path: Path,
        report_id: str,
        version: str,
        format: ArchiveFormat
    ) -> Path:
        """压缩归档文件"""
        archive_name = f"{report_id}_{version}"
        archive_path = self.archive_dir / f"{archive_name}.{format.value}"

        if format == ArchiveFormat.ZIP:
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                zf.write(report_path, report_path.name)

        elif format == ArchiveFormat.GZ:
            with open(report_path, 'rb') as f_in:
                with gzip.open(archive_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

        else:
            shutil.copy2(report_path, archive_path)

        return archive_path

    def _copy_archive(self, report_path: Path, report_id: str, version: str) -> Path:
        """复制归档文件"""
        archive_name = f"{report_id}_{version}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        archive_path = self.archive_dir / archive_name
        shutil.copy2(report_path, archive_path)
        return archive_path

    def _extract_zip(self, archive_path: Path, restore_path: Path):
        """解压缩ZIP文件"""
        with zipfile.ZipFile(archive_path, 'r') as zf:
            zf.extractall(restore_path.parent)
            # 获取第一个文件
            extracted_files = zf.namelist()
            if extracted_files:
                extracted_path = restore_path.parent / extracted_files[0]
                extracted_path.rename(restore_path)

    def _extract_gz(self, archive_path: Path, restore_path: Path):
        """解压缩GZ文件"""
        with gzip.open(archive_path, 'rb') as f_in:
            with open(restore_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

    def _recompress_report(self, report: ArchivedReport):
        """重新压缩报告"""
        archive_path = Path(report.archive_path)
        if not archive_path.exists():
            return

        # 压缩为GZ格式
        new_path = self.archive_dir / f"{report.report_id}_{report.version}.gz"
        with open(archive_path, 'rb') as f_in:
            with gzip.open(new_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        # 删除旧文件
        archive_path.unlink()

        # 更新记录
        report.archive_path = str(new_path)
        report.format = ArchiveFormat.GZ
        report.compressed_size = new_path.stat().st_size
        report.status = ArchiveStatus.COMPRESSED

    def _find_archived_report(
        self,
        report_id: str,
        version: str
    ) -> Optional[ArchivedReport]:
        """查找归档报告"""
        reports = self.archived_reports.get(report_id, [])
        return next((r for r in reports if r.version == version), None)


# 创建全局归档管理器实例
_archive_manager_instance: Optional[ArchiveManager] = None


def get_archive_manager() -> ArchiveManager:
    """获取归档管理器实例"""
    global _archive_manager_instance
    if _archive_manager_instance is None:
        _archive_manager_instance = ArchiveManager()
    return _archive_manager_instance


if __name__ == "__main__":
    # 示例：使用归档管理器
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 创建测试报告
    test_report = Path("test_report.html")
    with open(test_report, "w", encoding="utf-8") as f:
        f.write("<html><body><h1>测试报告</h1></body></html>")

    # 创建归档管理器
    archive_manager = ArchiveManager()

    # 归档报告
    archived = archive_manager.archive_report(
        report_path=str(test_report),
        report_id="test_report",
        version="v1.0.0"
    )

    if archived:
        print(f"已归档报告: {archived.archive_path}")
        print(f"压缩前大小: {archived.size} bytes")
        print(f"压缩后大小: {archived.compressed_size} bytes")

    # 恢复报告
    restored_path = archive_manager.restore_report("test_report", "v1.0.0")
    if restored_path:
        print(f"已恢复报告: {restored_path}")

    # 列出所有归档报告
    reports = archive_manager.list_archived_reports()
    print(f"归档报告数量: {len(reports)}")

    # 获取统计信息
    stats = archive_manager.get_statistics()
    print(f"归档统计: {json.dumps(stats, indent=2, ensure_ascii=False, default=str)}")

    # 检查存储使用情况
    storage = archive_manager.check_storage_limit()
    print(f"存储使用: {storage}")

    # 搜索报告
    search_results = archive_manager.search_reports("test")
    print(f"搜索结果: {len(search_results)}")
