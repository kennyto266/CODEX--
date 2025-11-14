"""
自定义报告参数配置模块

提供灵活的参数配置系统，支持：
- 模板参数配置
- 数据源参数
- 图表参数
- 邮件参数
- 调度参数
- 参数验证
"""

import json
import yaml
import os
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass, asdict, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class TemplateConfig:
    """模板配置"""
    name: str
    path: str
    format: str = "html"  # html, pdf, excel
    variables: Dict[str, Any] = field(default_factory=dict)
    custom_filters: List[str] = field(default_factory=list)


@dataclass
class DataSourceConfig:
    """数据源配置"""
    type: str  # hkex, yahoo, alpha_vantage
    symbols: List[str]
    start_date: str
    end_date: str
    fields: List[str] = field(default_factory=lambda: ["open", "high", "low", "close", "volume"])
    api_key: Optional[str] = None
    timeout: int = 30
    cache_enabled: bool = True


@dataclass
class ChartConfig:
    """图表配置"""
    width: int = 1200
    height: int = 800
    theme: str = "plotly_white"
    color_scheme: str = "Viridis"
    show_grid: bool = True
    show_legend: bool = True
    font_size: int = 12
    title_size: int = 16
    margin: Dict[str, int] = field(default_factory=lambda: {"l": 50, "r": 50, "t": 50, "b": 50})


@dataclass
class EmailConfig:
    """邮件配置"""
    smtp_server: str
    username: str
    password: str
    recipients: List[str]
    smtp_port: int = 587
    use_tls: bool = True
    cc: List[str] = field(default_factory=list)
    bcc: List[str] = field(default_factory=list)
    subject_template: str = "量化交易报告 - {report_date}"
    body_template: str = ""
    signature: str = ""
    reply_to: Optional[str] = None
    template_variables: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScheduleConfig:
    """调度配置"""
    cron_expression: str
    timezone: str = "Asia/Hong_Kong"
    enabled: bool = True
    max_retries: int = 3
    retry_delay: int = 60  # seconds
    priority: int = 1  # 1-10, higher is more important
    depends_on: List[str] = field(default_factory=list)
    timeout: int = 3600  # seconds


@dataclass
class ReportParams:
    """完整报告参数配置"""
    report_id: str
    name: str
    template: TemplateConfig
    data_source: DataSourceConfig
    output_path: str
    description: Optional[str] = None
    chart: ChartConfig = field(default_factory=ChartConfig)
    email: Optional[EmailConfig] = None
    schedule: Optional[ScheduleConfig] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


