#!/usr/bin/env python3
"""
数据真实性验证工具
Data Authenticity Verification Tool

功能：
1. 验证数据文件存在性和完整性
2. 检查数据新鲜度和更新频率
3. 验证数据源可靠性
4. 对比官方数据源
5. 生成数据质量报告

使用方法：
    python data_validation_tool.py --check-all
    python data_validation_tool.py --verify hkex
    python data_validation_tool.py --monitor

作者: Claude Code
日期: 2025-11-02
"""

import os
import sys
import json
import csv
import time
import argparse
import hashlib
import urllib.request
import urllib.parse
import ssl
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_validation.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class DataValidator:
    """数据验证器类"""

    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.opnspec_api = "http://18.180.162.113:9191/inst/getInst"
        self.report = {
            "timestamp": datetime.now().isoformat(),
            "validation_results": {},
            "summary": {}
        }

    def check_file_existence(self, file_path: str) -> Dict:
        """检查文件是否存在"""
        path = Path(file_path)
        result = {
            "exists": path.exists(),
            "size_bytes": 0,
            "last_modified": None,
            "is_readable": False
        }

        if path.exists():
            try:
                result["size_bytes"] = path.stat().st_size
                result["last_modified"] = datetime.fromtimestamp(
                    path.stat().st_mtime
                ).isoformat()
                result["is_readable"] = os.access(file_path, os.R_OK)
            except Exception as e:
                logger.error(f"Error checking file {file_path}: {e}")

        return result

    def check_data_freshness(self, file_path: str, max_age_hours: int = 24) -> Dict:
        """检查数据新鲜度"""
        path = Path(file_path)
        if not path.exists():
            return {"status": "FILE_NOT_FOUND", "error": "File does not exist"}

        try:
            file_time = datetime.fromtimestamp(path.stat().st_mtime)
            current_time = datetime.now()
            age_hours = (current_time - file_time).total_seconds() / 3600

            freshness_score = max(0, 10 - (age_hours / max_age_hours) * 10)

            return {
                "status": "FRESH" if age_hours < max_age_hours else "STALE",
                "age_hours": round(age_hours, 2),
                "max_age_hours": max_age_hours,
                "freshness_score": round(freshness_score, 2),
                "file_time": file_time.isoformat(),
                "current_time": current_time.isoformat()
            }
        except Exception as e:
            logger.error(f"Error checking freshness for {file_path}: {e}")
            return {"status": "ERROR", "error": str(e)}

    def check_data_completeness(self, file_path: str) -> Dict:
        """检查数据完整性"""
        path = Path(file_path)
        if not path.exists():
            return {"status": "FILE_NOT_FOUND"}

        try:
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames

                total_rows = 0
                valid_rows = 0
                empty_rows = 0
                first_valid_date = None
                last_valid_date = None

                for row in reader:
                    total_rows += 1

                    # 检查是否为有效行
                    if any(row.get(col) and str(row.get(col)).strip() != ''
                           for col in headers if col != 'Date'):
                        valid_rows += 1

                        # 跟踪日期范围
                        if 'Date' in row and row['Date']:
                            try:
                                date_obj = datetime.strptime(row['Date'], '%Y-%m-%d')
                                if not first_valid_date or date_obj < first_valid_date:
                                    first_valid_date = date_obj
                                if not last_valid_date or date_obj > last_valid_date:
                                    last_valid_date = date_obj
                            except:
                                pass
                    else:
                        empty_rows += 1

            completeness_pct = (valid_rows / total_rows * 100) if total_rows > 0 else 0

            return {
                "status": "COMPLETE" if completeness_pct > 95 else "INCOMPLETE",
                "total_rows": total_rows,
                "valid_rows": valid_rows,
                "empty_rows": empty_rows,
                "completeness_pct": round(completeness_pct, 2),
                "first_valid_date": first_valid_date.isoformat() if first_valid_date else None,
                "last_valid_date": last_valid_date.isoformat() if last_valid_date else None
            }
        except Exception as e:
            logger.error(f"Error checking completeness for {file_path}: {e}")
            return {"status": "ERROR", "error": str(e)}

    def verify_opnspec_api(self, symbol: str = "0700.hk", duration: int = 5) -> Dict:
        """验证OpenSpec API端点"""
        try:
            url = self.opnspec_api
            params = {
                "symbol": symbol.lower(),
                "duration": duration * 365  # 转换为天数
            }

            # 构建请求URL
            query_string = urllib.parse.urlencode(params)
            full_url = f"{url}?{query_string}"

            start_time = time.time()

            # 创建SSL上下文
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            # 发送请求
            with urllib.request.urlopen(full_url, timeout=30, context=ctx) as response:
                response_time = (time.time() - start_time) * 1000  # 毫秒
                data = response.read()
                json_data = json.loads(data.decode('utf-8'))

                return {
                    "status": "AVAILABLE",
                    "response_code": response.status,
                    "response_time_ms": round(response_time, 2),
                    "data_size": len(json.dumps(json_data)),
                    "has_data": bool(json_data)
                }
        except Exception as e:
            logger.error(f"Error verifying OpenSpec API: {e}")
            return {
                "status": "ERROR",
                "error": str(e)
            }

    def fetch_real_hkex_data(self, symbol: str = "0700.hk") -> Optional[Dict]:
        """获取真实HKEX数据用于对比"""
        try:
            url = self.opnspec_api
            params = {
                "symbol": symbol.lower(),
                "duration": 7  # 最近7天
            }

            # 构建请求URL
            query_string = urllib.parse.urlencode(params)
            full_url = f"{url}?{query_string}"

            # 创建SSL上下文
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            # 发送请求
            with urllib.request.urlopen(full_url, timeout=30, context=ctx) as response:
                if response.status == 200:
                    data = response.read()
                    return json.loads(data.decode('utf-8'))
            return None
        except Exception as e:
            logger.error(f"Error fetching real HKEX data: {e}")
            return None

    def validate_hkex_data(self) -> Dict:
        """验证HKEX数据"""
        logger.info("Validating HKEX data...")
        hkex_file = "hkex爬蟲/data/hkex_all_market_data.csv"

        results = {
            "file_existence": self.check_file_existence(hkex_file),
            "data_freshness": self.check_data_freshness(hkex_file, max_age_hours=24),
            "data_completeness": self.check_data_completeness(hkex_file)
        }

        # 验证OpenSpec API
        logger.info("Verifying OpenSpec API...")
        results["opnspec_api"] = self.verify_opnspec_api()

        # 对比真实数据
        if results["opnspec_api"]["status"] == "AVAILABLE":
            logger.info("Comparing with real data...")
            real_data = self.fetch_real_hkex_data()
            results["real_data_comparison"] = {
                "has_real_data": bool(real_data),
                "real_data_size": len(json.dumps(real_data)) if real_data else 0
            }

        return results

    def validate_gov_data(self) -> Dict:
        """验证政府数据"""
        logger.info("Validating government data...")
        gov_dir = "gov_crawler/data"

        if not Path(gov_dir).exists():
            return {"status": "DIR_NOT_FOUND", "error": f"Directory {gov_dir} not found"}

        results = {}
        for csv_file in Path(gov_dir).glob("*.csv"):
            results[csv_file.name] = {
                "file_existence": self.check_file_existence(str(csv_file)),
                "data_freshness": self.check_data_freshness(str(csv_file), max_age_hours=168),  # 7天
                "data_completeness": self.check_data_completeness(str(csv_file))
            }

        return results

    def generate_quality_score(self, validation_results: Dict) -> Dict:
        """生成数据质量分数"""
        scores = []

        # HKEX数据评分
        if "hkex_data" in validation_results:
            hkex = validation_results["hkex_data"]

            # 新鲜度评分 (40%)
            if hkex["data_freshness"].get("status") == "FRESH":
                freshness_score = 10
            elif hkex["data_freshness"].get("status") == "STALE":
                freshness_score = max(0, hkex["data_freshness"].get("freshness_score", 0))
            else:
                freshness_score = 0
            scores.append(("Freshness", freshness_score, 0.4))

            # 完整性评分 (30%)
            completeness_pct = hkex["data_completeness"].get("completeness_pct", 0)
            completeness_score = completeness_pct / 10
            scores.append(("Completeness", completeness_score, 0.3))

            # API可用性评分 (30%)
            if hkex["opnspec_api"].get("status") == "AVAILABLE":
                api_score = 10
            else:
                api_score = 0
            scores.append(("API_Availability", api_score, 0.3))

        # 计算加权平均分
        if scores:
            weighted_score = sum(score * weight for _, score, weight in scores)
            grade = self.get_quality_grade(weighted_score)
        else:
            weighted_score = 0
            grade = "F"

        return {
            "weighted_score": round(weighted_score, 2),
            "max_score": 10,
            "grade": grade,
            "components": {
                name: {"score": round(score, 2), "weight": weight}
                for name, score, weight in scores
            }
        }

    def get_quality_grade(self, score: float) -> str:
        """根据分数获取等级"""
        if score >= 9:
            return "A+"
        elif score >= 8:
            return "A"
        elif score >= 7:
            return "B+"
        elif score >= 6:
            return "B"
        elif score >= 5:
            return "C+"
        elif score >= 4:
            return "C"
        elif score >= 3:
            return "D"
        else:
            return "F"

    def run_full_validation(self) -> Dict:
        """运行完整验证"""
        logger.info("Starting full data validation...")

        # 验证各类数据
        self.report["validation_results"]["hkex_data"] = self.validate_hkex_data()
        self.report["validation_results"]["gov_data"] = self.validate_gov_data()

        # 生成质量分数
        self.report["quality_score"] = self.generate_quality_score(
            self.report["validation_results"]
        )

        # 生成总结
        self.generate_summary()

        return self.report

    def generate_summary(self):
        """生成验证总结"""
        summary = {
            "overall_status": "UNKNOWN",
            "critical_issues": [],
            "recommendations": []
        }

        # 检查HKEX数据
        hkex = self.report["validation_results"].get("hkex_data", {})

        if hkex.get("data_freshness", {}).get("status") == "STALE":
            summary["critical_issues"].append(
                f"HKEX data is stale: {hkex['data_freshness']['age_hours']} hours old"
            )
            summary["recommendations"].append("Fix HKEX crawler to implement daily auto-update")

        if hkex.get("data_completeness", {}).get("completeness_pct", 0) < 95:
            summary["critical_issues"].append(
                f"Insufficient data completeness: {hkex['data_completeness']['completeness_pct']}%"
            )
            summary["recommendations"].append("Check data collection logic to ensure complete data")

        if hkex.get("opnspec_api", {}).get("status") != "AVAILABLE":
            summary["critical_issues"].append("OpenSpec API is not available")
            summary["recommendations"].append("Check network connection and API endpoint")

        # 评估整体状态
        if len(summary["critical_issues"]) == 0:
            summary["overall_status"] = "GOOD"
        elif len(summary["critical_issues"]) <= 2:
            summary["overall_status"] = "WARNING"
        else:
            summary["overall_status"] = "CRITICAL"

        self.report["summary"] = summary

    def print_report(self):
        """打印验证报告"""
        print("\n" + "="*80)
        print("DATA AUTHENTICITY VERIFICATION REPORT")
        print("="*80)
        print(f"Validation Time: {self.report['timestamp']}")
        print()

        # 质量分数
        quality = self.report.get("quality_score", {})
        print(f"Data Quality Score: {quality.get('weighted_score', 0):.2f}/10")
        print(f"Quality Grade: {quality.get('grade', 'F')}")
        print()

        # 总结
        summary = self.report.get("summary", {})
        print(f"Overall Status: {summary.get('overall_status', 'UNKNOWN')}")
        print()

        if summary.get("critical_issues"):
            print("Critical Issues:")
            for issue in summary["critical_issues"]:
                print(f"  X {issue}")
            print()

        if summary.get("recommendations"):
            print("Recommendations:")
            for rec in summary["recommendations"]:
                print(f"  -> {rec}")
            print()

        # 详细结果
        hkex = self.report["validation_results"].get("hkex_data", {})
        if hkex:
            print("HKEX Data Details:")
            print(f"  File exists: {hkex.get('file_existence', {}).get('exists', False)}")
            print(f"  Data freshness: {hkex.get('data_freshness', {}).get('status', 'N/A')}")
            print(f"  Data completeness: {hkex.get('data_completeness', {}).get('completeness_pct', 0):.1f}%")
            print(f"  API status: {hkex.get('opnspec_api', {}).get('status', 'N/A')}")
            print()

    def save_report(self, output_file: str = "data_validation_report.json"):
        """保存报告到文件"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.report, f, indent=2, ensure_ascii=False)
            logger.info(f"报告已保存到: {output_file}")
        except Exception as e:
            logger.error(f"保存报告失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='数据真实性验证工具')
    parser.add_argument('--check-all', action='store_true',
                       help='运行完整验证')
    parser.add_argument('--verify', type=str, choices=['hkex', 'gov'],
                       help='验证特定数据源')
    parser.add_argument('--monitor', action='store_true',
                       help='持续监控模式')
    parser.add_argument('--output', type=str, default='data_validation_report.json',
                       help='报告输出文件')

    args = parser.parse_args()

    validator = DataValidator()

    if args.check_all or not any([args.verify, args.monitor]):
        # 运行完整验证
        report = validator.run_full_validation()
        validator.print_report()
        validator.save_report(args.output)

        # 返回退出码
        summary = report.get("summary", {})
        if summary.get("overall_status") == "GOOD":
            sys.exit(0)
        else:
            sys.exit(1)

    elif args.verify == "hkex":
        # 验证HKEX数据
        result = validator.validate_hkex_data()
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.verify == "gov":
        # 验证政府数据
        result = validator.validate_gov_data()
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.monitor:
        # 持续监控模式
        print("启动数据质量监控模式...")
        print("按 Ctrl+C 停止监控")
        try:
            while True:
                report = validator.run_full_validation()
                validator.print_report()

                # 检查是否需要告警
                summary = report.get("summary", {})
                if summary.get("overall_status") == "CRITICAL":
                    print("\n⚠️ 警告：检测到严重数据质量问题！")

                time.sleep(3600)  # 每小时检查一次
        except KeyboardInterrupt:
            print("\n监控已停止")


if __name__ == "__main__":
    main()
