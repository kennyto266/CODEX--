"""
HTML Data Tables Module
生成交互式数据表格的模块

This module provides:
- DataTables integration
- Table rendering and formatting
- Data export functionality
- Sorting and filtering
- Responsive table design
"""

from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime, date
import pandas as pd
import numpy as np
import json
import logging
from dataclasses import dataclass, asdict, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ColumnConfig:
    """列配置类"""
    name: str
    title: str
    data_type: str = "string"  # string, number, date, currency, percentage
    orderable: bool = True
    searchable: bool = True
    visible: bool = True
    width: Optional[str] = None
    class_name: Optional[str] = None
    render: Optional[str] = None  # Custom render function name
    formatter: Optional[Callable] = None  # Custom formatter function
    precision: int = 2  # For numeric types
    prefix: str = ""  # For currency display
    suffix: str = ""  # For percentage display
    color_positive: str = "success"  # For positive values
    color_negative: str = "danger"  # For negative values


@dataclass
class TableConfig:
    """表格配置类"""
    id: str
    title: str
    responsive: bool = True
    pagination: bool = True
    page_length: int = 10
    searching: bool = True
    ordering: bool = True
    info: bool = True
    length_change: bool = True
    processing: bool = False
    server_side: bool = False
    scroll_x: bool = False
    scroll_y: Optional[str] = None
    fixed_header: bool = False
    row_selection: bool = False
    export_buttons: bool = True
    language: str = "zh-CN"
    custom_options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TableData:
    """表格数据类"""
    columns: List[ColumnConfig]
    data: List[Dict[str, Any]]
    total_records: Optional[int] = None
    filtered_records: Optional[int] = None


