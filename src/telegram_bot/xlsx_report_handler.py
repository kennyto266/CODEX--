"""
Telegram Bot xlsx 报告处理器

集成 xlsx 股票分析功能到 Telegram Bot
用户可以通过 Telegram 命令请求生成 Excel 报告
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# 添加根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(current_dir))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# 导入 xlsx 分析模块
try:
    from xlsx_stock_analyzer import XlsxStockAnalyzer
    from create_xlsx_report import ExcelReportGenerator
    from simple_enhance_xlsx import enhance_excel
except ImportError as e:
    logging.warning(f"无法导入 xlsx 分析模块: {e}")


class XlsxReportHandler:
    """xlsx 报告处理器"""

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger("hk_quant_system.xlsx_bot_handler")
        self.reports_dir = Path("data/xlsx_reports/telegram")
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        # 存储用户的请求状态
        self.user_states = {}  # user_id -> state
        self.active_tasks = {}  # task_id -> info

    async def handle_message(self, message) -> bool:
        """处理消息"""
        try:
            user_id = message.from_user.id
            text = message.text.strip()

            # 处理命令
            if text.startswith('/'):
                return await self._handle_command(message, text)

            # 处理用户状态
            if user_id in self.user_states:
                return await self._handle_stateful_input(message, text)

            return False

        except Exception as e:
            self.logger.error(f"处理消息失败: {e}")
            return False

    async def _handle_command(self, message, command: str) -> bool:
        """处理命令"""
        user_id = message.from_user.id
        command = command.lower()

        if command == '/start':
            return await self._cmd_start(message)

        elif command == '/help':
            return await self._cmd_help(message)

        elif command == '/report':
            return await self._cmd_report(message)

        elif command == '/status':
            return await self._cmd_status(message)

        elif command == '/list':
            return await self._cmd_list(message)

        else:
            # 未知命令
            await message.reply(
                "❌ 未知命令\n\n"
                "使用 /help 查看可用命令"
            )
            return False

    async def _cmd_start(self, message):
        """开始命令"""
        user_name = message.from_user.first_name or "用户"
        welcome_text = f"""
👋 欢迎，{user_name}！

我是 xlsx 股票分析 Bot，可以为您生成专业的 Excel 分析报告。

📊 支持功能：
• 股票性能分析
• 策略回测对比
• 专业 Excel 报告
• 多种策略类型（BOLL, RSI, MACD, MA, KDJ, CCI）

📝 使用方法：
/report - 开始生成报告
/status - 查看当前任务状态
/list - 查看历史报告

输入 /help 查看详细帮助
        """
        await message.reply(welcome_text)
        return True

    async def _cmd_help(self, message):
        """帮助命令"""
        help_text = """
📚 xlsx 股票分析 Bot - 帮助文档

🔧 可用命令：

/start     - 开始使用
/report    - 生成新的分析报告
/status    - 查看当前任务状态
/list      - 查看历史报告
/help      - 显示此帮助

📊 生成报告步骤：

1. 输入 /report
2. 按提示输入股票代码（如：0001.HK）
3. 选择开始日期（YYYY-MM-DD）
4. 选择结束日期（YYYY-MM-DD）
5. 选择策略类型（可多选，用逗号分隔）
6. 等待分析完成（约 30-60 秒）
7. 接收 Excel 报告文件

💡 支持的策略：
• BOLL - 布林带策略
• RSI - 相对强弱指数
• MACD - 指数平滑异同平均线
• MA - 移动平均线
• KDJ - 随机指标
• CCI - 商品通道指数

📝 示例：
股票代码：0001.HK
日期范围：2023-01-01 到 2023-12-31
策略类型：BOLL,RSI

⚠️ 注意：
• 分析需要一定时间，请耐心等待
• 生成的报告将保存在服务器 24 小时
• 如有问题请联系管理员
        """
        await message.reply(help_text)
        return True

    async def _cmd_report(self, message):
        """报告命令"""
        user_id = message.from_user.id
        self.user_states[user_id] = {
            "step": "symbol",
            "data": {}
        }

        await message.reply(
            "📊 开始生成分析报告\n\n"
            "请输入股票代码（如：0001.HK）："
        )
        return True

    async def _cmd_status(self, message):
        """状态命令"""
        user_id = message.from_user.id

        # 查找用户的活跃任务
        active_tasks = [
            task for task in self.active_tasks.values()
            if task.get("user_id") == user_id and task["status"] == "running"
        ]

        if not active_tasks:
            await message.reply(
                "📊 当前没有正在运行的分析任务"
            )
            return True

        # 显示所有活跃任务
        for task in active_tasks:
            progress = task.get("progress", 0)
            message_text = task.get("message", "")
            symbol = task.get("symbol", "")
            period = f"{task.get('start_date')} 至 {task.get('end_date')}"

            status_text = f"""
📈 分析任务状态

股票代码：{symbol}
分析期间：{period}
进度：{progress}%
状态：{message_text}

