"""
HTML Report Example
HTML报告系统使用示例

This example demonstrates how to use the HTML report generation system
to create comprehensive, interactive reports.
"""

from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import random
from pathlib import Path
from typing import Dict, List, Any

from html_generator import HTMLReportGenerator, ReportMetadata, ReportConfig
from html_charts import ChartGenerator, ChartConfig, ChartData
from html_tables import DataTableGenerator, TableData, ColumnConfig, TableConfig


def generate_sample_data():
    """生成示例数据"""
    # 生成模拟的策略数据
    strategies = [
        {
            "name": "KDJ策略",
            "type": "震荡指标",
            "return": 15.23,
            "sharpe": 2.01,
            "max_drawdown": -3.45,
            "win_rate": 75.8,
            "trades": 178,
            "status": "active"
        },
        {
            "name": "MA交叉策略",
            "type": "趋势跟踪",
            "return": 12.45,
            "sharpe": 1.85,
            "max_drawdown": -4.23,
            "win_rate": 72.5,
            "trades": 156,
            "status": "active"
        },
        {
            "name": "RSI策略",
            "type": "均值回归",
            "return": 8.67,
            "sharpe": 1.52,
            "max_drawdown": -6.78,
            "win_rate": 65.3,
            "trades": 203,
            "status": "active"
        },
        {
            "name": "CCI策略",
            "type": "趋势指标",
            "return": 10.23,
            "sharpe": 1.68,
            "max_drawdown": -5.12,
            "win_rate": 69.4,
            "trades": 189,
            "status": "inactive"
        }
    ]

    # 生成模拟的KPI数据
    kpis = [
        {
            "title": "总收益率",
            "value": 15.68,
            "unit": "%",
            "change": 2.34,
            "trend": "up",
            "icon": "graph-up"
        },
        {
            "title": "夏普比率",
            "value": 1.85,
            "change": 0.12,
            "trend": "up",
            "icon": "target"
        },
        {
            "title": "最大回撤",
            "value": -5.23,
            "unit": "%",
            "change": -0.85,
            "trend": "down",
            "icon": "shield-exclamation"
        },
        {
            "title": "胜率",
            "value": 68.5,
            "unit": "%",
            "change": 3.2,
            "trend": "up",
            "icon": "check-circle"
        }
    ]

    # 生成月度表现数据
    dates = pd.date_range(start=datetime.now() - timedelta(days=180), end=datetime.now(), freq='D')
    monthly_data = []
    for i in range(6):
        start_idx = i * 30
        end_idx = min((i + 1) * 30, len(dates))
        month_data = {
            "date": dates[start_idx].strftime("%Y-%m"),
            "start_nav": 1.0000 + i * 0.02,
            "end_nav": 1.0000 + (i + 1) * 0.02 + random.uniform(-0.02, 0.04),
            "return": random.uniform(-0.02, 0.05),
            "cumulative": 0.02 * (i + 1) + random.uniform(-0.05, 0.1),
            "max_dd": random.uniform(-0.01, -0.03),
            "trades": random.randint(10, 25)
        }
        monthly_data.append(month_data)

    # 生成交易记录
    trades = []
    for i in range(50):
        trade = {
            "date": (datetime.now() - timedelta(days=random.randint(0, 180))).strftime("%Y-%m-%d"),
            "symbol": random.choice(["0700.HK", "0388.HK", "1398.HK", "0939.HK"]),
            "action": random.choice(["BUY", "SELL"]),
            "quantity": random.randint(100, 1000),
            "price": random.uniform(100, 500),
            "commission": random.uniform(10, 50),
            "pnl": random.uniform(-500, 800)
        }
        trades.append(trade)

    # 生成投资组合数据
    portfolio = [
        {
            "symbol": "0700.HK",
            "name": "腾讯控股",
            "quantity": 500,
            "cost_basis": 350.0,
            "current_price": 385.5,
            "market_value": 192750,
            "unrealized_pnl": 17750,
            "weight": 35.2
        },
        {
            "symbol": "0388.HK",
            "name": "港交所",
            "quantity": 300,
            "cost_basis": 280.0,
            "current_price": 295.0,
            "market_value": 88500,
            "unrealized_pnl": 4500,
            "weight": 16.1
        },
        {
            "symbol": "1398.HK",
            "name": "工商银行",
            "quantity": 2000,
            "cost_basis": 4.2,
            "current_price": 4.5,
            "market_value": 9000,
            "unrealized_pnl": 600,
            "weight": 1.6
        }
    ]

    # 生成风险指标
    risk_metrics = {
        "年化波动率": 12.5,
        "VaR (95%)": -2.3,
        "CVaR (95%)": -3.5,
        "最大回撤": -5.23,
        "平均回撤": -1.8,
        "Calmar比率": 3.52,
        "Beta系数": 0.85,
        "Alpha": 3.2
    }

    # 生成活动记录
    activities = [
        {
            "title": "策略执行成功",
            "description": "KDJ策略在0700.HK上产生买入信号",
            "timestamp": datetime.now() - timedelta(hours=2),
            "type": "success"
        },
        {
            "title": "数据更新完成",
            "description": "成功获取最新市场数据",
            "timestamp": datetime.now() - timedelta(hours=5),
            "type": "info"
        },
        {
            "title": "风险预警",
            "description": "RSI策略接近超买区域",
            "timestamp": datetime.now() - timedelta(hours=8),
            "type": "warning"
        }
    ]

    return {
        "strategies": strategies,
        "kpis": kpis,
        "monthly_data": monthly_data,
        "trades": trades,
        "portfolio": portfolio,
        "risk_metrics": risk_metrics,
        "activities": activities,
        "period": "2024年1月-11月",
        "total_return": 15.68,
        "annualized_return": 18.45,
        "sharpe_ratio": 1.85,
        "max_drawdown": -5.23,
        "win_rate": 68.5,
        "strategy_count": 4,
        "total_trades": 537,
        "executive_summary": {
            "title": "量化策略表现总结",
            "content": "本报告评估了4个量化策略在2024年1月至11月期间的表现。所有策略均实现正收益，整体表现优于基准指数。",
            "key_points": [
                "策略总收益达到15.68%，年化收益率18.45%",
                "夏普比率1.85，风险调整后收益表现优异",
                "最大回撤控制在5.23%以内，风险可控",
                "交易胜率68.5%，策略稳定性较高"
            ]
        },
        "recommendations": {
            "策略优化建议": [
                "继续使用KDJ策略，该策略表现最为优异",
                "适当增加仓位配置，提高资金利用率",
                "关注市场趋势变化，及时调整策略参数"
            ],
            "风险管理建议": [
                "建议设置止损位在-7%以控制下行风险",
                "定期评估投资组合相关性，降低集中度风险"
            ],
            "市场展望": [
                "预计短期内市场将保持震荡格局",
                "关注政策变化对港股市场的影响"
            ]
        },
        "strengths": [
            "整体收益表现优于基准指数",
            "风险控制措施有效，最大回撤较小",
            "交易频率适中，成本可控",
            "策略稳定性较高，可持续性强"
        ],
        "improvements": [
            "考虑增加多元化投资以降低风险",
            "优化止损机制，缩短恢复时间",
            "增强市场环境适应性",
            "定期回顾和调整策略参数"
        ]
    }