class DataTableGenerator:
    """交互式数据表格生成器"""

    # 预定义颜色主题
    COLOR_THEMES = {
        "primary": "#3b82f6",
        "success": "#10b981",
        "warning": "#f59e0b",
        "danger": "#ef4444",
        "info": "#0ea5e9",
        "secondary": "#6b7280"
    }

    def __init__(self, config: Optional[TableConfig] = None):
        """
        初始化表格生成器

        Args:
            config: 表格配置
        """
        self.config = config

    def generate_table(
        self,
        table_data: TableData,
        config: Optional[TableConfig] = None
    ) -> str:
        """
        生成HTML表格

        Args:
            table_data: 表格数据
            config: 表格配置

        Returns:
            HTML表格字符串
        """
        cfg = config or self.config or TableConfig(
            id="data-table",
            title="Data Table"
        )

        html = self._generate_table_header(cfg)
        html += self._generate_table_structure(table_data)
        html += self._generate_table_footer(cfg)

        return html

    def generate_datatable_js(
        self,
        table_data: TableData,
        config: Optional[TableConfig] = None
    ) -> str:
        """
        生成DataTable JavaScript代码

        Args:
            table_data: 表格数据
            config: 表格配置

        Returns:
            JavaScript代码字符串
        """
        cfg = config or self.config or TableConfig(
            id="data-table",
            title="Data Table"
        )

        js_options = self._build_datatable_options(table_data, cfg)

        return f"""
$(document).ready(function() {{
    $('#{cfg.id}').DataTable({json.dumps(js_options, indent=12)});
}});
"""

    def generate_complete_table(
        self,
        table_data: TableData,
        config: Optional[TableConfig] = None
    ) -> str:
        """
        生成完整的HTML表格页面

        Args:
            table_data: 表格数据
            config: 表格配置

        Returns:
            完整的HTML页面
        """
        cfg = config or self.config or TableConfig(
            id="data-table",
            title="Data Table"
        )

        html = f"""
<!-- {cfg.title} -->
<div class="card border-0 shadow-sm" id="table-section">
    <div class="card-header d-flex justify-content-between align-items-center">
        <h6 class="mb-0">
            <i class="bi bi-table me-2"></i>{cfg.title}
        </h6>
        {self._generate_export_buttons() if cfg.export_buttons else ''}
    </div>
    <div class="card-body p-0">
        <div class="table-responsive">
            <table class="table table-hover mb-0" id="{cfg.id}">
                <thead class="table-light">
                    <tr>
                        {"".join([f'<th>{col.title}</th>' for col in table_data.columns])}
                    </tr>
                </thead>
                <tbody>
                    {self._generate_table_rows(table_data)}
                </tbody>
            </table>
        </div>
    </div>
</div>

<script>
{self.generate_datatable_js(table_data, cfg)}
{self._generate_table_event_handlers(cfg, table_data)}
</script>
"""

        return html

    def create_performance_table(
        self,
        strategies: List[Dict[str, Any]],
        config: Optional[TableConfig] = None
    ) -> str:
        """
        创建策略表现表格

        Args:
            strategies: 策略数据列表
            config: 表格配置

        Returns:
            HTML表格字符串
        """
        columns = [
            ColumnConfig("name", "策略名称", "string"),
            ColumnConfig("type", "类型", "string"),
            ColumnConfig("return", "收益率", "percentage"),
            ColumnConfig("sharpe", "夏普比率", "number"),
            ColumnConfig("max_drawdown", "最大回撤", "percentage"),
            ColumnConfig("win_rate", "胜率", "percentage"),
            ColumnConfig("trades", "交易次数", "number"),
            ColumnConfig("status", "状态", "string"),
        ]

        table_data = TableData(columns=columns, data=strategies)

        cfg = config or TableConfig(
            id="performance-table",
            title="策略表现对比",
            page_length=10
        )

        return self.generate_complete_table(table_data, cfg)

    def create_trade_log_table(
        self,
        trades: List[Dict[str, Any]],
        config: Optional[TableConfig] = None
    ) -> str:
        """
        创建交易记录表格

        Args:
            trades: 交易数据列表
            config: 表格配置

        Returns:
            HTML表格字符串
        """
        columns = [
            ColumnConfig("date", "日期", "date"),
            ColumnConfig("symbol", "股票代码", "string"),
            ColumnConfig("action", "操作", "string"),
            ColumnConfig("quantity", "数量", "number"),
            ColumnConfig("price", "价格", "currency"),
            ColumnConfig("commission", "手续费", "currency"),
            ColumnConfig("pnl", "盈亏", "number"),
        ]

        table_data = TableData(columns=columns, data=trades)

        cfg = config or TableConfig(
            id="trade-table",
            title="交易记录",
            page_length=15
        )

        return self.generate_complete_table(table_data, cfg)

    def create_risk_metrics_table(
        self,
        metrics: Dict[str, Any],
        config: Optional[TableConfig] = None
    ) -> str:
        """
        创建风险指标表格

        Args:
            metrics: 风险指标数据
            config: 表格配置

        Returns:
            HTML表格字符串
        """
        data = []
        for key, value in metrics.items():
            data.append({
                "metric": key,
                "value": value,
                "benchmark": "",  # 需要从外部传入基准数据
                "rating": self._calculate_rating(key, value)
            })

        columns = [
            ColumnConfig("metric", "指标", "string"),
            ColumnConfig("value", "数值", "number"),
            ColumnConfig("benchmark", "基准", "number"),
            ColumnConfig("rating", "评级", "string"),
        ]

        table_data = TableData(columns=columns, data=data)

        cfg = config or TableConfig(
            id="risk-table",
            title="风险指标",
            page_length=-1
        )

        return self.generate_complete_table(table_data, cfg)

    def create_portfolio_table(
        self,
        holdings: List[Dict[str, Any]],
        config: Optional[TableConfig] = None
    ) -> str:
        """
        创建投资组合表格

        Args:
            holdings: 持仓数据列表
            config: 表格配置

        Returns:
            HTML表格字符串
        """
        columns = [
            ColumnConfig("symbol", "股票代码", "string"),
            ColumnConfig("name", "股票名称", "string"),
            ColumnConfig("quantity", "数量", "number"),
            ColumnConfig("cost_basis", "成本", "currency"),
            ColumnConfig("current_price", "现价", "currency"),
            ColumnConfig("market_value", "市值", "currency"),
            ColumnConfig("unrealized_pnl", "未实现盈亏", "number"),
            ColumnConfig("weight", "权重", "percentage"),
        ]

        table_data = TableData(columns=columns, data=holdings)

        cfg = config or TableConfig(
            id="portfolio-table",
            title="投资组合",
            page_length=10
        )

        return self.generate_complete_table(table_data, cfg)

    def export_to_csv(
        self,
        table_data: TableData,
        output_path: Union[str, Path],
        config: Optional[TableConfig] = None
    ) -> Path:
        """
        导出数据为CSV

        Args:
            table_data: 表格数据
            output_path: 输出路径
            config: 表格配置

        Returns:
            输出文件路径
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 转换为DataFrame
        df = pd.DataFrame(table_data.data)

        # 格式化数据
        for col in table_data.columns:
            if col.formatter:
                df[col.name] = df[col.name].apply(col.formatter)

        # 导出CSV
        df.to_csv(output_path, index=False, encoding='utf-8-sig')

        logger.info(f"Table exported to CSV: {output_path}")
        return output_path

    def export_to_excel(
        self,
        table_data: TableData,
        output_path: Union[str, Path],
        config: Optional[TableConfig] = None
    ) -> Path:
        """
        导出数据为Excel

        Args:
            table_data: 表格数据
            output_path: 输出路径
            config: 表格配置

        Returns:
            输出文件路径
        """
        try:
            import openpyxl
        except ImportError:
            logger.error("openpyxl not installed. Please install it to export Excel files.")
            raise

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 转换为DataFrame
        df = pd.DataFrame(table_data.data)

        # 格式化数据
        for col in table_data.columns:
            if col.formatter:
                df[col.name] = df[col.name].apply(col.formatter)

        # 导出Excel
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Data')

        logger.info(f"Table exported to Excel: {output_path}")
        return output_path

    def _generate_table_header(self, config: TableConfig) -> str:
        """生成表格HTML头部"""
        return f"""
