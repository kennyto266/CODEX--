"""
HTML Report Generator Module
生成响应式HTML报告的核心模块

This module provides:
- Jinja2-based template rendering
- Dynamic content generation
- Multi-page report support
- Theme management
- Export functionality
"""

from typing import Dict, List, Any, Optional, Union
from datetime import datetime, date
from pathlib import Path
import json
import logging
from dataclasses import dataclass, asdict
from jinja2 import Environment, FileSystemLoader, select_autoescape
from jinja2.exceptions import TemplateError

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class ReportMetadata:
    """报告元数据类"""
    title: str
    subtitle: str
    author: str
    created_at: datetime
    version: str = "1.0"
    description: str = ""
    keywords: List[str] = None
    language: str = "zh-CN"

    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []


@dataclass
class ReportConfig:
    """报告配置类"""
    theme: str = "modern"
    dark_mode: bool = False
    show_navigation: bool = True
    show_sidebar: bool = True
    responsive: bool = True
    include_toc: bool = True
    export_formats: List[str] = None
    custom_css: List[str] = None
    custom_js: List[str] = None

    def __post_init__(self):
        if self.export_formats is None:
            self.export_formats = ["html", "pdf"]
        if self.custom_css is None:
            self.custom_css = []
        if self.custom_js is None:
            self.custom_js = []