def create_dashboard_example():
    """创建仪表板报告示例"""
    print("Creating dashboard example...")

    # 初始化HTML报告生成器
    generator = HTMLReportGenerator(
        template_dir="templates/html",
        output_dir="reports/output"
    )

    # 创建报告元数据
    metadata = ReportMetadata(
        title="港股量化交易策略仪表板",
        subtitle="2024年1月-11月策略表现分析",
        author="港股量化交易系统",
        created_at=datetime.now(),
        version="2.0",
        description="全面展示港股量化交易策略的表现数据，包括收益、风险、交易记录等关键指标",
        keywords=["港股", "量化交易", "策略分析", "投资组合"]
    )

    # 生成示例数据
    data = generate_sample_data()

    # 创建仪表板
    output_path = generator.create_dashboard(
        data=data,
        metadata=metadata,
        config=ReportConfig(
            theme="modern",
            dark_mode=False,
            show_navigation=True,
            show_sidebar=True,
            include_toc=False
        )
    )

    print(f"Dashboard created: {output_path}")
    return output_path


def create_summary_example():
    """创建摘要报告示例"""
    print("Creating summary report example...")

    generator = HTMLReportGenerator(
        template_dir="templates/html",
        output_dir="reports/output"
    )

    metadata = ReportMetadata(
        title="量化策略执行摘要",
        subtitle="2024年第三季度报告",
        author="港股量化交易系统",
        created_at=datetime.now(),
        version="1.0"
    )

    data = generate_sample_data()

    output_path = generator.create_summary_report(
        data=data,
        metadata=metadata,
        config=ReportConfig(
            theme="modern",
            include_toc=True
        )
    )

    print(f"Summary report created: {output_path}")
    return output_path


