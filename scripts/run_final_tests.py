#!/usr/bin/env python
"""
最终测试运行器 (T240-T244)

运行所有最终测试并生成综合报告
"""

import os
import sys
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path


# ==================== 测试配置 ====================

class FinalTestConfig:
    """最终测试配置"""
    # 测试文件路径
    TEST_FILES = {
        'T240': 'tests/regression/test_full_regression.py',
        'T241': 'tests/performance/test_final_benchmarks.py',
        'T242': 'tests/security/test_security_audit.py',
        'T243': 'tests/acceptance/test_user_acceptance.py',
        'T244': 'scripts/docs_review.py'
    }

    # 报告目录
    REPORTS_DIR = 'tests/reports'
    FINAL_REPORT = 'tests/reports/final_test_report.json'


# ==================== 测试执行器 ====================

class FinalTestRunner:
    """最终测试执行器"""

    def __init__(self, config: FinalTestConfig):
        self.config = config
        self.results = {}

    def run_all_tests(self) -> dict:
        """运行所有最终测试"""
        print("=" * 80)
        print("港股量化交易系统 - 最终测试 (T240-T244)")
        print("=" * 80)
        print()

        # 准备报告目录
        os.makedirs(self.config.REPORTS_DIR, exist_ok=True)

        # 运行每个测试
        for test_name, test_file in self.config.TEST_FILES.items():
            print(f"\n{'=' * 80}")
            print(f"执行 {test_name}: {test_file}")
            print('=' * 80)

            result = self._run_test(test_name, test_file)
            self.results[test_name] = result

            # 打印结果
            self._print_test_result(result)

        return self.results

    def _run_test(self, test_name: str, test_file: str) -> dict:
        """运行单个测试"""
        start_time = time.time()
        result = {
            'test_name': test_name,
            'test_file': test_file,
            'start_time': datetime.fromtimestamp(start_time).isoformat(),
            'status': 'PENDING',
            'duration': 0,
            'output': '',
            'errors': '',
            'exit_code': 0
        }

        try:
            # 检查测试文件是否存在
            if not os.path.exists(test_file):
                result['status'] = 'ERROR'
                result['errors'] = f"测试文件不存在: {test_file}"
                result['exit_code'] = 1
                return result

            # 运行测试
            if test_file.endswith('.py'):
                # Python测试文件
                cmd = [sys.executable, test_file, '-v', '--tb=short']
            else:
                # 文档审查脚本
                cmd = [sys.executable, test_file, '--update', '--test-examples']

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.getcwd()
            )

            stdout, stderr = process.communicate()

            end_time = time.time()
            result['duration'] = end_time - start_time
            result['end_time'] = datetime.fromtimestamp(end_time).isoformat()
            result['output'] = stdout
            result['errors'] = stderr
            result['exit_code'] = process.returncode

            # 确定状态
            if process.returncode == 0:
                result['status'] = 'PASSED'
            elif process.returncode == 5:  # pytest: no tests collected
                result['status'] = 'SKIPPED'
            else:
                result['status'] = 'FAILED'

        except Exception as e:
            end_time = time.time()
            result['duration'] = end_time - start_time
            result['end_time'] = datetime.fromtimestamp(end_time).isoformat()
            result['status'] = 'ERROR'
            result['errors'] = str(e)
            result['exit_code'] = 1

        return result

    def _print_test_result(self, result: dict):
        """打印测试结果"""
        status_symbols = {
            'PASSED': '✓',
            'FAILED': '✗',
            'SKIPPED': '⊘',
            'ERROR': '⚠',
            'PENDING': '…'
        }

        symbol = status_symbols.get(result['status'], '?')
        duration = result['duration']

        print(f"\n{result['test_name']} {symbol}")
        print(f"  状态: {result['status']}")
        print(f"  耗时: {duration:.2f}秒")

        if result['errors']:
            print(f"  错误: {result['errors'][:200]}...")

    def generate_final_report(self) -> dict:
        """生成最终测试报告"""
        # 收集所有测试报告
        test_reports = {}
        reports_dir = Path(self.config.REPORTS_DIR)

        for report_file in reports_dir.glob('*_report.json'):
            try:
                with open(report_file, 'r', encoding='utf-8') as f:
                    test_reports[report_file.stem] = json.load(f)
            except Exception as e:
                print(f"警告: 无法读取报告 {report_file}: {e}")

        # 生成综合报告
        final_report = {
            'timestamp': datetime.now().isoformat(),
            'test_suite': 'T240-T244 最终测试',
            'version': '1.0.0',
            'summary': {
                'total_tests': len(self.results),
                'passed': sum(1 for r in self.results.values() if r['status'] == 'PASSED'),
                'failed': sum(1 for r in self.results.values() if r['status'] == 'FAILED'),
                'skipped': sum(1 for r in self.results.values() if r['status'] == 'SKIPPED'),
                'errors': sum(1 for r in self.results.values() if r['status'] == 'ERROR'),
                'success_rate': 0
            },
            'test_results': self.results,
            'individual_reports': test_reports,
            'recommendations': []
        }

        # 计算成功率
        total = final_report['summary']['total_tests']
        if total > 0:
            final_report['summary']['success_rate'] = (
                final_report['summary']['passed'] / total * 100
            )

        # 生成建议
        if final_report['summary']['failed'] > 0:
            final_report['recommendations'].append(
                "修复失败的测试用例"
            )

        if final_report['summary']['errors'] > 0:
            final_report['recommendations'].append(
                "解决测试执行中的错误"
            )

        if final_report['summary']['success_rate'] < 100:
            final_report['recommendations'].append(
                "提高测试覆盖率，确保所有功能正常"
            )

        # 保存报告
        with open(self.config.FINAL_REPORT, 'w', encoding='utf-8') as f:
            json.dump(final_report, f, indent=2, ensure_ascii=False)

        return final_report

    def print_final_summary(self, report: dict):
        """打印最终总结"""
        print("\n" + "=" * 80)
        print("最终测试总结")
        print("=" * 80)

        summary = report['summary']
        print(f"总测试数: {summary['total_tests']}")
        print(f"通过: {summary['passed']} ✓")
        print(f"失败: {summary['failed']} ✗")
        print(f"跳过: {summary['skipped']} ⊘")
        print(f"错误: {summary['errors']} ⚠")
        print(f"成功率: {summary['success_rate']:.1f}%")

        print("\n详细结果:")
        for test_name, result in self.results.items():
            status_symbol = {
                'PASSED': '✓',
                'FAILED': '✗',
                'SKIPPED': '⊘',
                'ERROR': '⚠'
            }.get(result['status'], '?')
            print(f"  {test_name}: {status_symbol} ({result['duration']:.2f}秒)")

        if report['recommendations']:
            print("\n建议:")
            for rec in report['recommendations']:
                print(f"  • {rec}")

        print(f"\n完整报告: {self.config.FINAL_REPORT}")

        # 退出码
        if summary['failed'] > 0 or summary['errors'] > 0:
            print("\n⚠ 测试未完全通过")
            return 1
        else:
            print("\n✓ 所有测试通过")
            return 0


# ==================== 主程序 ====================

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='运行最终测试 (T240-T244)')
    parser.add_argument('--skip-tests', nargs='*', choices=['T240', 'T241', 'T242', 'T243', 'T244'],
                        help='跳过的测试')
    parser.add_argument('--parallel', action='store_true', help='并行运行测试（实验性）')
    parser.add_argument('--output', type=str, default=None, help='输出报告路径')

    args = parser.parse_args()

    # 初始化配置
    config = FinalTestConfig()

    if args.output:
        config.FINAL_REPORT = args.output

    # 创建测试运行器
    runner = FinalTestRunner(config)

    # 跳过的测试
    if args.skip_tests:
        for test in args.skip_tests:
            if test in config.TEST_FILES:
                del config.TEST_FILES[test]
                print(f"跳过测试: {test}")

    # 运行测试
    try:
        results = runner.run_all_tests()
        report = runner.generate_final_report()
        exit_code = runner.print_final_summary(report)
        return exit_code
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        return 130
    except Exception as e:
        print(f"\n\n测试执行失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
