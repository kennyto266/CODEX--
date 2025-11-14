"""
文档监控系统 (T599)

提供文档状态监控、构建跟踪、覆盖率趋势和问题统计功能。
支持实时监控和历史数据分析。
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict, deque
import statistics


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentationMonitor:
    """文档监控系统主类"""

    def __init__(self, data_dir: str = './docs/.monitor'):
        """
        初始化监控系统

        Args:
            data_dir: 监控数据存储目录
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.metrics_file = self.data_dir / 'metrics.json'
        self.history_file = self.data_dir / 'history.json'
        self.alerts_file = self.data_dir / 'alerts.json'

        # 加载历史数据
        self.metrics = self._load_metrics()
        self.history = self._load_history()
        self.alerts = self._load_alerts()

        # 监控阈值
        self.thresholds = {
            'min_coverage': 70,  # 最低文档覆盖率
            'max_broken_links': 5,  # 最大断链数
            'max_issues': 20,  # 最大问题数
            'doc_age_days': 30  # 文档最大年龄（天）
        }

    def _load_metrics(self) -> Dict:
        """加载当前指标"""
        if self.metrics_file.exists():
            with open(self.metrics_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _load_history(self) -> Dict:
        """加载历史数据"""
        if self.history_file.exists():
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {'coverage': [], 'issues': [], 'build_status': []}

    def _load_alerts(self) -> List[Dict]:
        """加载告警记录"""
        if self.alerts_file.exists():
            with open(self.alerts_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def _save_metrics(self):
        """保存当前指标"""
        with open(self.metrics_file, 'w', encoding='utf-8') as f:
            json.dump(self.metrics, f, indent=2, ensure_ascii=False)

    def _save_history(self):
        """保存历史数据"""
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)

    def _save_alerts(self):
        """保存告警记录"""
        with open(self.alerts_file, 'w', encoding='utf-8') as f:
            json.dump(self.alerts, f, indent=2, ensure_ascii=False)

    def update_metrics(self, quality_report: Dict):
        """
        更新监控指标

        Args:
            quality_report: 质量检查报告
        """
        timestamp = datetime.now().isoformat()

        # 提取关键指标
        coverage = quality_report.get('details', {}).get('coverage', {})
        links = quality_report.get('details', {}).get('links', {})
        spelling = quality_report.get('details', {}).get('spelling', {})
        completeness = quality_report.get('details', {}).get('completeness', {})

        self.metrics = {
            'timestamp': timestamp,
            'coverage_percentage': coverage.get('documentation_percentage', 0),
            'total_code_files': coverage.get('code_files', 0),
            'documented_files': coverage.get('documented_files', 0),
            'broken_links': len(links.get('broken_links', [])),
            'total_links': links.get('total_links', 0),
            'spelling_errors': len(spelling.get('common_misspellings', [])),
            'missing_files': len(completeness.get('missing_files', [])),
            'incomplete_files': len(completeness.get('incomplete_files', [])),
            'total_issues': quality_report.get('summary', {}).get('total_issues', 0),
            'critical_issues': quality_report.get('summary', {}).get('critical_issues', 0)
        }

        # 更新历史数据
        self._update_history()

        # 检查告警条件
        self._check_alerts()

        # 保存数据
        self._save_metrics()
        self._save_history()
        self._save_alerts()

        logger.info("监控指标已更新")

    def _update_history(self):
        """更新历史趋势数据"""
        # 保持最近90天的数据
        max_history = 90

        # 覆盖率历史
        coverage_point = {
            'timestamp': self.metrics['timestamp'],
            'value': self.metrics['coverage_percentage']
        }
        self.history['coverage'].append(coverage_point)
        if len(self.history['coverage']) > max_history:
            self.history['coverage'] = self.history['coverage'][-max_history:]

        # 问题数历史
        issues_point = {
            'timestamp': self.metrics['timestamp'],
            'total': self.metrics['total_issues'],
            'critical': self.metrics['critical_issues']
        }
        self.history['issues'].append(issues_point)
        if len(self.history['issues']) > max_history:
            self.history['issues'] = self.history['issues'][-max_history:]

    def _check_alerts(self):
        """检查告警条件"""
        current_time = datetime.now()
        new_alerts = []

        # 检查覆盖率
        if self.metrics['coverage_percentage'] < self.thresholds['min_coverage']:
            new_alerts.append({
                'timestamp': current_time.isoformat(),
                'type': 'coverage',
                'level': 'warning',
                'message': f"文档覆盖率低于阈值: {self.metrics['coverage_percentage']:.1f}% < {self.thresholds['min_coverage']}%",
                'value': self.metrics['coverage_percentage']
            })

        # 检查断链
        if self.metrics['broken_links'] > self.thresholds['max_broken_links']:
            new_alerts.append({
                'timestamp': current_time.isoformat(),
                'type': 'links',
                'level': 'error',
                'message': f"断链数量超过阈值: {self.metrics['broken_links']} > {self.thresholds['max_broken_links']}",
                'value': self.metrics['broken_links']
            })

        # 检查总问题数
        if self.metrics['total_issues'] > self.thresholds['max_issues']:
            new_alerts.append({
                'timestamp': current_time.isoformat(),
                'type': 'issues',
                'level': 'error',
                'message': f"总问题数超过阈值: {self.metrics['total_issues']} > {self.thresholds['max_issues']}",
                'value': self.metrics['total_issues']
            })

        # 添加新告警
        if new_alerts:
            self.alerts.extend(new_alerts)
            # 只保留最近30天的告警
            cutoff_date = current_time - timedelta(days=30)
            self.alerts = [
                alert for alert in self.alerts
                if datetime.fromisoformat(alert['timestamp']) > cutoff_date
            ]

    def get_trend_analysis(self, days: int = 30) -> Dict:
        """
        获取趋势分析

        Args:
            days: 分析天数

        Returns:
            趋势分析结果
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        # 过滤数据
        recent_coverage = [
            point for point in self.history['coverage']
            if datetime.fromisoformat(point['timestamp']) > cutoff_date
        ]

        recent_issues = [
            point for point in self.history['issues']
            if datetime.fromisoformat(point['timestamp']) > cutoff_date
        ]

        analysis = {
            'period_days': days,
            'coverage': {},
            'issues': {}
        }

        # 覆盖率趋势分析
        if recent_coverage:
            coverage_values = [p['value'] for p in recent_coverage]
            analysis['coverage'] = {
                'current': coverage_values[-1] if coverage_values else 0,
                'average': statistics.mean(coverage_values),
                'min': min(coverage_values),
                'max': max(coverage_values),
                'trend': self._calculate_trend(coverage_values),
                'points': len(coverage_values)
            }

        # 问题趋势分析
        if recent_issues:
            total_issues = [p['total'] for p in recent_issues]
            critical_issues = [p['critical'] for p in recent_issues]

            analysis['issues'] = {
                'current_total': total_issues[-1] if total_issues else 0,
                'current_critical': critical_issues[-1] if critical_issues else 0,
                'avg_total': statistics.mean(total_issues),
                'avg_critical': statistics.mean(critical_issues),
                'trend_total': self._calculate_trend(total_issues),
                'trend_critical': self._calculate_trend(critical_issues),
                'points': len(recent_issues)
            }

        return analysis

    def _calculate_trend(self, values: List[float]) -> str:
        """
        计算趋势方向

        Args:
            values: 数值序列

        Returns:
            趋势方向: 'improving', 'declining', 'stable'
        """
        if len(values) < 2:
            return 'stable'

        # 计算线性回归斜率
        n = len(values)
        x = list(range(n))
        x_mean = sum(x) / n
        y_mean = sum(values) / n

        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return 'stable'

        slope = numerator / denominator

        # 判断趋势
        if slope > 0.1:
            return 'improving'
        elif slope < -0.1:
            return 'declining'
        else:
            return 'stable'

    def get_build_status(self) -> Dict:
        """获取构建状态"""
        return {
            'last_check': self.metrics.get('timestamp'),
            'status': 'success' if self.metrics.get('total_issues', 0) == 0 else 'failure',
            'coverage': self.metrics.get('coverage_percentage', 0),
            'issues': self.metrics.get('total_issues', 0)
        }

    def get_active_alerts(self) -> List[Dict]:
        """获取活跃告警（最近24小时）"""
        cutoff = datetime.now() - timedelta(days=1)
        return [
            alert for alert in self.alerts
            if datetime.fromisoformat(alert['timestamp']) > cutoff
        ]

    def generate_dashboard_data(self) -> Dict:
        """
        生成仪表板数据

        Returns:
            仪表板所需的数据
        """
        # 获取趋势分析
        trend_30d = self.get_trend_analysis(30)
        trend_7d = self.get_trend_analysis(7)

        return {
            'overview': {
                'coverage': {
                    'current': self.metrics.get('coverage_percentage', 0),
                    'status': 'good' if self.metrics.get('coverage_percentage', 0) >= self.thresholds['min_coverage'] else 'warning',
                    'trend': trend_30d.get('coverage', {}).get('trend', 'stable')
                },
                'issues': {
                    'total': self.metrics.get('total_issues', 0),
                    'critical': self.metrics.get('critical_issues', 0),
                    'status': 'good' if self.metrics.get('total_issues', 0) <= self.thresholds['max_issues'] else 'error'
                },
                'links': {
                    'broken': self.metrics.get('broken_links', 0),
                    'total': self.metrics.get('total_links', 0),
                    'status': 'good' if self.metrics.get('broken_links', 0) <= self.thresholds['max_broken_links'] else 'error'
                }
            },
            'trends': {
                'coverage_7d': trend_7d.get('coverage', {}),
                'coverage_30d': trend_30d.get('coverage', {}),
                'issues_7d': trend_7d.get('issues', {}),
                'issues_30d': trend_30d.get('issues', {})
            },
            'alerts': {
                'active': self.get_active_alerts(),
                'total': len(self.alerts)
            },
            'build_status': self.get_build_status(),
            'files': {
                'total_code': self.metrics.get('total_code_files', 0),
                'documented': self.metrics.get('documented_files', 0),
                'missing': self.metrics.get('total_code_files', 0) - self.metrics.get('documented_files', 0)
            }
        }

    def export_data(self, output_file: str):
        """
        导出所有数据

        Args:
            output_file: 输出文件路径
        """
        data = {
            'exported_at': datetime.now().isoformat(),
            'metrics': self.metrics,
            'history': self.history,
            'alerts': self.alerts,
            'dashboard_data': self.generate_dashboard_data()
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"监控数据已导出到: {output_file}")


def main():
    """主函数"""
    import sys

    if len(sys.argv) < 2:
        print("用法: python monitor.py <command> [args]")
        print("命令:")
        print("  update <report_file>  - 更新监控指标")
        print("  trend [days]          - 显示趋势分析")
        print("  alerts                - 显示活跃告警")
        print("  export <file>         - 导出数据")
        sys.exit(1)

    monitor = DocumentationMonitor()
    command = sys.argv[1]

    if command == 'update':
        if len(sys.argv) < 3:
            print("错误: 请提供报告文件路径")
            sys.exit(1)

        report_file = sys.argv[2]
        with open(report_file, 'r', encoding='utf-8') as f:
            report = json.load(f)

        monitor.update_metrics(report)
        print("监控指标已更新")

    elif command == 'trend':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        analysis = monitor.get_trend_analysis(days)

        print(f"\n最近 {days} 天趋势分析:")
        print("=" * 60)

        if 'coverage' in analysis:
            cov = analysis['coverage']
            print(f"\n【覆盖率】")
            print(f"  当前值: {cov.get('current', 0):.1f}%")
            print(f"  平均值: {cov.get('average', 0):.1f}%")
            print(f"  趋势: {cov.get('trend', 'stable')}")

        if 'issues' in analysis:
            iss = analysis['issues']
            print(f"\n【问题统计】")
            print(f"  当前总数: {iss.get('current_total', 0)}")
            print(f"  当前严重: {iss.get('current_critical', 0)}")
            print(f"  平均总数: {iss.get('avg_total', 0):.1f}")
            print(f"  趋势: {iss.get('trend_total', 'stable')}")

    elif command == 'alerts':
        alerts = monitor.get_active_alerts()
        print(f"\n活跃告警 ({len(alerts)}):")
        print("=" * 60)

        for alert in alerts[-10:]:  # 显示最近10个
            print(f"\n[{alert['level'].upper()}] {alert['type']}")
            print(f"  时间: {alert['timestamp']}")
            print(f"  消息: {alert['message']}")

    elif command == 'export':
        if len(sys.argv) < 3:
            print("错误: 请提供输出文件路径")
            sys.exit(1)

        output_file = sys.argv[2]
        monitor.export_data(output_file)
        print(f"数据已导出到: {output_file}")

    else:
        print(f"未知命令: {command}")
        sys.exit(1)


if __name__ == '__main__':
    main()