def create_detailed_example():
    """创建详细报告示例"""
    print("Creating detailed report example...")

    generator = HTMLReportGenerator(
        template_dir="templates/html",
        output_dir="reports/output"
    )

    metadata = ReportMetadata(
        title="详细策略分析报告",
        subtitle="技术指标与风险管理深度分析",
        author="港股量化交易系统",
        created_at=datetime.now(),
        version="1.0"
    )

    data = generate_sample_data()

    output_path = generator.create_detailed_report(
        data=data,
        metadata=metadata,
        config=ReportConfig(
            theme="modern",
            include_toc=True
        )
    )

    print(f"Detailed report created: {output_path}")
    return output_path


def create_chart_examples():
    """创建图表示例"""
    print("Creating chart examples...")

    chart_gen = ChartGenerator(theme="light")

    # 创建K线图
    dates = pd.date_range(start=datetime.now() - timedelta(days=100), end=datetime.now())
    ohlc_data = pd.DataFrame({
        "open": np.random.randn(len(dates)).cumsum() + 400,
        "high": np.random.randn(len(dates)).cumsum() + 410,
        "low": np.random.randn(len(dates)).cumsum() + 390,
        "close": np.random.randn(len(dates)).cumsum() + 400,
        "volume": np.random.randint(1000000, 10000000, len(dates))
    }, index=dates)

    candlestick_config = ChartConfig(
        title="0700.HK K线图",
        xaxis_title="日期",
        yaxis_title="价格 (HKD)"
    )

    candlestick_chart = chart_gen.create_candlestick_chart(ohlc_data, candlestick_config)
    chart_output = chart_gen.export_chart(
        candlestick_chart,
        "reports/output/candlestick_chart.html"
    )
    print(f"Candlestick chart created: {chart_output}")

    # 创建饼图
    labels = ["港股", "A股", "美股", "债券", "现金"]
    values = [35, 25, 20, 15, 5]

    pie_chart = chart_gen.create_pie_chart(labels, values, hole=0.4)
    pie_output = chart_gen.export_chart(
        pie_chart,
        "reports/output/allocation_chart.html"
    )
    print(f"Pie chart created: {pie_output}")

    return [chart_output, pie_output]


def create_table_examples():
    """创建表格示例"""
    print("Creating table examples...")

    table_gen = DataTableGenerator()

    data = generate_sample_data()

    # 创建策略表现表格
    performance_html = table_gen.create_performance_table(
        strategies=data["strategies"],
        config=TableConfig(
            id="performance-table",
            title="策略表现对比",
            page_length=10,
            export_buttons=True
        )
    )

    # 保存HTML文件
    output_dir = Path("reports/output")
    output_dir.mkdir(parents=True, exist_ok=True)

    performance_path = output_dir / "performance_table.html"
    with open(performance_path, 'w', encoding='utf-8') as f:
        f.write(performance_html)

    print(f"Performance table created: {performance_path}")

    # 导出CSV
    columns = [
        ColumnConfig("name", "策略名称", "string"),
        ColumnConfig("type", "类型", "string"),
        ColumnConfig("return", "收益率", "percentage"),
        ColumnConfig("sharpe", "夏普比率", "number"),
        ColumnConfig("max_drawdown", "最大回撤", "percentage"),
    ]

    table_data = TableData(columns=columns, data=data["strategies"])
    csv_path = table_gen.export_to_csv(table_data, output_dir / "strategies.csv")
    print(f"CSV exported: {csv_path}")

    return [performance_path, csv_path]


def main():
    """主函数 - 运行所有示例"""
    print("=" * 60)
    print("HTML Report System - Examples")
    print("=" * 60)

    # 创建输出目录
    output_dir = Path("reports/output")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 创建各类报告
    dashboard_path = create_dashboard_example()
    summary_path = create_summary_example()
    detailed_path = create_detailed_example()
    chart_paths = create_chart_examples()
    table_paths = create_table_examples()

    # 打印总结
    print("\n" + "=" * 60)
    print("Examples completed successfully!")
    print("=" * 60)
    print(f"\nGenerated files:")
    print(f"  Dashboard: {dashboard_path}")
    print(f"  Summary: {summary_path}")
    print(f"  Detailed: {detailed_path}")
    print(f"  Charts: {len(chart_paths)} files")
    print(f"  Tables: {len(table_paths)} files")
    print(f"\nAll files are saved in: {output_dir.absolute()}")
    print("\nOpen any HTML file in your browser to view the report.")


if __name__ == "__main__":
    main()