<div class="card border-0 shadow-sm" id="table-section">
    <div class="card-header d-flex justify-content-between align-items-center">
        <h6 class="mb-0">
            <i class="bi bi-table me-2"></i>{config.title}
        </h6>
        {self._generate_export_buttons() if config.export_buttons else ''}
    </div>
    <div class="card-body p-0">
"""

    def _generate_table_structure(self, table_data: TableData) -> str:
        """生成表格结构"""
        return f"""
        <div class="table-responsive">
            <table class="table table-hover mb-0" id="{self.config.id if self.config else 'data-table'}">
                <thead class="table-light">
                    <tr>
                        {"".join([f'<th>{col.title}</th>' for col in table_data.columns if col.visible])}
                    </tr>
                </thead>
                <tbody>
                    {self._generate_table_rows(table_data)}
                </tbody>
            </table>
        </div>
"""

    def _generate_table_rows(self, table_data: TableData) -> str:
        """生成表格行"""
        rows = []
        for item in table_data.data:
            row_cells = []
            for col in table_data.columns:
                if not col.visible:
                    continue

                value = item.get(col.name, "")
                formatted_value = self._format_value(value, col)
                cell_class = self._get_cell_class(value, col)
                cell_style = f'style="width: {col.width}"' if col.width else ""
                cell_html = f'<td {cell_style} class="{cell_class}">{formatted_value}</td>'
                row_cells.append(cell_html)

            rows.append(f"<tr>{''.join(row_cells)}</tr>")

        return "\n".join(rows)

    def _generate_table_footer(self, config: TableConfig) -> str:
        """生成表格HTML尾部"""
        return """
    </div>
</div>
"""

    def _generate_export_buttons(self) -> str:
        """生成导出按钮"""
        return """
        <div class="btn-group btn-group-sm">
            <button class="btn btn-outline-secondary" onclick="exportTableToCSV()">
                <i class="bi bi-download me-1"></i>CSV
            </button>
            <button class="btn btn-outline-secondary" onclick="exportTableToExcel()">
                <i class="bi bi-file-spreadsheet me-1"></i>Excel
            </button>
            <button class="btn btn-outline-secondary" onclick="printTable()">
                <i class="bi bi-printer me-1"></i>打印
            </button>
        </div>
"""

    def _generate_table_event_handlers(
        self,
        config: TableConfig,
        table_data: TableData
    ) -> str:
        """生成表格事件处理程序"""
        return f"""
function exportTableToCSV() {{
    const table = $('#{config.id}').DataTable();
    const data = table.data().toArray();
    const headers = {json.dumps([col.title for col in table_data.columns])};

    const csvContent = [headers.join(',')]
        .concat(data.map(row => Object.values(row).join(',')))
        .join('\\n');

    const blob = new Blob([csvContent], {{ type: 'text/csv;charset=utf-8;' }});
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = '{config.title.replace(' ', '_')}.csv';
    link.click();
}}

function exportTableToExcel() {{
    alert('Excel export functionality requires server-side processing');
}}

