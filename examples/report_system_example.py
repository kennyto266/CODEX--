"""
报告系统使用示例

演示如何使用自动化报告调度和邮件发送系统
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime, timedelta

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from reports.params import (
    ReportParams,
    EmailConfig,
    ScheduleConfig,
    get_params_manager,
    create_default_params
)
from reports.scheduler import get_scheduler
from reports.email_delivery import get_email_delivery
from reports.archive import get_archive_manager
from reports import ReportSystem, setup_daily_report, setup_weekly_report


def example_1_basic_setup():
    """示例1: 基本设置"""
    print("\n=== 示例1: 基本设置 ===")

    # 创建报告系统
    report_system = ReportSystem()

    # 设置每日报告
    success = setup_daily_report(
        report_id="daily_portfolio",
        name="每日投资组合报告",
        symbol="0700.HK",
        recipients=["trader@example.com"]
    )

    print(f"每日报告设置成功: {success}")

    # 设置每周报告
    success = setup_weekly_report(
        report_id="weekly_analysis",
        name="每周分析报告",
        symbol="0388.HK",
        recipients=["analyst@example.com"]
    )

    print(f"每周报告设置成功: {success}")


def example_2_custom_config():
    """示例2: 自定义配置"""
    print("\n=== 示例2: 自定义配置 ===")

    params_manager = get_params_manager()

    # 创建自定义报告参数
    email_config = EmailConfig(
        smtp_server="smtp.qq.com",
        smtp_port=587,
        username="your_email@qq.com",
        password="your_password",
        recipients=["team@example.com", "manager@example.com"],
        cc=["support@example.com"],
        subject_template="【重要】{name} - {report_date}",
        signature="量化交易系统 - 自动发送",
        use_tls=True
    )

    schedule_config = ScheduleConfig(
        cron_expression="0 18 1-5 * *",  # 每周一到周五下午6点
        timezone="Asia/Hong_Kong",
        enabled=True,
        max_retries=3,
        retry_delay=300
    )

    report_params = create_default_params(
        report_id="evening_summary",
        name="晚间交易摘要",
        symbol="0700.HK",
        output_path="reports/evening"
    )

    # 应用自定义配置
    report_params.email = email_config
    report_params.schedule = schedule_config

    # 添加到系统
    success = params_manager.add_params(report_params)
    print(f"自定义报告添加成功: {success}")


def example_3_scheduled_execution():
    """示例3: 定时执行"""
    print("\n=== 示例3: 定时执行 ===")

    async def main():
        # 获取调度器
        scheduler = get_scheduler()

        # 启动调度器
        scheduler.start()
        print("调度器已启动")

        # 添加报告任务
        params_manager = get_params_manager()
        params = create_default_params(
            report_id="hourly_update",
            name="每小时更新",
            symbol="0700.HK",
            output_path="reports/hourly"
        )

        # 设置为每小时执行
        params.schedule.cron_expression = "0 * * * *"  # 每小时
        params.schedule.enabled = True

        params_manager.add_params(params)
        scheduler.add_report_job("hourly_update")
        print("每小时更新任务已添加")

        # 立即运行一次
        execution = scheduler.run_report_now("hourly_update")
        if execution:
            print(f"立即执行任务ID: {execution.execution_id}")
            print("任务执行中...")

            # 等待完成
            await asyncio.sleep(3)

            # 查看执行历史
            history = scheduler.get_execution_history("hourly_update", limit=1)
            if history:
                latest = history[0]
                print(f"执行状态: {latest.status.value}")
                print(f"输出路径: {latest.output_path}")

        # 查看所有计划任务
        jobs = scheduler.list_scheduled_jobs()
        print(f"\n当前计划任务数量: {len(jobs)}")
        for job in jobs:
            print(f"  - {job['report_id']}: 下次运行 {job['next_run_time']}")

    # 运行异步代码
    asyncio.run(main())


def example_4_email_sending():
    """示例4: 邮件发送"""
    print("\n=== 示例4: 邮件发送 ===")

    email_delivery = get_email_delivery()

    # 配置邮件
    email_config = EmailConfig(
        smtp_server="smtp.gmail.com",
        smtp_port=587,
        username="your_email@gmail.com",
        password="your_app_password",
        recipients=["recipient@example.com"],
        use_tls=True,
        signature="量化交易系统"
    )

    email_delivery.set_config(email_config)

    # 测试SMTP连接
    if email_delivery.test_connection():
        print("SMTP连接成功")

        # 发送简单邮件
        result = email_delivery.send_email(
            subject="测试邮件",
            body="这是一封测试邮件，用于验证邮件配置。",
            body_html=False
        )
        print(f"简单邮件发送: {result.success} - {result.message}")

        # 发送HTML邮件
        result = email_delivery.send_email(
            subject="HTML邮件测试",
            body="<h1 style='color: blue;'>这是HTML邮件</h1><p>支持HTML格式</p>",
            body_html=True
        )
        print(f"HTML邮件发送: {result.success}")

        # 获取发送统计
        stats = email_delivery.get_statistics()
        print(f"发送统计: 成功 {stats['success_count']}, 失败 {stats['failed_count']}")

    else:
        print("SMTP连接失败 - 请检查配置")


def example_5_archive_management():
    """示例5: 归档管理"""
    print("\n=== 示例5: 归档管理 ===")

    # 创建测试报告
    test_report = Path("example_test_report.html")
    with open(test_report, "w", encoding="utf-8") as f:
        f.write("""
        <html>
        <head><title>测试报告</title></head>
        <body>
            <h1>量化交易报告</h1>
            <p>报告日期: 2024-01-01</p>
            <p>股票代码: 0700.HK</p>
            <p>收益率: 5.23%</p>
        </body>
        </html>
        """)

    # 获取归档管理器
    archive_manager = get_archive_manager()

    # 归档报告
    print(f"归档报告: {test_report}")
    archived = archive_manager.archive_report(
        report_path=str(test_report),
        report_id="test_report",
        version="v1.0.0",
        format="zip"
    )

    if archived:
        print(f"  ✓ 归档成功")
        print(f"    版本: {archived.version}")
        print(f"    路径: {archived.archive_path}")
        print(f"    大小: {archived.size} -> {archived.compressed_size} bytes")

    # 列出归档报告
    reports = archive_manager.list_archived_reports()
    print(f"\n归档报告总数: {len(reports)}")

    # 获取统计信息
    stats = archive_manager.get_statistics()
    print(f"归档统计:")
    print(f"  总归档数: {stats['total_archived_reports']}")
    print(f"  活跃数: {stats['active_reports']}")
    print(f"  总大小: {stats['total_size_gb']} GB")

    # 搜索报告
    search_results = archive_manager.search_reports("test")
    print(f"\n搜索'test'结果: {len(search_results)} 个")

    # 恢复报告
    if reports:
        first_report = reports[0]
        restored_path = archive_manager.restore_report(
            first_report.report_id,
            first_report.version
        )
        if restored_path:
            print(f"  ✓ 报告已恢复: {restored_path}")

    # 清理测试文件
    if test_report.exists():
        test_report.unlink()
    if Path("reports/restored").exists():
        import shutil
        shutil.rmtree("reports/restored")


def example_6_full_workflow():
    """示例6: 完整工作流"""
    print("\n=== 示例6: 完整工作流 ===")

    # 创建测试报告
    test_report = Path("workflow_test.html")
    with open(test_report, "w", encoding="utf-8") as f:
        f.write("<html><body><h1>工作流测试</h1></body></html>")

    # 1. 参数管理
    params_manager = get_params_manager()
    params = create_default_params(
        report_id="workflow_test",
        name="工作流测试报告",
        output_path="reports"
    )

    # 添加邮件配置
    params.email = EmailConfig(
        smtp_server="smtp.gmail.com",
        smtp_port=587,
        username="test@gmail.com",
        password="password",
        recipients=["test@example.com"]
    )

    params_manager.add_params(params)
    print("1. ✓ 报告参数已配置")

    # 2. 立即执行
    scheduler = get_scheduler()
    execution = scheduler.run_report_now("workflow_test")
    if execution:
        print(f"2. ✓ 报告已执行 (ID: {execution.execution_id})")

    # 3. 发送邮件
    email_delivery = get_email_delivery()
    email_delivery.set_config(params.email)
    result = email_delivery.send_email(
        subject="工作流测试",
        body="这是工作流测试邮件",
        body_html=False
    )
    print(f"3. {'✓' if result.success else '✗'} 邮件发送: {result.message}")

    # 4. 归档报告
    archive_manager = get_archive_manager()
    archived = archive_manager.archive_report(
        report_path=str(test_report),
        report_id="workflow_test"
    )
    if archived:
        print(f"4. ✓ 报告已归档: {archived.version}")

    # 5. 清理测试文件
    if test_report.exists():
        test_report.unlink()

    print("\n完整工作流演示结束")


def example_7_multiple_reports():
    """示例7: 多报告管理"""
    print("\n=== 示例7: 多报告管理 ===")

    params_manager = get_params_manager()
    scheduler = get_scheduler()
    email_delivery = get_email_delivery()
    archive_manager = get_archive_manager()

    # 股票列表
    stocks = [
        ("0700.HK", "腾讯"),
        ("0388.HK", "港交所"),
        ("0939.HK", "建行")
    ]

    # 为每只股票创建报告
    for symbol, name in stocks:
        report_id = f"daily_{symbol.replace('.', '_')}"

        # 创建参数
        params = create_default_params(
            report_id=report_id,
            name=f"每日{name}报告",
            symbol=symbol,
            output_path="reports/daily"
        )

        # 设置邮件
        params.email = EmailConfig(
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            username="trader@example.com",
            password="password",
            recipients=["portfolio@example.com"],
            subject_template=f"{name}日报 - {{{{ report_date }}}}"
        )

        # 设置调度
        params.schedule.cron_expression = "0 9 * * 1-5"  # 每工作日上午9点

        # 添加到系统
        params_manager.add_params(params)
        scheduler.add_report_job(report_id)

        print(f"✓ 已设置 {name} ({symbol}) 的日报")

    # 查看所有报告
    all_params = params_manager.get_all_params()
    print(f"\n系统共管理 {len(all_params)} 个报告")

    # 获取调度器统计
    stats = scheduler.get_statistics()
    print(f"计划任务数: {stats['total_scheduled_jobs']}")


if __name__ == "__main__":
    print("=" * 60)
    print("自动化报告调度和邮件发送系统 - 使用示例")
    print("=" * 60)

    # 运行所有示例
    try:
        example_1_basic_setup()
        example_2_custom_config()
        example_3_scheduled_execution()
        example_4_email_sending()
        example_5_archive_management()
        example_6_full_workflow()
        example_7_multiple_reports()

        print("\n" + "=" * 60)
        print("所有示例运行完成！")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\n用户中断操作")
    except Exception as e:
        print(f"\n\n运行错误: {e}")
        import traceback
        traceback.print_exc()
