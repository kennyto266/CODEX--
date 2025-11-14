# 报告模板系统 - 快速参考

## 🚀 快速开始

### 安装依赖
```bash
pip install jinja2 pandas
```

### 运行示例
```bash
cd src/dashboard/templates
python example_usage.py
```

### 基本使用
```python
from report_generator import ReportGenerator, ReportConfig

generator = ReportGenerator()
config = ReportConfig(
    template_type='performance',
    symbol='0700.HK',
    period='2023-01-01 至 2023-12-31'
)
output_path = generator.save_report(config)
print(f"报告已生成: {output_path}")
```

---

## 📋 模板类型

| 类型 | 文件名 | 描述 | 大小 |
|------|--------|------|------|
| performance | performance.html | 性能分析报告 | 21KB |
| risk | risk.html | 风险评估报告 | 21KB |
| comparison | comparison.html | 策略对比报告 | 36KB |
| executive_summary | executive_summary.html | 执行摘要报告 | 29KB |
| technical | technical_appendix.html | 技术附录 | 30KB |

---

## 🔧 核心文件

```
src/dashboard/templates/
├── 报告模板 (5个)
│   ├── performance.html
│   ├── risk.html
│   ├── comparison.html
│   ├── executive_summary.html
│   └── technical_appendix.html
├── 工具和示例
│   ├── report_generator.py      # 报告生成器
│   └── example_usage.py         # 使用示例
└── 文档
    ├── README.md                 # 完整文档
    ├── TEMPLATE_VARIABLES.md     # 变量说明
    ├── CUSTOMIZATION_GUIDE.md    # 自定义指南
    ├── QUICK_START.md            # 快速参考 (本文件)
    └── PHASE7A_COMPLETION_REPORT.md # 完成报告
```

---

## 📊 核心变量

### 通用变量
```python
symbol: str           # 股票代码
period: str           # 分析期间
timestamp: str        # 生成时间
```

### 性能分析 (performance)
```python
total_return: float   # 总收益率
annual_return: float  # 年化收益率
sharpe_ratio: float   # 夏普比率
max_drawdown: float   # 最大回撤
volatility: float     # 波动率
win_rate: float       # 胜率
```

### 风险评估 (risk)
```python
overall_risk_level: str  # 风险等级
var_95: float           # VaR 95%
cvar_95: float          # CVaR 95%
beta: float             # Beta系数
```

### 策略对比 (comparison)
```python
strategies: list     # 策略列表
performance_comparison: dict  # 性能对比数据
correlation_data: dict       # 相关性矩阵
```

### 执行摘要 (executive_summary)
```python
key_findings: list        # 主要发现
recommendations: list     # 投资建议
action_items: list        # 行动计划
```

---

## 🎨 自定义样式

### 修改颜色
```css
:root {
    --primary-color: #3b82f6;
    --success-color: #10b981;
    --danger-color: #ef4444;
}
```

### 自定义卡片
```html
<div class="custom-card">
    <h3>自定义标题</h3>
    <p>自定义内容</p>
</div>
```

---

## 📈 图表配置

### 性能曲线
```javascript
const trace1 = {
    x: dates,
    y: portfolio,
    type: 'scatter',
    mode: 'lines',
    name: '投资组合'
};
Plotly.newPlot('chart-id', [trace1], layout);
```

### 风险散点图
```javascript
const trace = {
    x: [risk],
    y: [return],
    type: 'scatter',
    mode: 'markers',
    marker: { size: 15 }
};
```

---

## 🏗 批量生成

### 多报告
```python
configs = [
    ReportConfig('performance', '0700.HK', '2023-Q1'),
    ReportConfig('risk', '0700.HK', '2023-Q1')
]
paths = generator.batch_generate(configs)
```

### 多股票
```python
symbols = ['0700.HK', '0388.HK', '0939.HK']
configs = [ReportConfig('performance', s, '2023-Q1') for s in symbols]
paths = generator.batch_generate(configs)
```

---

## 🎯 最佳实践

### 1. 数据验证
```python
def validate_data(data):
    required = ['total_return', 'sharpe_ratio']
    for field in required:
        if field not in data:
            raise ValueError(f"缺少字段: {field}")
```

### 2. 错误处理
```python
try:
    html = generator.generate_report(config)
except Exception as e:
    logger.error(f"生成失败: {e}")
    return render_error_template(str(e))
```

### 3. 性能优化
```python
# 使用分页
for page in paginate_data(large_data, 100):
    render_partial_report(page)

# 延迟加载图表
const observer = new IntersectionObserver((entries) => {
    if (entry.isIntersecting) {
        renderChart(entry.target);
        observer.unobserve(entry.target);
    }
});
```

---

## 🔍 调试技巧

### 检查模板变量
```html
<!-- 模板中调试 -->
{{ debug(total_return) }}

<!-- 或使用 -->
<pre>{{ __dict__ }}</pre>
```

### 查看渲染错误
```python
try:
    template = env.get_template('template.html')
    html = template.render(**data)
except TemplateError as e:
    print(f"模板错误: {e}")
```

### 日志记录
```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("报告生成完成")
```

---

## 📚 更多资源

- **完整文档**: README.md
- **变量说明**: TEMPLATE_VARIABLES.md
- **自定义指南**: CUSTOMIZATION_GUIDE.md
- **使用示例**: example_usage.py
- **完成报告**: PHASE7A_COMPLETION_REPORT.md

---

## ⚡ 常用代码片段

### 添加新指标
```python
# 在数据生成器中
data['custom_metric'] = 42.5

# 在模板中
<div class="metric-value">{{ custom_metric }}%</div>
```

### 条件显示
```html
{% if show_section %}
<section>内容</section>
{% endif %}
```

### 循环显示
```html
{% for strategy in strategies %}
<div class="strategy-card">
    <h3>{{ strategy.name }}</h3>
</div>
{% endfor %}
```

### 自定义过滤器
```python
# 注册自定义过滤器
def format_currency(value):
    return f"${value:,.2f}"

env.filters['currency'] = format_currency

# 模板中使用
{{ price|currency }}
```

---

## 🆘 常见问题

### Q: 模板找不到
A: 检查模板目录路径是否正确
```python
generator = ReportGenerator(template_dir='/path/to/templates')
```

### Q: 变量未定义
A: 使用默认值或检查数据
```python
{{ variable or 0 }}
{{ variable|default('N/A') }}
```

### Q: 图表不显示
A: 检查数据格式
```python
# 确保数据是列表
x: list, y: list
```

### Q: 样式不生效
A: 检查CSS加载
```html
<link rel="stylesheet" href="/path/to/css">
```

---

## 📞 支持

如需帮助，请查看：
1. 完整文档 (README.md)
2. 示例代码 (example_usage.py)
3. 变量说明 (TEMPLATE_VARIABLES.md)
4. 自定义指南 (CUSTOMIZATION_GUIDE.md)

---

© 2025 CODEX Trading System. All Rights Reserved.
