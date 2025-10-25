#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
持久终端管理器 - 修复Terminal not found错误
提供稳定的终端创建、等待和命令执行
"""

import time
import logging
from typing import Optional, Dict

logger = logging.getLogger("TERMINAL_MANAGER")

class PersistentTerminalManager:
    """改进的持久终端管理器"""

    def __init__(self):
        self.terminals: Dict[str, dict] = {}
        self.terminal_counter = 0
        logger.info("✅ 终端管理器已初始化")

    def create_terminal(self, cwd: str = ".", shell: str = "bash",
                       wait_time: float = 2.0, max_retries: int = 3) -> Optional[str]:
        """
        创建新终端并确保其完全就绪

        Args:
            cwd: 工作目录
            shell: shell类型
            wait_time: 创建后等待时间（秒）
            max_retries: 最大重试次数

        Returns:
            终端ID或None
        """
        from mcp__persistent_terminal__create_terminal_basic import create_terminal

        for attempt in range(max_retries):
            try:
                logger.info(f"尝试创建终端 (尝试 {attempt+1}/{max_retries})...")

                result = create_terminal(cwd=cwd, shell=shell)

                if result and "terminalId" in result:
                    terminal_id = result["terminalId"]

                    # 等待终端完全初始化
                    logger.info(f"等待终端初始化 ({wait_time}秒)...")
                    time.sleep(wait_time)

                    # 验证终端是否可用
                    if self._verify_terminal(terminal_id):
                        self.terminals[terminal_id] = {
                            "cwd": cwd,
                            "shell": shell,
                            "created_at": time.time(),
                            "last_used": time.time(),
                        }
                        logger.info(f"✅ 终端创建成功: {terminal_id}")
                        return terminal_id
                    else:
                        logger.warning(f"⚠️ 终端验证失败，重试...")
                        continue
                else:
                    logger.error(f"❌ 终端创建失败: {result}")

            except Exception as e:
                logger.error(f"❌ 创建终端异常 (尝试 {attempt+1}): {e}")
                time.sleep(1)

        logger.error(f"❌ 经过{max_retries}次尝试，无法创建终端")
        return None

    def _verify_terminal(self, terminal_id: str) -> bool:
        """
        验证终端是否可用

        Args:
            terminal_id: 终端ID

        Returns:
            终端是否可用
        """
        try:
            from mcp__persistent_terminal__read_terminal import read_terminal

            # 尝试读取终端
            result = read_terminal(terminalId=terminal_id)

            if result and "status" in result:
                status = result.get("status")
                logger.debug(f"终端 {terminal_id} 状态: {status}")
                return status == "active"

            return False

        except Exception as e:
            logger.debug(f"验证终端失败: {e}")
            return False

    def write_command(self, terminal_id: str, command: str,
                     max_retries: int = 3, wait_between_retries: float = 1.0) -> bool:
        """
        向终端写入命令，支持重试

        Args:
            terminal_id: 终端ID
            command: 要执行的命令
            max_retries: 最大重试次数
            wait_between_retries: 重试间隔（秒）

        Returns:
            命令是否写入成功
        """
        from mcp__persistent_terminal__write_terminal import write_terminal

        for attempt in range(max_retries):
            try:
                logger.info(f"写入命令到终端 (尝试 {attempt+1}/{max_retries}): {command[:50]}...")

                result = write_terminal(
                    terminalId=terminal_id,
                    input=command,
                    appendNewline=True
                )

                if result:
                    self.terminals[terminal_id]["last_used"] = time.time()
                    logger.info(f"✅ 命令写入成功")
                    return True

            except Exception as e:
                logger.warning(f"⚠️ 写入命令失败 (尝试 {attempt+1}): {e}")

                if attempt < max_retries - 1:
                    logger.info(f"等待 {wait_between_retries} 秒后重试...")
                    time.sleep(wait_between_retries)
                else:
                    logger.error(f"❌ 经过{max_retries}次尝试，命令写入失败")

        return False

    def read_output(self, terminal_id: str, max_retries: int = 3) -> Optional[str]:
        """
        从终端读取输出

        Args:
            terminal_id: 终端ID
            max_retries: 最大重试次数

        Returns:
            终端输出或None
        """
        from mcp__persistent_terminal__read_terminal import read_terminal

        for attempt in range(max_retries):
            try:
                logger.debug(f"读取终端输出 (尝试 {attempt+1}/{max_retries})...")

                result = read_terminal(terminalId=terminal_id)

                if result:
                    output = result.get("stdout", "")
                    self.terminals[terminal_id]["last_used"] = time.time()
                    return output

            except Exception as e:
                logger.warning(f"⚠️ 读取输出失败 (尝试 {attempt+1}): {e}")
                time.sleep(0.5)

        logger.error(f"❌ 无法读取终端输出")
        return None

    def list_terminals(self):
        """列出所有活跃终端"""
        logger.info(f"活跃终端数: {len(self.terminals)}")
        for terminal_id, info in self.terminals.items():
            uptime = time.time() - info["created_at"]
            logger.info(f"  - {terminal_id}: shell={info['shell']}, cwd={info['cwd']}, "
                       f"uptime={uptime:.1f}s")

    def cleanup_old_terminals(self, max_age_seconds: float = 3600):
        """清理超时的终端"""
        current_time = time.time()
        to_remove = []

        for terminal_id, info in self.terminals.items():
            age = current_time - info["last_used"]
            if age > max_age_seconds:
                logger.info(f"清理旧终端: {terminal_id} (age={age:.1f}s)")
                to_remove.append(terminal_id)

        for terminal_id in to_remove:
            del self.terminals[terminal_id]

        if to_remove:
            logger.info(f"✅ 已清理 {len(to_remove)} 个旧终端")


# 使用示例
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    manager = PersistentTerminalManager()

    # 创建终端
    terminal_id = manager.create_terminal(
        cwd="C:\\Users\\Penguin8n\\CODEX--\\CODEX--",
        shell="powershell"
    )

    if terminal_id:
        print(f"✅ 终端创建成功: {terminal_id}")

        # 执行命令
        manager.write_command(terminal_id, "python test_verification_system.py")

        # 读取输出
        time.sleep(5)
        output = manager.read_output(terminal_id)
        if output:
            print(f"✅ 获得输出:\n{output[:500]}")

        # 列出终端
        manager.list_terminals()
    else:
        print("❌ 终端创建失败")
