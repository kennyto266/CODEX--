#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
报告模板生成器
==================

专业的报告模板生成工具，支持创建性能分析、风险评估、策略对比等5种报告类型。

作者: CODEX Trading System
版本: 1.0
日期: 2025-11-09
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from jinja2 import Environment, FileSystemLoader, TemplateError
from dataclasses import dataclass, asdict
import pandas as pd


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ReportConfig:
    """报告配置类"""
    template_type: str  # 模板类型: performance, risk, comparison, executive_summary, technical
    symbol: str = "N/A"
    period: str = "N/A"
    output_dir: str = "./reports"
    output_filename: str = ""
    include_charts: bool = True
    print_mode: bool = False


class ReportGenerator:
    """报告生成器类"""

    # 支持的模板类型
    TEMPLATE_TYPES = {
        'performance': 'performance.html',
        'risk': 'risk.html',
        'comparison': 'comparison.html',
        'executive_summary': 'executive_summary.html',
        'technical': 'technical_appendix.html'
    }

    def __init__(self, template_dir: str = None):
        """
        初始化报告生成器

        Args:
            template_dir: 模板目录路径
        """
        if template_dir is None:
            # Use current directory where templates are located
            self.template_dir = os.path.dirname(__file__)
        else:
            self.template_dir = template_dir

        self.env = Environment(
            loader=FileSystemLoader(self.template_dir)
        )
        logger.info(f"Report generator initialized, template directory: {self.template_dir}")

    def _load_template(self, template_name: str):
        """
        加载模板

        Args:
            template_name: 模板文件名

        Returns:
            模板对象

        Raises:
            FileNotFoundError: 模板文件不存在
        """
        try:
            return self.env.get_template(template_name)
        except TemplateError as e:
            logger.error(f"加载模板失败: {template_name} - {e}")
            raise

    def _prepare_base_data(self, config: ReportConfig) -> Dict[str, Any]:
        """
        准备基础数据

        Args:
            config: 报告配置

        Returns:
            基础数据字典
        """
        return {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'symbol': config.symbol,
            'period': config.period,
            'title': config.template_type.replace('_', ' ').title()
        }

    def _generate_performance_data(self, symbol: str, period: str) -> Dict[str, Any]:
        """
        生成性能分析数据

        Args:
            symbol: 股票代码
            period: 期间

        Returns:
            性能数据字典
        """
        # TODO: 从实际数据源获取数据
        # 此处使用模拟数据
        dates = pd.date_range(start='2023-01', periods=12, freq='M').strftime('%Y-%m').tolist()
        portfolio = [i * 2 + (i ** 0.5) for i in range(12)]
        benchmark = [i * 1.5 + (i ** 0.3) for i in range(12)]

        monthly_returns = [
            {
                "date": dates[i],
                "return": round(portfolio[i] - (portfolio[i-1] if i > 0 else 0), 2),
                "cumulative": round(portfolio[i], 2),
                "benchmark": round(benchmark[i], 2),
                "alpha": round(portfolio[i] - benchmark[i], 2)
            }
            for i in range(12)
        ]

        return {
            # 核心指标
            'total_return': 25.63,
            'annual_return': 12.84,
            'sharpe_ratio': 1.85,
            'sortino_ratio': 2.12,
            'calmar_ratio': 1.58,
            'information_ratio': 0.82,
            'treynor_ratio': 0.15,
            'max_drawdown': -8.23,
            'volatility': 14.32,
            'win_rate': 62.5,
            'win_count': 45,
            'loss_count': 27,

            # 图表数据
            'performance_data': {
                'dates': dates,
                'portfolio': portfolio,
                'benchmark': benchmark
            },
            'attribution_data': {
                'labels': ['技术分析', '基本面', '宏观经济', '市场情绪', '其他'],
                'values': [35, 25, 20, 15, 5]
            },

            # 月度收益
            'monthly_returns': monthly_returns
        }

    def _generate_risk_data(self, symbol: str, period: str) -> Dict[str, Any]:
        """
        生成风险评估数据

        Args:
            symbol: 股票代码
            period: 期间

        Returns:
            风险数据字典
        """
        dates = pd.date_range(start='2023-01', periods=12, freq='M').strftime('%Y-%m').tolist()
        returns = [round((i * 0.02) - 0.01, 4) for i in range(len(dates) * 20)]

        return {
            # 风险概览
            'overall_risk_level': 'medium',
            'var_90': 2.34,
            'var_95': 3.45,
            'var_99': 5.67,
            'cvar_95': 4.23,
            'beta': 1.12,
            'max_drawdown': -8.23,
            'downside_deviation': 9.45,
            'sharpe_ratio': 1.85,
            'sortino_ratio': 2.12,

            # 图表数据
            'var_data': {
                'returns': returns,
                'var_95': -3.45,
                'max_y': 15
            },
            'drawdown_data': {
                'dates': dates,
                'values': [0, -1.2, -3.5, -8.2, -5.1, 0, -2.3, 0, -1.5, 0, -0.8, 0]
            },
            'stress_data': {
                'scenarios': ['市场崩盘', '经济衰退', '利率上升', '地缘政治', '流动性危机'],
                'impact': [-15.2, -8.5, -5.3, -6.8, -12.4]
            },

            # 风险事件
            'risk_events': [
                {
                    "date": "2023-03-15",
                    "description": "市场调整事件",
                    "severity": "high",
                    "loss": -8.2
                },
                {
                    "date": "2023-07-20",
                    "description": "单日大幅波动",
                    "severity": "medium",
                    "loss": -3.5
                }
            ]
        }

    def _generate_comparison_data(self, symbol: str, period: str) -> Dict[str, Any]:
        """
        生成策略对比数据

        Args:
            symbol: 股票代码
            period: 期间

        Returns:
            策略对比数据字典
        """
        strategies = [
            {
                "name": "KDJ策略",
                "type": "技术分析",
                "rank": 1,
                "total_return": 25.63,
                "annual_return": 12.84,
                "volatility": 14.32,
                "sharpe_ratio": 1.85,
                "sortino_ratio": 2.12,
                "calmar_ratio": 1.58,
                "information_ratio": 0.82,
                "max_drawdown": -8.23,
                "win_rate": 62.5,
                "trade_count": 156,
                "rating": 5,
                "pros": ["高夏普比率", "回撤控制良好", "信号清晰"],
                "cons": ["交易频率较高", "对市场环境敏感"],
                "recommendation": "适合稳健型投资者"
            },
            {
                "name": "RSI策略",
                "type": "技术分析",
                "rank": 2,
                "total_return": 22.45,
                "annual_return": 11.23,
                "volatility": 15.67,
                "sharpe_ratio": 1.43,
                "sortino_ratio": 1.89,
                "calmar_ratio": 1.35,
                "information_ratio": 0.68,
                "max_drawdown": -9.12,
                "win_rate": 58.3,
                "trade_count": 89,
                "rating": 4,
                "pros": ["参数简单", "易于理解"],
                "cons": ["在震荡市场中表现一般"],
                "recommendation": "适合初学者"
            },
            {
                "name": "MACD策略",
                "type": "技术分析",
                "rank": 3,
                "total_return": 20.12,
                "annual_return": 10.06,
                "volatility": 13.21,
                "sharpe_ratio": 1.52,
                "sortino_ratio": 1.98,
                "calmar_ratio": 1.28,
                "information_ratio": 0.75,
                "max_drawdown": -9.85,
                "win_rate": 55.6,
                "trade_count": 67,
                "rating": 4,
                "pros": ["趋势跟踪能力强", "信号滞后性小"],
                "cons": ["在横盘市场中容易产生虚假信号"],
                "recommendation": "适合趋势行情"
            }
        ]

        dates = pd.date_range(start='2023-01', periods=12, freq='M').strftime('%Y-%m').tolist()
        performance_comparison = {
            "dates": dates,
            "strategies": [
                {"name": s["name"], "returns": [i * 2 + j for i, j in enumerate([1, 2, 0.5])]}
                for s in strategies
            ]
        }

        risk_return_data = {
            "strategies": [
                {
                    "name": s["name"],
                    "risk": s["volatility"],
                    "return": s["annual_return"],
                    "rank": s["rank"]
                }
                for s in strategies
            ]
        }

        correlation_matrix = [
            [1.00, 0.75, 0.68],
            [0.75, 1.00, 0.72],
            [0.68, 0.72, 1.00]
        ]

        return {
            'strategies': strategies,
            'performance_comparison': performance_comparison,
            'risk_return_data': risk_return_data,
            'correlation_data': {
                'strategies': [s["name"] for s in strategies],
                'matrix': correlation_matrix
            }
        }

    def _generate_executive_summary_data(self, symbol: str, period: str) -> Dict[str, Any]:
        """
        生成执行摘要数据

        Args:
            symbol: 股票代码
            period: 期间

        Returns:
            执行摘要数据字典
        """
        return {
            'report_title': '量化交易策略分析报告',
            'date_range': period,
            'executive_summary': '本报告分析了当前量化交易策略的表现，主要策略在回测期间表现良好，累计收益率达到25.63%，夏普比率为1.85。风险控制方面，最大回撤控制在8.23%以内，整体风险可控。建议继续保持现有策略，并根据市场环境适度调整仓位配置。',

            # 风险指标
            'beta': 1.12,

            # KPI 指标
            'aum': 10000000.0,
            'aum_change': 5.2,
            'cumulative_return': 25.63,
            'annual_return': 12.84,
            'benchmark_return': 8.5,
            'sharpe_ratio': 1.85,
            'max_drawdown': -8.23,
            'win_rate': 62.5,
            'win_count': 45,
            'loss_count': 27,

            # 图表数据
            'performance_data': {
                'dates': pd.date_range(start='2023-01', periods=12, freq='M').strftime('%Y-%m').tolist(),
                'portfolio': [i * 2 + (i ** 0.5) for i in range(12)],
                'benchmark': [i * 1.5 + (i ** 0.3) for i in range(12)]
            },
            'risk_data': {
                'score': 65
            },

            # 主要发现
            'key_findings': [
                {
                    "type": "positive",
                    "icon": "check-circle",
                    "title": "策略表现优异",
                    "description": "累计收益率25.63%，超越基准17.13个百分点，夏普比率达到1.85，风险调整后收益表现良好。",
                    "impact": "年化收益提升12.84%"
                },
                {
                    "type": "positive",
                    "icon": "chart-line",
                    "title": "风险控制有效",
                    "description": "最大回撤控制在8.23%以内，VaR(95%)为3.45%，风险水平在可接受范围内。",
                    "impact": "降低投资风险"
                },
                {
                    "type": "neutral",
                    "icon": "info-circle",
                    "title": "交易频率较高",
                    "description": "回测期间共执行156笔交易，月均13笔，胜率62.5%，建议进一步优化信号。",
                    "impact": "交易成本约0.15%"
                }
            ],

            # 投资建议
            'recommendations': [
                {
                    "title": "保持现有策略",
                    "description": "继续执行当前量化策略，历史回测表现良好，建议保持不变。",
                    "priority": "high",
                    "timeframe": "持续执行"
                },
                {
                    "title": "优化仓位管理",
                    "description": "根据市场波动率动态调整仓位，在低波动期适当增加仓位，高波动期降低风险敞口。",
                    "priority": "medium",
                    "timeframe": "1-3个月"
                },
                {
                    "title": "增加另类数据",
                    "description": "考虑引入更多宏观经济指标和市场情绪数据，提升模型预测精度。",
                    "priority": "low",
                    "timeframe": "3-6个月"
                }
            ],

            # 风险提示
            'risks': [
                {
                    "title": "市场风险",
                    "description": "极端市场条件下（如黑天鹅事件），策略可能面临较大损失。"
                },
                {
                    "title": "模型风险",
                    "description": "历史数据拟合的模型在未来可能失效，需定期验证和更新。"
                },
                {
                    "title": "流动性风险",
                    "description": "小盘股流动性可能不足，实际交易中可能面临滑点成本。"
                }
            ],

            # 行动计划
            'action_items': [
                {
                    "task": "每周监控策略表现",
                    "owner": "量化团队",
                    "deadline": "每周五",
                    "priority": "high",
                    "completed": False
                },
                {
                    "task": "每月回顾并优化参数",
                    "owner": "研究团队",
                    "deadline": "每月末",
                    "priority": "medium",
                    "completed": False
                },
                {
                    "task": "季度风险评估",
                    "owner": "风险管理部",
                    "deadline": "每季度末",
                    "priority": "high",
                    "completed": False
                },
                {
                    "task": "年度策略审查",
                    "owner": "投委会",
                    "deadline": "年底",
                    "priority": "high",
                    "completed": False
                }
            ]
        }

    def _generate_technical_data(self, symbol: str, period: str) -> Dict[str, Any]:
        """
        生成技术附录数据

        Args:
            symbol: 股票代码
            period: 期间

        Returns:
            技术附录数据字典
        """
        return {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    def _get_data_generator(self, template_type: str):
        """
        获取数据生成器

        Args:
            template_type: 模板类型

        Returns:
            数据生成函数
        """
        generators = {
            'performance': self._generate_performance_data,
            'risk': self._generate_risk_data,
            'comparison': self._generate_comparison_data,
            'executive_summary': self._generate_executive_summary_data,
            'technical': self._generate_technical_data
        }
        return generators.get(template_type)

    def generate_report(
        self,
        config: ReportConfig,
        custom_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        生成报告

        Args:
            config: 报告配置
            custom_data: 自定义数据（可选）

        Returns:
            生成的HTML内容

        Raises:
            ValueError: 无效的模板类型
            Exception: 渲染失败
        """
        if config.template_type not in self.TEMPLATE_TYPES:
            raise ValueError(
                f"无效的模板类型: {config.template_type}。"
                f"支持的类型: {', '.join(self.TEMPLATE_TYPES.keys())}"
            )

        # 准备基础数据
        data = self._prepare_base_data(config)

        # 生成或合并数据
        data_generator = self._get_data_generator(config.template_type)
        if data_generator:
            template_data = data_generator(config.symbol, config.period)
            data.update(template_data)

        # 合并自定义数据
        if custom_data:
            data.update(custom_data)

        # 加载并渲染模板
        template_name = self.TEMPLATE_TYPES[config.template_type]
        template = self._load_template(template_name)

        try:
            html = template.render(**data)
            logger.info(f"报告生成成功: {config.template_type}")
            return html
        except Exception as e:
            logger.error(f"渲染模板失败: {e}")
            raise

    def save_report(
        self,
        config: ReportConfig,
        custom_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        生成并保存报告

        Args:
            config: 报告配置
            custom_data: 自定义数据（可选）

        Returns:
            输出文件路径
        """
        # 生成HTML
        html = self.generate_report(config, custom_data)

        # 确保输出目录存在
        os.makedirs(config.output_dir, exist_ok=True)

        # 确定文件名
        if not config.output_filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            config.output_filename = f"{config.template_type}_{timestamp}.html"

        # 完整路径
        output_path = os.path.join(config.output_dir, config.output_filename)

        # 保存文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        logger.info(f"报告已保存到: {output_path}")
        return output_path

    def batch_generate(
        self,
        configs: List[ReportConfig],
        custom_data: Optional[Dict[str, List[Dict[str, Any]]]] = None
    ) -> List[str]:
        """
        批量生成报告

        Args:
            configs: 报告配置列表
            custom_data: 自定义数据字典 {config_index: data}

        Returns:
            输出文件路径列表
        """
        output_paths = []

        for i, config in enumerate(configs):
            # 获取对应的自定义数据
            data = None
            if custom_data and i in custom_data:
                data = custom_data[i]

            # 生成并保存
            path = self.save_report(config, data)
            output_paths.append(path)

        logger.info(f"批量生成完成，共 {len(output_paths)} 个报告")
        return output_paths


def main():
    """主函数 - 演示用法"""
    # 创建报告生成器
    generator = ReportGenerator()

    # 示例1: 生成性能分析报告
    config1 = ReportConfig(
        template_type='performance',
        symbol='0700.HK',
        period='2023-01-01 至 2023-12-31',
        output_dir='./output/reports/performance'
    )

    path1 = generator.save_report(config1)
    print(f"性能分析报告已生成: {path1}")

    # 示例2: 生成风险评估报告
    config2 = ReportConfig(
        template_type='risk',
        symbol='0700.HK',
        period='2023-01-01 至 2023-12-31',
        output_dir='./output/reports/risk'
    )

    path2 = generator.save_report(config2)
    print(f"风险评估报告已生成: {path2}")

    # 示例3: 生成策略对比报告
    config3 = ReportConfig(
        template_type='comparison',
        symbol='0700.HK',
        period='2023-01-01 至 2023-12-31',
        output_dir='./output/reports/comparison'
    )

    path3 = generator.save_report(config3)
    print(f"策略对比报告已生成: {path3}")

    # 示例4: 批量生成
    configs = [
        ReportConfig('executive_summary', '0700.HK', '2023-01-01 至 2023-12-31', './output/reports'),
        ReportConfig('technical', '0700.HK', '2023-01-01 至 2023-12-31', './output/reports')
    ]

    paths = generator.batch_generate(configs)
    print(f"批量生成完成: {len(paths)} 个报告")


if __name__ == '__main__':
    main()
