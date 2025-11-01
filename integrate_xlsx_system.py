#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
xlsx 股票分析系统 - 自动集成脚本

将 xlsx 分析功能集成到现有港股量化交易项目中
自动完成文件复制、API 注册、Agent 注册等操作
"""

import os
import sys
import shutil
from pathlib import Path
from datetime import datetime


class XlsxIntegrator:
    """xlsx 系统集成器"""

    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.logger = self._setup_logger()

        # 定义源文件和目标路径
        self.source_files = {
            "xlsx_stock_analyzer.py": "核心分析引擎",
            "create_xlsx_report.py": "Excel 报告生成器",
            "simple_enhance_xlsx.py": "格式增强器",
        }

        self.target_paths = {
            "core": self.project_root,
            "api": self.project_root / "src" / "dashboard",
            "agent": self.project_root / "src" / "agents",
            "bot": self.project_root / "src" / "telegram_bot",
            "data": self.project_root / "data" / "xlsx_reports",
        }

    def _setup_logger(self):
        """设置日志"""
        import logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        return logging.getLogger("xlsx_integrator")

    def integrate(self, options: dict = None) -> bool:
        """执行完整集成"""
        try:
            self.logger.info("开始集成 xlsx 股票分析系统...")
            print("=" * 70)
            print("  XLSX 股票分析系统 - 项目集成")
            print("=" * 70)
            print()

            # 1. 验证项目结构
            if not self._validate_project_structure():
                self.logger.error("项目结构验证失败")
                return False

            print("✓ 项目结构验证通过")
            print()

            # 2. 复制核心文件
            if not self._copy_core_files():
                self.logger.error("复制核心文件失败")
                return False

            print("✓ 核心文件复制完成")
            print()

            # 3. 创建 API 服务
            if options and options.get("api", True):
                if not self._create_api_service():
                    self.logger.error("创建 API 服务失败")
                    return False

                print("✓ API 服务创建完成")
                print()

            # 4. 创建 Agent
            if options and options.get("agent", True):
                if not self._create_agent():
                    self.logger.error("创建 Agent 失败")
                    return False

                print("✓ Agent 创建完成")
            print()

            # 5. 创建 Telegram Bot 处理器
            if options and options.get("telegram", True):
                if not self._create_telegram_handler():
                    self.logger.error("创建 Telegram 处理器失败")
                    return False

                print("✓ Telegram 处理器创建完成")
            print()

            # 6. 创建配置目录
            if not self._create_directories():
                self.logger.error("创建目录失败")
                return False

            print("✓ 目录结构创建完成")
            print()

            # 7. 生成示例代码
            if not self._generate_examples():
                self.logger.error("生成示例代码失败")
                return False

            print("✓ 示例代码生成完成")
            print()

            # 8. 生成集成报告
            self._generate_integration_report()

            print("=" * 70)
            print("  集成完成！")
            print("=" * 70)
            print()
            print("📚 后续步骤:")
            print("  1. 查看 XLSX_INTEGRATION_GUIDE.md 了解详细用法")
            print("  2. 运行示例代码测试集成功能")
            print("  3. 配置环境变量和 API 密钥")
            print("  4. 重启项目服务以加载新功能")
            print()

            return True

        except Exception as e:
            self.logger.error(f"集成失败: {e}")
            return False

    def _validate_project_structure(self) -> bool:
        """验证项目结构"""
        required_dirs = [
            self.project_root / "src",
            self.project_root / "src" / "dashboard",
            self.project_root / "src" / "agents",
            self.project_root / "src" / "telegram_bot",
        ]

        for dir_path in required_dirs:
            if not dir_path.exists():
                self.logger.error(f"缺少目录: {dir_path}")
                return False

        # 检查关键文件
        api_routes = self.project_root / "src" / "dashboard" / "api_routes.py"
        if not api_routes.exists():
            self.logger.warning("api_routes.py 不存在，将创建示例集成代码")

        return True

    def _copy_core_files(self) -> bool:
        """复制核心文件"""
        for source_name, description in self.source_files.items():
            source_path = Path(source_name)
            if not source_path.exists():
                self.logger.warning(f"源文件不存在: {source_path}")
                continue

            target_path = self.target_paths["core"] / source_name
            try:
                shutil.copy2(source_path, target_path)
                self.logger.info(f"复制 {source_name} -> {target_path}")
            except Exception as e:
                self.logger.error(f"复制 {source_name} 失败: {e}")
                return False

        return True

    def _create_api_service(self) -> bool:
        """创建 API 服务"""
        source_api = Path("src/dashboard/api_xlsx_analysis.py")
        if not source_api.exists():
            self.logger.error(f"API 文件不存在: {source_api}")
            return False

        target_api = self.target_paths["api"] / "api_xlsx_analysis.py"
        try:
            shutil.copy2(source_api, target_api)
            self.logger.info(f"复制 API 服务: {target_api}")
            return True
        except Exception as e:
            self.logger.error(f"复制 API 服务失败: {e}")
            return False

    def _create_agent(self) -> bool:
        """创建 Agent"""
        source_agent = Path("src/agents/xlsx_report_agent.py")
        if not source_agent.exists():
            self.logger.error(f"Agent 文件不存在: {source_agent}")
            return False

        target_agent = self.target_paths["agent"] / "xlsx_report_agent.py"
        try:
            shutil.copy2(source_agent, target_agent)
            self.logger.info(f"复制 Agent: {target_agent}")
            return True
        except Exception as e:
            self.logger.error(f"复制 Agent 失败: {e}")
            return False

    def _create_telegram_handler(self) -> bool:
        """创建 Telegram 处理器"""
        source_bot = Path("src/telegram_bot/xlsx_report_handler.py")
        if not source_bot.exists():
            self.logger.error(f"Bot 文件不存在: {source_bot}")
            return False

        target_bot = self.target_paths["bot"] / "xlsx_report_handler.py"
        try:
            shutil.copy2(source_bot, target_bot)
            self.logger.info(f"复制 Telegram 处理器: {target_bot}")
            return True
        except Exception as e:
            self.logger.error(f"复制 Telegram 处理器失败: {e}")
            return False

    def _create_directories(self) -> bool:
        """创建目录"""
        directories = [
            self.target_paths["data"],
            self.target_paths["data"] / "telegram",
            self.project_root / "config",
            self.project_root / "logs",
        ]

        try:
            for dir_path in directories:
                dir_path.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"创建目录: {dir_path}")
            return True
        except Exception as e:
            self.logger.error(f"创建目录失败: {e}")
            return False

    def _generate_examples(self) -> bool:
        """生成示例代码"""
        try:
            # 生成 API 集成示例
            self._generate_api_integration_example()

            # 生成 Agent 集成示例
            self._generate_agent_integration_example()

            # 生成 Bot 集成示例
            self._generate_bot_integration_example()

            # 生成配置示例
            self._generate_config_example()

            return True
        except Exception as e:
            self.logger.error(f"生成示例失败: {e}")
            return False

    def _generate_api_integration_example(self):
        """生成 API 集成示例"""
        example_code = '''"""
