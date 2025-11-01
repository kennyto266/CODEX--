#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志轮转和归档系统
支持自动轮转、压缩、归档和清理功能
"""

import os
import sys
import time
import gzip
import shutil
import logging
import logging.handlers
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict
import threading
from dataclasses import dataclass

@dataclass
class LogRotationConfig:
    """日志轮转配置"""
    max_size: int = 100 * 1024 * 1024  # 100MB
    backup_count: int = 10
    compression: bool = True
    archive_after_days: int = 30
    delete_after_days: int = 365
    archive_dir: str = "logs/archive"
    compress_format: str = "gzip"  # gzip, bzip2
    utc_timestamp: bool = True

class AdvancedRotatingFileHandler(logging.handlers.BaseRotatingHandler):
    """高级轮转文件处理器"""

    def __init__(self, filename: str, mode: str = 'a', encoding: str = None,
                 delay: bool = False, errors: str = None,
                 config: Optional[LogRotationConfig] = None):
        self.config = config or LogRotationConfig()
        self.archive_lock = threading.Lock()

        super().__init__(filename, mode, encoding, delay, errors)

    def shouldRollover(self, record):
        """判断是否需要轮转"""
        if self.stream is None:
            self.stream = self._open()

        if self.config.max_size > 0 and os.path.exists(self.baseFilename):
            file_size = os.path.getsize(self.baseFilename)
            if file_size >= self.config.max_size:
                return 1

        return 0

    def doRollover(self):
        """执行轮转"""
        if self.stream:
            self.stream.close()
            self.stream = None

        # 创建时间戳
        if self.config.utc_timestamp:
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 生成备份文件名
        dfn = self.rotation_filename(f"{self.baseFilename}.{timestamp}")
        self.rotate(self.baseFilename, dfn)

    def rotation_filename(self, default_name):
        """生成轮转文件名"""
        return default_name

    def rotate(self, source, dest):
        """轮转日志文件"""
        with self.archive_lock:
            try:
                # 移动文件
                if os.path.exists(source):
                    shutil.move(source, dest)
                    print(f"📁 日志轮转: {source} -> {dest}")

                # 压缩（如果启用）
                if self.config.compression:
                    compressed_path = self._compress_file(dest)
                    if compressed_path:
                        os.remove(dest)  # 删除未压缩的文件
                        dest = compressed_path
                        print(f"🗜️  压缩日志: {dest}")

                # 移动到归档目录
                if self.config.archive_dir:
                    archive_path = self._archive_file(dest)
                    if archive_path:
                        os.remove(dest)  # 删除原文件
                        print(f"📦 归档日志: {archive_path}")

            except Exception as e:
                print(f"❌ 日志轮转失败: {e}")
                raise

    def _compress_file(self, filepath: str) -> Optional[str]:
        """压缩文件"""
        try:
            compressed_path = f"{filepath}.gz"

            with open(filepath, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

            print(f"✅ 文件压缩成功: {compressed_path}")
            return compressed_path

        except Exception as e:
            print(f"❌ 文件压缩失败: {e}")
            return None

    def _archive_file(self, filepath: str) -> Optional[str]:
        """移动文件到归档目录"""
        try:
            os.makedirs(self.config.archive_dir, exist_ok=True)

            filename = os.path.basename(filepath)
            timestamp = datetime.now().strftime('%Y%m%d')
            archive_filename = f"{timestamp}_{filename}"
            archive_path = os.path.join(self.config.archive_dir, archive_filename)

            # 处理文件名冲突
            counter = 1
            while os.path.exists(archive_path):
                base, ext = os.path.splitext(archive_filename)
                archive_filename = f"{base}_{counter}{ext}"
                archive_path = os.path.join(self.config.archive_dir, archive_filename)
                counter += 1

            shutil.move(filepath, archive_path)
            print(f"✅ 文件归档成功: {archive_path}")
            return archive_path

        except Exception as e:
            print(f"❌ 文件归档失败: {e}")
            return None

class LogArchiver:
    """日志归档器"""

    def __init__(self, config: LogRotationConfig):
        self.config = config
        self.archive_thread = None
        self.running = False

    def start_background_archive(self):
        """启动后台归档任务"""
        if self.running:
            return

        self.running = True
        self.archive_thread = threading.Thread(target=self._archive_worker, daemon=True)
        self.archive_thread.start()
        print("🗂️  日志归档任务已启动")

    def stop_background_archive(self):
        """停止后台归档任务"""
        self.running = False
        if self.archive_thread:
            self.archive_thread.join()
        print("🛑 日志归档任务已停止")

    def _archive_worker(self):
        """归档工作线程"""
        while self.running:
            try:
                self._archive_old_files()
                time.sleep(3600)  # 每小时检查一次
            except Exception as e:
                print(f"❌ 归档任务异常: {e}")
                time.sleep(300)  # 出错后等待5分钟再试

    def _archive_old_files(self):
        """归档旧文件"""
        if not self.config.archive_dir:
            return

        log_dir = Path(self.config.archive_dir).parent
        archive_dir = Path(self.config.archive_dir)

        # 扫描需要归档的文件
        cutoff_date = datetime.now() - timedelta(days=self.config.archive_after_days)

        for log_file in log_dir.glob("*.log*"):
            if log_file.name.endswith(('.gz', '.bz2')):  # 已压缩
                continue

            file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
            if file_time < cutoff_date:
                self._archive_single_file(log_file)

        # 清理过期文件
        self._cleanup_old_archives()

    def _archive_single_file(self, filepath: Path):
        """归档单个文件"""
        try:
            # 压缩文件
            if self.config.compression:
                compressed_path = self._compress_file(filepath)
                if compressed_path:
                    os.remove(filepath)
                    filepath = Path(compressed_path)

            # 移动到归档目录
            os.makedirs(self.config.archive_dir, exist_ok=True)
            archive_path = archive_dir / filepath.name

            counter = 1
            while archive_path.exists():
                base = filepath.stem
                ext = filepath.suffix
                archive_path = archive_dir / f"{base}_{counter}{ext}"
                counter += 1

            shutil.move(str(filepath), str(archive_path))
            print(f"📦 已归档: {archive_path}")

        except Exception as e:
            print(f"❌ 归档文件失败 {filepath}: {e}")

    def _compress_file(self, filepath: Path) -> Optional[str]:
        """压缩文件"""
        try:
            compressed_path = f"{filepath}.gz"

            with open(filepath, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

            return compressed_path

        except Exception as e:
            print(f"❌ 压缩文件失败 {filepath}: {e}")
            return None

    def _cleanup_old_archives(self):
        """清理过期归档文件"""
        try:
            archive_dir = Path(self.config.archive_dir)
            if not archive_dir.exists():
                return

            cutoff_date = datetime.now() - timedelta(days=self.config.delete_after_days)

            for archive_file in archive_dir.glob("*"):
                if archive_file.is_file():
                    file_time = datetime.fromtimestamp(archive_file.stat().st_mtime)
                    if file_time < cutoff_date:
                        archive_file.unlink()
                        print(f"🗑️  已删除过期归档: {archive_file}")

        except Exception as e:
            print(f"❌ 清理归档失败: {e}")

class LogRotationManager:
    """日志轮转管理器"""

    def __init__(self, config: Optional[LogRotationConfig] = None):
        self.config = config or LogRotationConfig()
        self.handlers: Dict[str, AdvancedRotatingFileHandler] = {}
        self.archiver = LogArchiver(self.config)
        self.logger = logging.getLogger(__name__)

    def setup_logger(self, name: str, log_file: str, level: int = logging.INFO,
                    formatter: Optional[logging.Formatter] = None) -> logging.Logger:
        """设置日志记录器"""

        # 创建日志目录
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        # 创建轮转处理器
        handler = AdvancedRotatingFileHandler(
            log_file,
            config=self.config
        )

        # 设置格式器
        if formatter is None:
            formatter = logging.Formatter(
                fmt='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )

        handler.setFormatter(formatter)
        handler.setLevel(level)

        # 创建或获取记录器
        logger = logging.getLogger(name)
        logger.setLevel(level)
        logger.addHandler(handler)

        # 避免重复添加处理器
        for existing_handler in logger.handlers[:]:
            if isinstance(existing_handler, AdvancedRotatingFileHandler):
                logger.removeHandler(existing_handler)

        logger.addHandler(handler)

        # 保存处理器引用
        self.handlers[name] = handler

        return logger

    def get_structured_logger(self, name: str, log_file: str) -> logging.Logger:
        """获取结构化日志记录器"""
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        return self.setup_logger(name, log_file, formatter=formatter)

    def start_archiving(self):
        """启动归档功能"""
        self.archiver.start_background_archive()

    def stop_archiving(self):
        """停止归档功能"""
        self.archiver.stop_background_archive()

    def get_log_stats(self) -> Dict:
        """获取日志统计信息"""
        stats = {
            'active_handlers': len(self.handlers),
            'log_files': [],
            'archive_files': [],
            'total_size': 0
        }

        # 统计活动处理器
        for name, handler in self.handlers.items():
            if hasattr(handler, 'baseFilename'):
                log_file = handler.baseFilename
                file_size = os.path.getsize(log_file) if os.path.exists(log_file) else 0
                stats['log_files'].append({
                    'handler': name,
                    'file': log_file,
                    'size': file_size
                })
                stats['total_size'] += file_size

        # 统计归档文件
        if os.path.exists(self.config.archive_dir):
            for archive_file in Path(self.config.archive_dir).glob("*"):
                if archive_file.is_file():
                    file_size = archive_file.stat().st_size
                    stats['archive_files'].append({
                        'file': str(archive_file),
                        'size': file_size
                    })
                    stats['total_size'] += file_size

        return stats

    def cleanup_all(self):
        """清理所有日志资源"""
        self.stop_archiving()

        for name, handler in self.handlers.items():
            try:
                handler.close()
                print(f"✅ 已关闭日志处理器: {name}")
            except Exception as e:
                print(f"❌ 关闭日志处理器失败 {name}: {e}")

        self.handlers.clear()

def create_app_logger(name: str, log_dir: str = "logs",
                     config: Optional[LogRotationConfig] = None) -> logging.Logger:
    """创建应用程序日志记录器"""

    if config is None:
        config = LogRotationConfig(
            max_size=50 * 1024 * 1024,  # 50MB
            backup_count=5,
            compression=True,
            archive_after_days=7,
            delete_after_days=90,
            archive_dir=os.path.join(log_dir, "archive")
        )

    manager = LogRotationManager(config)
    log_file = os.path.join(log_dir, "app.log")

    # 启动归档
    manager.start_archiving()

    logger = manager.get_structured_logger(name, log_file)

    # 添加应用信息
    logger.info(f"🚀 日志系统初始化完成")
    logger.info(f"📁 日志目录: {log_dir}")
    logger.info(f"📦 归档目录: {config.archive_dir}")

    return logger

def create_trading_logger(name: str = "trading", log_dir: str = "logs") -> logging.Logger:
    """创建交易专用日志记录器"""

    config = LogRotationConfig(
        max_size=100 * 1024 * 1024,  # 100MB - 交易日志可能较大
        backup_count=20,  # 保留更多备份
        compression=True,
        archive_after_days=3,  # 更频繁归档
        delete_after_days=180,  # 保留更长时间
        archive_dir=os.path.join(log_dir, "trading_archive")
    )

    manager = LogRotationManager(config)
    log_file = os.path.join(log_dir, "trading.log")

    manager.start_archiving()
    logger = manager.get_structured_logger(name, log_file)

    logger.info(f"📊 交易日志系统初始化完成")

    return logger

def create_access_logger(name: str = "access", log_dir: str = "logs") -> logging.Logger:
    """创建访问日志记录器"""

    config = LogRotationConfig(
        max_size=200 * 1024 * 1024,  # 200MB - 访问日志最大
        backup_count=30,
        compression=True,
        archive_after_days=2,
        delete_after_days=365,
        archive_dir=os.path.join(log_dir, "access_archive")
    )

    manager = LogRotationManager(config)
    log_file = os.path.join(log_dir, "access.log")

    manager.start_archiving()
    logger = manager.get_structured_logger(name, log_file)

    logger.info(f"🌐 访问日志系统初始化完成")

    return logger

# 全局日志管理器实例
_log_manager: Optional[LogRotationManager] = None

def get_global_logger() -> LogRotationManager:
    """获取全局日志管理器"""
    global _log_manager
    if _log_manager is None:
        _log_manager = LogRotationManager()
    return _log_manager

def setup_production_logging():
    """设置生产环境日志"""
    config = LogRotationConfig(
        max_size=200 * 1024 * 1024,  # 200MB
        backup_count=50,
        compression=True,
        archive_after_days=1,
        delete_after_days=365,
        archive_dir="logs/archive",
        utc_timestamp=True
    )

    manager = LogRotationManager(config)
    manager.start_archiving()

    # 设置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # 控制台处理器（开发环境）
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_formatter = logging.Formatter(
        fmt='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # 文件处理器（所有日志）
    log_file = "logs/app.log"
    app_handler = AdvancedRotatingFileHandler(log_file, config=config)
    app_handler.setLevel(logging.INFO)
    app_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    app_handler.setFormatter(app_formatter)
    root_logger.addHandler(app_handler)

    print("📋 生产环境日志系统已初始化")
    return manager

if __name__ == "__main__":
    # 测试日志轮转系统
    print("🧪 测试日志轮转系统...")

    logger = create_app_logger("test", "logs")
    logger.info("测试信息")
    logger.warning("测试警告")
    logger.error("测试错误")

    # 模拟日志增长
    for i in range(1000):
        logger.info(f"测试日志条目 {i}: " + "x" * 100)

    time.sleep(2)

    # 显示统计信息
    manager = get_global_logger()
    stats = manager.get_log_stats()
    print(f"\n📊 日志统计:")
    print(f"  活跃处理器: {stats['active_handlers']}")
    print(f"  总大小: {stats['total_size'] / 1024 / 1024:.2f} MB")
    print(f"  日志文件数: {len(stats['log_files'])}")
    print(f"  归档文件数: {len(stats['archive_files'])}")

    # 清理
    manager.cleanup_all()
    print("\n✅ 日志轮转系统测试完成")
