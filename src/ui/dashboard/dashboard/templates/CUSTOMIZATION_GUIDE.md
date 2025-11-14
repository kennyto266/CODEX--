# 报告模板自定义指南

## 概述

本指南将帮助您深入定制报告模板系统，从简单的样式调整到复杂的功能扩展，满足您的个性化需求。

---

## 目录

1. [快速定制](#快速定制)
2. [样式定制](#样式定制)
3. [内容扩展](#内容扩展)
4. [新模板创建](#新模板创建)
5. [图表定制](#图表定制)
6. [数据处理](#数据处理)
7. [国际化支持](#国际化支持)
8. [高级功能](#高级功能)
9. [最佳实践](#最佳实践)

---

## 快速定制

### 1. 修改公司品牌

**更改Logo和公司信息:**

```html
<!-- 在所有模板的header部分 -->
<header class="bg-white shadow-sm border-b border-gray-200">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div class="flex justify-between items-center">
            <div>
                <img src="/static/logo.png" alt="公司Logo" class="h-8">
                <h1 class="text-2xl font-bold text-gray-900">{% block header_title %}报告标题{% endblock %}</h1>
            </div>
            <div class="text-sm text-gray-600">
                © 2025 您的公司名称 | 机密文档
            </div>
        </div>
    </div>
</header>
```

**自定义颜色主题:**

```html
<style>
:root {
    --primary-color: #3b82f6;      /* 主色调 */
    --success-color: #10b981;      /* 成功色 */
    --warning-color: #f59e0b;      /* 警告色 */
    --danger-color: #ef4444;       /* 危险色 */
    --background-color: #f8fafc;   /* 背景色 */
    --text-color: #1e293b;         /* 文本色 */
}
</style>
```

### 2. 调整页面布局

**修改页面宽度:**

```css
/* 全局容器最大宽度 */
.max-w-7xl {
    max-width: 90rem; /* 修改为更大的宽度 */
}

/* 或使用自定义宽度 */
.custom-container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 0 2rem;
}
```

**调整卡片间距:**

```css
.performance-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); /* 调整最小宽度 */
    gap: 2rem; /* 调整间距 */
}

.comparison-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); /* 调整列宽 */
    gap: 1.5rem;
}
```

### 3. 添加自定义字段

**在模板中添加:**

```html
<!-- 在性能指标卡片中 -->
<div class="metric-card">
    <div class="metric-label">自定义指标</div>
    <div class="metric-value" style="color: #3b82f6;">
        {{ custom_metric or 0 }}%
    </div>
    <div class="metric-change">
        <i class="fas fa-info-circle mr-1"></i>
        自定义说明
    </div>
</div>
```

**在数据生成器中添加:**

```python
# 在 report_generator.py 中
def _generate_performance_data(self, symbol, period):
    data = {
        # 现有字段...
        'custom_metric': 42.5,  # 添加自定义指标
        'custom_note': '这是自定义说明'
    }
    return data
```

---

## 样式定制

### 1. 自定义CSS类

**创建全局样式:**

```css
/* 创建一个 custom.css 文件 */
.custom-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 12px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease;
}

.custom-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 12px rgba(0, 0, 0, 0.15);
}

.custom-title {
    font-size: 1.5rem;
    font-weight: 700;
    background: linear-gradient(45deg, #667eea, #764ba2);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
```

**在模板中引用:**

```html
<!-- 在 <head> 部分 -->
<link rel="stylesheet" href="/static/css/custom.css">

<!-- 在HTML中使用 -->
<div class="custom-card">
    <h3 class="custom-title">自定义标题</h3>
</div>
```

### 2. 响应式设计调整

**移动端优化:**

```css
/* 小屏幕优化 */
@media (max-width: 640px) {
    .performance-grid {
        grid-template-columns: 1fr; /* 单列布局 */
        gap: 1rem;
    }

    .metric-value {
        font-size: 2rem; /* 缩小字体 */
    }

    .section-header {
        font-size: 1.5rem;
    }

    table {
        font-size: 0.75rem; /* 缩小表格字体 */
    }
}

/* 平板端优化 */
@media (min-width: 641px) and (max-width: 1024px) {
    .comparison-grid {
        grid-template-columns: repeat(2, 1fr); /* 2列布局 */
    }
}
```

### 3. 打印样式优化

```css
@media print {
    /* 移除背景色，节省墨水 */
    body {
        background: white !important;
        color: black !important;
    }

    /* 分页控制 */
    .chart-container {
        page-break-inside: avoid;
        break-inside: avoid;
    }

    /* 隐藏不需要的元素 */
    .no-print {
        display: none !important;
    }

    /* 调整页边距 */
    @page {
        margin: 1cm;
    }

    /* 优化表格打印 */
    table {
        page-break-inside: avoid;
    }

    th, td {
        padding: 8px !important;
        border: 1px solid #ccc !important;
    }
}
```

### 4. 深色模式支持

```css
/* 深色模式样式 */
@media (prefers-color-scheme: dark) {
    body {
        background: #0f172a;
        color: #e2e8f0;
    }

    .metric-card {
        background: #1e293b;
        border-color: #334155;
    }

    .chart-container {
        background: #1e293b;
        border-color: #334155;
    }

    table {
        color: #e2e8f0;
    }

    th {
        background: #334155;
    }
}
```

---

## 内容扩展

### 1. 添加新章节

**在模板中添加:**

```html
<!-- 新章节 -->
<section class="mb-8">
    <h2 class="section-header">
        <i class="fas fa-star mr-2 text-yellow-500"></i>
        特色分析
    </h2>
    <div class="grid md:grid-cols-2 gap-6">
        <div class="chart-container">
            <h3 class="subsection-header">子章节1</h3>
            <p class="text-gray-700">内容描述...</p>
        </div>
        <div class="chart-container">
            <h3 class="subsection-header">子章节2</h3>
            <p class="text-gray-700">内容描述...</p>
        </div>
    </div>
</section>
```

**在数据生成器中添加数据:**

```python
def _generate_performance_data(self, symbol, period):
    return {
        # 现有数据...
        'special_analysis': {
            'section1': {
                'title': '市场环境分析',
                'content': '分析当前市场环境对策略的影响...'
            },
            'section2': {
                'title': '未来展望',
                'content': '基于当前数据，预期未来表现...'
            }
        }
    }
```

### 2. 动态内容显示

```html
<!-- 条件显示 -->
{% if show_subsection %}
<section>
    <h2>可选章节</h2>
    <p>{{ optional_content }}</p>
</section>
{% endif %}

<!-- 循环显示 -->
{% for item in custom_list %}
<div class="custom-item">
    <h3>{{ item.title }}</h3>
    <p>{{ item.description }}</p>
</div>
{% endfor %}
```

### 3. 自定义工具提示

```html
<!-- 使用 title 属性 -->
<div class="metric-value" title="这是详细说明">
    {{ metric_value }}%
</div>

<!-- 使用自定义提示 -->
<div class="tooltip">
    <span class="tooltip-trigger" data-tooltip="{{ tooltip_text }}">
        <i class="fas fa-info-circle"></i>
    </span>
</div>
```

**JavaScript 实现:**

```javascript
// 工具提示功能
document.querySelectorAll('.tooltip-trigger').forEach(trigger => {
    trigger.addEventListener('mouseenter', function() {
        const tooltip = document.createElement('div');
        tooltip.className = 'tooltip-popup';
        tooltip.textContent = this.dataset.tooltip;
        document.body.appendChild(tooltip);

        const rect = this.getBoundingClientRect();
        tooltip.style.left = rect.left + 'px';
        tooltip.style.top = (rect.bottom + 5) + 'px';
    });

    trigger.addEventListener('mouseleave', function() {
        const tooltip = document.querySelector('.tooltip-popup');
        if (tooltip) tooltip.remove();
    });
});
```

---

## 新模板创建

### 1. 创建新模板文件

**创建 `custom_report.html`:**

```html
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}自定义报告{% endblock %}</title>

    <!-- 引入依赖 -->
    <script src="https://unpkg.com/plotly.js-dist-min@2.26.0/plotly.min.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">

    <!-- 自定义样式 -->
    <style>
        /* 自定义样式 */
    </style>
</head>
<body>
    <div class="min-h-screen">
        <!-- Header -->
        <header>
            <h1>{% block header_title %}自定义报告{% endblock %}</h1>
        </header>

        <!-- Main Content -->
        <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <!-- 使用变量 -->
            <section>
                <h2>报告信息</h2>
                <p>股票代码: {{ symbol }}</p>
                <p>分析期间: {{ period }}</p>
                <p>生成时间: {{ timestamp }}</p>
            </section>
        </main>
    </div>
</body>
</html>
```

### 2. 注册新模板

**在 `report_generator.py` 中添加:**

```python
# 在 TEMPLATE_TYPES 中添加
TEMPLATE_TYPES = {
    # 现有模板...
    'custom': 'custom_report.html'  # 添加新模板
}

# 在 _get_data_generator 中添加
def _get_data_generator(self, template_type: str):
    generators = {
        # 现有生成器...
        'custom': self._generate_custom_data  # 添加新生成器
    }
    return generators.get(template_type)

# 实现数据生成器
def _generate_custom_data(self, symbol: str, period: str) -> Dict[str, Any]:
    return {
        'custom_field1': 'value1',
        'custom_field2': 42.5,
        'custom_data': [
            {'label': 'A', 'value': 10},
            {'label': 'B', 'value': 20}
        ]
    }
```

### 3. 使用新模板

```python
config = ReportConfig(
    template_type='custom',
    symbol='0700.HK',
    period='2023-01-01 至 2023-12-31'
)

generator = ReportGenerator()
output_path = generator.save_report(config)
```

---

## 图表定制

### 1. 自定义图表样式

```javascript
// 定义自定义主题
const customTheme = {
    layout: {
        font: {
            family: 'Inter, sans-serif',
            size: 12,
            color: '#1e293b'
        },
        paper_bgcolor: 'white',
        plot_bgcolor: 'white',
        margin: { t: 20, r: 20, b: 50, l: 60 },
        xaxis: {
            gridcolor: '#e5e7eb',
            linecolor: '#9ca3af'
        },
        yaxis: {
            gridcolor: '#e5e7eb',
            linecolor: '#9ca3af'
        }
    }
};

// 使用自定义主题
Plotly.newPlot('chart', data, customTheme.layout);
```

### 2. 添加新图表类型

**雷达图:**

```javascript
const radarData = [{
    type: 'scatterpolar',
    r: [metrics.value1, metrics.value2, metrics.value3, metrics.value4, metrics.value5],
    theta: ['指标1', '指标2', '指标3', '指标4', '指标5'],
    fill: 'toself',
    name: '策略A',
    line: { color: '#3b82f6' }
}];

const radarLayout = {
    polar: {
        radialaxis: {
            visible: true,
            range: [0, 100]
        }
    },
    showlegend: true
};

Plotly.newPlot('radar-chart', radarData, radarLayout);
```

**热力图:**

```javascript
const heatmapData = [{
    z: correlation_matrix,
    x: strategies,
    y: strategies,
    type: 'heatmap',
    colorscale: 'RdBu',
    zmid: 0
}];

const heatmapLayout = {
    title: '相关性热力图',
    margin: { t: 50, r: 50, b: 50, l: 50 }
};

Plotly.newPlot('heatmap', heatmapData, heatmapLayout);
```

### 3. 交互式图表

```javascript
// 添加事件监听
document.getElementById('chart').on('plotly_click', function(data) {
    const point = data.points[0];
    alert(`点击了: ${point.x}, ${point.y}`);

    // 可以触发其他操作
    showDetails(point.x, point.y);
});

// 添加缩放事件
document.getElementById('chart').on('plotly_relayout', function(eventdata) {
    console.log('缩放范围:', eventdata['xaxis.range']);
});
```

### 4. 数据下钻

```javascript
// 初始图表
function renderInitialChart() {
    const trace = {
        x: data.dates,
        y: data.values,
        type: 'scatter',
        mode: 'lines'
    };

    Plotly.newPlot('main-chart', [trace], layout);
}

// 点击后显示详细图表
function showDetails(category) {
    const filteredData = rawData.filter(item => item.category === category);
    // 渲染详细图表
    renderDetailChart(filteredData);
}
```

---

## 数据处理

### 1. 数据验证

```python
from typing import Dict, Any
import logging

def validate_data(data: Dict[str, Any]) -> bool:
    """验证数据完整性"""
    required_fields = ['total_return', 'sharpe_ratio', 'max_drawdown']
    for field in required_fields:
        if field not in data:
            logging.error(f"缺少必填字段: {field}")
            return False

    # 验证数值范围
    if not isinstance(data['total_return'], (int, float)):
        logging.error("total_return 必须是数字")
        return False

    return True
```

### 2. 数据转换

```python
def transform_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """转换数据格式"""
    # 计算额外指标
    data = raw_data.copy()
    data['annualized_return'] = calculate_annual_return(data['total_return'])
    data['risk_adjusted_return'] = data['annual_return'] / data['volatility']

    # 格式化百分比
    for key in ['total_return', 'annual_return', 'volatility', 'max_drawdown']:
        if key in data:
            data[key] = round(data[key], 2)

    return data
```

### 3. 数据聚合

```python
def aggregate_monthly_data(daily_data: List[Dict]) -> List[Dict]:
    """将日数据聚合为月数据"""
    monthly_data = {}
    for item in daily_data:
        month = item['date'][:7]  # 取年月
        if month not in monthly_data:
            monthly_data[month] = []
        monthly_data[month].append(item)

    # 计算月度统计
    result = []
    for month, values in monthly_data.items():
        result.append({
            'date': month,
            'return': sum(v['return'] for v in values) / len(values),
            'max': max(v['return'] for v in values),
            'min': min(v['return'] for v in values)
        })

    return result
```

### 4. 缓存机制

```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=128)
def get_cached_data(symbol: str, period: str) -> Dict[str, Any]:
    """缓存数据获取"""
    # 生成缓存键
    cache_key = hashlib.md5(f"{symbol}_{period}".encode()).hexdigest()

    # 从缓存或数据库获取
    data = fetch_from_database(cache_key)
    if not data:
        data = generate_data(symbol, period)
        save_to_cache(cache_key, data)

    return data
```

---

## 国际化支持

### 1. 多语言文本

```python
# 创建语言字典
LANGUAGES = {
    'zh': {
        'total_return': '总收益率',
        'sharpe_ratio': '夏普比率',
        'max_drawdown': '最大回撤',
        'performance_report': '性能报告'
    },
    'en': {
        'total_return': 'Total Return',
        'sharpe_ratio': 'Sharpe Ratio',
        'max_drawdown': 'Maximum Drawdown',
        'performance_report': 'Performance Report'
    }
}

def get_text(key: str, lang: str = 'zh') -> str:
    """获取翻译文本"""
    return LANGUAGES.get(lang, {}).get(key, key)
```

### 2. 在模板中使用

```html
<!-- 使用翻译函数 -->
<h1>{{ get_text('performance_report', language) }}</h1>
<table>
    <thead>
        <tr>
            <th>{{ get_text('total_return', language) }}</th>
            <th>{{ get_text('sharpe_ratio', language) }}</th>
            <th>{{ get_text('max_drawdown', language) }}</th>
        </tr>
    </thead>
    <tbody>
        <!-- 数据行 -->
    </tbody>
</table>
```

### 3. 数字格式本地化

```javascript
// 中文格式
function formatNumberCN(value) {
    return value.toLocaleString('zh-CN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

// 百分比格式
function formatPercentage(value) {
    return (value * 100).toFixed(2) + '%';
}

// 货币格式
function formatCurrency(value, currency = 'HKD') {
    return value.toLocaleString('zh-CN', {
        style: 'currency',
        currency: currency
    });
}
```

### 4. 日期本地化

```python
from datetime import datetime

def format_date(date: datetime, locale: str = 'zh-CN') -> str:
    """格式化日期"""
    if locale == 'zh-CN':
        return date.strftime('%Y年%m月%d日')
    else:
        return date.strftime('%B %d, %Y')
```

---

## 高级功能

### 1. 实时数据更新

```javascript
// WebSocket 连接
const socket = new WebSocket('ws://localhost:8000/ws/reports');

socket.onmessage = function(event) {
    const data = JSON.parse(event.data);
    updateReport(data);
};

function updateReport(data) {
    // 更新指标
    document.querySelector('#total-return').textContent = data.total_return + '%';
    document.querySelector('#sharpe-ratio').textContent = data.sharpe_ratio;

    // 更新图表
    Plotly.update('chart', {
        y: [data.portfolio_values]
    });
}
```

### 2. 动态报告生成

```python
def generate_dynamic_report(template_type: str, config: Dict) -> str:
    """动态生成报告"""
    # 根据配置决定使用的模板
    template = select_template(template_type, config)

    # 动态提取数据
    data = extract_data_from_sources(config)

    # 动态生成内容
    return template.render(**data)
```

### 3. 报告模板继承

```html
<!-- base.html -->
<!DOCTYPE html>
<html>
<head>
    {% block head %}{% endblock %}
</head>
<body>
    <header>{% block header %}{% endblock %}</header>
    <main>{% block content %}{% endblock %}</main>
    <footer>{% block footer %}{% endblock %}</footer>
</body>
</html>

<!-- performance.html 继承 base.html -->
{% extends "base.html" %}

{% block content %}
<section>
    <h2>性能分析</h2>
    <!-- 性能分析内容 -->
</section>
{% endblock %}
```

### 4. 组件化开发

```html
<!-- 创建可重用组件 -->
<!-- metric-card.html -->
<div class="metric-card">
    <div class="metric-label">{{ label }}</div>
    <div class="metric-value" style="color: {{ color }};">
        {{ value }}
    </div>
    <div class="metric-change">
        <i class="fas {{ icon }} mr-1"></i>
        {{ description }}
    </div>
</div>

<!-- 使用组件 -->
{% for metric in metrics %}
    {% include "metric-card.html" with {
        'label': metric.label,
        'value': metric.value,
        'color': metric.color,
        'icon': metric.icon,
        'description': metric.description
    } %}
{% endfor %}
```

---

## 最佳实践

### 1. 代码组织

```
templates/
├── base.html              # 基础模板
├── performance.html       # 性能分析模板
├── risk.html             # 风险评估模板
├── components/           # 组件目录
│   ├── metric-card.html
│   ├── chart-container.html
│   └── table.html
└── static/               # 静态资源
    ├── css/
    │   ├── base.css
    │   ├── custom.css
    │   └── print.css
    ├── js/
    │   ├── charts.js
    │   └── utils.js
    └── images/
```

### 2. 性能优化

**使用分页:**

```python
def paginate_data(data, page_size=100):
    """分页数据"""
    for i in range(0, len(data), page_size):
        yield data[i:i+page_size]
```

**延迟加载图表:**

```javascript
// 使用 Intersection Observer
const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            renderChart(entry.target);
            observer.unobserve(entry.target);
        }
    });
});

document.querySelectorAll('.chart-container').forEach(chart => {
    observer.observe(chart);
});
```

### 3. 错误处理

```python
def safe_render(template, data):
    """安全的模板渲染"""
    try:
        # 数据验证
        if not validate_data(data):
            raise ValueError("数据验证失败")

        # 安全渲染
        return template.render(**data)

    except TemplateError as e:
        logger.error(f"模板渲染错误: {e}")
        return render_error_template(str(e))

    except Exception as e:
        logger.error(f"未知错误: {e}")
        return render_error_template("系统错误，请联系管理员")
```

### 4. 测试

```python
import unittest

class TestReportGenerator(unittest.TestCase):
    def test_performance_data_generation(self):
        """测试性能数据生成"""
        generator = ReportGenerator()
        data = generator._generate_performance_data('0700.HK', '2023-01-01')

        self.assertIn('total_return', data)
        self.assertIn('sharpe_ratio', data)
        self.assertIsInstance(data['total_return'], (int, float))

    def test_template_rendering(self):
        """测试模板渲染"""
        generator = ReportGenerator()
        config = ReportConfig('performance', '0700.HK', '2023-01-01')

        html = generator.generate_report(config)
        self.assertIn('总收益率', html)
        self.assertIn('夏普比率', html)
```

### 5. 部署建议

**生产环境配置:**

```python
# 生产环境设置
DEBUG = False
TEMPLATES_AUTO_RELOAD = False
TEMPLATES_DIRS = ['/var/www/templates']

# 缓存设置
CACHE_TYPE = 'redis'
CACHE_DEFAULT_TIMEOUT = 300

# 日志设置
LOG_LEVEL = 'INFO'
LOG_FILE = '/var/log/reports.log'
```

**Docker 部署:**

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:app"]
```

---

## 总结

本指南涵盖了报告模板系统的所有自定义选项。通过这些技术，您可以：

1. **快速定制** - 修改品牌、样式、布局
2. **深度扩展** - 添加新功能、新模板、新图表
3. **性能优化** - 分页、缓存、延迟加载
4. **国际化** - 多语言、多格式支持
5. **生产就绪** - 错误处理、测试、部署

如需更多信息，请参考：
- [README.md](./README.md) - 完整文档
- [TEMPLATE_VARIABLES.md](./TEMPLATE_VARIABLES.md) - 变量说明
- [example_usage.py](./example_usage.py) - 使用示例

---

© 2025 CODEX Trading System. All Rights Reserved.