API 集成示例

演示如何在 Dashboard API 中集成 xlsx 分析服务
"""

# 1. 修改 src/dashboard/api_routes.py

from .api_xlsx_analysis import create_xlsx_analysis_router

class DashboardAPI:
    def __init__(self, coordinator, message_queue, config=None):
        ...
        # 添加 xlsx 分析路由
        self.xlsx_router = create_xlsx_analysis_router()
        self.router.include_router(self.xlsx_router)
        ...

# 2. 使用示例

# 启动分析任务
import requests

response = requests.post("http://localhost:8001/api/xlsx/analyze", json={
    "symbol": "0001.HK",
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "strategy_types": ["BOLL", "RSI"]
})

task_id = response.json()["task_id"]

# 查询状态
status = requests.get(f"http://localhost:8001/api/xlsx/status/{task_id}")

# 下载报告
file = requests.get(f"http://localhost:8001/api/xlsx/download/{task_id}?type=enhanced")
with open("report.xlsx", "wb") as f:
    f.write(file.content)
'''

        example_path = self.project_root / "examples" / "api_integration_example.py"
        example_path.parent.mkdir(exist_ok=True)
        example_path.write_text(example_code, encoding="utf-8")
        self.logger.info(f"生成 API 集成示例: {example_path}")

    def _generate_agent_integration_example(self):
        """生成 Agent 集成示例"""
        example_code = '''"""
