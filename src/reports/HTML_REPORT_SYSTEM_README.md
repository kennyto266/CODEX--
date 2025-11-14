# HTML Report System Documentation

## 港股量化交易系统 - HTML报告模块

### 概述

本HTML报告系统提供了一套完整的响应式报告生成解决方案，支持交互式图表、数据表格、多主题切换等功能。系统基于Jinja2模板引擎、Plotly.js和Bootstrap 5构建，支持现代化UI设计和移动端适配。

---

## 核心功能

### ✨ 特性

- **响应式设计** - 完美适配桌面端、平板和移动设备
- **交互式图表** - 基于Plotly.js的动态图表，支持缩放、平移、悬停提示
- **多主题支持** - 内置现代风格、深色风格、经典风格三种主题
- **数据表格** - 支持排序、过滤、分页、搜索的DataTable
- **导出功能** - 支持HTML、PDF、CSV、Excel格式导出
- **打印优化** - 专门的打印样式，确保打印效果完美
- **多语言支持** - 内置中英文支持
- **模块化设计** - 高度可定制和可扩展

### 📦 核心模块

1. **html_generator.py** - HTML报告生成器
2. **html_charts.py** - 交互式图表生成器
3. **html_tables.py** - 数据表格生成器
4. **templates/html/** - HTML模板文件
5. **templates/css/** - 自定义样式文件
6. **static/js/** - JavaScript交互脚本

---

## 快速开始

### 1. 安装依赖

```bash
pip install jinja2 pandas plotly numpy
# 可选依赖
pip install openpyxl  # Excel导出
pip install weasyprint  # PDF导出
```

### 2. 运行示例

```bash
cd src/reports
python example_html_report.py
```

### 3. 查看报告

生成的报告文件保存在 `reports/output/` 目录下，使用浏览器打开HTML文件即可查看。

---

## 详细使用指南

### HTML报告生成器 (html_generator.py)

#### 基本用法

```python
from html_generator import HTMLReportGenerator, ReportMetadata, ReportConfig
from datetime import datetime

# 初始化生成器
generator = HTMLReportGenerator(
    template_dir="templates/html",
    output_dir="reports/output"
)

# 创建报告元数据
metadata = ReportMetadata(
    title="量化策略报告",
    subtitle="2024年Q3分析",
    author="量化团队",
    created_at=datetime.now(),
    version="1.0"
)

# 创建报告配置
config = ReportConfig(
    theme="modern",      # 主题: modern, dark, classic
    dark_mode=False,     # 深色模式
    show_navigation=True,  # 显示导航栏
    show_sidebar=True,     # 显示侧边栏
    include_toc=True       # 包含目录
)

# 生成报告
output_path = generator.generate_report(
    template_name="summary.html",
    data=your_data,
    metadata=metadata,
    config=config
)
```

#### 支持的模板

- **dashboard.html** - 仪表板模板
- **summary.html** - 摘要报告模板
- **detailed.html** - 详细分析模板
- **index.html** - 多页面报告索引

#### 主题配置

```python
config = ReportConfig(
    theme="modern",  # 现代风格
    custom_css=[
        "/static/css/custom.css"
    ],
    custom_js=[
        "/static/js/custom.js"
    ]
)
```

### 交互式图表生成器 (html_charts.py)

#### 支持的图表类型

- **线图 (Line Chart)**
- **柱状图 (Bar Chart)**
- **饼图 (Pie Chart)**
- **散点图 (Scatter Plot)**
- **K线图 (Candlestick)**
- **OHLC图**
- **热力图 (Heatmap)**
- **面积图 (Area Chart)**
- **箱线图 (Box Plot)**
- **3D散点图**
- **技术指标图**

#### 创建线图

```python
from html_charts import ChartGenerator, ChartData, ChartConfig

# 初始化图表生成器
chart_gen = ChartGenerator(theme="light")

# 准备数据
data = [
    ChartData(
        x=dates,
        y=values1,
        name="策略收益",
        mode="lines"
    ),
    ChartData(
        x=dates,
        y=values2,
        name="基准收益",
        mode="lines"
    )
]

# 配置图表
config = ChartConfig(
    title="收益对比",
    xaxis_title="日期",
    yaxis_title="收益率 (%)",
    height=400
)

# 生成图表
chart = chart_gen.create_line_chart(data, config)
```

#### 创建K线图

```python
import pandas as pd

# OHLC数据
df = pd.DataFrame({
    "open": [...],
    "high": [...],
    "low": [...],
    "close": [...],
    "volume": [...]
})

# 创建K线图
config = ChartConfig(title="股票价格", xaxis_title="日期", yaxis_title="价格")
candlestick = chart_gen.create_candlestick_chart(df, config)

# 导出图表
output_path = chart_gen.export_chart(candlestick, "reports/output/chart.html")
```

#### 导出图表

```python
# 导出为HTML
chart_gen.export_chart(chart, "output.html", format="html")

# 导出为JSON
chart_gen.export_chart(chart, "output.json", format="json")

# 导出为PNG (需要plotly-orca或其他导出工具)
chart_gen.export_chart(chart, "output.png", format="png")
```

### 数据表格生成器 (html_tables.py)

#### 创建策略表现表格

```python
from html_tables import DataTableGenerator, TableConfig

# 策略数据
strategies = [
    {
        "name": "KDJ策略",
        "type": "震荡指标",
        "return": 15.23,
        "sharpe": 2.01,
        "max_drawdown": -3.45,
        "trades": 178
    },
    # 更多数据...
]

# 初始化表格生成器
table_gen = DataTableGenerator()

# 创建表格
html = table_gen.create_performance_table(
    strategies=strategies,
    config=TableConfig(
        id="performance-table",
        title="策略表现对比",
        page_length=10,
        export_buttons=True
    )
)
```

#### 创建自定义表格

```python
from html_tables import TableData, ColumnConfig

# 定义列
columns = [
    ColumnConfig("date", "日期", "date"),
    ColumnConfig("symbol", "股票代码", "string"),
    ColumnConfig("return", "收益率", "percentage"),
    ColumnConfig("pnl", "盈亏", "number", color_positive="success"),
]

# 创建表格数据
table_data = TableData(columns=columns, data=trade_data)

# 生成HTML
html = table_gen.generate_complete_table(table_data)
```

#### 导出数据

```python
# 导出CSV
csv_path = table_gen.export_to_csv(table_data, "output/strategies.csv")

# 导出Excel
excel_path = table_gen.export_to_excel(table_data, "output/strategies.xlsx")
```

---

## 模板系统

### 自定义模板

在 `templates/html/` 目录下创建自定义模板：

```html
{% extends "base.html" %}

{% block title %}自定义报告 - {{ metadata.title }}{% endblock %}

{% block content %}
<div class="row">
    <div class="col-12">
        <h2>{{ data.title }}</h2>
        <p>{{ data.description }}</p>
    </div>
</div>
{% endblock %}
```

### 可用的块 (Blocks)

- `title` - 页面标题
- `head` - 自定义HTML头部
- `body_class` - 页面CSS类
- `breadcrumb` - 面包屑导航
- `sidebar_nav` - 侧边栏导航
- `content` - 主要内容
- `scripts` - JavaScript代码

### 可用的变量

- `metadata` - 报告元数据
- `config` - 报告配置
- `theme` - 主题配置
- `data` - 报告数据
- `current_year` - 当前年份
- `base_url` - 基础URL

---

## 样式系统

### CSS变量

在 `templates/css/report.css` 中定义：

```css
:root {
  --color-primary: #3b82f6;
  --color-success: #10b981;
  --color-warning: #f59e0b;
  --color-danger: #ef4444;
  /* 更多变量... */
}
```

### 自定义样式

```css
.custom-card {
  background: var(--bg-card);
  border-radius: var(--border-radius-lg);
  box-shadow: 0 4px 6px var(--shadow-color);
}
```

### 响应式设计

```css
/* 桌面端 */
@media (min-width: 992px) {
  .custom-class {
    /* 桌面端样式 */
  }
}

