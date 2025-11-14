"""
Phase 8b - T354: 数据质量报告生成系统
实现质量评分算法、HTML/PDF报告生成、趋势分析和改进建议
"""

__all__ = [
    "QualityReporter",
    "QualityReport",
    "QualityScoreCalculator",
    "ReportGenerator",
    "TrendAnalyzer",
    "ReportFormatter"
]

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import base64
import io
import asyncio
from jinja2 import Template
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_agg import FigureCanvasAgg
import warnings

warnings.filterwarnings('ignore')

logger = logging.getLogger('quant_system.data.quality_reporter')


@dataclass
class QualityReport:
    """数据质量报告"""
    symbol: str
    timestamp: datetime
    overall_score: float
    grade: str
    dimensions: Dict[str, float]
    validation_results: List[Dict[str, Any]] = field(default_factory=list)
    anomaly_results: List[Dict[str, Any]] = field(default_factory=list)
    verification_results: List[Dict[str, Any]] = field(default_factory=list)
    freshness_results: List[Dict[str, Any]] = field(default_factory=list)
    trends: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    charts: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'symbol': self.symbol,
            'timestamp': self.timestamp.isoformat(),
            'overall_score': self.overall_score,
            'grade': self.grade,
            'dimensions': self.dimensions,
            'validation_results': self.validation_results,
            'anomaly_results': self.anomaly_results,
            'verification_results': self.verification_results,
            'freshness_results': self.freshness_results,
            'trends': self.trends,
            'recommendations': self.recommendations,
            'summary': self.summary,
            'charts': self.charts,
            'metadata': self.metadata
        }

    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class QualityScoreCalculator:
    """质量评分计算器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化质量评分计算器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.weights = self.config.get('weights', {
            'completeness': 0.25,
            'accuracy': 0.25,
            'consistency': 0.20,
            'timeliness': 0.15,
            'validity': 0.10,
            'uniqueness': 0.05
        })
        self.grade_thresholds = self.config.get('grade_thresholds', {
            'A': 0.9,
            'B': 0.8,
            'C': 0.7,
            'D': 0.6,
            'F': 0.0
        })

    def calculate_overall_score(self, dimension_scores: Dict[str, float]) -> float:
        """
        计算总体质量分数

        Args:
            dimension_scores: 各维度分数

        Returns:
            总体分数 (0-1)
        """
        total_weight = 0.0
        weighted_score = 0.0

        for dimension, score in dimension_scores.items():
            weight = self.weights.get(dimension, 0.0)
            weighted_score += score * weight
            total_weight += weight

        if total_weight == 0:
            return 0.0

        return min(1.0, max(0.0, weighted_score / total_weight))

    def calculate_dimension_scores(self, validation_results: List[Dict[str, Any]],
                                  anomaly_results: List[Dict[str, Any]],
                                  verification_results: List[Dict[str, Any]],
                                  freshness_results: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        计算各维度分数

        Args:
            validation_results: 验证结果
            anomaly_results: 异常检测结果
            verification_results: 跨源验证结果
            freshness_results: 新鲜度检查结果

        Returns:
            各维度分数
        """
        scores = {}

        # 完整性 (Completeness)
        scores['completeness'] = self._calculate_completeness_score(validation_results)

        # 准确性 (Accuracy)
        scores['accuracy'] = self._calculate_accuracy_score(anomaly_results)

        # 一致性 (Consistency)
        scores['consistency'] = self._calculate_consistency_score(verification_results)

        # 及时性 (Timeliness)
        scores['timeliness'] = self._calculate_timeliness_score(freshness_results)

        # 有效性 (Validity)
        scores['validity'] = self._calculate_validity_score(validation_results)

        # 唯一性 (Uniqueness)
        scores['uniqueness'] = self._calculate_uniqueness_score(anomaly_results)

        return scores

    def _calculate_completeness_score(self, validation_results: List[Dict[str, Any]]) -> float:
        """计算完整性分数"""
        if not validation_results:
            return 1.0

        completeness_scores = []
        for result in validation_results:
            # 从验证结果中提取完整性信息
            if 'stages' in result:
                for stage_name, stage_result in result['stages'].items():
                    if 'details' in stage_result and 'completeness' in stage_result['details']:
                        completeness_pct = stage_result['details']['completeness']
                        if isinstance(completeness_pct, dict):
                            # 多个列的平均完整性
                            avg_completeness = np.mean(list(completeness_pct.values()))
                            completeness_scores.append(avg_completeness / 100)
                        else:
                            completeness_scores.append(completeness_pct / 100)

        if not completeness_scores:
            return 1.0

        return np.mean(completeness_scores)

    def _calculate_accuracy_score(self, anomaly_results: List[Dict[str, Any]]) -> float:
        """计算准确性分数"""
        if not anomaly_results:
            return 1.0

        total_anomalies = sum(
            len(result.get('anomalies', []))
            for result in anomaly_results
        )

        total_data_points = sum(
            result.get('summary', {}).get('total_anomalies', 0)
            for result in anomaly_results
        )

        if total_data_points == 0:
            return 1.0

        # 基于异常率计算准确性
        anomaly_rate = total_anomalies / total_data_points
        accuracy_score = max(0.0, 1.0 - anomaly_rate)

        return accuracy_score

    def _calculate_consistency_score(self, verification_results: List[Dict[str, Any]]) -> float:
        """计算一致性分数"""
        if not verification_results:
            return 1.0

        consistency_scores = []
        for result in verification_results:
            consistency_score = result.get('consistency_score', 0.0)
            consistency_scores.append(consistency_score)

        if not consistency_scores:
            return 1.0

        return np.mean(consistency_scores)

    def _calculate_timeliness_score(self, freshness_results: List[Dict[str, Any]]) -> float:
        """计算及时性分数"""
        if not freshness_results:
            return 1.0

        timeliness_scores = []
        for result in freshness_results:
            freshness_score = result.get('freshness_score', 0.0)
            timeliness_scores.append(freshness_score)

        if not timeliness_scores:
            return 1.0

        return np.mean(timeliness_scores)

    def _calculate_validity_score(self, validation_results: List[Dict[str, Any]]) -> float:
        """计算有效性分数"""
        if not validation_results:
            return 1.0

        validity_scores = []
        for result in validation_results:
            is_valid = result.get('is_valid', False)
            validity_scores.append(1.0 if is_valid else 0.5)

        return np.mean(validity_scores) if validity_scores else 1.0

    def _calculate_uniqueness_score(self, anomaly_results: List[Dict[str, Any]]) -> float:
        """计算唯一性分数"""
        total_duplicates = 0
        total_records = 0

        for result in anomaly_results:
            anomalies = result.get('anomalies', [])
            for anomaly in anomalies:
                if anomaly.get('type') == 'duplicate':
                    total_duplicates += 1
            total_records += 1

        if total_records == 0:
            return 1.0

        duplicate_rate = total_duplicates / total_records
        uniqueness_score = max(0.0, 1.0 - duplicate_rate)

        return uniqueness_score

    def get_grade(self, score: float) -> str:
        """
        根据分数获取等级

        Args:
            score: 质量分数

        Returns:
            等级 (A-F)
        """
        for grade, threshold in sorted(self.grade_thresholds.items(), key=lambda x: x[1], reverse=True):
            if score >= threshold:
                return grade
        return 'F'


