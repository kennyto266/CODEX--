"""
报告生成系统

提供自动化报告生成、调度、邮件发送和归档功能。

主要模块：
- params: 自定义报告参数配置
- scheduler: 定时报告生成器
- email_delivery: 邮件自动发送
- archive: 报告归档和版本管理
"""

# 暂时只导入params模块，避免依赖问题
try:
    from .params import (
        ReportParams,
        ReportParamsManager,
        TemplateConfig,
        DataSourceConfig,
        ChartConfig,
        EmailConfig,
        ScheduleConfig,
        get_params_manager,
        create_default_params,
        ParamsValidator
    )
    PARAMS_AVAILABLE = True
except ImportError:
    PARAMS_AVAILABLE = False

__version__ = "3.0.0"
__author__ = "Quant Trading System"

__all__ = [
    "ReportParams",
    "ReportParamsManager",
    "TemplateConfig",
    "DataSourceConfig",
    "ChartConfig",
    "EmailConfig",
    "ScheduleConfig",
    "get_params_manager",
    "create_default_params",
    "ParamsValidator",
]

# 创建全局参数管理器实例
_params_manager_instance = None

def get_params_manager():
    """获取参数管理器实例"""
    global _params_manager_instance
    if _params_manager_instance is None and PARAMS_AVAILABLE:
        _params_manager_instance = ReportParamsManager()
    return _params_manager_instance

def create_default_params(
    report_id: str,
    name: str,
    symbol: str = "0700.HK",
    output_path: str = "reports"
):
    """创建默认的报告参数配置"""
    template = TemplateConfig(
        name="默认模板",
        path="templates/default.html",
        format="html",
        variables={"title": name}
    )

    data_source = DataSourceConfig(
        type="hkex",
        symbols=[symbol],
        start_date="2020-01-01",
        end_date="2024-01-01"
    )

    schedule = ScheduleConfig(
        cron_expression="0 0 9 * * 1-5",  # 每周一到周五上午9点
        enabled=True
    )

    return ReportParams(
        report_id=report_id,
        name=name,
        template=template,
        data_source=data_source,
        schedule=schedule,
        output_path=f"{output_path}/{report_id}_{datetime.now().strftime('%Y%m%d')}.html"
    )