/* 平板 */
@media (max-width: 991px) and (min-width: 768px) {
  .custom-class {
    /* 平板样式 */
  }
}

/* 移动端 */
@media (max-width: 767px) {
  .custom-class {
    /* 移动端样式 */
  }
}
```

---

## JavaScript API

### 全局对象

```javascript
// 图表管理器
window.chartManager = new ChartManager();

// 表格管理器
window.dataTableManager = new DataTableManager();

// 主题管理器
window.themeManager = new ThemeManager();

// 导出管理器
window.exportManager = new ExportManager();
```

### 创建图表

```javascript
// 创建线图
window.chartManager.createChart(
    'chart-div',
    chartData,
    chartLayout,
    chartConfig
);

// 下载图表
window.chartManager.downloadChart('chart-div', 'png');
```

### 搜索表格

```javascript
// 搜索表格
window.dataTableManager.searchTable('#table-id', 'search term');

// 导出表格
window.dataTableManager.exportToCSV('#table-id', 'filename');
```

### 主题切换

```javascript
// 切换主题
window.themeManager.toggleTheme();

// 设置特定主题
window.themeManager.setTheme('dark');
```

---

## 配置选项

### 报告配置 (ReportConfig)

```python
config = ReportConfig(
    theme="modern",          # 主题: modern, dark, classic
    dark_mode=False,         # 深色模式
    show_navigation=True,    # 显示导航栏
    show_sidebar=True,       # 显示侧边栏
    responsive=True,         # 响应式设计
    include_toc=True,        # 包含目录
    export_formats=[         # 支持的导出格式
        "html", "pdf", "csv"
    ],
    custom_css=[],           # 自定义CSS文件
    custom_js=[]             # 自定义JavaScript文件
)
```

### 图表配置 (ChartConfig)

```python
config = ChartConfig(
    width=800,               # 宽度
    height=600,              # 高度
    responsive=True,         # 响应式
    show_legend=True,        # 显示图例
    show_grid=True,          # 显示网格
    theme="plotly",          # 主题
    title="图表标题",         # 标题
    xaxis_title="X轴标题",    # X轴标题
    yaxis_title="Y轴标题",    # Y轴标题
    hover_mode="x unified",  # 悬停模式
    stacked=False,           # 堆叠
    barmode="group"          # 柱状图模式
)
```

### 表格配置 (TableConfig)

```python
config = TableConfig(
    id="table-id",           # 表格ID
    title="表格标题",         # 表格标题
    responsive=True,         # 响应式
    pagination=True,         # 分页
    page_length=10,          # 每页行数
    searching=True,          # 搜索
    ordering=True,           # 排序
    info=True,               # 显示信息
    length_change=True,      # 允许改变每页行数
    processing=False,        # 处理中提示
    server_side=False,       # 服务端处理
    scroll_x=False,          # 水平滚动
    scroll_y=None,           # 垂直滚动
    fixed_header=False,      # 固定表头
    row_selection=False,     # 行选择
    export_buttons=True,     # 导出按钮
    language="zh-CN"         # 语言
)
```

---

## 导出功能

### 支持的格式

1. **HTML** - 完整的交互式报告
2. **PDF** - 静态文档（需要weasyprint或playwright）
3. **CSV** - 纯数据文件
4. **Excel** - 带格式的电子表格
5. **PNG/SVG** - 图表图片

### PDF导出

```python
# 使用weasyprint
pip install weasyprint