{'█' * (progress // 10)}{'░' * (10 - progress // 10)}
            """
            await message.reply(status_text)

        return True

    async def _cmd_list(self, message):
        """列表命令"""
        user_id = message.from_user.id

        # 查找用户的历史任务
        user_tasks = [
            task for task in self.active_tasks.values()
            if task.get("user_id") == user_id and task["status"] == "completed"
        ]

        if not user_tasks:
            await message.reply(
                "📊 暂无历史报告"
            )
            return True

        # 显示最近的 5 个报告
        recent_tasks = sorted(
            user_tasks,
            key=lambda x: x.get("completed_at", datetime.min),
            reverse=True
        )[:5]

        message_text = "📊 最近的分析报告：\n\n"
        for i, task in enumerate(recent_tasks, 1):
            symbol = task.get("symbol", "")
            completed_at = task.get("completed_at", "").strftime("%Y-%m-%d %H:%M")
            task_id = task.get("task_id", "")[:8]

            message_text += f"{i}. {symbol} - {completed_at}\n"
            message_text += f"   任务ID: {task_id}\n\n"

        message_text += "输入任务ID的前8位来下载报告"
        await message.reply(message_text)

        return True

    async def _handle_stateful_input(self, message, text: str) -> bool:
        """处理有状态的用户输入"""
        user_id = message.from_user.id
        state = self.user_states[user_id]
        step = state["step"]

        try:
            if step == "symbol":
                return await self._handle_symbol_input(message, text)

            elif step == "start_date":
                return await self._handle_start_date_input(message, text)

            elif step == "end_date":
                return await self._handle_end_date_input(message, text)

            elif step == "strategies":
                return await self._handle_strategies_input(message, text)

            else:
                # 未知步骤，重置状态
                del self.user_states[user_id]
                await message.reply("❌ 发生错误，请重新输入 /report")
                return False

        except Exception as e:
            self.logger.error(f"处理用户输入失败: {e}")
            del self.user_states[user_id]
            await message.reply(f"❌ 发生错误: {str(e)}")
            return False

    async def _handle_symbol_input(self, message, text: str):
        """处理股票代码输入"""
        symbol = text.upper().strip()

        # 验证股票代码格式
        if not symbol or len(symbol) < 4:
            await message.reply("❌ 股票代码格式错误，请重新输入（如：0001.HK）")
            return False

        # 保存股票代码
        self.user_states[message.from_user.id]["data"]["symbol"] = symbol
        self.user_states[message.from_user.id]["step"] = "start_date"

        await message.reply(
            f"✅ 股票代码：{symbol}\n\n"
            "请输入开始日期（YYYY-MM-DD）："
        )
        return True

    async def _handle_start_date_input(self, message, text: str):
        """处理开始日期输入"""
        date = text.strip()

        # 验证日期格式
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            await message.reply("❌ 日期格式错误，请输入 YYYY-MM-DD 格式")
            return False

        # 保存开始日期
        self.user_states[message.from_user.id]["data"]["start_date"] = date
        self.user_states[message.from_user.id]["step"] = "end_date"

        await message.reply(
            f"✅ 开始日期：{date}\n\n"
            "请输入结束日期（YYYY-MM-DD）："
        )
        return True

    async def _handle_end_date_input(self, message, text: str):
        """处理结束日期输入"""
        date = text.strip()

        # 验证日期格式
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            await message.reply("❌ 日期格式错误，请输入 YYYY-MM-DD 格式")
            return False

        # 验证日期范围
        start_date = self.user_states[message.from_user.id]["data"]["start_date"]
        if date <= start_date:
            await message.reply("❌ 结束日期必须晚于开始日期")
            return False

        # 保存结束日期
        self.user_states[message.from_user.id]["data"]["end_date"] = date
        self.user_states[message.from_user.id]["step"] = "strategies"

        await message.reply(
            f"✅ 结束日期：{date}\n\n"
            "请输入策略类型（用逗号分隔，可多选）：\n"
            "可用策略：BOLL, RSI, MACD, MA, KDJ, CCI\n\n"
            "示例：BOLL,RSI"
        )
        return True

    async def _handle_strategies_input(self, message, text: str):
        """处理策略类型输入"""
        strategies = [s.strip().upper() for s in text.split(',')]
        available_strategies = ["BOLL", "RSI", "MACD", "MA", "KDJ", "CCI"]

        # 验证策略
        invalid_strategies = [s for s in strategies if s not in available_strategies]
        if invalid_strategies:
            await message.reply(
                f"❌ 不支持的策略：{invalid_strategies}\n"
                f"可用策略：{', '.join(available_strategies)}\n\n"
                "请重新输入："
            )
            return False

        # 保存策略
        data = self.user_states[message.from_user.id]["data"]
        data["strategies"] = strategies
        data["user_id"] = message.from_user.id

        # 启动分析任务
        await self._start_analysis_task(message, data)

        # 清除状态
        del self.user_states[message.from_user.id]

        return True

    async def _start_analysis_task(self, message, data: Dict):
        """启动分析任务"""
        user_id = data["user_id"]
        symbol = data["symbol"]
        start_date = data["start_date"]
        end_date = data["end_date"]
        strategies = data["strategies"]

        # 生成任务ID
        task_id = f"tg_{user_id}_{int(datetime.now().timestamp())}"

        # 保存任务信息
        self.active_tasks[task_id] = {
            "task_id": task_id,
            "user_id": user_id,
            "symbol": symbol,
            "start_date": start_date,
            "end_date": end_date,
            "strategies": strategies,
            "status": "running",
            "progress": 0,
            "message": "准备中...",
            "started_at": datetime.now()
        }

        # 发送确认消息
        await message.reply(
            "📊 分析任务已启动\n\n"
            f"股票代码：{symbol}\n"
            f"分析期间：{start_date} 至 {end_date}\n"
            f"策略类型：{', '.join(strategies)}\n\n"
            "⏳ 预计需要 30-60 秒，请耐心等待...\n"
            "可以使用 /status 查看进度"
        )

        # 在后台运行分析
        asyncio.create_task(
            self._run_analysis(task_id, data)
        )

    async def _run_analysis(self, task_id: str, data: Dict):
        """运行分析"""
        try:
            self.logger.info(f"开始分析: {task_id}")

            # 更新进度
            await self._update_task_progress(task_id, 10, "加载数据...")

            # 导入并运行分析
            analyzer = XlsxStockAnalyzer()
            await analyzer.load_data(
                symbol=data["symbol"],
                start_date=data["start_date"],
                end_date=data["end_date"]
            )

            await self._update_task_progress(task_id, 30, "计算性能指标...")
            await analyzer.calculate_performance_metrics()
            await analyzer.analyze_strategies(data["strategies"])

            await self._update_task_progress(task_id, 50, "生成分析结果...")
            results = await analyzer.generate_results()

            # 保存分析结果
            results_file = self.reports_dir / f"{task_id}_analysis.json"
            import json
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)

            excel_files = {}

            # 生成 Excel 报告
            await self._update_task_progress(task_id, 60, "生成 Excel 报告...")
            generator = ExcelReportGenerator()
            basic_excel = self.reports_dir / f"{task_id}_basic.xlsx"
            await generator.create_report(results, str(basic_excel))
            excel_files["basic"] = str(basic_excel)

            await self._update_task_progress(task_id, 80, "增强格式...")
            enhanced_excel = self.reports_dir / f"{task_id}_enhanced.xlsx"
            import shutil
            shutil.copy2(basic_excel, enhanced_excel)

            # 增强格式
            try:
                os.chdir(enhanced_excel.parent)
                enhance_excel()
            except Exception as e:
                self.logger.warning(f"增强格式失败: {e}")

            excel_files["enhanced"] = str(enhanced_excel)

            # 完成
            await self._update_task_progress(task_id, 100, "分析完成")
            self.active_tasks[task_id]["status"] = "completed"
            self.active_tasks[task_id]["completed_at"] = datetime.now()
            self.active_tasks[task_id]["excel_files"] = excel_files

            # 发送完成消息和文件
            await self._send_completion_message(task_id, results)

            self.logger.info(f"分析完成: {task_id}")

        except Exception as e:
            self.logger.error(f"分析失败: {e}")
            self.active_tasks[task_id]["status"] = "failed"
            self.active_tasks[task_id]["message"] = str(e)

            # 发送失败消息
            user_id = self.active_tasks[task_id]["user_id"]
            await self.bot.send_message(
                chat_id=user_id,
                text=f"❌ 分析失败：{str(e)}"
            )

    async def _update_task_progress(self, task_id: str, progress: int, message: str):
        """更新任务进度"""
        if task_id in self.active_tasks:
            self.active_tasks[task_id]["progress"] = progress
            self.active_tasks[task_id]["message"] = message

    async def _send_completion_message(self, task_id: str, results: Dict):
        """发送完成消息"""
        task = self.active_tasks[task_id]
        user_id = task["user_id"]
        symbol = task["symbol"]

        # 发送结果摘要
        metrics = results.get("performance_metrics", {}).get("stock", {})
        total_return = metrics.get("total_return", 0)

        summary_text = f"""
✅ 分析完成！

股票代码：{symbol}
总收益率：{total_return:.2f}%

📁 报告文件：
• 基础版：{task_id}_basic.xlsx
• 增强版：{task_id}_enhanced.xlsx（推荐）

正在发送文件，请稍候...
        """

        await self.bot.send_message(chat_id=user_id, text=summary_text)

        # 发送增强版 Excel 文件
        enhanced_file = task["excel_files"]["enhanced"]
        if os.path.exists(enhanced_file):
            try:
                with open(enhanced_file, 'rb') as f:
                    await self.bot.send_document(
                        chat_id=user_id,
                        document=f,
                        filename=f"{symbol}_xlsx_analysis_report.xlsx",
                        caption=f"📊 {symbol} xlsx 分析报告\n\n"
                                f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                                f"任务ID：{task_id}"
                    )
            except Exception as e:
                self.logger.error(f"发送文件失败: {e}")
                await self.bot.send_message(
                    chat_id=user_id,
                    text=f"⚠️ 文件发送失败：{str(e)}"
                )
