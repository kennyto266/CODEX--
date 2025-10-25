#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
改进的持久终端MCP包装器
提供自动重试、验证和错误恢复功能
解决 "Terminal not found" 问题
"""

import time
import logging
from typing import Optional, Dict, Any
from enum import Enum

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TERMINAL_MCP_WRAPPER")


class TerminalState(Enum):
    """终端状态枚举"""
    CREATED = "created"
    ACTIVE = "active"
    IDLE = "idle"
    ERROR = "error"
    DEAD = "dead"


class ImprovedTerminalMCP:
    """改进的终端MCP包装器"""

    def __init__(self, max_retries: int = 3, wait_time: float = 1.0):
        """
        初始化终端包装器

        Args:
            max_retries: 最大重试次数
            wait_time: 重试等待时间（秒）
        """
        self.max_retries = max_retries
        self.wait_time = wait_time
        self.terminals: Dict[str, Dict[str, Any]] = {}
        self.operation_history: list = []
        logger.info("✅ 改进的终端MCP包装器已初始化")

    def create_terminal(self, cwd: str = ".", shell: str = "bash") -> Optional[str]:
        """
        创建新终端（带重试）

        Args:
            cwd: 工作目录
            shell: Shell类型

        Returns:
            终端ID或None
        """
        from mcp__persistent_terminal__create_terminal_basic import mcp__persistent_terminal__create_terminal_basic

        logger.info(f"开始创建终端: cwd={cwd}, shell={shell}")

        for attempt in range(self.max_retries):
            try:
                logger.info(f"  尝试 {attempt + 1}/{self.max_retries}...")

                # 调用MCP函数
                result = mcp__persistent_terminal__create_terminal_basic(cwd=cwd, shell=shell)

                if result and "terminalId" in result:
                    terminal_id = result["terminalId"]

                    # 记录终端信息
                    self.terminals[terminal_id] = {
                        "state": TerminalState.CREATED,
                        "cwd": cwd,
                        "shell": shell,
                        "created_at": time.time(),
                        "last_used": time.time(),
                        "operation_count": 0,
                        "error_count": 0,
                    }

                    logger.info(f"✅ 终端创建成功: {terminal_id}")
                    self._log_operation("CREATE", terminal_id, True)
                    return terminal_id

                else:
                    logger.warning(f"⚠️  尝试 {attempt + 1} 失败: 无效响应 {result}")

            except Exception as e:
                logger.warning(f"⚠️  尝试 {attempt + 1} 异常: {e}")

            # 等待后重试
            if attempt < self.max_retries - 1:
                logger.info(f"  等待 {self.wait_time}秒后重试...")
                time.sleep(self.wait_time)

        logger.error(f"❌ 经过{self.max_retries}次尝试，无法创建终端")
        self._log_operation("CREATE", "unknown", False)
        return None

    def write_to_terminal(self, terminal_id: str, command: str) -> bool:
        """
        向终端写入命令（带重试和验证）

        Args:
            terminal_id: 终端ID
            command: 命令

        Returns:
            成功与否
        """
        from mcp__persistent_terminal__write_terminal import mcp__persistent_terminal__write_terminal

        if terminal_id not in self.terminals:
            logger.error(f"❌ 终端不存在: {terminal_id}")
            return False

        logger.info(f"向终端写入命令: {terminal_id}")
        logger.info(f"  命令: {command[:60]}...")

        for attempt in range(self.max_retries):
            try:
                # 调用MCP函数
                result = mcp__persistent_terminal__write_terminal(
                    terminalId=terminal_id,
                    input=command,
                    appendNewline=True
                )

                if result:
                    # 更新终端状态
                    self.terminals[terminal_id]["last_used"] = time.time()
                    self.terminals[terminal_id]["operation_count"] += 1
                    self.terminals[terminal_id]["state"] = TerminalState.ACTIVE

                    logger.info(f"✅ 命令写入成功")
                    self._log_operation("WRITE", terminal_id, True)
                    return True

                else:
                    logger.warning(f"⚠️  尝试 {attempt + 1} 失败: write返回False")

            except Exception as e:
                error_str = str(e).lower()

                # 检测"Terminal not found"错误
                if "terminal" in error_str and "not found" in error_str:
                    logger.warning(f"⚠️  检测到 Terminal not found 错误 (尝试 {attempt + 1})")
                    self.terminals[terminal_id]["error_count"] += 1

                    # 如果不是最后一次尝试，等待并重试
                    if attempt < self.max_retries - 1:
                        wait = self.wait_time * (2 ** attempt)  # 指数退避
                        logger.info(f"  等待 {wait}秒后重试...")
                        time.sleep(wait)
                        continue

                logger.warning(f"⚠️  尝试 {attempt + 1} 异常: {e}")

        logger.error(f"❌ 经过{self.max_retries}次尝试，无法写入命令")
        self.terminals[terminal_id]["state"] = TerminalState.ERROR
        self._log_operation("WRITE", terminal_id, False)
        return False

    def read_from_terminal(self, terminal_id: str, max_retries: int = 3) -> Optional[str]:
        """
        从终端读取输出（带重试）

        Args:
            terminal_id: 终端ID
            max_retries: 最大重试次数

        Returns:
            输出文本或None
        """
        from mcp__persistent_terminal__read_terminal import mcp__persistent_terminal__read_terminal

        if terminal_id not in self.terminals:
            logger.error(f"❌ 终端不存在: {terminal_id}")
            return None

        logger.info(f"从终端读取输出: {terminal_id}")

        for attempt in range(max_retries):
            try:
                # 调用MCP函数
                result = mcp__persistent_terminal__read_terminal(terminalId=terminal_id)

                if result:
                    output = result.get("stdout", "") or result.get("output", "")

                    # 更新终端状态
                    self.terminals[terminal_id]["last_used"] = time.time()
                    self.terminals[terminal_id]["state"] = TerminalState.IDLE

                    logger.info(f"✅ 成功读取 {len(output)} 字符")
                    self._log_operation("READ", terminal_id, True)
                    return output

                else:
                    logger.warning(f"⚠️  尝试 {attempt + 1} 失败: read返回False")

            except Exception as e:
                logger.warning(f"⚠️  尝试 {attempt + 1} 异常: {e}")

            if attempt < max_retries - 1:
                time.sleep(self.wait_time)

        logger.error(f"❌ 经过{max_retries}次尝试，无法读取输出")
        self._log_operation("READ", terminal_id, False)
        return None

    def execute_command_safe(self, terminal_id: str, command: str, wait_for_output: float = 2.0) -> Optional[str]:
        """
        安全执行命令：写入 + 等待 + 读取

        Args:
            terminal_id: 终端ID
            command: 命令
            wait_for_output: 等待输出的时间（秒）

        Returns:
            命令输出或None
        """
        logger.info(f"安全执行命令: {command[:50]}...")

        # 第1步: 写入命令
        if not self.write_to_terminal(terminal_id, command):
            logger.error("❌ 写入命令失败")
            return None

        # 第2步: 等待处理
        logger.info(f"  等待 {wait_for_output}秒处理命令...")
        time.sleep(wait_for_output)

        # 第3步: 读取输出
        output = self.read_from_terminal(terminal_id)

        if output:
            logger.info(f"✅ 命令执行完成，获得 {len(output)} 字符输出")
        else:
            logger.warning("⚠️  命令执行成功但无法读取输出")

        return output

    def list_terminals(self) -> Dict[str, Dict[str, Any]]:
        """列出所有终端"""
        logger.info(f"活跃终端数: {len(self.terminals)}")

        for term_id, info in self.terminals.items():
            uptime = time.time() - info["created_at"]
            logger.info(f"  - {term_id}:")
            logger.info(f"    • 状态: {info['state'].value}")
            logger.info(f"    • Shell: {info['shell']}")
            logger.info(f"    • CWD: {info['cwd']}")
            logger.info(f"    • 正常运行时间: {uptime:.1f}s")
            logger.info(f"    • 操作数: {info['operation_count']}")
            logger.info(f"    • 错误数: {info['error_count']}")

        return self.terminals

    def _log_operation(self, op_type: str, terminal_id: str, success: bool):
        """记录操作历史"""
        self.operation_history.append({
            "timestamp": time.time(),
            "type": op_type,
            "terminal_id": terminal_id,
            "success": success,
        })

    def get_operation_stats(self) -> Dict[str, Any]:
        """获取操作统计"""
        total = len(self.operation_history)
        success = sum(1 for op in self.operation_history if op["success"])
        failed = total - success

        return {
            "total_operations": total,
            "successful": success,
            "failed": failed,
            "success_rate": (success / total * 100) if total > 0 else 0,
            "terminals_created": len(self.terminals),
        }

    def print_stats(self):
        """打印统计信息"""
        stats = self.get_operation_stats()

        logger.info("\n" + "=" * 60)
        logger.info("📊 终端MCP操作统计")
        logger.info("=" * 60)
        logger.info(f"总操作数: {stats['total_operations']}")
        logger.info(f"成功: {stats['successful']}")
        logger.info(f"失败: {stats['failed']}")
        logger.info(f"成功率: {stats['success_rate']:.1f}%")
        logger.info(f"已创建终端: {stats['terminals_created']}")
        logger.info("=" * 60 + "\n")


# 使用示例
if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🧪 改进的终端MCP包装器测试")
    print("=" * 70)

    # 创建包装器实例
    wrapper = ImprovedTerminalMCP(max_retries=3, wait_time=1.0)

    # 创建终端
    print("\n📝 Step 1: 创建终端")
    print("-" * 70)
    terminal_id = wrapper.create_terminal(
        cwd="C:\\Users\\Penguin8n\\CODEX--\\CODEX--",
        shell="powershell"
    )

    if terminal_id:
        print(f"✅ 终端创建成功: {terminal_id}\n")

        # 执行命令 1: 显示目录
        print("📝 Step 2: 执行命令 (获取目录)")
        print("-" * 70)
        output = wrapper.execute_command_safe(terminal_id, "dir", wait_for_output=1.5)
        if output:
            print(f"✅ 获得输出 (前200字符):")
            print(output[:200])

        # 执行命令 2: Python版本
        print("\n📝 Step 3: 执行命令 (Python版本)")
        print("-" * 70)
        output = wrapper.execute_command_safe(terminal_id, "python --version", wait_for_output=1.0)
        if output:
            print(f"✅ 获得输出: {output.strip()}")

        # 列出终端
        print("\n📝 Step 4: 列出所有终端")
        print("-" * 70)
        wrapper.list_terminals()

        # 打印统计
        print("\n")
        wrapper.print_stats()

    else:
        print("❌ 终端创建失败")