# 或使用playwright
pip install playwright
playwright install chromium

# 代码中会自动检测和使用可用的工具
output_path = generator.export_to_pdf(html_file, output_path=None)
```

### 自定义导出

```python
# 导出多个页面为单一PDF
pages = [
    {"template": "dashboard.html", "data": data, "title": "仪表板"},
    {"template": "summary.html", "data": data, "title": "摘要"},
    {"template": "detailed.html", "data": data, "title": "详细"}
]

index_path = generator.generate_multi_page_report(
    pages=pages,
    metadata=metadata,
    config=config
)
```

---

## 最佳实践

### 1. 数据准备

```python
# 确保数据格式正确
data = {
    "strategies": [
        {
            "name": "策略名",
            "type": "策略类型",
            "return": 15.23,  # 数值类型
            "date": "2024-01-01"  # 日期格式
        }
    ]
}
```

### 2. 性能优化

```python
# 大数据集使用服务端处理
config = TableConfig(
    server_side=True,  # 启用服务端处理
    page_length=25
)

# 图表使用延迟加载
# JavaScript中动态创建图表
```

### 3. 移动端适配

```python
config = ReportConfig(
    responsive=True,  # 启用响应式
    show_navigation=True,
    show_sidebar=False  # 移动端隐藏侧边栏
)
```

### 4. 打印优化

```python
# CSS媒体查询处理打印
@media print {
    .no-print { display: none !important; }
    .card { page-break-inside: avoid; }
}
```

### 5. 可访问性

```html
<!-- 添加ARIA标签 -->
<table role="table" aria-label="策略表现表">
    <thead>
        <tr>
            <th scope="col">策略名称</th>
            <th scope="col">收益率</th>
        </tr>
    </thead>
</table>
```

---

## 故障排除

### 常见问题

**Q: 图表不显示？**
A: 检查Plotly.js是否正确加载，确保数据格式正确。

**Q: 表格样式异常？**
A: 确认Bootstrap和DataTables CSS文件已加载。

**Q: PDF导出失败？**
A: 安装weasyprint或playwright：`pip install weasyprint`

**Q: 移动端布局错乱？**
A: 检查CSS媒体查询，确保viewport meta标签正确。

**Q: 中文显示乱码？**
A: 确保文件编码为UTF-8。

### 调试技巧

1. 查看浏览器开发者工具Console
2. 检查网络请求是否成功
3. 验证数据格式是否正确
4. 查看CSS样式是否应用

---

## 扩展开发

### 添加新图表类型

```python
def create_custom_chart(self, data, config):
    chart_data = [{
        "type": "custom",
        "data": data,
        "options": config.custom_options
    }]
    return {"data": chart_data, "layout": {}, "config": {}}
```

### 添加新模板

```html
{% extends "base.html" %}
{% block content %}
<!-- 自定义内容 -->
{% endblock %}
```

### 添加新导出格式

```python
def export_to_custom(self, data, output_path):
    # 实现自定义导出逻辑
    pass
```

---

## API参考

完整的API参考请查看各模块的docstring：

- `html_generator.py` - HTMLReportGenerator类
- `html_charts.py` - ChartGenerator类
- `html_tables.py` - DataTableGenerator类

---

## 更新日志

### v2.0 (2024-11-09)
- ✅ 完整的HTML报告系统
- ✅ 响应式设计
- ✅ 多主题支持
- ✅ 交互式图表
- ✅ 数据表格
- ✅ 导出功能

---

## 许可证

本项目采用MIT许可证。

---

## 技术支持

如有问题或建议，请联系开发团队。

---

**感谢使用港股量化交易系统HTML报告模块！**