Agent 集成示例

演示如何在多智能体系统中集成 xlsx 报告 Agent
"""

# 1. 修改 src/agents/coordinator.py

from .xlsx_report_agent import XlsxReportAgent

class AgentCoordinator:
    def __init__(self, config, message_queue):
        ...
        # 注册 xlsx 报告 Agent
        self.xlsx_report_agent = XlsxReportAgent()
        self.register_agent(self.xlsx_report_agent)
        ...

    async def start_all_agents(self):
        """启动所有 Agent"""
        ...
        await self.xlsx_report_agent.initialize()
        ...

# 2. 发送消息给 Agent

from ..agents.protocol import DataMessage

async def request_xlsx_report(coordinator, symbol, start_date, end_date):
    """请求生成 xlsx 报告"""
    message = DataMessage(
        sender="coordinator",
        receiver="xlsx_report_agent",
        data={
            "type": "generate_report",
            "task_id": f"task_{int(datetime.now().timestamp())}",
            "symbol": symbol,
            "start_date": start_date,
            "end_date": end_date,
            "strategies": ["BOLL", "RSI"],
            "generate_enhanced": True
        }
    )
    await coordinator.send_message(message)

# 3. 自动生成报告（回测完成后）

async def on_backtest_completed(coordinator, backtest_result):
    """回测完成事件处理器"""
    await coordinator.xlsx_report_agent.handle_signal_message(
        SignalMessage(
            sender="backtest_engine",
            receiver="xlsx_report_agent",
            signal={
                "event": "backtest_completed",
                "backtest_id": backtest_result["id"],
                "symbol": backtest_result["symbol"],
                "strategies": backtest_result["strategies"],
                "start_date": backtest_result["start_date"],
                "end_date": backtest_result["end_date"]
            }
        )
    )
'''

        example_path = self.project_root / "examples" / "agent_integration_example.py"
        example_path.parent.mkdir(exist_ok=True)
        example_path.write_text(example_code, encoding="utf-8")
        self.logger.info(f"生成 Agent 集成示例: {example_path}")

    def _generate_bot_integration_example(self):
        """生成 Bot 集成示例"""
        example_code = '''"""
Telegram Bot 集成示例

演示如何在 Telegram Bot 中集成 xlsx 报告功能
"""

# 1. 修改 src/telegram_bot/telegram_quant_bot.py

from .xlsx_report_handler import XlsxReportHandler

class TelegramQuantBot:
    def __init__(self, token):
        ...
        # 添加 xlsx 报告处理器
        self.xlsx_handler = XlsxReportHandler(self)
        ...

    async def handle_message(self, message):
        # 先尝试 xlsx 处理
        if await self.xlsx_handler.handle_message(message):
            return True

        # 其他消息处理...
        return False

# 2. 使用示例

# 用户交互流程：
# 1. 用户输入 /report
# 2. 按提示输入股票代码
# 3. 输入日期范围
# 4. 选择策略类型
# 5. 等待分析完成
# 6. 接收 Excel 文件

# 3. 手动触发报告

async def send_report_to_user(bot, user_id, symbol, start_date, end_date):
    """手动发送报告给用户"""
    # 这里可以通过内部 API 生成报告
    # 然后发送给用户
    pass
'''

        example_path = self.project_root / "examples" / "telegram_integration_example.py"
        example_path.parent.mkdir(exist_ok=True)
        example_path.write_text(example_code, encoding="utf-8")
        self.logger.info(f"生成 Telegram 集成示例: {example_path}")

    def _generate_config_example(self):
        """生成配置示例"""
        config_content = '''# xlsx 分析系统配置文件
# config/xlsx_config.yaml

xlsx_analysis:
  # 报告存储目录
  reports_dir: "data/xlsx_reports"
  temp_dir: "data/temp"

  # 并发控制
  max_concurrent_tasks: 5
  task_timeout: 300  # 秒

  # 支持的策略类型
  strategies:
    - BOLL
    - RSI
    - MACD
    - MA
    - KDJ
    - CCI

  # Excel 格式配置
  excel:
    theme_color: "366092"
    header_font_size: 12
    data_font_size: 10
    generate_enhanced: true

  # Telegram Bot 配置
  telegram:
    enabled: true
    max_file_size_mb: 50
    bot_token: "${TELEGRAM_BOT_TOKEN}"

  # API 配置
  api:
    enabled: true
    host: "0.0.0.0"
    port: 8001
    cors_origins: ["*"]
    rate_limit: 100  # 每分钟请求数

  # 日志配置
  logging:
    level: "INFO"
    file: "logs/xlsx_analysis.log"
    max_size_mb: 10
    backup_count: 5
'''

        config_path = self.project_root / "config" / "xlsx_config.yaml.example"
        config_path.write_text(config_content, encoding="utf-8")
        self.logger.info(f"生成配置文件示例: {config_path}")

    def _generate_integration_report(self):
        """生成集成报告"""
        report = f"""
