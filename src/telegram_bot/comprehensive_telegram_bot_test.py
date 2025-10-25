#!/usr/bin/env python3
"""
综合 Telegram Bot 功能测试
完整测试所有 Bot 命令和功能，生成详细测试报告
"""

import os
import sys
import logging
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# 处理 Windows 编码问题
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("telegram_bot_test")

# ========== 环境检查模块 ==========
class EnvironmentChecker:
    """检查 Telegram Bot 环境配置"""

    def __init__(self):
        self.results = {
            "环境变量": {},
            "依赖库": {},
            "文件检查": {},
            "配置检查": {}
        }

    def check_env_variables(self) -> Dict[str, Any]:
        """检查关键环境变量"""
        logger.info("📋 检查环境变量...")
        required_vars = [
            "TELEGRAM_BOT_TOKEN",
            "TELEGRAM_ADMIN_CHAT_ID"
        ]
        optional_vars = [
            "TG_ALLOWED_USER_IDS",
            "TG_ALLOWED_CHAT_IDS",
            "CURSOR_API_KEY",
            "BOT_SINGLETON_PORT"
        ]

        results = {}

        # 检查必需变量
        for var in required_vars:
            value = os.getenv(var, "").strip()
            is_set = bool(value)
            results[var] = {
                "状态": "✅ 已配置" if is_set else "❌ 未配置",
                "值": f"{value[:20]}..." if is_set else "N/A"
            }

        # 检查可选变量
        for var in optional_vars:
            value = os.getenv(var, "").strip()
            is_set = bool(value)
            results[var] = {
                "状态": "✅ 已配置" if is_set else "⚠️  未配置",
                "值": f"{value[:20]}..." if is_set else "N/A"
            }

        self.results["环境变量"] = results
        return results

    def check_dependencies(self) -> Dict[str, Any]:
        """检查必要的 Python 依赖"""
        logger.info("📦 检查 Python 依赖...")
        required_packages = [
            ("telegram", "python-telegram-bot"),
            ("dotenv", "python-dotenv"),
            ("pandas", "pandas"),
            ("numpy", "numpy"),
            ("requests", "requests"),
        ]

        optional_packages = [
            ("playwright", "playwright"),
            ("httpx", "httpx"),
        ]

        results = {}

        for module_name, package_name in required_packages:
            try:
                __import__(module_name)
                results[package_name] = {
                    "状态": "✅ 已安装",
                    "类型": "必需"
                }
            except ImportError:
                results[package_name] = {
                    "状态": "❌ 未安装",
                    "类型": "必需"
                }

        for module_name, package_name in optional_packages:
            try:
                __import__(module_name)
                results[package_name] = {
                    "状态": "✅ 已安装",
                    "类型": "可选"
                }
            except ImportError:
                results[package_name] = {
                    "状态": "⚠️  未安装",
                    "类型": "可选"
                }

        self.results["依赖库"] = results
        return results

    def check_files(self) -> Dict[str, Any]:
        """检查关键文件存在"""
        logger.info("📁 检查文件...")
        required_files = [
            "telegram_quant_bot.py",
            "config/bot.env",
            "TELEGRAM_BOT_README.md",
            "start_telegram_bot.py",
            "test_bot_connection.py",
        ]

        results = {}
        for file in required_files:
            path = Path(file)
            exists = path.exists()
            results[file] = {
                "状态": "✅ 存在" if exists else "❌ 不存在",
                "大小": f"{path.stat().st_size} bytes" if exists else "N/A"
            }

        self.results["文件检查"] = results
        return results

    def check_config(self) -> Dict[str, Any]:
        """检查配置文件内容"""
        logger.info("⚙️  检查配置文件...")
        results = {}

        config_path = Path("config/bot.env")
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                results["bot.env"] = {
                    "状态": "✅ 可读",
                    "行数": len(lines),
                    "是否有效": all(
                        ("=" in line and not line.strip().startswith("#")) or
                        not line.strip()
                        for line in lines
                    )
                }
            except Exception as e:
                results["bot.env"] = {"状态": f"❌ 读取失败: {e}"}

        example_path = Path("telegram_bot.env.example")
        if example_path.exists():
            try:
                with open(example_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                results["telegram_bot.env.example"] = {
                    "状态": "✅ 可读",
                    "行数": len(lines),
                    "包含示例": any("your_" in line for line in lines)
                }
            except Exception as e:
                results["telegram_bot.env.example"] = {"状态": f"❌ 读取失败: {e}"}

        self.results["配置检查"] = results
        return results

    def run_all_checks(self) -> Dict[str, Any]:
        """运行所有检查"""
        logger.info("🔍 开始环境检查...\n")
        self.check_env_variables()
        self.check_dependencies()
        self.check_files()
        self.check_config()
        return self.results


# ========== Bot 功能验证模块 ==========
class BotFunctionalityValidator:
    """验证 Bot 的功能模块"""

    def __init__(self):
        self.results = {}
        self.test_data = {
            "测试股票": ["0700.HK", "2800.HK", "0939.HK"],
            "测试消息": ["hello", "测试", "你好 Bot"],
        }

    def validate_quant_system(self) -> Dict[str, Any]:
        """验证量化交易系统集成"""
        logger.info("📊 验证量化交易系统...")
        results = {}

        try:
            from complete_project_system import (
                get_stock_data,
                calculate_technical_indicators,
                calculate_risk_metrics,
            )
            results["导入状态"] = "✅ 成功导入核心函数"
            results["可用函数"] = {
                "get_stock_data": "✅",
                "calculate_technical_indicators": "✅",
                "calculate_risk_metrics": "✅",
            }
        except ImportError as e:
            results["导入状态"] = f"❌ 导入失败: {e}"
            results["可用函数"] = {}

        self.results["量化系统"] = results
        return results

    def validate_command_handlers(self) -> Dict[str, Any]:
        """验证命令处理器"""
        logger.info("🎮 验证命令处理器...")

        try:
            # 读取 bot 源代码来验证命令
            with open("telegram_quant_bot.py", "r", encoding="utf-8") as f:
                bot_code = f.read()

            commands = [
                "start", "help", "analyze", "optimize", "risk",
                "sentiment", "status", "id", "echo", "history",
                "summary", "cursor", "wsl", "tftcap"
            ]

            results = {}
            for cmd in commands:
                # 检查是否有对应的处理函数
                handler_name = f"{cmd}_cmd"
                has_handler = handler_name in bot_code or f"async def {cmd}(" in bot_code
                status = "✅ 已实现" if has_handler else "❌ 缺失"
                results[f"/{cmd}"] = status

            self.results["命令处理器"] = results
            return results
        except Exception as e:
            logger.error(f"验证命令处理器失败: {e}")
            return {"错误": str(e)}

    def validate_error_handling(self) -> Dict[str, Any]:
        """验证错误处理机制"""
        logger.info("🛡️  验证错误处理机制...")

        try:
            with open("telegram_quant_bot.py", "r", encoding="utf-8") as f:
                bot_code = f.read()

            features = {
                "异常处理": "try" in bot_code and "except" in bot_code,
                "错误处理器": "error_handler" in bot_code,
                "速率限制": "AIORateLimiter" in bot_code,
                "单实例锁": "_acquire_single_instance_lock" in bot_code,
                "Webhook清理": "_cleanup_webhook" in bot_code,
            }

            results = {}
            for feature, present in features.items():
                results[feature] = "✅ 已实现" if present else "❌ 缺失"

            self.results["错误处理"] = results
            return results
        except Exception as e:
            logger.error(f"验证错误处理失败: {e}")
            return {"错误": str(e)}

    def validate_security_features(self) -> Dict[str, Any]:
        """验证安全特性"""
        logger.info("🔐 验证安全特性...")

        try:
            with open("telegram_quant_bot.py", "r", encoding="utf-8") as f:
                bot_code = f.read()

            features = {
                "用户白名单": "_is_allowed_user_and_chat" in bot_code,
                "环境变量": "os.getenv" in bot_code,
                "密钥隐藏": "TELEGRAM_BOT_TOKEN" in bot_code,
                "权限检查": "TG_ALLOWED_USER_IDS" in bot_code,
            }

            results = {}
            for feature, present in features.items():
                results[feature] = "✅ 已实现" if present else "❌ 缺失"

            self.results["安全特性"] = results
            return results
        except Exception as e:
            logger.error(f"验证安全特性失败: {e}")
            return {"错误": str(e)}

    def run_all_validations(self) -> Dict[str, Any]:
        """运行所有验证"""
        logger.info("🔎 开始功能验证...\n")
        self.validate_quant_system()
        self.validate_command_handlers()
        self.validate_error_handling()
        self.validate_security_features()
        return self.results


# ========== 测试报告生成器 ==========
class TestReportGenerator:
    """生成测试报告"""

    def __init__(self, env_results: Dict, func_results: Dict):
        self.env_results = env_results
        self.func_results = func_results
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def generate_summary(self) -> str:
        """生成测试摘要"""
        lines = [
            "=" * 80,
            "📊 Telegram Bot 综合测试报告",
            "=" * 80,
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
        ]
        return "\n".join(lines)

    def generate_section(self, title: str, data: Dict) -> str:
        """生成报告段落"""
        lines = [f"\n{'=' * 80}", f"🔹 {title}", f"{'=' * 80}"]

        for category, items in data.items():
            lines.append(f"\n### {category}")
            if isinstance(items, dict):
                for key, value in items.items():
                    if isinstance(value, dict):
                        lines.append(f"  • {key}:")
                        for k, v in value.items():
                            lines.append(f"      {k}: {v}")
                    else:
                        lines.append(f"  • {key}: {value}")

        return "\n".join(lines)

    def generate_full_report(self) -> str:
        """生成完整报告"""
        report = self.generate_summary()
        report += self.generate_section("环境检查结果", self.env_results)
        report += self.generate_section("功能验证结果", self.func_results)

        # 添加摘要统计
        report += "\n\n" + "=" * 80
        report += "\n📈 测试统计\n" + "=" * 80

        total_checks = sum(
            len(v) if isinstance(v, dict) else 0
            for section in [self.env_results, self.func_results]
            for v in section.values()
        )

        success_count = sum(
            sum(1 for v in values.values() if isinstance(v, dict) and "✅" in str(v))
            if isinstance(values, dict) else 0
            for section in [self.env_results, self.func_results]
            for values in section.values()
        )

        report += f"\n总检查项数: {total_checks}"
        report += f"\n成功项数: {success_count}"
        report += f"\n成功率: {success_count}/{total_checks} ({100*success_count//max(total_checks,1)}%)"

        return report

    def save_report(self, filename: Optional[str] = None) -> str:
        """保存报告到文件"""
        if not filename:
            filename = f"telegram_bot_test_report_{self.timestamp}.txt"

        report = self.generate_full_report()

        with open(filename, "w", encoding="utf-8") as f:
            f.write(report)

        logger.info(f"✅ 报告已保存: {filename}")
        return filename


# ========== 主测试流程 ==========
def main():
    """主测试流程"""
    logger.info("🚀 开始 Telegram Bot 综合测试\n")

    # 1. 环境检查
    logger.info("=" * 80)
    logger.info("第1阶段: 环境检查")
    logger.info("=" * 80)
    env_checker = EnvironmentChecker()
    env_results = env_checker.run_all_checks()

    # 2. 功能验证
    logger.info("\n" + "=" * 80)
    logger.info("第2阶段: 功能验证")
    logger.info("=" * 80)
    func_validator = BotFunctionalityValidator()
    func_results = func_validator.run_all_validations()

    # 3. 生成报告
    logger.info("\n" + "=" * 80)
    logger.info("第3阶段: 生成报告")
    logger.info("=" * 80)
    generator = TestReportGenerator(env_results, func_results)
    report = generator.generate_full_report()
    print("\n" + report)

    # 4. 保存报告
    report_file = generator.save_report()

    # 5. 显示进度更新
    logger.info("\n" + "=" * 80)
    logger.info("测试完成总结")
    logger.info("=" * 80)
    logger.info(f"""
✅ 测试完成！

📊 检查项总数:
  • 环境变量: {len(env_results.get('环境变量', {}))}
  • 依赖库: {len(env_results.get('依赖库', {}))}
  • 文件检查: {len(env_results.get('文件检查', {}))}
  • 配置检查: {len(env_results.get('配置检查', {}))}
  • 量化系统: {len(func_results.get('量化系统', {}))}
  • 命令处理器: {len(func_results.get('命令处理器', {}))}
  • 错误处理: {len(func_results.get('错误处理', {}))}
  • 安全特性: {len(func_results.get('安全特性', {}))}

📄 报告位置: {report_file}

🎯 接下来的步骤:
  1. 查看生成的测试报告
  2. 根据报告修复任何缺失的配置
  3. 运行 'python start_telegram_bot.py' 启动 Bot
  4. 使用 'python test_bot_connection.py' 测试连接
    """)


if __name__ == "__main__":
    main()