class TrendAnalyzer:
    """趋势分析器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化趋势分析器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.trend_window = self.config.get('trend_window', 30)  # 天数
        self.min_data_points = self.config.get('min_data_points', 10)

    def analyze_trends(self, historical_reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析质量趋势

        Args:
            historical_reports: 历史报告列表

        Returns:
            趋势分析结果
        """
        if len(historical_reports) < self.min_data_points:
            return {
                'has_trend': False,
                'message': f"数据点不足 (需要 {self.min_data_points}，实际 {len(historical_reports)})"
            }

        try:
            # 按时间排序
            sorted_reports = sorted(historical_reports, key=lambda x: x['timestamp'])

            # 提取指标
            scores = [r['overall_score'] for r in sorted_reports]
            timestamps = [datetime.fromisoformat(r['timestamp']) for r in sorted_reports]

            # 计算趋势
            trend_result = self._calculate_trend(scores, timestamps)

            # 维度趋势
            dimension_trends = self._analyze_dimension_trends(sorted_reports)

            # 异常趋势
            anomaly_trends = self._analyze_anomaly_trends(sorted_reports)

            return {
                'has_trend': True,
                'overall_trend': trend_result,
                'dimension_trends': dimension_trends,
                'anomaly_trends': anomaly_trends,
                'data_points': len(sorted_reports),
                'time_range': {
                    'start': timestamps[0].isoformat(),
                    'end': timestamps[-1].isoformat()
                }
            }

        except Exception as e:
            logger.error(f"趋势分析失败: {str(e)}")
            return {
                'has_trend': False,
                'error': str(e)
            }

    def _calculate_trend(self, scores: List[float],
                        timestamps: List[datetime]) -> Dict[str, Any]:
        """计算趋势"""
        if len(scores) < 2:
            return {'direction': 'stable', 'slope': 0.0, 'r_squared': 0.0}

        # 简单线性回归
        x = np.arange(len(scores))
        slope, intercept = np.polyfit(x, scores, 1)
        r_squared = self._calculate_r_squared(scores, slope, intercept)

        # 确定方向
        if slope > 0.01:
            direction = 'improving'
        elif slope < -0.01:
            direction = 'declining'
        else:
            direction = 'stable'

        return {
            'direction': direction,
            'slope': slope,
            'r_squared': r_squared,
            'description': self._get_trend_description(direction, slope, r_squared)
        }

    def _calculate_r_squared(self, scores: List[float], slope: float,
                           intercept: float) -> float:
        """计算R²值"""
        y_pred = [slope * x + intercept for x in np.arange(len(scores))]
        ss_res = sum((y - y_pred[i]) ** 2 for i, y in enumerate(scores))
        ss_tot = sum((y - np.mean(scores)) ** 2 for y in scores)
        return 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

    def _get_trend_description(self, direction: str, slope: float,
                             r_squared: float) -> str:
        """获取趋势描述"""
        if direction == 'improving':
            return f"数据质量呈上升趋势 (斜率: {slope:.3f}, R²: {r_squared:.2f})"
        elif direction == 'declining':
            return f"数据质量呈下降趋势 (斜率: {slope:.3f}, R²: {r_squared:.2f})"
        else:
            return f"数据质量保持稳定 (R²: {r_squared:.2f})"

    def _analyze_dimension_trends(self, reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析维度趋势"""
        dimension_trends = {}

        for dimension in ['completeness', 'accuracy', 'consistency', 'timeliness', 'validity', 'uniqueness']:
            scores = []
            for report in reports:
                if 'dimensions' in report and dimension in report['dimensions']:
                    scores.append(report['dimensions'][dimension])

            if len(scores) >= 2:
                trend = self._calculate_trend(scores, [])
                dimension_trends[dimension] = trend

        return dimension_trends

    def _analyze_anomaly_trends(self, reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析异常趋势"""
        anomaly_counts = []
        for report in reports:
            total_anomalies = 0
            for key in ['anomaly_results', 'verification_results', 'freshness_results']:
                if key in report:
                    for result in report[key]:
                        if key == 'anomaly_results':
                            total_anomalies += result.get('summary', {}).get('total_anomalies', 0)
                        else:
                            total_anomalies += len(result.get('differences', []))
            anomaly_counts.append(total_anomalies)

        if len(anomaly_counts) >= 2:
            trend = self._calculate_trend(anomaly_counts, [])
            return {
                'anomaly_count_trend': trend,
                'current_anomalies': anomaly_counts[-1] if anomaly_counts else 0,
                'average_anomalies': np.mean(anomaly_counts)
            }

        return {}


class ReportFormatter:
    """报告格式化器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化报告格式化器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.template_dir = self.config.get('template_dir', None)
        self.output_dir = self.config.get('output_dir', 'reports')

        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)

    def format_html_report(self, report: QualityReport) -> str:
        """
        格式化HTML报告

        Args:
            report: 质量报告

        Returns:
            HTML字符串
        """
        html_template = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>数据质量报告 - {{ report.symbol }}</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }
        h2 {
            color: #34495e;
            margin-top: 30px;
            border-left: 4px solid #3498db;
            padding-left: 15px;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
        }
        .score-badge {
            font-size: 48px;
            font-weight: bold;
            padding: 20px 40px;
            border-radius: 8px;
            text-align: center;
        }
        .grade-A { background-color: #2ecc71; color: white; }
        .grade-B { background-color: #3498db; color: white; }
        .grade-C { background-color: #f39c12; color: white; }
        .grade-D { background-color: #e67e22; color: white; }
        .grade-F { background-color: #e74c3c; color: white; }
        .dimension-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .dimension-card {
            background-color: #ecf0f1;
            padding: 15px;
            border-radius: 6px;
            border-left: 4px solid #3498db;
        }
        .dimension-name {
            font-weight: bold;
            margin-bottom: 5px;
        }
        .dimension-score {
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
        }
        .recommendations {
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
        }
        .recommendations ul {
            margin: 10px 0;
            padding-left: 20px;
        }
        .anomalies {
            background-color: #f8d7da;
            border-left: 4px solid #dc3545;
            padding: 15px;
            margin: 20px 0;
        }
        .timestamp {
            color: #7f8c8d;
            font-size: 14px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #3498db;
            color: white;
        }
        .severity-high { color: #e74c3c; font-weight: bold; }
        .severity-medium { color: #f39c12; }
        .severity-low { color: #3498db; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1>数据质量报告</h1>
                <p class="timestamp">生成时间: {{ report.timestamp.strftime('%Y-%m-%d %H:%M:%S') }}</p>
                <p><strong>股票代码:</strong> {{ report.symbol }}</p>
            </div>
            <div class="score-badge grade-{{ report.grade }}">
                {{ report.overall_score | round(2) }}
                <div style="font-size: 18px; margin-top: 10px;">等级: {{ report.grade }}</div>
            </div>
        </div>

        <h2>质量维度评分</h2>
        <div class="dimension-grid">
            {% for dimension, score in report.dimensions.items() %}
            <div class="dimension-card">
                <div class="dimension-name">{{ dimension | title }}</div>
                <div class="dimension-score">{{ (score * 100) | round(1) }}%</div>
            </div>
            {% endfor %}
        </div>

        <h2>数据验证结果</h2>
        {% if report.validation_results %}
        <table>
            <tr>
                <th>阶段</th>
                <th>是否通过</th>
                <th>分数</th>
                <th>错误数量</th>
            </tr>
            {% for result in report.validation_results %}
            {% if result.stages %}
            {% for stage_name, stage_data in result.stages.items() %}
            <tr>
                <td>{{ stage_name | title }}</td>
                <td>{{ "✓" if stage_data.is_passed else "✗" }}</td>
                <td>{{ stage_data.score | round(2) }}</td>
                <td>{{ stage_data.errors | length }}</td>
            </tr>
            {% endfor %}
            {% endif %}
            {% endfor %}
        </table>
        {% else %}
        <p>无验证数据</p>
        {% endif %}

        <h2>异常检测结果</h2>
        {% if report.anomaly_results %}
        {% for result in report.anomaly_results %}
        <div class="anomalies">
            <p><strong>检测到 {{ result.summary.total_anomalies }} 个异常</strong></p>
            {% if result.anomalies %}
            <table>
                <tr>
                    <th>类型</th>
                    <th>严重程度</th>
                    <th>描述</th>
                </tr>
                {% for anomaly in result.anomalies[:10] %}
                <tr>
                    <td>{{ anomaly.type }}</td>
                    <td class="severity-{{ anomaly.severity }}">{{ anomaly.severity | title }}</td>
                    <td>{{ anomaly.description }}</td>
                </tr>
                {% endfor %}
            </table>
            {% endif %}
        </div>
        {% endfor %}
        {% else %}
        <p>无异常检测数据</p>
        {% endif %}

        <h2>跨源验证结果</h2>
        {% if report.verification_results %}
        {% for result in report.verification_results %}
        <p><strong>状态:</strong> {{ result.status }} | <strong>一致性分数:</strong> {{ result.consistency_score | round(2) }}</p>
        {% if result.differences %}
        <p>发现 {{ result.differences | length }} 个差异</p>
        {% endif %}
        {% endfor %}
        {% else %}
        <p>无跨源验证数据</p>
        {% endif %}

        <h2>数据新鲜度</h2>
        {% if report.freshness_results %}
        {% for result in report.freshness_results %}
        <p><strong>状态:</strong> {{ result.status }} | <strong>新鲜度分数:</strong> {{ result.freshness_score | round(2) }}</p>
        <p><strong>数据年龄:</strong> {{ result.age_hours | round(1) }} 小时</p>
        {% endfor %}
        {% else %}
        <p>无新鲜度数据</p>
        {% endif %}

        <h2>质量趋势</h2>
        {% if report.trends.has_trend %}
        <p>{{ report.trends.overall_trend.description }}</p>
        {% if report.trends.dimension_trends %}
        <h3>各维度趋势:</h3>
        <ul>
        {% for dimension, trend in report.trends.dimension_trends.items() %}
            <li>{{ dimension | title }}: {{ trend.description }}</li>
        {% endfor %}
        </ul>
        {% endif %}
        {% else %}
        <p>趋势数据不足</p>
        {% endif %}

        <h2>改进建议</h2>
        {% if report.recommendations %}
        <div class="recommendations">
            <ul>
            {% for recommendation in report.recommendations %}
                <li>{{ recommendation }}</li>
            {% endfor %}
            </ul>
        </div>
        {% else %}
        <p>暂无建议</p>
        {% endif %}

        <h2>数据总结</h2>
        <ul>
            <li>总体质量分数: {{ (report.overall_score * 100) | round(1) }}%</li>
            <li>数据等级: {{ report.grade }}</li>
            <li>验证阶段数: {{ report.validation_results | length }}</li>
            <li>异常数量: {{ report.anomaly_results | sum(attribute='summary.total_anomalies') }}</li>
        </ul>
    </div>
</body>
</html>
        """

        template = Template(html_template)
        return template.render(report=report, datetime=datetime)

    def save_html_report(self, report: QualityReport, filename: Optional[str] = None) -> str:
        """
        保存HTML报告

        Args:
            report: 质量报告
            filename: 文件名 (可选)

        Returns:
            保存的文件路径
        """
        if filename is None:
            timestamp = report.timestamp.strftime('%Y%m%d_%H%M%S')
            filename = f"{report.symbol}_{timestamp}_quality_report.html"

        filepath = os.path.join(self.output_dir, filename)
        html_content = self.format_html_report(report)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return filepath

    def create_charts(self, report: QualityReport) -> List[Dict[str, Any]]:
        """
        创建图表

        Args:
            report: 质量报告

        Returns:
            图表列表
        """
        charts = []

        try:
            # 维度评分雷达图
            radar_chart = self._create_radar_chart(report)
            if radar_chart:
                charts.append(radar_chart)

            # 趋势图
            if report.trends.get('has_trend', False):
                trend_chart = self._create_trend_chart(report)
                if trend_chart:
                    charts.append(trend_chart)

            # 异常分布图
            if report.anomaly_results:
                anomaly_chart = self._create_anomaly_chart(report)
                if anomaly_chart:
                    charts.append(anomaly_chart)

        except Exception as e:
            logger.error(f"图表创建失败: {str(e)}")

        return charts

    def _create_radar_chart(self, report: QualityReport) -> Optional[Dict[str, Any]]:
        """创建雷达图"""
        try:
            fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))

            dimensions = list(report.dimensions.keys())
            scores = list(report.dimensions.values())

            # 角度
            angles = np.linspace(0, 2 * np.pi, len(dimensions), endpoint=False)
            scores = np.concatenate((scores, [scores[0]]))
            angles = np.concatenate((angles, [angles[0]]))

            # 绘制
            ax.plot(angles, scores, 'o-', linewidth=2, label=report.symbol)
            ax.fill(angles, scores, alpha=0.25)
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(dimensions)
            ax.set_ylim(0, 1)
            ax.set_title(f'数据质量维度评分 - {report.symbol}', y=1.08)
            ax.grid(True)

            # 保存
            img_data = self._fig_to_base64(fig)
            plt.close(fig)

            return {
                'type': 'radar',
                'title': '质量维度雷达图',
                'image_base64': img_data
            }

        except Exception as e:
            logger.error(f"雷达图创建失败: {str(e)}")
            return None

    def _create_trend_chart(self, report: QualityReport) -> Optional[Dict[str, Any]]:
        """创建趋势图"""
        try:
            if not report.trends.get('has_trend', False):
                return None

            fig, ax = plt.subplots(figsize=(10, 6))

            # 模拟趋势数据 (实际应从历史报告中获取)
            dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
            # 这里使用随机数据模拟，实际应用中应使用真实历史数据
            trend_scores = np.linspace(report.overall_score - 0.1, report.overall_score, 30)

            ax.plot(dates, trend_scores, marker='o', linewidth=2)
            ax.set_title(f'数据质量趋势 - {report.symbol}')
            ax.set_xlabel('日期')
            ax.set_ylabel('质量分数')
            ax.grid(True, alpha=0.3)

            # 保存
            img_data = self._fig_to_base64(fig)
            plt.close(fig)

            return {
                'type': 'trend',
                'title': '质量趋势图',
                'image_base64': img_data
            }

        except Exception as e:
            logger.error(f"趋势图创建失败: {str(e)}")
            return None

    def _create_anomaly_chart(self, report: QualityReport) -> Optional[Dict[str, Any]]:
        """创建异常分布图"""
        try:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

            # 异常类型分布
            anomaly_types = {}
            for result in report.anomaly_results:
                for anomaly in result.get('anomalies', []):
                    anomaly_type = anomaly.get('type', 'unknown')
                    anomaly_types[anomaly_type] = anomaly_types.get(anomaly_type, 0) + 1

            if anomaly_types:
                ax1.pie(anomaly_types.values(), labels=anomaly_types.keys(), autopct='%1.1f%%')
                ax1.set_title('异常类型分布')

            # 严重程度分布
            severity_counts = {'high': 0, 'medium': 0, 'low': 0}
            for result in report.anomaly_results:
                for anomaly in result.get('anomalies', []):
                    severity = anomaly.get('severity', 'low')
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1

            ax2.bar(severity_counts.keys(), severity_counts.values())
            ax2.set_title('异常严重程度分布')
            ax2.set_xlabel('严重程度')
            ax2.set_ylabel('数量')

            # 保存
            img_data = self._fig_to_base64(fig)
            plt.close(fig)

            return {
                'type': 'anomaly',
                'title': '异常分布图',
                'image_base64': img_data
            }

        except Exception as e:
            logger.error(f"异常图创建失败: {str(e)}")
            return None

    def _fig_to_base64(self, fig) -> str:
        """将图表转换为base64字符串"""
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return image_base64