class HTMLReportGenerator:
    """HTML报告生成器主类"""

    # 主题映射
    THEMES = {
        "modern": {
            "name": "Modern",
            "primary_color": "#3b82f6",
            "secondary_color": "#8b5cf6",
            "success_color": "#10b981",
            "warning_color": "#f59e0b",
            "danger_color": "#ef4444",
            "background": "#ffffff",
            "text_color": "#1f2937"
        },
        "dark": {
            "name": "Dark",
            "primary_color": "#60a5fa",
            "secondary_color": "#a78bfa",
            "success_color": "#34d399",
            "warning_color": "#fbbf24",
            "danger_color": "#f87171",
            "background": "#111827",
            "text_color": "#f9fafb"
        },
        "classic": {
            "name": "Classic",
            "primary_color": "#1e40af",
            "secondary_color": "#7c3aed",
            "success_color": "#059669",
            "warning_color": "#d97706",
            "danger_color": "#dc2626",
            "background": "#f8fafc",
            "text_color": "#0f172a"
        }
    }

    def __init__(
        self,
        template_dir: Optional[Union[str, Path]] = None,
        output_dir: Optional[Union[str, Path]] = None,
        base_url: str = ""
    ):
        """
        初始化HTML报告生成器

        Args:
            template_dir: 模板目录路径
            output_dir: 输出目录路径
            base_url: 基础URL
        """
        self.base_url = base_url
        self.template_dir = Path(template_dir) if template_dir else Path("templates/html")
        self.output_dir = Path(output_dir) if output_dir else Path("reports/output")

        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 设置Jinja2环境
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )

        # 添加自定义过滤器
        self._register_filters()

        logger.info(f"HTML Report Generator initialized with template dir: {self.template_dir}")

    def _register_filters(self):
        """注册自定义Jinja2过滤器"""
        def format_currency(value, currency="HKD", decimals=2):
            """货币格式化过滤器"""
            if value is None:
                return "-"
            return f"{currency} {value:,.{decimals}f}"

        def format_percentage(value, decimals=2):
            """百分比格式化过滤器"""
            if value is None:
                return "-"
            return f"{value:.{decimals}%}"

        def format_number(value, decimals=2):
            """数字格式化过滤器"""
            if value is None:
                return "-"
            return f"{value:,.{decimals}f}"

        def format_date(value, format_str="%Y-%m-%d"):
            """日期格式化过滤器"""
            if isinstance(value, str):
                try:
                    value = datetime.fromisoformat(value)
                except:
                    return value
            if isinstance(value, (date, datetime)):
                return value.strftime(format_str)
            return str(value)

        def format_datetime(value, format_str="%Y-%m-%d %H:%M:%S"):
            """日期时间格式化过滤器"""
            if isinstance(value, str):
                try:
                    value = datetime.fromisoformat(value)
                except:
                    return value
            if isinstance(value, (date, datetime)):
                return value.strftime(format_str)
            return str(value)

        # 注册过滤器
        self.env.filters['currency'] = format_currency
        self.env.filters['percentage'] = format_percentage
        self.env.filters['number'] = format_number
        self.env.filters['date'] = format_date
        self.env.filters['datetime'] = format_datetime

    def generate_report(
        self,
        template_name: str,
        data: Dict[str, Any],
        metadata: ReportMetadata,
        config: ReportConfig,
        output_filename: Optional[str] = None
    ) -> Path:
        """
        生成HTML报告

        Args:
            template_name: 模板名称
            data: 报告数据
            metadata: 报告元数据
            config: 报告配置
            output_filename: 输出文件名

        Returns:
            生成的报告文件路径
        """
        try:
            # 准备模板数据
            template_data = {
                'data': data,
                'metadata': asdict(metadata),
                'config': asdict(config),
                'theme': self.THEMES.get(config.theme, self.THEMES['modern']),
                'current_year': datetime.now().year,
                'base_url': self.base_url
            }

            # 渲染模板
            template = self.env.get_template(template_name)
            html_content = template.render(**template_data)

            # 生成输出文件名
            if not output_filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"report_{metadata.title}_{timestamp}.html"

            # 保存文件
            output_path = self.output_dir / output_filename
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            logger.info(f"Report generated successfully: {output_path}")
            return output_path

        except TemplateError as e:
            logger.error(f"Template rendering error: {e}")
            raise
        except Exception as e:
            logger.error(f"Report generation error: {e}")
            raise

    def generate_multi_page_report(
        self,
        pages: List[Dict[str, Any]],
        metadata: ReportMetadata,
        config: ReportConfig
    ) -> Path:
        """
        生成多页面报告

        Args:
            pages: 页面列表，每个页面包含template、data、title等信息
            metadata: 报告元数据
            config: 报告配置

        Returns:
            生成的报告文件路径
        """
        try:
            # 生成每个页面
            page_files = []
            for i, page in enumerate(pages):
                page_data = {
                    'data': page.get('data', {}),
                    'metadata': asdict(metadata),
                    'config': asdict(config),
                    'theme': self.THEMES.get(config.theme, self.THEMES['modern']),
                    'current_year': datetime.now().year,
                    'base_url': self.base_url,
                    'page_title': page.get('title', f'Page {i+1}'),
                    'page_number': i + 1,
                    'total_pages': len(pages),
                    'is_first_page': i == 0,
                    'is_last_page': i == len(pages) - 1
                }

                template = self.env.get_template(page.get('template', 'base.html'))
                html_content = template.render(**page_data)

                # 保存页面文件
                page_filename = f"page_{i+1}_{page.get('title', 'page').replace(' ', '_')}.html"
                page_path = self.output_dir / page_filename
                with open(page_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)

                page_files.append({
                    'path': page_path,
                    'title': page.get('title', f'Page {i+1}'),
                    'filename': page_filename
                })

            # 生成索引页面
            index_data = {
                'metadata': asdict(metadata),
                'config': asdict(config),
                'theme': self.THEMES.get(config.theme, self.THEMES['modern']),
                'current_year': datetime.now().year,
                'pages': page_files
            }

            index_template = self.env.get_template('index.html')
            index_content = index_template.render(**index_data)

            # 保存索引文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            index_filename = f"report_index_{timestamp}.html"
            index_path = self.output_dir / index_filename
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(index_content)

            logger.info(f"Multi-page report generated successfully: {index_path}")
            return index_path

        except Exception as e:
            logger.error(f"Multi-page report generation error: {e}")
            raise

    def create_dashboard(
        self,
        data: Dict[str, Any],
        metadata: ReportMetadata,
        config: ReportConfig = None
    ) -> Path:
        """
        创建仪表板报告

        Args:
            data: 仪表板数据
            metadata: 报告元数据
            config: 报告配置

        Returns:
            生成的仪表板文件路径
        """
        if config is None:
            config = ReportConfig(
                theme="modern",
                show_navigation=True,
                show_sidebar=True,
                include_toc=False
            )

        return self.generate_report(
            template_name="dashboard.html",
            data=data,
            metadata=metadata,
            config=config
        )

    def create_summary_report(
        self,
        data: Dict[str, Any],
        metadata: ReportMetadata,
        config: ReportConfig = None
    ) -> Path:
        """
        创建摘要报告

        Args:
            data: 摘要数据
            metadata: 报告元数据
            config: 报告配置

        Returns:
            生成的摘要报告文件路径
        """
        if config is None:
            config = ReportConfig(
                theme="modern",
                include_toc=True
            )

        return self.generate_report(
            template_name="summary.html",
            data=data,
            metadata=metadata,
            config=config
        )

    def create_detailed_report(
        self,
        data: Dict[str, Any],
        metadata: ReportMetadata,
        config: ReportConfig = None
    ) -> Path:
        """
        创建详细报告

        Args:
            data: 详细数据
            metadata: 报告元数据
            config: 报告配置

        Returns:
            生成的详细报告文件路径
        """
        if config is None:
            config = ReportConfig(
                theme="modern",
                include_toc=True
            )

        return self.generate_report(
            template_name="detailed.html",
            data=data,
            metadata=metadata,
            config=config
        )

    def export_to_pdf(
        self,
        html_file: Path,
        output_path: Optional[Path] = None
    ) -> Optional[Path]:
        """
        导出HTML为PDF (需要安装weasyprint或playwright)

        Args:
            html_file: HTML文件路径
            output_path: 输出路径

        Returns:
            生成的PDF文件路径
        """
        try:
            # 尝试使用weasyprint
            try:
                from weasyprint import HTML
                if output_path is None:
                    output_path = html_file.with_suffix('.pdf')

                HTML(filename=str(html_file)).write_pdf(str(output_path))
                logger.info(f"PDF exported successfully: {output_path}")
                return output_path
            except ImportError:
                logger.warning("weasyprint not installed, trying playwright")

            # 尝试使用playwright
            try:
                from playwright.sync_api import sync_playwright
                if output_path is None:
                    output_path = html_file.with_suffix('.pdf')

                with sync_playwright() as p:
                    browser = p.chromium.launch()
                    page = browser.new_page()
                    page.goto(f"file://{html_file.absolute()}")
                    page.pdf(path=str(output_path), format='A4')
                    browser.close()

                logger.info(f"PDF exported successfully: {output_path}")
                return output_path
            except ImportError:
                logger.error("Neither weasyprint nor playwright is installed")
                return None

        except Exception as e:
            logger.error(f"PDF export error: {e}")
            return None

    def get_available_themes(self) -> List[str]:
        """获取可用主题列表"""
        return list(self.THEMES.keys())

    def validate_data(self, data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """
        验证报告数据

        Args:
            data: 要验证的数据
            schema: 数据模式

        Returns:
            验证是否通过
        """
        # 简单的数据验证实现
        # 可以扩展为更复杂的数据验证
        try:
            for key, expected_type in schema.items():
                if key not in data:
                    logger.warning(f"Missing required field: {key}")
                    return False
                if not isinstance(data[key], expected_type):
                    logger.warning(f"Invalid type for {key}: expected {expected_type}, got {type(data[key])}")
                    return False
            return True
        except Exception as e:
            logger.error(f"Data validation error: {e}")
            return False
