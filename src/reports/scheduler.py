"""
定时报告生成器

使用APScheduler实现定时任务调度，支持：
- Cron表达式
- 多种调度频率
- 任务队列管理
- 任务状态监控
- 失败重试机制
- 任务日志记录
"""

import asyncio
import json
import os
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

    from apscheduler.job import Job
    from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, JobExecutionEvent
except ImportError:
    raise ImportError("请安装APScheduler: pip install APScheduler")


class JobStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRY = "retry"


@dataclass
class JobExecutionRecord:
    """任务执行记录"""
    job_id: str
    report_id: str
    start_time: str
    end_time: Optional[str] = None
    status: JobStatus = JobStatus.PENDING
    message: str = ""
    error: Optional[str] = None
    output_path: Optional[str] = None
    execution_time: float = 0.0
    retry_count: int = 0
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))


class ReportScheduler:
    """报告调度器"""

    def __init__(self, storage_path: str = "data/scheduler"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.scheduler = AsyncIOScheduler(
            timezone="Asia/Hong_Kong",
            job_defaults={
                'coalesce': False,
                'max_instances': 1,
                'misfire_grace_time': 300
            }
        )

        self.params_manager = get_params_manager()
        self.generator = HTMLReportGenerator()
        self.executor = ThreadPoolExecutor(max_workers=4)

        # 任务记录存储
        self.execution_history: Dict[str, List[JobExecutionRecord]] = {}

        # 任务状态跟踪
        self.job_status: Dict[str, JobStatus] = {}

        # 事件监听
        self.scheduler.add_listener(
            self._job_executed,
            EVENT_JOB_EXECUTED | EVENT_JOB_ERROR
        )

        # 加载历史执行记录
        self._load_execution_history()

    def start(self):
        """启动调度器"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("报告调度器已启动")

            # 重新加载所有计划任务
            self._reload_scheduled_jobs()

    def shutdown(self):
        """关闭调度器"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("报告调度器已关闭")

    def add_report_job(
        self,
        report_id: str,
        report_params: Optional[ReportParams] = None
    ) -> bool:
        """添加报告任务"""
        try:
            if report_params is None:
                report_params = self.params_manager.get_params(report_id)
                if not report_params:
                    logger.error(f"报告参数不存在: {report_id}")
                    return False

            if not report_params.schedule or not report_params.schedule.enabled:
                logger.warning(f"报告调度已禁用: {report_id}")
                return False

            job_id = f"report_{report_id}"

            # 创建任务
            trigger = CronTrigger.from_crontab(
                report_params.schedule.cron_expression,
                timezone=report_params.schedule.timezone
            )

            self.scheduler.add_job(
                func=self._execute_report_job,
                trigger=trigger,
                id=job_id,
                args=[report_id],
                kwargs={},
                max_instances=report_params.schedule.max_retries,
                misfire_grace_time=300,
                replace_existing=True
            )

            self.job_status[job_id] = JobStatus.PENDING
            logger.info(f"已添加报告任务: {report_id}, Cron: {report_params.schedule.cron_expression}")
            return True

        except Exception as e:
            logger.error(f"添加报告任务失败: {e}\n{traceback.format_exc()}")
            return False

    def remove_report_job(self, report_id: str) -> bool:
        """移除报告任务"""
        try:
            job_id = f"report_{report_id}"
            job = self.scheduler.get_job(job_id)

            if job:
                self.scheduler.remove_job(job_id)
                self.job_status[job_id] = JobStatus.CANCELLED
                logger.info(f"已移除报告任务: {report_id}")
                return True
            else:
                logger.warning(f"报告任务不存在: {report_id}")
                return False

        except Exception as e:
            logger.error(f"移除报告任务失败: {e}")
            return False

    def run_report_now(self, report_id: str) -> Optional[JobExecutionRecord]:
        """立即运行报告"""
        try:
            report_params = self.params_manager.get_params(report_id)
            if not report_params:
                logger.error(f"报告参数不存在: {report_id}")
                return None

            # 创建执行记录
            execution = self._create_execution_record(report_id)

            # 异步执行
            asyncio.create_task(self._execute_report_job(report_id, execution))

            logger.info(f"已启动即时报告任务: {report_id}")
            return execution

        except Exception as e:
            logger.error(f"启动即时报告失败: {e}\n{traceback.format_exc()}")
            return None

    def pause_job(self, report_id: str) -> bool:
        """暂停任务"""
        try:
            job_id = f"report_{report_id}"
            self.scheduler.pause_job(job_id)
            logger.info(f"已暂停任务: {report_id}")
            return True
        except Exception as e:
            logger.error(f"暂停任务失败: {e}")
            return False

    def resume_job(self, report_id: str) -> bool:
        """恢复任务"""
        try:
            job_id = f"report_{report_id}"
            self.scheduler.resume_job(job_id)
            logger.info(f"已恢复任务: {report_id}")
            return True
        except Exception as e:
            logger.error(f"恢复任务失败: {e}")
            return False

    def get_job_status(self, report_id: str) -> Optional[JobStatus]:
        """获取任务状态"""
        job_id = f"report_{report_id}"
        return self.job_status.get(job_id)

    def get_execution_history(
        self,
        report_id: Optional[str] = None,
        limit: int = 100
    ) -> List[JobExecutionRecord]:
        """获取执行历史"""
        if report_id:
            return self.execution_history.get(report_id, [])[-limit:]
        else:
            all_records = []
            for history in self.execution_history.values():
                all_records.extend(history)
            return sorted(all_records, key=lambda x: x.start_time, reverse=True)[:limit]

    def get_next_run_time(self, report_id: str) -> Optional[datetime]:
        """获取下次运行时间"""
        try:
            job_id = f"report_{report_id}"
            job = self.scheduler.get_job(job_id)
            if job:
                return job.next_run_time
            return None
        except Exception as e:
            logger.error(f"获取下次运行时间失败: {e}")
            return None

    def list_scheduled_jobs(self) -> List[Dict[str, Any]]:
        """列出所有计划任务"""
        jobs = []
        for job in self.scheduler.get_jobs():
            report_id = job.id.replace("report_", "")
            status = self.job_status.get(job.id, JobStatus.PENDING)
            next_run = job.next_run_time

            jobs.append({
                "report_id": report_id,
                "job_id": job.id,
                "next_run_time": next_run.isoformat() if next_run else None,
                "status": status.value,
                "max_instances": job.max_instances
            })

        return jobs

    async def _execute_report_job(
        self,
        report_id: str,
        execution: Optional[JobExecutionRecord] = None
    ):
        """执行报告生成任务"""
        if execution is None:
            execution = self._create_execution_record(report_id)

        job_id = f"report_{report_id}"
        self.job_status[job_id] = JobStatus.RUNNING

        try:
            logger.info(f"开始执行报告任务: {report_id}")

            # 获取报告参数
            report_params = self.params_manager.get_params(report_id)
            if not report_params:
                raise ValueError(f"报告参数不存在: {report_id}")

            # 生成报告
            start_time = datetime.now()

            # 使用线程池执行
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                self._generate_report_sync,
                report_params
            )

            execution.output_path = result
            execution.status = JobStatus.SUCCESS
            execution.message = "报告生成成功"

            end_time = datetime.now()
            execution.end_time = end_time.isoformat()
            execution.execution_time = (end_time - start_time).total_seconds()

            logger.info(f"报告任务执行成功: {report_id}, 耗时: {execution.execution_time:.2f}秒")

        except Exception as e:
            error_msg = str(e)
            execution.status = JobStatus.FAILED
            execution.error = error_msg
            execution.message = f"报告生成失败: {error_msg}"
            execution.end_time = datetime.now().isoformat()

            # 错误处理和重试
            report_params = self.params_manager.get_params(report_id)
            if report_params and report_params.schedule:
                max_retries = report_params.schedule.max_retries
                if execution.retry_count < max_retries:
                    execution.status = JobStatus.RETRY
                    execution.retry_count += 1
                    execution.message = f"第{execution.retry_count}次重试失败，将在{report_params.schedule.retry_delay}秒后重试"

                    # 延迟重试
                    await asyncio.sleep(report_params.schedule.retry_delay)
                    await self._execute_report_job(report_id, execution)
                    return

            logger.error(f"报告任务执行失败: {report_id}\n{traceback.format_exc()}")

        finally:
            # 保存执行记录
            self._save_execution_record(execution)
            self.job_status[job_id] = execution.status

    def _generate_report_sync(self, report_params: ReportParams) -> str:
        """同步生成报告"""
        try:
            # 生成输出路径
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{report_params.report_id}_{timestamp}.html"
            output_path = Path(report_params.output_path).parent / output_filename
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # 生成报告
            self.generator.generate_report(
                report_params=report_params,
                output_path=str(output_path)
            )

            return str(output_path)

        except Exception as e:
            logger.error(f"同步生成报告失败: {e}")
            raise

    def _create_execution_record(self, report_id: str) -> JobExecutionRecord:
        """创建执行记录"""
        execution = JobExecutionRecord(
            job_id=f"report_{report_id}",
            report_id=report_id,
            start_time=datetime.now().isoformat()
        )

        if report_id not in self.execution_history:
            self.execution_history[report_id] = []

        return execution

    def _save_execution_record(self, execution: JobExecutionRecord):
        """保存执行记录"""
        if execution.report_id not in self.execution_history:
            self.execution_history[execution.report_id] = []

        self.execution_history[execution.report_id].append(execution)

        # 保存到文件
        history_file = self.storage_path / f"{execution.report_id}_history.json"
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(
                [asdict(record) for record in self.execution_history[execution.report_id]],
                f,
                ensure_ascii=False,
                indent=2
            )

    def _load_execution_history(self):
        """加载执行历史"""
        for file_path in self.storage_path.glob("*_history.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    report_id = file_path.stem.replace("_history", "")

                    self.execution_history[report_id] = []
                    for item in data:
                        record = JobExecutionRecord(**item)
                        self.execution_history[report_id].append(record)

            except Exception as e:
                logger.error(f"加载执行历史失败: {file_path}, {e}")

    def _reload_scheduled_jobs(self):
        """重新加载所有计划任务"""
        for report_params in self.params_manager.get_all_params():
            if report_params.schedule and report_params.schedule.enabled:
                self.add_report_job(report_params.report_id, report_params)

    def _job_executed(self, event: JobExecutionEvent):
        """任务执行事件监听"""
        job_id = event.job_id
        report_id = job_id.replace("report_", "")

        if event.exception:
            logger.error(f"任务执行异常: {job_id}, {event.exception}")
        else:
            logger.info(f"任务执行完成: {job_id}")

    def cleanup_old_executions(self, days: int = 30):
        """清理旧的执行记录"""
        cutoff_date = datetime.now() - timedelta(days=days)

        for report_id, history in self.execution_history.items():
            # 保留最近的记录
            recent_records = [
                record for record in history
                if datetime.fromisoformat(record.start_time) > cutoff_date
            ]

            if len(recent_records) < len(history):
                self.execution_history[report_id] = recent_records

                # 保存到文件
                history_file = self.storage_path / f"{report_id}_history.json"
                with open(history_file, "w", encoding="utf-8") as f:
                    json.dump(
                        [asdict(record) for record in recent_records],
                        f,
                        ensure_ascii=False,
                        indent=2
                    )

                logger.info(f"已清理报告 {report_id} 的旧执行记录")

    def get_statistics(self) -> Dict[str, Any]:
        """获取调度器统计信息"""
        total_jobs = len(self.scheduler.get_jobs())
        total_executions = sum(len(history) for history in self.execution_history.values())

        # 统计执行状态
        status_counts = {
            "PENDING": 0,
            "RUNNING": 0,
            "SUCCESS": 0,
            "FAILED": 0,
            "CANCELLED": 0,
            "RETRY": 0
        }

        for history in self.execution_history.values():
            for record in history:
                status_counts[record.status.value.upper()] += 1

        # 计算平均执行时间
        success_records = [
            record for history in self.execution_history.values()
            for record in history if record.status == JobStatus.SUCCESS
        ]

        avg_execution_time = 0
        if success_records:
            avg_execution_time = sum(r.execution_time for r in success_records) / len(success_records)

        return {
            "total_scheduled_jobs": total_jobs,
            "total_executions": total_executions,
            "status_distribution": status_counts,
            "average_execution_time": round(avg_execution_time, 2),
            "scheduler_running": self.scheduler.running
        }


# 创建全局调度器实例
_scheduler_instance: Optional[ReportScheduler] = None


def get_scheduler() -> ReportScheduler:
    """获取调度器实例"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = ReportScheduler()
    return _scheduler_instance


def start_scheduler():
    """启动调度器（简化接口）"""
    scheduler = get_scheduler()
    scheduler.start()
    return scheduler


if __name__ == "__main__":
    # 示例：使用调度器
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 创建并启动调度器
    scheduler = ReportScheduler()
    scheduler.start()

    # 添加示例任务
    from .params import create_default_params

    default_params = create_default_params(
        report_id="daily_summary",
        name="每日交易摘要"
    )
    default_params.schedule.cron_expression = "0 */6 * * *"  # 每6小时执行一次

    # 添加到参数管理器
    params_manager = get_params_manager()
    params_manager.add_params(default_params)

    # 添加到调度器
    scheduler.add_report_job("daily_summary")

    # 立即运行一次
    execution = scheduler.run_report_now("daily_summary")
    print(f"执行记录: {execution.execution_id}")

    # 查看下次运行时间
    next_run = scheduler.get_next_run_time("daily_summary")
    print(f"下次运行时间: {next_run}")

    # 列出所有任务
    jobs = scheduler.list_scheduled_jobs()
    print(f"计划任务: {json.dumps(jobs, indent=2, ensure_ascii=False)}")

    # 获取统计信息
    stats = scheduler.get_statistics()
    print(f"统计信息: {json.dumps(stats, indent=2, ensure_ascii=False)}")

    # 保持运行
    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        scheduler.shutdown()
