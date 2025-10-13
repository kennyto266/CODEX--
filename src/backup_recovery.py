import os
import shutil
import gzip
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import subprocess

logger = logging.getLogger('quant_system')

class BackupManager:
    """备份和恢复管理器"""

    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)

        # 备份配置
        self.retention_days = int(os.getenv('BACKUP_RETENTION_DAYS', '30'))
        self.max_backups = int(os.getenv('MAX_BACKUPS', '10'))

    def create_database_backup(self, db_url: str, backup_name: Optional[str] = None) -> str:
        """创建数据库备份"""
        if backup_name is None:
            backup_name = f"db_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        backup_path = self.backup_dir / f"{backup_name}.sql.gz"

        try:
            # 使用pg_dump创建PostgreSQL备份
            cmd = [
                "pg_dump",
                db_url,
                "|",
                "gzip",
                ">",
                str(backup_path)
            ]

            # 执行备份命令
            result = subprocess.run(" ".join(cmd), shell=True, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info(f"Database backup created: {backup_path}")
                return str(backup_path)
            else:
                logger.error(f"Database backup failed: {result.stderr}")
                return ""

        except Exception as e:
            logger.error(f"Database backup error: {e}")
            return ""

    def create_file_backup(self, source_dirs: List[str], backup_name: Optional[str] = None) -> str:
        """创建文件备份"""
        if backup_name is None:
            backup_name = f"files_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        backup_path = self.backup_dir / f"{backup_name}.tar.gz"

        try:
            # 使用tar创建压缩备份
            cmd = ["tar", "-czf", str(backup_path)] + source_dirs

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info(f"File backup created: {backup_path}")
                return str(backup_path)
            else:
                logger.error(f"File backup failed: {result.stderr}")
                return ""

        except Exception as e:
            logger.error(f"File backup error: {e}")
            return ""

    def create_full_backup(self, db_url: str, source_dirs: List[str]) -> Dict[str, str]:
        """创建完整备份（数据库+文件）"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"full_backup_{timestamp}"

        backups = {}

        # 数据库备份
        db_backup = self.create_database_backup(db_url, f"{backup_name}_db")
        if db_backup:
            backups['database'] = db_backup

        # 文件备份
        file_backup = self.create_file_backup(source_dirs, f"{backup_name}_files")
        if file_backup:
            backups['files'] = file_backup

        # 创建备份清单
        manifest = {
            'timestamp': timestamp,
            'backups': backups,
            'source_dirs': source_dirs,
            'db_url': self._mask_db_url(db_url)
        }

        manifest_path = self.backup_dir / f"{backup_name}_manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)

        logger.info(f"Full backup completed: {backup_name}")
        return backups

    def restore_database(self, backup_path: str, db_url: str) -> bool:
        """恢复数据库"""
        try:
            # 解压并恢复数据库
            cmd = [
                "gunzip",
                "-c",
                backup_path,
                "|",
                "psql",
                db_url
            ]

            result = subprocess.run(" ".join(cmd), shell=True, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info(f"Database restored from: {backup_path}")
                return True
            else:
                logger.error(f"Database restore failed: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Database restore error: {e}")
            return False

    def restore_files(self, backup_path: str, target_dir: str) -> bool:
        """恢复文件"""
        try:
            # 解压文件到目标目录
            cmd = ["tar", "-xzf", backup_path, "-C", target_dir]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info(f"Files restored to: {target_dir}")
                return True
            else:
                logger.error(f"File restore failed: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"File restore error: {e}")
            return False

    def restore_full_backup(self, manifest_path: str) -> bool:
        """从清单恢复完整备份"""
        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)

            success = True

            # 恢复数据库
            if 'database' in manifest.get('backups', {}):
                db_backup = manifest['backups']['database']
                db_url = os.getenv('DATABASE_URL', '')
                if not self.restore_database(db_backup, db_url):
                    success = False

            # 恢复文件
            if 'files' in manifest.get('backups', {}):
                file_backup = manifest['backups']['files']
                # 恢复到当前目录（可配置）
                if not self.restore_files(file_backup, '.'):
                    success = False

            if success:
                logger.info(f"Full restore completed from: {manifest_path}")
            else:
                logger.error(f"Full restore partially failed from: {manifest_path}")

            return success

        except Exception as e:
            logger.error(f"Full restore error: {e}")
            return False

    def cleanup_old_backups(self):
        """清理旧备份文件"""
        try:
            # 获取所有备份文件
            backup_files = list(self.backup_dir.glob("*"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            # 保留最新的备份
            files_to_keep = backup_files[:self.max_backups]

            # 删除旧文件
            for file_path in backup_files[self.max_backups:]:
                # 检查是否超过保留天数
                file_age = datetime.now() - datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_age.days > self.retention_days:
                    file_path.unlink()
                    logger.info(f"Deleted old backup: {file_path}")

            # 同时清理空目录
            for dir_path in self.backup_dir.rglob('*'):
                if dir_path.is_dir() and not list(dir_path.iterdir()):
                    dir_path.rmdir()

        except Exception as e:
            logger.error(f"Cleanup error: {e}")

    def list_backups(self) -> List[Dict]:
        """列出所有备份"""
        backups = []

        try:
            for manifest_file in self.backup_dir.glob("*_manifest.json"):
                with open(manifest_file, 'r') as f:
                    manifest = json.load(f)

                backups.append({
                    'name': manifest_file.stem.replace('_manifest', ''),
                    'timestamp': manifest.get('timestamp'),
                    'backups': manifest.get('backups', {}),
                    'size': self._calculate_backup_size(manifest.get('backups', {}))
                })

        except Exception as e:
            logger.error(f"List backups error: {e}")

        return sorted(backups, key=lambda x: x['timestamp'], reverse=True)

    def _mask_db_url(self, db_url: str) -> str:
        """遮罩数据库URL中的敏感信息"""
        # 简单的遮罩，实际使用时应该更安全
        return "postgresql://***:***@***:***/***"

    def _calculate_backup_size(self, backups: Dict[str, str]) -> str:
        """计算备份总大小"""
        total_size = 0

        for backup_type, backup_path in backups.items():
            try:
                total_size += Path(backup_path).stat().st_size
            except:
                pass

        # 转换为人类可读格式
        for unit in ['B', 'KB', 'MB', 'GB']:
            if total_size < 1024:
                return f"{total_size:.1f}{unit}"
            total_size /= 1024

        return f"{total_size:.1f}TB"

    def get_backup_stats(self) -> Dict:
        """获取备份统计信息"""
        backups = self.list_backups()

        return {
            'total_backups': len(backups),
            'oldest_backup': backups[-1]['timestamp'] if backups else None,
            'newest_backup': backups[0]['timestamp'] if backups else None,
            'total_size': sum(float(b['size'].rstrip('BKMGT').rstrip('B')) *
                            {'B': 1, 'KB': 1024, 'MB': 1024**2, 'GB': 1024**3, 'TB': 1024**4}
                            .get(b['size'][-2:], 1) for b in backups)
        }

# 全局实例
backup_manager = BackupManager()

# 便捷函数
def schedule_backup(db_url: str, source_dirs: List[str], interval_hours: int = 24):
    """计划定期备份"""
    import asyncio

    async def backup_loop():
        while True:
            try:
                backup_manager.create_full_backup(db_url, source_dirs)
                backup_manager.cleanup_old_backups()
                await asyncio.sleep(interval_hours * 3600)
            except Exception as e:
                logger.error(f"Scheduled backup failed: {e}")
                await asyncio.sleep(3600)  # 出错后1小时重试

    asyncio.create_task(backup_loop())
    logger.info(f"Scheduled backup every {interval_hours} hours")