class QualityReporter:
    """数据质量报告生成器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化质量报告生成器

        Args:
            config: 配置字典
        """
        self.config = config or {}

        # 初始化组件
        self.score_calculator = QualityScoreCalculator(
            self.config.get('score_calculator', {})
        )
        self.trend_analyzer = TrendAnalyzer(
            self.config.get('trend_analyzer', {})
        )
        self.formatter = ReportFormatter(
            self.config.get('formatter', {})
        )

        # 统计信息
        self.stats = {
            'reports_generated': 0,
            'html_reports': 0,
            'charts_created': 0,
            'total_score_sum': 0.0
        }

        logger.info("数据质量报告生成器初始化完成")

    async def generate_report(self,
                             symbol: str,
                             validation_results: Optional[List[Dict[str, Any]]] = None,
                             anomaly_results: Optional[List[Dict[str, Any]]] = None,
                             verification_results: Optional[List[Dict[str, Any]]] = None,
                             freshness_results: Optional[List[Dict[str, Any]]] = None,
                             historical_reports: Optional[List[Dict[str, Any]]] = None) -> QualityReport:
        """
        生成数据质量报告

        Args:
            symbol: 股票代码
            validation_results: 验证结果
            anomaly_results: 异常检测结果
            verification_results: 跨源验证结果
            freshness_results: 新鲜度检查结果
            historical_reports: 历史报告

        Returns:
            质量报告
        """
        try:
            # 初始化参数
            validation_results = validation_results or []
            anomaly_results = anomaly_results or []
            verification_results = verification_results or []
            freshness_results = freshness_results or []

            # 计算维度分数
            dimension_scores = self.score_calculator.calculate_dimension_scores(
                validation_results,
                anomaly_results,
                verification_results,
                freshness_results
            )

            # 计算总体分数
            overall_score = self.score_calculator.calculate_overall_score(dimension_scores)

            # 获取等级
            grade = self.score_calculator.get_grade(overall_score)

            # 趋势分析
            trends = {}
            if historical_reports:
                trends = self.trend_analyzer.analyze_trends(historical_reports)

            # 生成建议
            recommendations = self._generate_recommendations(
                dimension_scores, anomaly_results, verification_results, freshness_results
            )

            # 创建报告
            report = QualityReport(
                symbol=symbol,
                timestamp=datetime.utcnow(),
                overall_score=overall_score,
                grade=grade,
                dimensions=dimension_scores,
                validation_results=validation_results,
                anomaly_results=anomaly_results,
                verification_results=verification_results,
                freshness_results=freshness_results,
                trends=trends,
                recommendations=recommendations,
                summary=self._generate_summary(
                    overall_score, grade, dimension_scores, validation_results,
                    anomaly_results, verification_results, freshness_results
                )
            )

            # 创建图表
            charts = self.formatter.create_charts(report)
            report.charts = charts

            # 更新统计
            self.stats['reports_generated'] += 1
            self.stats['html_reports'] += 1
            self.stats['charts_created'] += len(charts)
            self.stats['total_score_sum'] += overall_score

            return report

        except Exception as e:
            logger.error(f"报告生成失败: {str(e)}", exc_info=True)
            raise

    def save_html_report(self, report: QualityReport,
                        filename: Optional[str] = None) -> str:
        """
        保存HTML报告

        Args:
            report: 质量报告
            filename: 文件名

        Returns:
            保存的文件路径
        """
        return self.formatter.save_html_report(report, filename)

    def _generate_recommendations(self,
                                 dimension_scores: Dict[str, float],
                                 anomaly_results: List[Dict[str, Any]],
                                 verification_results: List[Dict[str, Any]],
                                 freshness_results: List[Dict[str, Any]]) -> List[str]:
        """生成改进建议"""
        recommendations = []

        # 基于维度的建议
        for dimension, score in dimension_scores.items():
            if score < 0.7:
                if dimension == 'completeness':
                    recommendations.append("增加数据采集频率，提高数据完整性")
                elif dimension == 'accuracy':
                    recommendations.append("加强异常值检测和清理，提高数据准确性")
                elif dimension == 'consistency':
                    recommendations.append("统一数据源标准，提高跨源数据一致性")
                elif dimension == 'timeliness':
                    recommendations.append("优化数据更新流程，缩短数据延迟")
                elif dimension == 'validity':
                    recommendations.append("加强数据验证规则，确保数据符合业务要求")
                elif dimension == 'uniqueness':
                    recommendations.append("处理重复数据，确保数据唯一性")

        # 基于异常的建议
        if anomaly_results:
            total_anomalies = sum(
                r.get('summary', {}).get('total_anomalies', 0)
                for r in anomaly_results
            )
            if total_anomalies > 0:
                recommendations.append(f"发现 {total_anomalies} 个异常，建议进行深入分析")

        # 基于一致性的建议
        if verification_results:
            for result in verification_results:
                if result.get('consistency_score', 1.0) < 0.8:
                    recommendations.append("数据源间存在不一致，建议使用数据融合技术")

        # 基于新鲜度的建议
        if freshness_results:
            for result in freshness_results:
                if result.get('freshness_score', 1.0) < 0.8:
                    recommendations.append("数据更新不及时，建议增加数据刷新频率")

        # 通用建议
        if not recommendations:
            recommendations.append("数据质量良好，继续保持当前数据管理策略")

        return recommendations

    def _generate_summary(self,
                         overall_score: float,
                         grade: str,
                         dimension_scores: Dict[str, float],
                         validation_results: List[Dict[str, Any]],
                         anomaly_results: List[Dict[str, Any]],
                         verification_results: List[Dict[str, Any]],
                         freshness_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成报告总结"""
        # 统计验证阶段
        total_stages = 0
        passed_stages = 0
        for result in validation_results:
            if 'stages' in result:
                total_stages += len(result['stages'])
                for stage_data in result['stages'].values():
                    if stage_data.get('is_passed', False):
                        passed_stages += 1

        # 统计异常
        total_anomalies = sum(
            r.get('summary', {}).get('total_anomalies', 0)
            for r in anomaly_results
        )

        # 统计差异
        total_differences = sum(
            len(r.get('differences', []))
            for r in verification_results
        )

        return {
            'overall_score': overall_score,
            'grade': grade,
            'quality_level': self._get_quality_level(grade),
            'total_validation_stages': total_stages,
            'passed_validation_stages': passed_stages,
            'validation_success_rate': (passed_stages / total_stages) if total_stages > 0 else 1.0,
            'total_anomalies': total_anomalies,
            'total_differences': total_differences,
            'best_dimension': max(dimension_scores.items(), key=lambda x: x[1]),
            'worst_dimension': min(dimension_scores.items(), key=lambda x: x[1]),
            'data_freshness': freshness_results[0].get('status', 'unknown') if freshness_results else 'unknown'
        }

    def _get_quality_level(self, grade: str) -> str:
        """获取质量等级描述"""
        level_map = {
            'A': '优秀',
            'B': '良好',
            'C': '一般',
            'D': '较差',
            'F': '很差'
        }
        return level_map.get(grade, '未知')

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = self.stats.copy()
        if self.stats['reports_generated'] > 0:
            stats['average_score'] = self.stats['total_score_sum'] / self.stats['reports_generated']
        return stats

    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            'reports_generated': 0,
            'html_reports': 0,
            'charts_created': 0,
            'total_score_sum': 0.0
        }


# 便捷函数
async def generate_quality_report(symbol: str,
                                 validation_results: Optional[List[Dict[str, Any]]] = None,
                                 anomaly_results: Optional[List[Dict[str, Any]]] = None,
                                 verification_results: Optional[List[Dict[str, Any]]] = None,
                                 freshness_results: Optional[List[Dict[str, Any]]] = None,
                                 config: Optional[Dict[str, Any]] = None) -> QualityReport:
    """
    便捷的质量报告生成函数

    Args:
        symbol: 股票代码
        validation_results: 验证结果
        anomaly_results: 异常检测结果
        verification_results: 跨源验证结果
        freshness_results: 新鲜度检查结果
        config: 配置

    Returns:
        质量报告
    """
    reporter = QualityReporter(config)
    return await reporter.generate_report(
        symbol, validation_results, anomaly_results,
        verification_results, freshness_results
    )


def create_quality_reporter(config: Optional[Dict[str, Any]] = None) -> QualityReporter:
    """
    创建质量报告生成器实例

    Args:
        config: 配置字典

    Returns:
        质量报告生成器实例
    """
    return QualityReporter(config)


# 使用示例
if __name__ == "__main__":
    import asyncio

    async def test_quality_reporter():
        # 创建模拟数据
        validation_results = [
            {
                'is_valid': True,
                'overall_score': 0.9,
                'stages': {
                    'structure': {'is_passed': True, 'score': 0.95, 'errors': []},
                    'data_type': {'is_passed': True, 'score': 0.92, 'errors': []},
                    'business_logic': {'is_passed': True, 'score': 0.88, 'errors': []}
                }
            }
        ]

        anomaly_results = [
            {
                'summary': {'total_anomalies': 5},
                'anomalies': [
                    {'type': 'statistical', 'severity': 'high', 'description': 'Z-Score异常'},
                    {'type': 'value', 'severity': 'medium', 'description': '负值异常'},
                ]
            }
        ]

        verification_results = [
            {
                'status': 'consistent',
                'consistency_score': 0.85,
                'differences': [{'type': 'field_inconsistency', 'description': '字段不一致'}]
            }
        ]

        freshness_results = [
            {
                'status': 'up_to_date',
                'freshness_score': 0.9,
                'age_hours': 1.5
            }
        ]

        # 创建质量报告生成器
        config = {
            'score_calculator': {
                'weights': {
                    'completeness': 0.25,
                    'accuracy': 0.25,
                    'consistency': 0.20,
                    'timeliness': 0.15,
                    'validity': 0.10,
                    'uniqueness': 0.05
                }
            },
            'formatter': {
                'output_dir': 'reports'
            }
        }

        reporter = QualityReporter(config)

        # 生成报告
        print("生成数据质量报告...")
        report = await reporter.generate_report(
            '0700.HK',
            validation_results,
            anomaly_results,
            verification_results,
            freshness_results
        )

        # 打印结果
        print(f"\n=== 数据质量报告 ===")
        print(f"股票代码: {report.symbol}")
        print(f"总体分数: {report.overall_score:.2f}")
        print(f"等级: {report.grade}")
        print(f"质量水平: {report.summary['quality_level']}")

        print(f"\n各维度分数:")
        for dimension, score in report.dimensions.items():
            print(f"  {dimension}: {score:.2f}")

        print(f"\n总结:")
        for key, value in report.summary.items():
            if key not in ['best_dimension', 'worst_dimension']:
                print(f"  {key}: {value}")

        print(f"\n改进建议:")
        for i, rec in enumerate(report.recommendations, 1):
            print(f"  {i}. {rec}")

        # 保存HTML报告
        print(f"\n保存HTML报告...")
        filepath = reporter.save_html_report(report)
        print(f"报告已保存到: {filepath}")

        # 获取统计信息
        stats = reporter.get_stats()
        print(f"\n报告统计: {stats}")

    # 运行测试
    asyncio.run(test_quality_reporter())
