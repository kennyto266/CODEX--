#!/usr/bin/env python3
"""
数据质量监控系统
Data Quality Monitoring System

功能：
1. 持续监控数据质量
2. 自动检测数据问题
3. 生成质量告警
4. 记录监控历史
5. 支持多种通知方式

使用方法：
    python data_quality_monitor.py --monitor
    python data_quality_monitor.py --check
    python data_quality_monitor.py --daemon

作者: Claude Code
日期: 2025-11-02
"""

import os
import sys
import json
import time
import argparse
import logging
import smtplib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass
import subprocess

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_quality_monitor.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class DataQualityIssue:
    """数据质量问题"""
    issue_type: str
    severity: str  # CRITICAL, WARNING, INFO
    message: str
    timestamp: str
    file_path: Optional[str] = None
    suggested_action: Optional[str] = None


class DataQualityMonitor:
    """数据质量监控器"""

    def __init__(self, data_dir: str = "data", config_file: str = "monitor_config.json"):
        self.data_dir = Path(data_dir)
        self.config_file = config_file
        self.config = self.load_config()
        self.issues: List[DataQualityIssue] = []

        # 阈值配置
        self.thresholds = {
            'max_data_age_hours': 24,  # 数据最大陈旧时间（小时）
            'min_data_completeness': 0.95,  # 最小数据完整性
            'max_missing_days': 1,  # 最大缺失天数
            'min_file_size_bytes': 1000,  # 最小文件大小
        }

    def load_config(self) -> Dict:
        """加载配置文件"""
        default_config = {
            "email": {
                "enabled": False,
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "",
                "password": "",
                "to_addresses": []
            },
            "notifications": {
                "on_critical": True,
                "on_warning": True
            },
            "monitoring": {
                "check_interval_minutes": 60,
                "history_retention_days": 30
            }
        }

        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                # 合并配置
                for key, value in user_config.items():
                    if key in default_config:
                        default_config[key].update(value)
                    else:
                        default_config[key] = value
            except Exception as e:
                logger.error(f"Error loading config: {e}")

        return default_config

    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info(f"Config saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")

    def check_file_freshness(self) -> List[DataQualityIssue]:
        """检查数据文件新鲜度"""
        issues = []

        # 获取最近24小时内的数据文件
        cutoff_time = datetime.now() - timedelta(hours=self.thresholds['max_data_age_hours'])

        for file_path in self.data_dir.glob("*.csv"):
            try:
                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)

                if file_time < cutoff_time:
                    age_hours = (datetime.now() - file_time).total_seconds() / 3600
                    severity = "CRITICAL" if age_hours > 48 else "WARNING"

                    issue = DataQualityIssue(
                        issue_type="STALE_DATA",
                        severity=severity,
                        message=f"File {file_path.name} is {age_hours:.1f} hours old",
                        timestamp=datetime.now().isoformat(),
                        file_path=str(file_path),
                        suggested_action="Run data fetcher to update data"
                    )
                    issues.append(issue)

            except Exception as e:
                issue = DataQualityIssue(
                    issue_type="FILE_ERROR",
                    severity="WARNING",
                    message=f"Error checking file {file_path.name}: {e}",
                    timestamp=datetime.now().isoformat(),
                    file_path=str(file_path),
                    suggested_action="Check file permissions and access"
                )
                issues.append(issue)

        return issues

    def check_data_completeness(self) -> List[DataQualityIssue]:
        """检查数据完整性"""
        issues = []

        for file_path in self.data_dir.glob("*.csv"):
            try:
                import csv
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)

                    if not rows:
                        issue = DataQualityIssue(
                            issue_type="EMPTY_FILE",
                            severity="CRITICAL",
                            message=f"File {file_path.name} is empty",
                            timestamp=datetime.now().isoformat(),
                            file_path=str(file_path),
                            suggested_action="Check data fetcher and API connectivity"
                        )
                        issues.append(issue)
                        continue

                    # 检查文件大小
                    file_size = file_path.stat().st_size
                    if file_size < self.thresholds['min_file_size_bytes']:
                        issue = DataQualityIssue(
                            issue_type="SMALL_FILE",
                            severity="WARNING",
                            message=f"File {file_path.name} is too small ({file_size} bytes)",
                            timestamp=datetime.now().isoformat(),
                            file_path=str(file_path),
                            suggested_action="Check if data is complete"
                        )
                        issues.append(issue)

                    # 检查数据连续性
                    dates = [row.get('Date') for row in rows if row.get('Date')]
                    if dates:
                        latest_date = max(dates)
                        # 去除时区信息以便比较
                        latest_date_clean = latest_date.split('T')[0] if 'T' in latest_date else latest_date
                        today = datetime.now().strftime("%Y-%m-%d")

                        # 检查是否今天有数据
                        if today != latest_date_clean:
                            try:
                                latest_dt = datetime.fromisoformat(latest_date_clean)
                                days_missing = (datetime.now().date() - latest_dt.date()).days
                                if days_missing > self.thresholds['max_missing_days']:
                                    issue = DataQualityIssue(
                                        issue_type="MISSING_RECENT_DATA",
                                        severity="CRITICAL",
                                        message=f"Missing recent data: {days_missing} days since {latest_date_clean}",
                                        timestamp=datetime.now().isoformat(),
                                        file_path=str(file_path),
                                        suggested_action="Check if market is open and data fetcher is running"
                                    )
                                    issues.append(issue)
                            except Exception as e:
                                # 日期解析失败，跳过连续性检查
                                pass

            except Exception as e:
                issue = DataQualityIssue(
                    issue_type="READ_ERROR",
                    severity="WARNING",
                    message=f"Error reading file {file_path.name}: {e}",
                    timestamp=datetime.now().isoformat(),
                    file_path=str(file_path),
                    suggested_action="Check file format and encoding"
                )
                issues.append(issue)

        return issues

    def check_data_consistency(self) -> List[DataQualityIssue]:
        """检查数据一致性"""
        issues = []

        # 检查合并文件是否存在且是最新的
        merged_files = list(self.data_dir.glob("merged_hkex_data_*.csv"))
        if merged_files:
            latest_merged = max(merged_files, key=lambda x: x.stat().st_mtime)
            file_time = datetime.fromtimestamp(latest_merged.stat().st_mtime)
            cutoff_time = datetime.now() - timedelta(hours=self.thresholds['max_data_age_hours'])

            if file_time < cutoff_time:
                issue = DataQualityIssue(
                    issue_type="STALE_MERGED_DATA",
                    severity="WARNING",
                    message=f"Merged data file is outdated: {latest_merged.name}",
                    timestamp=datetime.now().isoformat(),
                    file_path=str(latest_merged),
                    suggested_action="Run auto-update to regenerate merged data"
                )
                issues.append(issue)
        else:
            issue = DataQualityIssue(
                issue_type="NO_MERGED_DATA",
                severity="WARNING",
                message="No merged data file found",
                timestamp=datetime.now().isoformat(),
                suggested_action="Run auto-update to create merged data"
            )
            issues.append(issue)

        return issues

    def check_system_health(self) -> List[DataQualityIssue]:
        """检查系统健康"""
        issues = []

        # 检查数据获取器日志
        log_files = ['hkex_fetcher.log', 'data_validation.log']
        for log_file in log_files:
            if os.path.exists(log_file):
                try:
                    # 检查最近是否有错误
                    with open(log_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        recent_lines = lines[-100:]  # 最近100行

                    errors = [line for line in recent_lines if 'ERROR' in line or 'CRITICAL' in line]
                    if errors:
                        issue = DataQualityIssue(
                            issue_type="SYSTEM_ERRORS",
                            severity="WARNING",
                            message=f"Found {len(errors)} errors in {log_file}",
                            timestamp=datetime.now().isoformat(),
                            file_path=log_file,
                            suggested_action="Check log file for details and fix errors"
                        )
                        issues.append(issue)

                except Exception as e:
                    issue = DataQualityIssue(
                        issue_type="LOG_READ_ERROR",
                        severity="INFO",
                        message=f"Error reading {log_file}: {e}",
                        timestamp=datetime.now().isoformat(),
                        suggested_action="Check log file permissions"
                    )
                    issues.append(issue)
            else:
                issue = DataQualityIssue(
                    issue_type="MISSING_LOG",
                    severity="INFO",
                    message=f"Log file {log_file} not found",
                    timestamp=datetime.now().isoformat(),
                    suggested_action="Ensure data fetcher is running"
                )
                issues.append(issue)

        return issues

    def check_all(self) -> Dict:
        """执行所有检查"""
        logger.info("Starting data quality check...")

        all_issues = []
        all_issues.extend(self.check_file_freshness())
        all_issues.extend(self.check_data_completeness())
        all_issues.extend(self.check_data_consistency())
        all_issues.extend(self.check_system_health())

        self.issues = all_issues

        # 统计结果
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_issues': len(all_issues),
            'by_severity': {
                'CRITICAL': len([i for i in all_issues if i.severity == 'CRITICAL']),
                'WARNING': len([i for i in all_issues if i.severity == 'WARNING']),
                'INFO': len([i for i in all_issues if i.severity == 'INFO'])
            },
            'issues': [
                {
                    'type': issue.issue_type,
                    'severity': issue.severity,
                    'message': issue.message,
                    'timestamp': issue.timestamp,
                    'file': issue.file_path,
                    'action': issue.suggested_action
                }
                for issue in all_issues
            ]
        }

        return summary

    def send_email_alert(self, issues: List[DataQualityIssue]):
        """发送邮件告警"""
        if not self.config['email']['enabled']:
            return

        try:
            critical_issues = [i for i in issues if i.severity == 'CRITICAL']
            if not critical_issues:
                return  # 只发送严重问题告警

            msg = MIMEMultipart()
            msg['From'] = self.config['email']['username']
            msg['To'] = ', '.join(self.config['email']['to_addresses'])
            msg['Subject'] = f"Data Quality Alert - {len(critical_issues)} Critical Issue(s)"

            # 构建邮件正文
            body = "Data Quality Monitoring System Alert\n\n"
            body += f"Timestamp: {datetime.now().isoformat()}\n\n"
            body += f"Critical Issues Found: {len(critical_issues)}\n\n"

            for issue in critical_issues:
                body += f"Type: {issue.issue_type}\n"
                body += f"Message: {issue.message}\n"
                if issue.file_path:
                    body += f"File: {issue.file_path}\n"
                if issue.suggested_action:
                    body += f"Action: {issue.suggested_action}\n"
                body += "\n" + "-"*50 + "\n\n"

            msg.attach(MIMEText(body, 'plain'))

            # 发送邮件
            server = smtplib.SMTP(self.config['email']['smtp_server'], self.config['email']['smtp_port'])
            server.starttls()
            server.login(self.config['email']['username'], self.config['email']['password'])
            server.send_message(msg)
            server.quit()

            logger.info(f"Email alert sent to {len(self.config['email']['to_addresses'])} recipients")

        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")

    def save_report(self, summary: Dict, output_file: str = "data_quality_report.json"):
        """保存监控报告"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            logger.info(f"Monitor report saved to {output_file}")
        except Exception as e:
            logger.error(f"Error saving report: {e}")

    def print_summary(self, summary: Dict):
        """打印监控摘要"""
        print("\n" + "="*80)
        print("DATA QUALITY MONITORING REPORT")
        print("="*80)
        print(f"Check Time: {summary['timestamp']}")
        print(f"Total Issues: {summary['total_issues']}")
        print()

        print("Issues by Severity:")
        print(f"  CRITICAL: {summary['by_severity']['CRITICAL']}")
        print(f"  WARNING: {summary['by_severity']['WARNING']}")
        print(f"  INFO: {summary['by_severity']['INFO']}")
        print()

        if summary['issues']:
            print("Issues Detail:")
            for issue in summary['issues']:
                severity_icon = {
                    'CRITICAL': 'X',
                    'WARNING': '!',
                    'INFO': 'i'
                }.get(issue['severity'], '?')

                print(f"  [{severity_icon}] {issue['type']}: {issue['message']}")
                if issue['file']:
                    print(f"      File: {issue['file']}")
                if issue['action']:
                    print(f"      Action: {issue['action']}")
                print()

        if summary['by_severity']['CRITICAL'] == 0:
            print("Status: HEALTHY - All systems operational")
        elif summary['by_severity']['CRITICAL'] <= 2:
            print("Status: WARNING - Some issues need attention")
        else:
            print("Status: CRITICAL - Immediate action required")

    def auto_fix(self, summary: Dict):
        """自动修复可修复的问题"""
        fixed_count = 0

        for issue in summary['issues']:
            if issue['type'] == 'STALE_MERGED_DATA' or issue['type'] == 'NO_MERGED_DATA':
                # 尝试运行数据更新
                try:
                    logger.info(f"Attempting to fix: {issue['type']}")
                    result = subprocess.run(
                        ['python3', 'hkex_real_data_fetcher.py', '--auto-update', '--output', str(self.data_dir)],
                        capture_output=True,
                        text=True,
                        timeout=300
                    )
                    if result.returncode == 0:
                        logger.info("Auto-fix successful")
                        fixed_count += 1
                    else:
                        logger.error(f"Auto-fix failed: {result.stderr}")
                except Exception as e:
                    logger.error(f"Auto-fix error: {e}")

        if fixed_count > 0:
            logger.info(f"Auto-fixed {fixed_count} issue(s)")

    def run_monitor_once(self):
        """运行一次监控检查"""
        summary = self.check_all()

        # 发送告警
        if summary['by_severity']['CRITICAL'] > 0:
            self.send_email_alert(self.issues)

        # 自动修复
        if summary['by_severity']['CRITICAL'] > 0:
            self.auto_fix(summary)

        # 保存并打印报告
        self.save_report(summary)
        self.print_summary(summary)

        return summary

    def run_daemon(self):
        """运行守护进程模式"""
        logger.info("Starting data quality monitoring daemon...")
        check_interval = self.config['monitoring']['check_interval_minutes'] * 60

        while True:
            try:
                summary = self.run_monitor_once()
                logger.info(f"Next check in {check_interval} seconds...")
                time.sleep(check_interval)
            except KeyboardInterrupt:
                logger.info("Monitoring daemon stopped")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)  # 出错后等待1分钟再重试


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Data Quality Monitor')
    parser.add_argument('--check', action='store_true',
                       help='Run a single check')
    parser.add_argument('--monitor', action='store_true',
                       help='Run continuously with auto-fix')
    parser.add_argument('--daemon', action='store_true',
                       help='Run as daemon process')
    parser.add_argument('--config', type=str, default='monitor_config.json',
                       help='Config file path')
    parser.add_argument('--data-dir', type=str, default='data',
                       help='Data directory to monitor')

    args = parser.parse_args()

    monitor = DataQualityMonitor(data_dir=args.data_dir, config_file=args.config)

    if args.check:
        # 单次检查
        monitor.run_monitor_once()

    elif args.monitor:
        # 持续监控模式
        while True:
            monitor.run_monitor_once()
            time.sleep(60)  # 每分钟检查一次

    elif args.daemon:
        # 守护进程模式
        monitor.run_daemon()

    else:
        # 默认：单次检查
        monitor.run_monitor_once()


if __name__ == "__main__":
    main()
