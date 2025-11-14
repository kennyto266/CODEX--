#!/usr/bin/env python3
"""
HKMA HIBOR数据适配器 - 演示脚本
展示如何使用5个HKMA模块进行完整的HIBOR数据处理
"""

import asyncio
import json
import logging
from datetime import date, datetime, timedelta
from typing import Dict, Any

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 导入HKMA模块
from src.data_adapters.hkma_hibor import HKMAHibiorAdapter
from src.data_adapters.hibor_validator import HibiorDataValidator
from src.data_adapters.hkma_scheduler import TaskScheduler, hibor_update_handler
from src.data_adapters.hkma_error_handler import HKMAErrorHandler
from src.data_adapters.hkma_monitor import HKMAMonitor


class HKMASystemDemo:
    """HKMA HIBOR系统演示类"""

    def __init__(self):
        self.adapter = None
        self.validator = None
        self.scheduler = None
        self.error_handler = None
        self.monitor = None

    async def initialize(self):
        """初始化所有组件"""
        logger.info("初始化HKMA HIBOR系统...")

        # 创建适配器
        self.adapter = HKMAHibiorAdapter(config={
            'timeout': 30,
            'max_retries': 3
        })

        # 创建验证器
        self.validator = HibiorDataValidator(config={
            'strict_mode': False,
            'check_trends': True
        })

        # 创建调度器
        self.scheduler = TaskScheduler(config={
            'scheduler_interval': 60,
            'max_concurrent_tasks': 3
        })
        self.scheduler.register_handler("daily_update", hibor_update_handler)
        self.scheduler.register_handler("historical_update", hibor_update_handler)

        # 创建错误处理器
        self.error_handler = HKMAErrorHandler(config={
            'degraded_mode_threshold': 5
        })

        # 创建监控器
        self.monitor = HKMAMonitor(config={
            'monitor_interval': 300,
            'auto_monitoring': True
        })

        # 添加告警回调
        self.monitor.add_alert_callback(self._alert_callback)

        logger.info("所有组件初始化完成")

    async def _alert_callback(self, alert):
        """告警回调函数"""
        logger.warning(
            f"🚨 数据质量告警 [{alert.level.value.upper()}]: "
            f"{alert.message} (值: {alert.value:.1f}, 阈值: {alert.threshold:.1f})"
        )

    async def demo_fetch_latest_data(self):
        """演示：获取最新HIBOR数据"""
        logger.info("\n" + "=" * 60)
        logger.info("演示1: 获取最新HIBOR数据")
        logger.info("=" * 60)

        try:
            async with self.adapter as adapter:
                # 尝试获取最新HIBOR数据
                result = await self.error_handler.execute_with_retry(
                    adapter.fetch_latest_hibor,
                    max_retries=3,
                    context={'operation': 'fetch_latest'}
                )

                if result:
                    logger.info("✅ 成功获取最新HIBOR数据:")
                    logger.info(f"  日期: {result.get('date')}")
                    if 'data' in result:
                        for key, value in result['data'].items():
                            if value is not None:
                                logger.info(f"  {key}: {value}")
                    return result
                else:
                    logger.warning("⚠️ 未能获取HIBOR数据（可能是网络问题）")
                    return None

        except Exception as e:
            logger.error(f"❌ 获取数据失败: {e}")
            return None

    async def demo_validate_data(self, data: Dict[str, Any]):
        """演示：验证数据质量"""
        logger.info("\n" + "=" * 60)
        logger.info("演示2: 验证数据质量")
        logger.info("=" * 60)

        if not data:
            logger.warning("⚠️ 没有数据可验证")
            return None

        try:
            # 验证数据
            result = self.validator.validate_hibor_data(data, term='1m')

            logger.info(f"验证结果:")
            logger.info(f"  总体状态: {'✅ 有效' if result.is_valid else '❌ 无效'}")
            logger.info(f"  有效记录: {result.valid_count}")
            logger.info(f"  无效记录: {result.invalid_count}")
            logger.info(f"  警告数量: {result.warning_count}")
            logger.info(f"  总问题数: {result.total_issues}")

            if result.issues:
                logger.info("\n问题详情:")
                for issue in result.issues[:5]:  # 只显示前5个问题
                    icon = {
                        'info': 'ℹ️',
                        'warning': '⚠️',
                        'error': '❌',
                        'critical': '🚨'
                    }.get(issue.severity.value, '•')

                    logger.info(
                        f"  {icon} [{issue.severity.value.upper()}] "
                        f"{issue.field}: {issue.message}"
                    )

                    if issue.value is not None:
                        logger.info(f"    实际值: {issue.value}")
                    if issue.expected is not None:
                        logger.info(f"    期望值: {issue.expected}")

            return result

        except Exception as e:
            logger.error(f"❌ 数据验证失败: {e}")
            return None

    async def demo_monitor_data(self, data: Dict[str, Any]):
        """演示：监控数据质量"""
        logger.info("\n" + "=" * 60)
        logger.info("演示3: 监控数据质量")
        logger.info("=" * 60)

        if not data:
            logger.warning("⚠️ 没有数据可监控")
            return None

        try:
            # 添加数据点到监控器
            await self.monitor.add_data_point(data)

            # 计算质量指标
            metrics = await self.monitor.calculate_quality_metrics()

            logger.info(f"数据质量指标:")
            logger.info(f"  总体评分: {metrics.overall_score:.1f}/100")
            logger.info(f"  质量等级: {metrics.get_quality_level().value.upper()}")

            detailed_metrics = {
                '新鲜度': metrics.freshness_score,
                '完整性': metrics.completeness_score,
                '准确性': metrics.accuracy_score,
                '一致性': metrics.consistency_score,
                '趋势': metrics.trend_score,
                '波动性': metrics.volatility_score,
                '可用性': metrics.availability_score
            }

            logger.info("\n详细指标:")
            for name, score in detailed_metrics.items():
                bar = '█' * int(score / 10) + '░' * (10 - int(score / 10))
                logger.info(f"  {name}: [{bar}] {score:.1f}")

            logger.info(f"\n统计信息:")
            logger.info(f"  数据点数: {metrics.data_points}")
            logger.info(f"  缺失值: {metrics.missing_count}")
            logger.info(f"  异常值: {metrics.anomalies_count}")

            # 生成质量报告
            report = await self.monitor.get_quality_report()
            logger.info(f"\n建议:")
            for rec in report['recommendations']:
                logger.info(f"  • {rec}")

            return metrics

        except Exception as e:
            logger.error(f"❌ 数据监控失败: {e}")
            return None

    async def demo_schedule_tasks(self):
        """演示：调度定时任务"""
        logger.info("\n" + "=" * 60)
        logger.info("演示4: 调度定时任务")
        logger.info("=" * 60)

        try:
            # 计划每日更新任务
            task_id1 = await self.scheduler.schedule_daily_update(
                "hibor_morning",
                "08:00",
                {'frequency': 'daily'},
                priority=2  # HIGH
            )
            logger.info(f"✅ 已计划每日更新任务: {task_id1}")

            # 计划历史数据更新任务
            start_date = date.today() - timedelta(days=30)
            end_date = date.today()
            task_id2 = await self.scheduler.schedule_historical_data_update(
                start_date,
                end_date,
                priority=1  # NORMAL
            )
            logger.info(f"✅ 已计划历史数据更新任务: {task_id2}")

            # 查看任务列表
            tasks = await self.scheduler.list_tasks(limit=10)
            logger.info(f"\n当前任务列表 ({len(tasks)} 个):")
            for task in tasks:
                status_icon = {
                    'pending': '⏳',
                    'running': '🔄',
                    'completed': '✅',
                    'failed': '❌',
                    'cancelled': '🚫'
                }.get(task['status'], '•')

                priority_icon = {
                    1: '🔵',
                    2: '🟡',
                    3: '🟠',
                    4: '🔴'
                }.get(task['priority'], '•')

                logger.info(
                    f"  {status_icon} {priority_icon} {task['name']} "
                    f"({task['type']}) - {task['status']}"
                )

            # 获取统计信息
            stats = self.scheduler.get_statistics()
            logger.info(f"\n调度器统计:")
            logger.info(f"  总任务: {stats['total_tasks']}")
            logger.info(f"  待执行: {stats['pending_tasks']}")
            logger.info(f"  运行中: {stats['running_tasks']}")
            logger.info(f"  已完成: {stats['completed_tasks']}")
            logger.info(f"  已失败: {stats['failed_tasks']}")

            return [task_id1, task_id2]

        except Exception as e:
            logger.error(f"❌ 任务调度失败: {e}")
            return []

    async def demo_error_handling(self):
        """演示：错误处理和重试"""
        logger.info("\n" + "=" * 60)
        logger.info("演示5: 错误处理和重试")
        logger.info("=" * 60)

        # 模拟一个会失败的函数
        attempt_count = 0

        async def flaky_function():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise ConnectionError("模拟网络错误")
            return f"第{attempt_count}次尝试成功"

        try:
            logger.info("测试重试机制...")
            result = await self.error_handler.execute_with_retry(
                flaky_function,
                max_retries=5,
                context={'operation': 'test_retry'}
            )
            logger.info(f"✅ 重试成功: {result}")

        except Exception as e:
            logger.error(f"❌ 重试失败: {e}")

        # 获取错误统计
        summary = self.error_handler.get_error_summary()
        logger.info(f"\n错误统计:")
        logger.info(f"  总错误数: {summary['total_errors']}")
        logger.info(f"  错误类型: {summary['unique_error_types']}")

        if summary['most_common_error']:
            logger.info(
                f"  最常见错误: {summary['most_common_error']['type']} "
                f"({summary['most_common_error']['count']} 次)"
            )

        return summary

    async def demo_full_workflow(self):
        """演示：完整工作流程"""
        logger.info("\n" + "=" * 60)
        logger.info("演示6: 完整工作流程")
        logger.info("=" * 60)

        try:
            # 1. 获取数据
            logger.info("步骤1: 获取数据...")
            data = await self.demo_fetch_latest_data()

            # 2. 验证数据
            logger.info("步骤2: 验证数据...")
            validation_result = await self.demo_validate_data(data)

            # 3. 监控数据
            logger.info("步骤3: 监控数据...")
            metrics = await self.demo_monitor_data(data)

            # 4. 生成报告
            logger.info("步骤4: 生成报告...")
            report = await self.monitor.get_quality_report()
            logger.info(f"\n📊 最终质量报告:")
            logger.info(f"  总体评分: {report['overall_score']:.1f}/100")
            logger.info(f"  质量等级: {report['quality_level'].upper()}")
            logger.info(f"  质量趋势: {report['quality_trend']}")
            logger.info(f"  活跃告警: {report['active_alerts']}")

            # 5. 检查质量趋势
            logger.info("步骤5: 分析趋势...")
            trend = self.monitor.get_quality_trend(days=7)
            logger.info(f"\n📈 质量趋势 (7天):")
            logger.info(f"  趋势方向: {trend['trend']}")
            logger.info(f"  平均评分: {trend['avg_score']:.1f}")
            logger.info(f"  最高评分: {trend['max_score']:.1f}")
            logger.info(f"  最低评分: {trend['min_score']:.1f}")

            logger.info("\n✅ 完整工作流程演示完成")

        except Exception as e:
            logger.error(f"❌ 工作流程失败: {e}")
            import traceback
            traceback.print_exc()

    async def run_all_demos(self):
        """运行所有演示"""
        logger.info("\n" + "=" * 60)
        logger.info("🚀 HKMA HIBOR数据适配器 - 完整演示")
        logger.info("=" * 60)

        # 初始化
        await self.initialize()

        # 演示各个功能
        await self.demo_schedule_tasks()
        await self.demo_error_handling()
        await self.demo_full_workflow()

        logger.info("\n" + "=" * 60)
        logger.info("✨ 所有演示完成")
        logger.info("=" * 60)


async def main():
    """主函数"""
    demo = HKMASystemDemo()
    await demo.run_all_demos()


if __name__ == "__main__":
    # 运行演示
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n演示被用户中断")
    except Exception as e:
        logger.error(f"\n演示运行失败: {e}")
        import traceback
        traceback.print_exc()
