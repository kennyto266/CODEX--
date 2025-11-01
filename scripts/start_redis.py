#!/usr/bin/env python3
"""
Redis自动启动脚本
用于在系统启动时自动启动Redis服务器
"""

import subprocess
import sys
import time
import logging
import os
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_redis_running():
    """检查Redis是否已经在运行"""
    try:
        result = subprocess.run(
            ['redis-cli', 'ping'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip() == 'PONG':
            logger.info("Redis is already running")
            return True
    except FileNotFoundError:
        logger.warning("redis-cli not found in PATH")
    except subprocess.TimeoutExpired:
        logger.warning("Redis ping timeout")
    except Exception as e:
        logger.warning(f"Redis check error: {e}")

    return False


def start_redis_server():
    """启动Redis服务器"""
    try:
        logger.info("Starting Redis server...")

        # 尝试使用redis-server.exe (Windows)
        redis_cmd = 'redis-server.exe'

        # 启动Redis服务器（后台运行）
        process = subprocess.Popen(
            [redis_cmd],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
        )

        logger.info(f"Redis process started with PID: {process.pid}")
        return process

    except FileNotFoundError:
        logger.error(f"Redis command not found: {redis_cmd}")
        logger.error("Please ensure Redis is installed and in PATH")
        return None
    except Exception as e:
        logger.error(f"Failed to start Redis: {e}")
        return None


def wait_for_redis(max_wait=30):
    """等待Redis启动完成"""
    logger.info("Waiting for Redis to be ready...")

    for i in range(max_wait):
        try:
            result = subprocess.run(
                ['redis-cli', 'ping'],
                capture_output=True,
                text=True,
                timeout=3
            )

            if result.returncode == 0 and result.stdout.strip() == 'PONG':
                logger.info(f"Redis is ready! (took {i+1} seconds)")
                return True

        except Exception:
            pass

        time.sleep(1)

    logger.error(f"Redis did not become ready within {max_wait} seconds")
    return False


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("Redis Auto-Start Script")
    logger.info("=" * 60)

    # 检查Redis是否已经在运行
    if check_redis_running():
        logger.info("✅ Redis is already running - no action needed")
        return 0

    # 启动Redis服务器
    redis_process = start_redis_server()
    if not redis_process:
        logger.error("❌ Failed to start Redis server")
        return 1

    # 等待Redis启动
    if not wait_for_redis():
        logger.error("❌ Redis startup timeout")
        return 1

    logger.info("=" * 60)
    logger.info("✅ Redis auto-start completed successfully!")
    logger.info("=" * 60)

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