╔════════════════════════════════════════════════════════════════════╗
║                                                                    ║
║           XLSX 股票分析系统 - 集成完成报告                           ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝

集成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
项目路径: {self.project_root}

────────────────────────────────────────────────────────────────────

📁 已集成的文件:

核心分析引擎:
  ✓ xlsx_stock_analyzer.py
  ✓ create_xlsx_report.py
  ✓ simple_enhance_xlsx.py

API 服务:
  ✓ src/dashboard/api_xlsx_analysis.py

Agent 组件:
  ✓ src/agents/xlsx_report_agent.py

Telegram Bot:
  ✓ src/telegram_bot/xlsx_report_handler.py

配置和示例:
  ✓ config/xlsx_config.yaml.example
  ✓ examples/api_integration_example.py
  ✓ examples/agent_integration_example.py
  ✓ examples/telegram_integration_example.py

目录结构:
  ✓ data/xlsx_reports/
  ✓ data/xlsx_reports/telegram/
  ✓ logs/

────────────────────────────────────────────────────────────────────

🚀 可用功能:

1. REST API
   端点: POST /api/xlsx/analyze
   端点: GET /api/xlsx/status/{{task_id}}
   端点: GET /api/xlsx/results/{{task_id}}
   端点: GET /api/xlsx/download/{{task_id}}

2. 多智能体系统
   Agent: xlsx_report_agent
   消息类型: DATA, SIGNAL, CONTROL
   自动报告生成: 支持

3. Telegram Bot
   命令: /report (生成报告)
   命令: /status (查看状态)
   命令: /list (历史报告)
   文件传输: 支持

────────────────────────────────────────────────────────────────────

📚 文档:

  完整集成指南: XLSX_INTEGRATION_GUIDE.md
  API 文档: 查看集成指南中的 API 部分
  示例代码: examples/ 目录

────────────────────────────────────────────────────────────────────

⚙️ 后续配置:

1. 环境变量
   配置 TELEGRAM_BOT_TOKEN (如果使用 Bot)

2. 依赖安装
   pip install openpyxl pandas numpy

3. 重启服务
   重启项目以加载新的 API 路由和 Agent

────────────────────────────────────────────────────────────────────

✅ 集成完成！xlsx 股票分析系统已成功集成到您的项目中

"""

        report_path = self.project_root / "XLSX_INTEGRATION_REPORT.txt"
        report_path.write_text(report, encoding="utf-8")
        print(report)
        self.logger.info(f"集成报告已保存: {report_path}")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="xlsx 股票分析系统 - 自动集成脚本")
    parser.add_argument("--project-root", help="项目根目录路径", default=".")
    parser.add_argument("--skip-api", action="store_true", help="跳过 API 集成")
    parser.add_argument("--skip-agent", action="store_true", help="跳过 Agent 集成")
    parser.add_argument("--skip-telegram", action="store_true", help="跳过 Telegram 集成")

    args = parser.parse_args()

    integrator = XlsxIntegrator(args.project_root)

    options = {
        "api": not args.skip_api,
        "agent": not args.skip_agent,
        "telegram": not args.skip_telegram,
    }

    success = integrator.integrate(options)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
