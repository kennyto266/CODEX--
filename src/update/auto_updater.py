"""
HKEX量化交易系统 - 自动更新模块
Auto-updater for HKEX Quantitative Trading System
"""

import os
import sys
import json
import hashlib
import logging
import requests
import zipfile
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from packaging import version
from pydantic import BaseModel, Field

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('update.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class UpdateConfig(BaseModel):
    """更新配置模型"""
    current_version: str = Field(default="1.0.0")
    update_server_url: str = Field(default="https://updates.hkex.com")
    check_interval: int = Field(default=86400)  # 24小时
    auto_update: bool = Field(default=False)
    update_channel: str = Field(default="stable")  # stable, beta, dev
    backup_before_update: bool = Field(default=True)
    max_backup_versions: int = Field(default=5)


class ReleaseInfo(BaseModel):
    """发布信息模型"""
    version: str
    release_date: str
    description: str
    download_url: str
    file_size: int
    file_hash: str
    notes: List[str] = []
    min_system_version: Optional[str] = None
    changelog_url: Optional[str] = None
    is_mandatory: bool = False


class UpdateManager:
    """更新管理器"""

    def __init__(self, config: UpdateConfig = None):
        self.config = config or UpdateConfig()
        self.app_dir = Path(__file__).parent.parent.parent
        self.update_dir = self.app_dir / "updates"
        self.backup_dir = self.app_dir / "backups"
        self.temp_dir = self.app_dir / "temp"

        # 确保目录存在
        self.update_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)

        # 加载版本信息
        self._load_version_info()

    def _load_version_info(self) -> None:
        """加载版本信息"""
        try:
            version_file = self.app_dir / "version.py"
            if version_file.exists():
                exec(version_file.open().read(), globals())
                if '__version__' in globals():
                    self.config.current_version = globals()['__version__']
        except Exception as e:
            logger.warning(f"无法加载版本信息: {e}")

    def get_current_version(self) -> str:
        """获取当前版本"""
        return self.config.current_version

    def check_for_updates(self) -> Optional[ReleaseInfo]:
        """检查更新"""
        logger.info(f"检查更新: {self.config.current_version} -> {self.config.update_channel}")

        try:
            # 构建API URL
            api_url = f"{self.config.update_server_url}/api/check-update"
            params = {
                "current_version": self.config.current_version,
                "channel": self.config.update_channel,
                "platform": self._get_platform()
            }

            response = requests.get(api_url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data.get("has_update"):
                release_info = ReleaseInfo(**data["release_info"])
                logger.info(f"发现新版本: {release_info.version}")
                return release_info
            else:
                logger.info("当前已是最新版本")
                return None

        except requests.RequestException as e:
            logger.error(f"检查更新失败: {e}")
            return None
        except Exception as e:
            logger.error(f"处理更新信息失败: {e}")
            return None

    def download_update(self, release_info: ReleaseInfo) -> Optional[Path]:
        """下载更新包"""
        logger.info(f"开始下载更新: {release_info.version}")

        try:
            update_file = self.update_dir / f"update_{release_info.version}.zip"

            # 下载文件
            with requests.get(release_info.download_url, stream=True) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))

                downloaded = 0
                with open(update_file, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)

                            # 显示进度
                            if total_size > 0:
                                percent = (downloaded / total_size) * 100
                                print(f"\r下载进度: {percent:.1f}%", end='')

            print()  # 换行
            logger.info(f"下载完成: {update_file}")

            # 验证文件哈希
            if release_info.file_hash:
                if not self._verify_file_hash(update_file, release_info.file_hash):
                    logger.error("文件哈希验证失败")
                    update_file.unlink()
                    return None

            return update_file

        except Exception as e:
            logger.error(f"下载更新失败: {e}")
            return None

    def _verify_file_hash(self, file_path: Path, expected_hash: str) -> bool:
        """验证文件哈希"""
        try:
            sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    sha256.update(chunk)

            actual_hash = sha256.hexdigest()
            return actual_hash.lower() == expected_hash.lower()
        except Exception as e:
            logger.error(f"验证哈希失败: {e}")
            return False

    def create_backup(self) -> Optional[Path]:
        """创建备份"""
        if not self.config.backup_before_update:
            return None

        logger.info("创建系统备份...")

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"backup_{timestamp}.zip"

            # 排除的目录和文件
            exclude_patterns = [
                "__pycache__",
                "*.pyc",
                ".git",
                "venv",
                ".venv",
                "env",
                ".env",
                "updates",
                "backups",
                "temp",
                "*.log",
                "update.log"
            ]

            with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                for root, dirs, files in os.walk(self.app_dir):
                    # 过滤排除的目录
                    dirs[:] = [d for d in dirs if not any(p in d for p in exclude_patterns)]

                    for file in files:
                        file_path = Path(root) / file
                        # 跳过排除的文件
                        if any(p in str(file_path) for p in exclude_patterns):
                            continue

                        arcname = file_path.relative_to(self.app_dir)
                        zf.write(file_path, arcname)

            # 清理旧备份
            self._cleanup_old_backups()

            logger.info(f"备份创建成功: {backup_file}")
            return backup_file

        except Exception as e:
            logger.error(f"创建备份失败: {e}")
            return None

    def _cleanup_old_backups(self) -> None:
        """清理旧备份"""
        try:
            backups = sorted(
                self.backup_dir.glob("backup_*.zip"),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )

            for backup in backups[self.config.max_backup_versions:]:
                backup.unlink()
                logger.info(f"删除旧备份: {backup}")
        except Exception as e:
            logger.error(f"清理备份失败: {e}")

    def apply_update(self, update_file: Path) -> bool:
        """应用更新"""
        logger.info("开始应用更新...")

        try:
            # 创建备份
            backup_path = self.create_backup()
            if backup_path:
                logger.info(f"备份位置: {backup_path}")

            # 解压更新包
            logger.info("解压更新文件...")
            with zipfile.ZipFile(update_file, 'r') as zf:
                zf.extractall(self.app_dir)

            logger.info("更新应用成功")

            # 记录更新
            self._record_update(update_file.stem)

            return True

        except Exception as e:
            logger.error(f"应用更新失败: {e}")

            # 如果更新失败，可以从备份恢复
            if backup_path and backup_path.exists():
                logger.info("尝试从备份恢复...")
                self._restore_from_backup(backup_path)

            return False

    def _restore_from_backup(self, backup_path: Path) -> None:
        """从备份恢复"""
        try:
            with zipfile.ZipFile(backup_path, 'r') as zf:
                zf.extractall(self.app_dir)
            logger.info("备份恢复成功")
        except Exception as e:
            logger.error(f"备份恢复失败: {e}")

    def _record_update(self, version: str) -> None:
        """记录更新信息"""
        try:
            update_record = {
                "version": version,
                "timestamp": datetime.now().isoformat(),
                "success": True
            }

            record_file = self.app_dir / "update_history.json"

            if record_file.exists():
                with open(record_file, 'r') as f:
                    history = json.load(f)
            else:
                history = []

            history.append(update_record)

            with open(record_file, 'w') as f:
                json.dump(history, f, indent=2)

        except Exception as e:
            logger.error(f"记录更新信息失败: {e}")

    def get_update_history(self) -> List[Dict]:
        """获取更新历史"""
        try:
            record_file = self.app_dir / "update_history.json"
            if record_file.exists():
                with open(record_file, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            logger.error(f"读取更新历史失败: {e}")
            return []

    def _get_platform(self) -> str:
        """获取平台信息"""
        if sys.platform.startswith('win'):
            return 'windows'
        elif sys.platform.startswith('darwin'):
            return 'macos'
        elif sys.platform.startswith('linux'):
            return 'linux'
        else:
            return 'unknown'

    def start_auto_update_check(self) -> None:
        """启动自动更新检查"""
        logger.info("启动自动更新检查服务...")

        def check_loop():
            while True:
                try:
                    release_info = self.check_for_updates()
                    if release_info:
                        if self.config.auto_update:
                            logger.info("自动下载并应用更新...")
                            self._perform_full_update(release_info)
                        else:
                            logger.info(f"发现新版本 {release_info.version}，等待用户确认")

                    # 等待下次检查
                    import time
                    time.sleep(self.config.check_interval)

                except Exception as e:
                    logger.error(f"自动更新检查失败: {e}")
                    import time
                    time.sleep(self.config.check_interval)

        import threading
        thread = threading.Thread(target=check_loop, daemon=True)
        thread.start()
        logger.info("自动更新检查服务已启动")

    def _perform_full_update(self, release_info: ReleaseInfo) -> bool:
        """执行完整更新流程"""
        try:
            # 下载更新
            update_file = self.download_update(release_info)
            if not update_file:
                return False

            # 应用更新
            success = self.apply_update(update_file)

            if success:
                logger.info("更新完成！系统将重启...")
                # 可以在这里添加重启逻辑
                # subprocess.Popen([sys.executable] + sys.argv)

            return success

        except Exception as e:
            logger.error(f"更新流程失败: {e}")
            return False

    def update(self, release_info: ReleaseInfo = None, auto: bool = None) -> bool:
        """手动触发更新"""
        if auto is not None:
            self.config.auto_update = auto

        if release_info is None:
            release_info = self.check_for_updates()
            if not release_info:
                logger.info("没有可用更新")
                return True

        return self._perform_full_update(release_info)


def main():
    """命令行接口"""
    import argparse

    parser = argparse.ArgumentParser(description='HKEX量化交易系统更新工具')
    parser.add_argument('--check', action='store_true', help='检查更新')
    parser.add_argument('--update', action='store_true', help='下载并应用更新')
    parser.add_argument('--auto', action='store_true', help='自动更新模式')
    parser.add_argument('--version', help='指定版本')
    parser.add_argument('--config', help='配置文件路径')

    args = parser.parse_args()

    # 加载配置
    config = UpdateConfig()
    if args.config and Path(args.config).exists():
        with open(args.config) as f:
            config_data = json.load(f)
            config = UpdateConfig(**config_data)

    updater = UpdateManager(config)

    if args.check:
        release_info = updater.check_for_updates()
        if release_info:
            print(f"发现新版本: {release_info.version}")
            print(f"发布说明: {release_info.description}")
            print(f"文件大小: {release_info.file_size / 1024 / 1024:.2f} MB")
        else:
            print("当前已是最新版本")

    elif args.update:
        success = updater.update()
        if success:
            print("更新成功！")
            sys.exit(0)
        else:
            print("更新失败！")
            sys.exit(1)

    elif args.auto:
        updater.config.auto_update = True
        updater.start_auto_update_check()
        import time
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("退出自动更新检查")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
