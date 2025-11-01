"""
xlsx 报告分析 Agent

专门负责生成 Excel 报告的 AI Agent
集成到现有的多智能体系统中
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from ..agents.base_agent import BaseAgent
from ..agents.protocol import (
    Message,
    MessageType,
    AgentMessage,
    ControlMessage,
    DataMessage,
    SignalMessage
)


class XlsxReportAgent(BaseAgent):
    """xlsx 报告分析 Agent"""

    def __init__(self, agent_id: str = "xlsx_report_agent"):
        super().__init__(agent_id)
        self.logger = logging.getLogger(f"hk_quant_system.{agent_id}")
        self.reports_dir = Path("data/xlsx_reports")
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        # 支持的策略类型
        self.supported_strategies = ["BOLL", "RSI", "MACD", "MA", "KDJ", "CCI"]

        # Agent 状态
        self.current_tasks = {}  # task_id -> task_info
        self.completed_reports = {}  # task_id -> report_info

    async def initialize(self) -> bool:
        """初始化 Agent"""
        try:
            self.logger.info("初始化 xlsx 报告分析 Agent...")

            # 注册消息处理
            self.message_handler.register_handler(
                MessageType.DATA,
                self.handle_data_message
            )
            self.message_handler.register_handler(
                MessageType.SIGNAL,
                self.handle_signal_message
            )
            self.message_handler.register_handler(
                MessageType.CONTROL,
                self.handle_control_message
            )

            self.logger.info("xlsx 报告分析 Agent 初始化完成")
            return True

        except Exception as e:
            self.logger.error(f"Agent 初始化失败: {e}")
            return False

    async def process_message(self, message: Message) -> bool:
        """处理消息"""
        try:
            self.logger.debug(f"处理消息: {message.message_type}")

            if message.message_type == MessageType.DATA:
                return await self.handle_data_message(message)

            elif message.message_type == MessageType.SIGNAL:
                return await self.handle_signal_message(message)

            elif message.message_type == MessageType.CONTROL:
                return await self.handle_control_message(message)

            else:
                self.logger.warning(f"未知消息类型: {message.message_type}")
                return False

        except Exception as e:
            self.logger.error(f"处理消息失败: {e}")
            return False

    async def handle_data_message(self, message: DataMessage) -> bool:
        """处理数据消息"""
        try:
            data = message.data

            # 支持的消息类型
            if data.get("type") == "generate_report":
                return await self._generate_report_request(data)

            elif data.get("type") == "get_report_status":
                return await self._get_report_status(data)

            elif data.get("type") == "list_reports":
                return await self._list_reports(data)

            else:
                self.logger.warning(f"未知数据消息类型: {data.get('type')}")
                return False

        except Exception as e:
            self.logger.error(f"处理数据消息失败: {e}")
            return False

    async def handle_signal_message(self, message: SignalMessage) -> bool:
        """处理信号消息"""
        try:
            signal = message.signal

            # 如果是回测完成信号，自动生成报告
            if signal.get("event") == "backtest_completed":
                await self._auto_generate_report(signal)

            return True

        except Exception as e:
            self.logger.error(f"处理信号消息失败: {e}")
            return False

    async def handle_control_message(self, message: ControlMessage) -> bool:
        """处理控制消息"""
        try:
            control = message.control

            if control.get("action") == "stop":
                # 停止所有运行中的任务
                for task_id in self.current_tasks:
                    self.current_tasks[task_id]["status"] = "stopped"

                self.logger.info("已停止所有任务")

            return True

        except Exception as e:
            self.logger.error(f"处理控制消息失败: {e}")
            return False

    async def _generate_report_request(self, data: Dict) -> bool:
        """生成报告请求"""
        try:
            task_id = data.get("task_id")
            symbol = data.get("symbol")
            start_date = data.get("start_date")
            end_date = data.get("end_date")
            strategies = data.get("strategies", ["BOLL", "RSI"])
            generate_enhanced = data.get("generate_enhanced", True)

            # 验证参数
            if not all([task_id, symbol, start_date, end_date]):
                await self._send_error(task_id, "缺少必要参数")
                return False

            # 验证策略类型
            invalid_strategies = [s for s in strategies if s not in self.supported_strategies]
            if invalid_strategies:
                await self._send_error(task_id, f"不支持的策略: {invalid_strategies}")
                return False

            # 启动分析任务
            self.current_tasks[task_id] = {
                "task_id": task_id,
                "symbol": symbol,
                "start_date": start_date,
                "end_date": end_date,
                "strategies": strategies,
                "generate_enhanced": generate_enhanced,
                "status": "running",
                "progress": 0,
                "started_at": datetime.now()
            }

            # 在后台运行分析
            asyncio.create_task(
                self._run_analysis(task_id, symbol, start_date, end_date, strategies, generate_enhanced)
            )

            # 发送确认消息
            await self.broadcast_message(
                message_type=MessageType.DATA,
                content={
                    "type": "report_started",
                    "task_id": task_id,
                    "symbol": symbol,
                    "period": f"{start_date} 至 {end_date}"
                }
            )

            return True

        except Exception as e:
            self.logger.error(f"生成报告请求失败: {e}")
            return False

    async def _run_analysis(
        self,
        task_id: str,
        symbol: str,
        start_date: str,
        end_date: str,
        strategies: List[str],
        generate_enhanced: bool
    ):
        """运行分析"""
        try:
            self.logger.info(f"开始分析: {task_id}, {symbol}")

            # 更新进度
            await self._update_progress(task_id, 10, "加载数据...")

            # 1. 导入并运行分析引擎
            import sys
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            root_dir = os.path.dirname(os.path.dirname(current_dir))
            if root_dir not in sys.path:
                sys.path.insert(0, root_dir)

            try:
                from xlsx_stock_analyzer import XlsxStockAnalyzer
                from create_xlsx_report import ExcelReportGenerator
                from simple_enhance_xlsx import enhance_excel
            except ImportError as e:
                await self._send_error(task_id, f"无法导入分析模块: {e}")
                return

            # 运行分析
            analyzer = XlsxStockAnalyzer()
            await analyzer.load_data(symbol=symbol, start_date=start_date, end_date=end_date)
            await analyzer.calculate_performance_metrics()
            await analyzer.analyze_strategies(strategies)

            await self._update_progress(task_id, 50, "生成分析结果...")
            results = await analyzer.generate_results()

            # 保存分析结果
            results_file = self.reports_dir / f"{task_id}_analysis.json"
            import json
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)

            excel_files = {}

            # 生成 Excel 报告
            await self._update_progress(task_id, 60, "生成 Excel 报告...")
            generator = ExcelReportGenerator()
            basic_excel = self.reports_dir / f"{task_id}_basic.xlsx"
            await generator.create_report(results, str(basic_excel))
            excel_files["basic"] = str(basic_excel)

            if generate_enhanced:
                await self._update_progress(task_id, 80, "增强格式...")
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
            await self._update_progress(task_id, 100, "分析完成")
            self.current_tasks[task_id]["status"] = "completed"
            self.completed_reports[task_id] = {
                "task_id": task_id,
                "symbol": symbol,
                "period": {"start": start_date, "end": end_date},
                "strategies": strategies,
                "excel_files": excel_files,
                "metrics": results.get("performance_metrics", {}),
                "completed_at": datetime.now()
            }

            # 发送完成消息
            await self.broadcast_message(
                message_type=MessageType.DATA,
                content={
                    "type": "report_completed",
                    "task_id": task_id,
                    "symbol": symbol,
                    "excel_files": excel_files,
                    "metrics": results.get("performance_metrics", {})
                }
            )

            self.logger.info(f"分析完成: {task_id}")

        except Exception as e:
            self.logger.error(f"分析失败: {e}")
            self.current_tasks[task_id]["status"] = "failed"
            await self._send_error(task_id, str(e))

    async def _get_report_status(self, data: Dict) -> bool:
        """获取报告状态"""
        try:
            task_id = data.get("task_id")
            request_id = data.get("request_id")

            if task_id not in self.current_tasks:
                await self._send_error(request_id, "任务不存在")
                return False

            task_info = self.current_tasks[task_id]

            await self.broadcast_message(
                message_type=MessageType.DATA,
                content={
                    "type": "report_status",
                    "request_id": request_id,
                    "task_id": task_id,
                    "status": task_info["status"],
                    "progress": task_info["progress"],
                    "message": task_info.get("message", ""),
                    "symbol": task_info["symbol"],
                    "period": f"{task_info['start_date']} 至 {task_info['end_date']}"
                }
            )

            return True

        except Exception as e:
            self.logger.error(f"获取报告状态失败: {e}")
            return False

    async def _list_reports(self, data: Dict) -> bool:
        """列出报告"""
        try:
            request_id = data.get("request_id")

            reports = []
            for task_id, report in self.completed_reports.items():
                reports.append({
                    "task_id": task_id,
                    "symbol": report["symbol"],
                    "period": report["period"],
                    "strategies": report["strategies"],
                    "completed_at": report["completed_at"].isoformat(),
                    "excel_files": list(report["excel_files"].keys())
                })

            await self.broadcast_message(
                message_type=MessageType.DATA,
                content={
                    "type": "reports_list",
                    "request_id": request_id,
                    "reports": reports
                }
            )

            return True

        except Exception as e:
            self.logger.error(f"列出报告失败: {e}")
            return False

    async def _auto_generate_report(self, signal: Dict):
        """自动生成报告"""
        try:
            backtest_id = signal.get("backtest_id")
            symbol = signal.get("symbol")
            strategies = signal.get("strategies", ["BOLL", "RSI"])

            self.logger.info(f"收到回测完成信号，自动生成报告: {backtest_id}")

            # 生成报告
            await self._generate_report_request({
                "task_id": f"auto_{backtest_id}",
                "symbol": symbol,
                "start_date": signal.get("start_date"),
                "end_date": signal.get("end_date"),
                "strategies": strategies,
                "generate_enhanced": True
            })

        except Exception as e:
            self.logger.error(f"自动生成报告失败: {e}")

    async def _update_progress(self, task_id: str, progress: int, message: str):
        """更新进度"""
        if task_id in self.current_tasks:
            self.current_tasks[task_id]["progress"] = progress
            self.current_tasks[task_id]["message"] = message

            # 广播进度更新
            await self.broadcast_message(
                message_type=MessageType.DATA,
                content={
                    "type": "report_progress",
                    "task_id": task_id,
                    "progress": progress,
                    "message": message
                }
            )

    async def _send_error(self, request_id: str, error_message: str):
        """发送错误消息"""
        await self.broadcast_message(
            message_type=MessageType.DATA,
            content={
                "type": "error",
                "request_id": request_id,
                "error": error_message
            }
        )

    async def cleanup(self):
        """清理资源"""
        try:
            self.logger.info("清理 xlsx 报告分析 Agent...")
            # 可以在这里清理临时文件等
            self.logger.info("清理完成")
        except Exception as e:
            self.logger.error(f"清理失败: {e}")
