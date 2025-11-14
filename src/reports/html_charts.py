"""
HTML Interactive Charts Module
生成交互式图表的模块

This module provides:
- Plotly.js integration
- Interactive chart generation
- Chart customization
- Multiple chart types
- Responsive design support
"""

from typing import Dict, List, Any, Optional, Union
from datetime import datetime, date
import pandas as pd
import numpy as np
import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ChartConfig:
    """图表配置类"""
    width: Optional[int] = None
    height: Optional[int] = 600
    responsive: bool = True
    show_legend: bool = True
    show_grid: bool = True
    theme: str = "plotly"
    colors: Optional[List[str]] = None
    title: Optional[str] = None
    xaxis_title: Optional[str] = None
    yaxis_title: Optional[str] = None
    hover_mode: str = "x unified"
    stacked: bool = False
    barmode: str = "group"


@dataclass
class ChartData:
    """图表数据类"""
    x: Union[List, pd.Series, np.ndarray]
    y: Union[List, pd.Series, np.ndarray]
    name: str
    type: str = "scatter"
    mode: str = "lines"
    color: Optional[str] = None
    fill: Optional[str] = None
    opacity: float = 1.0
    marker_size: Optional[int] = None
    line_width: int = 2
    custom_data: Optional[List] = None


class ChartGenerator:
    """交互式图表生成器"""

    # 默认颜色调色板
    DEFAULT_COLORS = [
        "#3b82f6",  # Blue
        "#10b981",  # Emerald
        "#f59e0b",  # Amber
        "#ef4444",  # Red
        "#8b5cf6",  # Violet
        "#ec4899",  # Pink
        "#14b8a6",  # Teal
        "#f97316",  # Orange
        "#6366f1",  # Indigo
        "#84cc16",  # Lime
    ]

    # 深色主题颜色
    DARK_COLORS = [
        "#60a5fa",
        "#34d399",
        "#fbbf24",
        "#f87171",
        "#a78bfa",
        "#f472b6",
        "#2dd4bf",
        "#fb923c",
        "#818cf8",
        "#a3e635",
    ]

    def __init__(self, theme: str = "light", config: Optional[ChartConfig] = None):
        """
        初始化图表生成器

        Args:
            theme: 主题 ('light' or 'dark')
            config: 图表配置
        """
        self.theme = theme
        self.config = config or ChartConfig()
        self.colors = self.DARK_COLORS if theme == "dark" else self.DEFAULT_COLORS

    def create_line_chart(
        self,
        data: List[ChartData],
        config: Optional[ChartConfig] = None
    ) -> Dict[str, Any]:
        """
        创建线图

        Args:
            data: 图表数据列表
            config: 图表配置

        Returns:
            Plotly图表配置
        """
        cfg = config or self.config
        chart_data = []

        for i, series in enumerate(data):
            trace = {
                "x": self._prepare_data(series.x),
                "y": self._prepare_data(series.y),
                "type": "scatter",
                "mode": series.mode,
                "name": series.name,
                "line": {
                    "width": series.line_width,
                    "color": series.color or self.colors[i % len(self.colors)]
                },
                "fill": series.fill,
                "opacity": series.opacity
            }

            if series.custom_data:
                trace["customdata"] = series.custom_data

            if series.mode == "markers":
                trace["marker"] = {
                    "size": series.marker_size or 8,
                    "color": series.color or self.colors[i % len(self.colors)]
                }

            chart_data.append(trace)

        layout = self._create_layout(cfg)

        return {
            "data": chart_data,
            "layout": layout,
            "config": self._create_config(cfg)
        }

    def create_bar_chart(
        self,
        data: List[ChartData],
        config: Optional[ChartConfig] = None
    ) -> Dict[str, Any]:
        """
        创建柱状图

        Args:
            data: 图表数据列表
            config: 图表配置

        Returns:
            Plotly图表配置
        """
        cfg = config or self.config
        chart_data = []

        for i, series in enumerate(data):
            trace = {
                "x": self._prepare_data(series.x),
                "y": self._prepare_data(series.y),
                "type": "bar",
                "name": series.name,
                "marker": {
                    "color": series.color or self.colors[i % len(self.colors)],
                    "opacity": series.opacity
                }
            }

            if series.custom_data:
                trace["customdata"] = series.custom_data

            chart_data.append(trace)

        layout = self._create_layout(cfg)
        layout["barmode"] = cfg.barmode

        return {
            "data": chart_data,
            "layout": layout,
            "config": self._create_config(cfg)
        }

    def create_pie_chart(
        self,
        labels: List[str],
        values: List[float],
        config: Optional[ChartConfig] = None,
        hole: float = 0
    ) -> Dict[str, Any]:
        """
        创建饼图

        Args:
            labels: 标签列表
            values: 数值列表
            config: 图表配置
            hole: 环形图孔径大小 (0-1)

        Returns:
            Plotly图表配置
        """
        cfg = config or self.config
        chart_data = [{
            "labels": labels,
            "values": values,
            "type": "pie",
            "hole": hole,
            "marker": {
                "colors": self.colors[:len(labels)]
            },
            "textinfo": "label+percent",
            "insidetextorientation": "radial"
        }]

        layout = self._create_layout(cfg)
        layout["showlegend"] = True

        return {
            "data": chart_data,
            "layout": layout,
            "config": self._create_config(cfg)
        }

    def create_scatter_chart(
        self,
        data: List[ChartData],
        config: Optional[ChartConfig] = None
    ) -> Dict[str, Any]:
        """
        创建散点图

        Args:
            data: 图表数据列表
            config: 图表配置

        Returns:
            Plotly图表配置
        """
        cfg = config or self.config
        chart_data = []

        for i, series in enumerate(data):
            trace = {
                "x": self._prepare_data(series.x),
                "y": self._prepare_data(series.y),
                "type": "scatter",
                "mode": series.mode,
                "name": series.name,
                "marker": {
                    "size": series.marker_size or 10,
                    "color": series.color or self.colors[i % len(self.colors)],
                    "opacity": series.opacity
                }
            }

            if series.custom_data:
                trace["customdata"] = series.custom_data

            chart_data.append(trace)

        layout = self._create_layout(cfg)
        layout["hovermode"] = "closest"

        return {
            "data": chart_data,
            "layout": layout,
            "config": self._create_config(cfg)
        }

    def create_heatmap(
        self,
        data: np.ndarray,
        x_labels: List[str],
        y_labels: List[str],
        config: Optional[ChartConfig] = None
    ) -> Dict[str, Any]:
        """
        创建热力图

        Args:
            data: 2D数据数组
            x_labels: X轴标签
            y_labels: Y轴标签
            config: 图表配置

        Returns:
            Plotly图表配置
        """
        cfg = config or self.config
        chart_data = [{
            "z": data.tolist(),
            "x": x_labels,
            "y": y_labels,
            "type": "heatmap",
            "colorscale": "Viridis",
            "showscale": True
        }]

        layout = self._create_layout(cfg)

        return {
            "data": chart_data,
            "layout": layout,
            "config": self._create_config(cfg)
        }

    def create_candlestick_chart(
        self,
        data: pd.DataFrame,
        config: Optional[ChartConfig] = None
    ) -> Dict[str, Any]:
        """
        创建K线图

        Args:
            data: 包含OHLCV的DataFrame
            config: 图表配置

        Returns:
            Plotly图表配置
        """
        cfg = config or self.config

        # 确保数据包含必要列
        required_cols = ["open", "high", "low", "close"]
        if not all(col in data.columns for col in required_cols):
            raise ValueError(f"Data must contain columns: {required_cols}")

        chart_data = [{
            "x": data.index if isinstance(data.index, list) else data.index.tolist(),
            "open": data["open"].tolist(),
            "high": data["high"].tolist(),
            "low": data["low"].tolist(),
            "close": data["close"].tolist(),
            "type": "candlestick",
            "name": "Price",
            "increasing": {"line": {"color": "#10b981"}},
            "decreasing": {"line": {"color": "#ef4444"}}
        }]

        # 添加成交量（如果存在）
        if "volume" in data.columns:
            chart_data.append({
                "x": data.index if isinstance(data.index, list) else data.index.tolist(),
                "y": data["volume"].tolist(),
                "type": "bar",
                "name": "Volume",
                "yaxis": "y2",
                "marker": {"color": "#94a3b8", "opacity": 0.5}
            })

        layout = self._create_layout(cfg)
        layout["yaxis"] = {"title": cfg.yaxis_title or "Price"}
        layout["yaxis2"] = {"title": "Volume", "overlaying": "y", "side": "right"}

        return {
            "data": chart_data,
            "layout": layout,
            "config": self._create_config(cfg)
        }

    def create_ohlc_chart(
        self,
        data: pd.DataFrame,
        config: Optional[ChartConfig] = None
    ) -> Dict[str, Any]:
        """
        创建OHLC图

        Args:
            data: 包含OHLC的DataFrame
            config: 图表配置

        Returns:
            Plotly图表配置
        """
        cfg = config or self.config

        chart_data = [{
            "x": data.index if isinstance(data.index, list) else data.index.tolist(),
            "open": data["open"].tolist(),
            "high": data["high"].tolist(),
            "low": data["low"].tolist(),
            "close": data["close"].tolist(),
            "type": "ohlc",
            "name": "OHLC"
        }]

        layout = self._create_layout(cfg)

        return {
            "data": chart_data,
            "layout": layout,
            "config": self._create_config(cfg)
        }

    def create_area_chart(
        self,
        data: List[ChartData],
        config: Optional[ChartConfig] = None
    ) -> Dict[str, Any]:
        """
        创建面积图

        Args:
            data: 图表数据列表
            config: 图表配置

        Returns:
            Plotly图表配置
        """
        cfg = config or self.config
        chart_data = []

        for i, series in enumerate(data):
            trace = {
                "x": self._prepare_data(series.x),
                "y": self._prepare_data(series.y),
                "type": "scatter",
                "mode": "lines",
                "name": series.name,
                "line": {
                    "width": 0
                },
                "fill": "tozeroy" if i == 0 else f"tonextx",
                "fillcolor": self._hex_to_rgba(series.color or self.colors[i % len(self.colors)], 0.5)
            }
            chart_data.append(trace)

        layout = self._create_layout(cfg)

        return {
            "data": chart_data,
            "layout": layout,
            "config": self._create_config(cfg)
        }

    def create_box_plot(
        self,
        data: List[ChartData],
        config: Optional[ChartConfig] = None
    ) -> Dict[str, Any]:
        """
        创建箱线图

        Args:
            data: 图表数据列表
            config: 图表配置

        Returns:
            Plotly图表配置
        """
        cfg = config or self.config
        chart_data = []

        for i, series in enumerate(data):
            trace = {
                "y": self._prepare_data(series.y),
                "type": "box",
                "name": series.name,
                "marker": {"color": series.color or self.colors[i % len(self.colors)]}
            }
            chart_data.append(trace)

        layout = self._create_layout(cfg)
        layout["showlegend"] = False

        return {
            "data": chart_data,
            "layout": layout,
            "config": self._create_config(cfg)
        }

    def create_histogram(
        self,
        data: List[float],
        bins: int = 30,
        config: Optional[ChartConfig] = None
    ) -> Dict[str, Any]:
        """
        创建直方图

        Args:
            data: 数据列表
            bins: 分箱数量
            config: 图表配置

        Returns:
            Plotly图表配置
        """
        cfg = config or self.config
        chart_data = [{
            "x": data,
            "type": "histogram",
            "nbinsx": bins,
            "marker": {"color": self.colors[0], "opacity": 0.7}
        }]

        layout = self._create_layout(cfg)

        return {
            "data": chart_data,
            "layout": layout,
            "config": self._create_config(cfg)
        }

    def create_3d_scatter(
        self,
        x: List[float],
        y: List[float],
        z: List[float],
        labels: List[str],
        config: Optional[ChartConfig] = None
    ) -> Dict[str, Any]:
        """
        创建3D散点图

        Args:
            x: X轴数据
            y: Y轴数据
            z: Z轴数据
            labels: 数据点标签
            config: 图表配置

        Returns:
            Plotly图表配置
        """
        cfg = config or self.config
        chart_data = [{
            "x": x,
            "y": y,
            "z": z,
            "type": "scatter3d",
            "mode": "markers",
            "marker": {
                "size": 5,
                "color": list(range(len(x))),
                "colorscale": "Viridis",
                "showscale": True,
                "colorbar": {"title": "Index"}
            },
            "text": labels,
            "hovertemplate": "%{text}<br>X: %{x}<br>Y: %{y}<br>Z: %{z}<extra></extra>"
        }]

        layout = self._create_layout(cfg)
        layout["scene"] = {
            "xaxis": {"title": cfg.xaxis_title or "X"},
            "yaxis": {"title": cfg.yaxis_title or "Y"},
            "zaxis": {"title": "Z"}
        }

        return {
            "data": chart_data,
            "layout": layout,
            "config": self._create_config(cfg)
        }

    def create_financial_indicators(
        self,
        data: pd.DataFrame,
        indicators: List[str],
        config: Optional[ChartConfig] = None
    ) -> Dict[str, Any]:
        """
        创建技术指标图表

        Args:
            data: 包含价格数据的DataFrame
            indicators: 指标列表 ('MA', 'RSI', 'MACD', 'BB', 'KDJ')
            config: 图表配置

        Returns:
            Plotly图表配置
        """
        cfg = config or self.config
        chart_data = []
        subplot_count = 1

        # 主图：价格和移动平均线
        if "MA" in indicators:
            chart_data.append({
                "x": data.index.tolist(),
                "y": data["close"].tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": "Close",
                "line": {"color": "#3b82f6", "width": 2}
            })

            if "MA5" not in data.columns:
                data["MA5"] = data["close"].rolling(5).mean()
            if "MA20" not in data.columns:
                data["MA20"] = data["close"].rolling(20).mean()

            chart_data.append({
                "x": data.index.tolist(),
                "y": data["MA5"].tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": "MA5",
                "line": {"color": "#f59e0b", "width": 1, "dash": "dot"}
            })

            chart_data.append({
                "x": data.index.tolist(),
                "y": data["MA20"].tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": "MA20",
                "line": {"color": "#10b981", "width": 1, "dash": "dash"}
            })

        # 副图：RSI
        if "RSI" in indicators:
            subplot_count += 1
            if "RSI" not in data.columns:
                delta = data["close"].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                data["RSI"] = 100 - (100 / (1 + rs))

            chart_data.append({
                "x": data.index.tolist(),
                "y": data["RSI"].tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": "RSI",
                "yaxis": "y2",
                "line": {"color": "#8b5cf6", "width": 2}
            })

        # 副图：MACD
        if "MACD" in indicators:
            subplot_count += 1
            if "MACD" not in data.columns:
                ema12 = data["close"].ewm(span=12).mean()
                ema26 = data["close"].ewm(span=26).mean()
                data["MACD"] = ema12 - ema26
                data["Signal"] = data["MACD"].ewm(span=9).mean()
                data["Histogram"] = data["MACD"] - data["Signal"]

            chart_data.append({
                "x": data.index.tolist(),
                "y": data["MACD"].tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": "MACD",
                "yaxis": "y3",
                "line": {"color": "#3b82f6", "width": 2}
            })

        layout = self._create_layout(cfg)
        layout["grid"] = {"rows": subplot_count, "columns": 1, "subplot_titles": ["Price", "RSI", "MACD"][:subplot_count]}

        return {
            "data": chart_data,
            "layout": layout,
            "config": self._create_config(cfg)
        }

    def export_chart(
        self,
        chart_config: Dict[str, Any],
        output_path: Union[str, Path],
        format: str = "html"
    ) -> Path:
        """
        导出图表

        Args:
            chart_config: 图表配置
            output_path: 输出路径
            format: 导出格式 ('html', 'json', 'png', 'svg', 'pdf')

        Returns:
            输出文件路径
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format == "html":
            html_content = self._generate_html(chart_config)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
        elif format == "json":
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(chart_config, f, indent=2, default=str)
        else:
            logger.warning(f"Format {format} not yet supported for export")

        return output_path

    def _create_layout(self, config: ChartConfig) -> Dict[str, Any]:
        """创建图表布局"""
        layout = {
            "title": {
                "text": config.title,
                "x": 0.5,
                "xanchor": "center"
            } if config.title else {},
            "xaxis": {
                "title": config.xaxis_title,
                "showgrid": config.show_grid,
                "gridcolor": "#e5e7eb"
            },
            "yaxis": {
                "title": config.yaxis_title,
                "showgrid": config.show_grid,
                "gridcolor": "#e5e7eb"
            },
            "legend": {
                "orientation": "h",
                "y": -0.2,
                "x": 0.5,
                "xanchor": "center"
            } if config.show_legend else {"visible": False},
            "hovermode": config.hover_mode,
            "plot_bgcolor": "white",
            "paper_bgcolor": "white",
            "font": {"family": "Inter, system-ui, sans-serif"},
            "margin": {"l": 50, "r": 20, "t": 60 if config.title else 30, "b": 60}
        }

        if self.theme == "dark":
            layout["plot_bgcolor"] = "#1f2937"
            layout["paper_bgcolor"] = "#111827"
            layout["xaxis"]["gridcolor"] = "#374151"
            layout["yaxis"]["gridcolor"] = "#374151"
            layout["font"]["color"] = "#f9fafb"

        return layout

    def _create_config(self, config: ChartConfig) -> Dict[str, Any]:
        """创建图表配置"""
        return {
            "responsive": config.responsive,
            "displayModeBar": True,
            "displaylogo": False,
            "modeBarButtonsToAdd": [
                "drawline",
                "drawopenpath",
                "drawclosedpath",
                "drawcircle",
                "drawrect",
                "eraseshape"
            ],
            "toImageButtonOptions": {
                "format": "png",
                "filename": "chart",
                "height": config.height or 600,
                "width": config.width or 800,
                "scale": 2
            }
        }

    def _generate_html(self, chart_config: Dict[str, Any]) -> str:
        """生成HTML文件内容"""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Interactive Chart</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{
            font-family: Inter, system-ui, sans-serif;
            margin: 0;
            padding: 20px;
            background: white;
        }}
        .chart-container {{
            width: 100%;
            height: 600px;
        }}
    </style>
</head>
<body>
    <div id="chart" class="chart-container"></div>
    <script>
        var chartData = {json.dumps(chart_config, indent=2)};
        Plotly.newPlot('chart', chartData.data, chartData.layout, chartData.config);
    </script>
</body>
</html>
"""

    def _prepare_data(self, data) -> List:
        """准备数据"""
        if isinstance(data, pd.Series):
            return data.tolist()
        elif isinstance(data, np.ndarray):
            return data.tolist()
        elif isinstance(data, (date, datetime)):
            return data.isoformat()
        else:
            return list(data)

    def _hex_to_rgba(self, hex_color: str, alpha: float) -> str:
        """将HEX颜色转换为RGBA"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {alpha})"