function printTable() {{
    window.print();
}}
"""

    def _build_datatable_options(
        self,
        table_data: TableData,
        config: TableConfig
    ) -> Dict[str, Any]:
        """构建DataTable选项"""
        columns = []
        for col in table_data.columns:
            column_def = {
                "data": col.name,
                "title": col.title,
                "orderable": col.orderable,
                "searchable": col.searchable,
                "visible": col.visible
            }

            if col.render:
                column_def["render"] = col.render

            columns.append(column_def)

        options = {
            "pageLength": config.page_length,
            "responsive": config.responsive,
            "paging": config.pagination,
            "searching": config.searching,
            "ordering": config.ordering,
            "info": config.info,
            "lengthChange": config.length_change,
            "processing": config.processing,
            "serverSide": config.server_side,
            "columns": columns,
            "language": self._get_language_config(config.language)
        }

        if config.scroll_x:
            options["scrollX"] = True

        if config.scroll_y:
            options["scrollY"] = config.scroll_y

        if config.fixed_header:
            options["fixedHeader"] = True

        if config.custom_options:
            options.update(config.custom_options)

        return options

    def _get_language_config(self, language: str) -> Dict[str, str]:
        """获取语言配置"""
        configs = {
            "zh-CN": {
                "url": "//cdn.datatables.net/plug-ins/1.13.7/i18n/zh.json"
            },
            "en": {
                "decimal": "",
                "emptyTable": "No data available in table",
                "info": "Showing _START_ to _END_ of _TOTAL_ entries",
                "infoEmpty": "Showing 0 to 0 of 0 entries",
                "infoFiltered": "(filtered from _MAX_ total entries)",
                "infoPostFix": "",
                "thousands": ",",
                "lengthMenu": "Show _MENU_ entries",
                "loadingRecords": "Loading...",
                "processing": "",
                "search": "Search:",
                "zeroRecords": "No matching records found",
                "paginate": {
                    "first": "First",
                    "last": "Last",
                    "next": "Next",
                    "previous": "Previous"
                },
                "aria": {
                    "sortAscending": ": activate to sort column ascending",
                    "sortDescending": ": activate to sort column descending"
                }
            }
        }

        return configs.get(language, configs["en"])

    def _format_value(self, value: Any, column: ColumnConfig) -> str:
        """格式化列值"""
        if value is None or value == "":
            return "-"

        # 自定义格式化器
        if column.formatter:
            return str(column.formatter(value))

        # 根据数据类型格式化
        if column.data_type == "number":
            precision = column.precision
            if isinstance(value, (int, float)):
                formatted = f"{value:,.{precision}f}"
            else:
                formatted = str(value)
            return f"{column.prefix}{formatted}{column.suffix}"

        elif column.data_type == "currency":
            precision = column.precision
            if isinstance(value, (int, float)):
                formatted = f"HKD {value:,.{precision}f}"
            else:
                formatted = str(value)
            return formatted

        elif column.data_type == "percentage":
            precision = column.precision
            if isinstance(value, (int, float)):
                formatted = f"{value * 100:.{precision}f}%"
            else:
                formatted = str(value)
            return formatted

        elif column.data_type == "date":
            if isinstance(value, str):
                try:
                    date_obj = datetime.fromisoformat(value)
                    return date_obj.strftime("%Y-%m-%d")
                except:
                    return value
            elif isinstance(value, (date, datetime)):
                return value.strftime("%Y-%m-%d")

        return str(value)

    def _get_cell_class(self, value: Any, column: ColumnConfig) -> str:
        """获取单元格CSS类"""
        classes = []

        # 数值颜色类
        if column.data_type in ["number", "currency", "percentage"]:
            if isinstance(value, (int, float)):
                if value > 0:
                    classes.append(f"text-{column.color_positive}")
                elif value < 0:
                    classes.append(f"text-{column.color_negative}")

        # 自定义类
        if column.class_name:
            classes.append(column.class_name)

        return " ".join(classes) if classes else ""

    def _calculate_rating(self, metric: str, value: float) -> str:
        """计算指标评级"""
        # 简单的评级逻辑，实际应该基于行业标准
        if metric in ["夏普比率", "Sortino比率"]:
            if value >= 2:
                return "优秀"
            elif value >= 1:
                return "良好"
            else:
                return "一般"

        elif metric in ["最大回撤", "波动率"]:
            if value <= 5:
                return "优秀"
            elif value <= 10:
                return "良好"
            else:
                return "一般"

        return "良好"