class ReportParamsManager:
    """报告参数管理器"""

    def __init__(self, config_dir: str = "config/reports"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.params_db: Dict[str, ReportParams] = {}
        self._load_all_params()

    def _load_all_params(self):
        """加载所有参数配置"""
        self.params_db = {}
        for file_path in self.config_dir.glob("*.yaml"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if data:
                        params = self._dict_to_params(data)
                        self.params_db[params.report_id] = params
                        logger.info(f"已加载报告配置: {params.report_id}")
            except Exception as e:
                logger.error(f"加载配置文件失败 {file_path}: {e}")

    def _dict_to_params(self, data: Dict[str, Any]) -> ReportParams:
        """将字典转换为ReportParams对象"""
        # 转换嵌套对象
        data['template'] = TemplateConfig(**data.get('template', {}))
        data['data_source'] = DataSourceConfig(**data.get('data_source', {}))
        data['chart'] = ChartConfig(**data.get('chart', {}))

        if data.get('email'):
            data['email'] = EmailConfig(**data['email'])

        if data.get('schedule'):
            data['schedule'] = ScheduleConfig(**data['schedule'])

        return ReportParams(**data)

    def _params_to_dict(self, params: ReportParams) -> Dict[str, Any]:
        """将ReportParams对象转换为字典"""
        return asdict(params)

    def _save_to_file(self, params: ReportParams):
        """保存配置到文件"""
        file_path = self.config_dir / f"{params.report_id}.yaml"
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(self._params_to_dict(params), f, default_flow_style=False, allow_unicode=True)
        logger.info(f"已保存报告配置: {params.report_id}")

    def add_params(self, params: ReportParams) -> bool:
        """添加报告参数"""
        try:
            if params.report_id in self.params_db:
                logger.warning(f"报告ID已存在: {params.report_id}")
                return False

            # 验证配置
            self._validate_params(params)

            # 保存到内存和文件
            self.params_db[params.report_id] = params
            self._save_to_file(params)
            return True
        except Exception as e:
            logger.error(f"添加报告参数失败: {e}")
            return False

    def update_params(self, report_id: str, params: ReportParams) -> bool:
        """更新报告参数"""
        try:
            if report_id not in self.params_db:
                logger.error(f"报告ID不存在: {report_id}")
                return False

            params.report_id = report_id  # 确保ID不变
            params.updated_at = datetime.now().isoformat()

            # 验证配置
            self._validate_params(params)

            # 保存到内存和文件
            self.params_db[report_id] = params
            self._save_to_file(params)
            return True
        except Exception as e:
            logger.error(f"更新报告参数失败: {e}")
            return False

    def get_params(self, report_id: str) -> Optional[ReportParams]:
        """获取报告参数"""
        return self.params_db.get(report_id)

    def get_all_params(self) -> List[ReportParams]:
        """获取所有报告参数"""
        return list(self.params_db.values())

    def delete_params(self, report_id: str) -> bool:
        """删除报告参数"""
        try:
            if report_id not in self.params_db:
                logger.error(f"报告ID不存在: {report_id}")
                return False

            # 从内存中删除
            del self.params_db[report_id]

            # 删除文件
            file_path = self.config_dir / f"{report_id}.yaml"
            if file_path.exists():
                file_path.unlink()

            logger.info(f"已删除报告配置: {report_id}")
            return True
        except Exception as e:
            logger.error(f"删除报告参数失败: {e}")
            return False

    def _validate_params(self, params: ReportParams):
        """验证报告参数"""
        # 验证数据源配置
        if params.data_source:
            if not params.data_source.symbols:
                raise ValueError("股票代码列表不能为空")

        # 验证邮件配置
        if params.email:
            if not params.email.recipients:
                raise ValueError("收件人列表不能为空")

        # 验证输出路径
        output_dir = Path(params.output_path).parent
        if not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)

    def export_params(self, report_id: str, export_format: str = "json") -> Optional[Dict[str, Any]]:
        """导出报告参数"""
        params = self.get_params(report_id)
        if not params:
            return None

        if export_format == "json":
            return self._params_to_dict(params)
        elif export_format == "yaml":
            return yaml.dump(self._params_to_dict(params), default_flow_style=False, allow_unicode=True)
        else:
            raise ValueError(f"不支持的导出格式: {export_format}")

    def clone_params(self, source_id: str, target_id: str, target_name: str) -> Optional[ReportParams]:
        """克隆报告参数"""
        source_params = self.get_params(source_id)
        if not source_params:
            return None

        # 创建新参数
        params_dict = self._params_to_dict(source_params)
        params_dict["report_id"] = target_id
        params_dict["name"] = target_name
        params_dict["created_at"] = datetime.now().isoformat()
        params_dict["updated_at"] = datetime.now().isoformat()

        try:
            return self._dict_to_params(params_dict)
        except Exception as e:
            logger.error(f"克隆报告参数失败: {e}")
            return None


class ParamsValidator:
    """参数验证器"""

    @staticmethod
    def validate_cron_expression(cron: str) -> bool:
        """验证Cron表达式"""
        import re
        # 简单的Cron表达式验证
        parts = cron.split()
        if len(parts) != 6:
            return False

        # 可以是数字、*、*/n 或 a-b 格式
        for part in parts:
            if not re.match(r"^(\*|\*/\d+|\d+(-\d+)?(,\d+(-\d+)?)*)$", part):
                return False
        return True

    @staticmethod
    def validate_email_config(email_config: EmailConfig) -> List[str]:
        """验证邮件配置，返回错误列表"""
        import re
        errors = []

        if not email_config.smtp_server:
            errors.append("SMTP服务器不能为空")

        if not email_config.username:
            errors.append("用户名不能为空")

        if not email_config.password:
            errors.append("密码不能为空")

        if not email_config.recipients:
            errors.append("收件人列表不能为空")
        else:
            email_pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
            for email in email_config.recipients:
                if not email_pattern.match(email):
                    errors.append(f"无效的邮件地址: {email}")

        if email_config.smtp_port <= 0 or email_config.smtp_port > 65535:
            errors.append("SMTP端口号无效")

        return errors

    @staticmethod
    def validate_data_source_config(ds_config: DataSourceConfig) -> List[str]:
        """验证数据源配置"""
        errors = []

        if ds_config.type not in ["hkex", "yahoo", "alpha_vantage"]:
            errors.append(f"不支持的数据源类型: {ds_config.type}")

        if not ds_config.symbols:
            errors.append("股票代码列表不能为空")

        try:
            datetime.fromisoformat(ds_config.start_date)
            datetime.fromisoformat(ds_config.end_date)
        except ValueError:
            errors.append("日期格式必须是YYYY-MM-DD")

        if ds_config.timeout <= 0:
            errors.append("超时时间必须大于0")

        return errors


# 创建全局参数管理器实例
_params_manager_instance: Optional[ReportParamsManager] = None


def get_params_manager() -> ReportParamsManager:
    """获取参数管理器实例"""
    global _params_manager_instance
    if _params_manager_instance is None:
        _params_manager_instance = ReportParamsManager()
    return _params_manager_instance


def create_default_params(
    report_id: str,
    name: str,
    symbol: str = "0700.HK",
    output_path: str = "reports"
) -> ReportParams:
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


if __name__ == "__main__":
    # 示例：创建默认参数
    default_params = create_default_params(
        report_id="daily_summary",
        name="每日交易摘要",
        symbol="0700.HK"
    )

    # 添加到管理器
    params_manager = get_params_manager()
    params_manager.add_params(default_params)

    # 导出为JSON
    export_data = params_manager.export_params("daily_summary", "json")
    print(json.dumps(export_data, indent=2, ensure_ascii=False))
