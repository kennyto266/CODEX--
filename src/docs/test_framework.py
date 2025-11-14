"""
文档测试框架 (T599)

负责测试文档中的示例代码、验证API调用和执行代码片段。
支持自动发现、并行执行和详细报告。
"""

import os
import re
import ast
import sys
import json
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from datetime import datetime
import concurrent.futures
from dataclasses import dataclass
from enum import Enum


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestStatus(Enum):
    """测试状态枚举"""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class CodeTestResult:
    """代码测试结果"""
    file_path: str
    test_name: str
    status: TestStatus
    execution_time: float
    output: str
    error: Optional[str] = None
    stdout: str = ""
    stderr: str = ""


class DocumentationTestFramework:
    """文档测试框架主类"""

    def __init__(self, docs_path: str, src_path: str):
        """
        初始化测试框架

        Args:
            docs_path: 文档目录路径
            src_path: 源代码目录路径
        """
        self.docs_path = Path(docs_path)
        self.src_path = Path(src_path)
        self.test_results: List[CodeTestResult] = []

        # 支持的代码块语言
        self.supported_languages = {
            'python': '.py',
            'py': '.py',
            'bash': '.sh',
            'shell': '.sh',
            'javascript': '.js',
            'js': '.js'
        }

        # 测试模式
        self.test_modes = {
            'syntax': '语法检查',
            'execution': '执行测试',
            'api': 'API测试',
            'import': '导入测试'
        }

    def discover_tests(self) -> List[Dict]:
        """
        自动发现文档中的测试

        Returns:
            发现的测试列表
        """
        logger.info("发现文档中的代码测试...")

        tests = []
        code_block_pattern = re.compile(
            r'```(\w+)?(?:\{([^}]+)\})?\n(.*?)\n```',
            re.DOTALL
        )

        for doc_file in self.docs_path.rglob('*.md'):
            try:
                with open(doc_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 查找代码块
                for match in code_block_pattern.finditer(content):
                    lang = match.group(1) or ''
                    metadata = match.group(2) or ''
                    code = match.group(3)

                    # 跳过纯文本代码
                    if lang not in self.supported_languages:
                        continue

                    test_info = {
                        'file': str(doc_file),
                        'relative_file': str(doc_file.relative_to(self.docs_path)),
                        'language': lang,
                        'code': code,
                        'metadata': self._parse_metadata(metadata),
                        'line_number': content[:match.start()].count('\n') + 1
                    }

                    tests.append(test_info)

            except Exception as e:
                logger.error(f"处理文件 {doc_file} 时出错: {e}")

        logger.info(f"发现 {len(tests)} 个测试")
        return tests

    def _parse_metadata(self, metadata: str) -> Dict:
        """
        解析代码块元数据

        Args:
            metadata: 元数据字符串

        Returns:
            解析后的元数据字典
        """
        result = {
            'test': False,
            'skip': False,
            'timeout': 30,
            'expected_output': None
        }

        # 解析键值对
        for item in metadata.split(','):
            item = item.strip()
            if '=' in item:
                key, value = item.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"\'')

                if key == 'test':
                    result['test'] = value.lower() in ('true', '1', 'yes')
                elif key == 'skip':
                    result['skip'] = value.lower() in ('true', '1', 'yes')
                elif key == 'timeout':
                    try:
                        result['timeout'] = int(value)
                    except:
                        pass
                elif key == 'expected':
                    result['expected_output'] = value

        return result

    def run_all_tests(self, max_workers: int = 4, test_types: Set[str] = None) -> List[CodeTestResult]:
        """
        运行所有测试

        Args:
            max_workers: 最大并行工作线程数
            test_types: 要运行的测试类型集合

        Returns:
            测试结果列表
        """
        logger.info("开始运行文档测试...")

        tests = self.discover_tests()

        if not tests:
            logger.warning("没有发现测试")
            return []

        # 过滤测试
        if test_types:
            tests = [t for t in tests if self._should_run_test(t, test_types)]

        self.test_results = []

        # 并行执行测试
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_test = {
                executor.submit(self._run_single_test, test): test
                for test in tests
            }

            for future in concurrent.futures.as_completed(future_to_test):
                test = future_to_test[future]
                try:
                    result = future.result()
                    self.test_results.append(result)
                except Exception as e:
                    logger.error(f"执行测试时出错: {e}")

        # 生成报告
        self._generate_report()

        logger.info(f"测试完成，共 {len(self.test_results)} 个")
        return self.test_results

    def _should_run_test(self, test: Dict, test_types: Set[str]) -> bool:
        """
        判断是否应该运行测试

        Args:
            test: 测试信息
            test_types: 测试类型集合

        Returns:
            True if should run
        """
        metadata = test.get('metadata', {})

        # 跳过标记为skip的测试
        if metadata.get('skip'):
            return False

        # 如果指定了test类型，只运行标记为test的
        if 'test' in test_types:
            return metadata.get('test', False)

        # 默认运行所有支持的代码块
        return True

    def _run_single_test(self, test: Dict) -> CodeTestResult:
        """
        运行单个测试

        Args:
            test: 测试信息

        Returns:
            测试结果
        """
        start_time = time.time()
        language = test['language']
        code = test['code']
        metadata = test.get('metadata', {})
        file_path = test['relative_file']

        # 根据语言执行
        if language in ('python', 'py'):
            result = self._run_python_test(code, metadata, test)
        elif language in ('bash', 'shell'):
            result = self._run_bash_test(code, metadata, test)
        elif language in ('javascript', 'js'):
            result = self._run_js_test(code, metadata, test)
        else:
            result = CodeTestResult(
                file_path=file_path,
                test_name=f"test_{hash(code) % 10000}",
                status=TestStatus.SKIPPED,
                execution_time=time.time() - start_time,
                output="Unsupported language",
                stderr=f"Language '{language}' not supported"
            )

        result.execution_time = time.time() - start_time
        return result

    def _run_python_test(self, code: str, metadata: Dict, test: Dict) -> CodeTestResult:
        """
        运行Python代码测试

        Args:
            code: Python代码
            metadata: 元数据
            test: 测试信息

        Returns:
            测试结果
        """
        file_path = test['relative_file']
        test_name = f"{Path(file_path).stem}_line_{test['line_number']}"

        try:
            # 语法检查
            try:
                ast.parse(code)
            except SyntaxError as e:
                return CodeTestResult(
                    file_path=file_path,
                    test_name=test_name,
                    status=TestStatus.FAILED,
                    execution_time=0,
                    output="",
                    error=f"Syntax error: {e}"
                )

            # 如果只是语法检查模式
            if not metadata.get('test', False):
                return CodeTestResult(
                    file_path=file_path,
                    test_name=test_name,
                    status=TestStatus.PASSED,
                    execution_time=0,
                    output="Syntax check passed"
                )

            # 执行代码
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name

            try:
                # 捕获输出
                process = subprocess.run(
                    [sys.executable, temp_file],
                    capture_output=True,
                    text=True,
                    timeout=metadata.get('timeout', 30)
                )

                stdout = process.stdout
                stderr = process.stderr
                exit_code = process.returncode

                if exit_code == 0:
                    # 检查期望输出
                    expected = metadata.get('expected_output')
                    if expected and expected not in stdout:
                        return CodeTestResult(
                            file_path=file_path,
                            test_name=test_name,
                            status=TestStatus.FAILED,
                            execution_time=0,
                            output=stdout,
                            error=f"Expected output not found: {expected}"
                        )

                    return CodeTestResult(
                        file_path=file_path,
                        test_name=test_name,
                        status=TestStatus.PASSED,
                        execution_time=0,
                        output=stdout,
                        stdout=stdout,
                        stderr=stderr
                    )
                else:
                    return CodeTestResult(
                        file_path=file_path,
                        test_name=test_name,
                        status=TestStatus.FAILED,
                        execution_time=0,
                        output=stdout,
                        error=stderr or f"Exit code: {exit_code}"
                    )
            finally:
                os.unlink(temp_file)

        except subprocess.TimeoutExpired:
            return CodeTestResult(
                file_path=file_path,
                test_name=test_name,
                status=TestStatus.FAILED,
                execution_time=0,
                output="",
                error="Test timeout"
            )
        except Exception as e:
            return CodeTestResult(
                file_path=file_path,
                test_name=test_name,
                status=TestStatus.ERROR,
                execution_time=0,
                output="",
                error=str(e)
            )

    def _run_bash_test(self, code: str, metadata: Dict, test: Dict) -> CodeTestResult:
        """运行Bash脚本测试"""
        file_path = test['relative_file']
        test_name = f"{Path(file_path).stem}_line_{test['line_number']}"

        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
                f.write(code)
                temp_file = f.name

            os.chmod(temp_file, 0o755)

            try:
                process = subprocess.run(
                    ['bash', temp_file],
                    capture_output=True,
                    text=True,
                    timeout=metadata.get('timeout', 30)
                )

                stdout = process.stdout
                stderr = process.stderr

                if process.returncode == 0:
                    return CodeTestResult(
                        file_path=file_path,
                        test_name=test_name,
                        status=TestStatus.PASSED,
                        execution_time=0,
                        output=stdout,
                        stdout=stdout,
                        stderr=stderr
                    )
                else:
                    return CodeTestResult(
                        file_path=file_path,
                        test_name=test_name,
                        status=TestStatus.FAILED,
                        execution_time=0,
                        output=stdout,
                        error=stderr or f"Exit code: {process.returncode}"
                    )
            finally:
                os.unlink(temp_file)

        except Exception as e:
            return CodeTestResult(
                file_path=file_path,
                test_name=test_name,
                status=TestStatus.ERROR,
                execution_time=0,
                output="",
                error=str(e)
            )

    def _run_js_test(self, code: str, metadata: Dict, test: Dict) -> CodeTestResult:
        """运行JavaScript测试"""
        # JavaScript测试实现
        file_path = test['relative_file']
        return CodeTestResult(
            file_path=file_path,
            test_name=f"js_test_{hash(code) % 10000}",
            status=TestStatus.SKIPPED,
            execution_time=0,
            output="JavaScript tests not yet implemented"
        )

    def _generate_report(self):
        """生成测试报告"""
        if not self.test_results:
            return

        print("\n" + "="*80)
        print("文档测试报告".center(80))
        print("="*80)

        # 统计信息
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in self.test_results if r.status == TestStatus.FAILED)
        errors = sum(1 for r in self.test_results if r.status == TestStatus.ERROR)
        skipped = sum(1 for r in self.test_results if r.status == TestStatus.SKIPPED)

        print(f"\n总测试数: {total}")
        print(f"  通过: {passed} ({passed/total*100:.1f}%)")
        print(f"  失败: {failed}")
        print(f"  错误: {errors}")
        print(f"  跳过: {skipped}")

        # 显示失败的测试
        if failed > 0 or errors > 0:
            print("\n【失败/错误测试详情】")
            for result in self.test_results:
                if result.status in (TestStatus.FAILED, TestStatus.ERROR):
                    print(f"\n文件: {result.file_path}")
                    print(f"测试: {result.test_name}")
                    print(f"状态: {result.status.value.upper()}")
                    if result.error:
                        print(f"错误: {result.error[:200]}")
                    if result.stdout:
                        print(f"输出: {result.stdout[:200]}")

    def save_results(self, output_file: str):
        """
        保存测试结果

        Args:
            output_file: 输出文件路径
        """
        results = {
            'timestamp': datetime.now().isoformat(),
            'total_tests': len(self.test_results),
            'summary': {
                'passed': sum(1 for r in self.test_results if r.status == TestStatus.PASSED),
                'failed': sum(1 for r in self.test_results if r.status == TestStatus.FAILED),
                'errors': sum(1 for r in self.test_results if r.status == TestStatus.ERROR),
                'skipped': sum(1 for r in self.test_results if r.status == TestStatus.SKIPPED)
            },
            'tests': [
                {
                    'file_path': r.file_path,
                    'test_name': r.test_name,
                    'status': r.status.value,
                    'execution_time': r.execution_time,
                    'output': r.output,
                    'error': r.error,
                    'stdout': r.stdout,
                    'stderr': r.stderr
                }
                for r in self.test_results
            ]
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        logger.info(f"测试结果已保存到: {output_file}")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='文档测试框架')
    parser.add_argument('docs_path', help='文档目录路径')
    parser.add_argument('src_path', help='源代码目录路径')
    parser.add_argument('--output', '-o', default='docs_test_results.json', help='输出文件路径')
    parser.add_argument('--workers', '-w', type=int, default=4, help='并行工作线程数')
    parser.add_argument('--types', '-t', nargs='+', default=None, help='测试类型 (syntax, execution, api, import)')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')

    args = parser.parse_args()

    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 运行测试
    framework = DocumentationTestFramework(args.docs_path, args.src_path)

    test_types = set(args.types) if args.types else None
    results = framework.run_all_tests(max_workers=args.workers, test_types=test_types)

    # 保存结果
    framework.save_results(args.output)

    # 返回退出码
    failed = sum(1 for r in results if r.status == TestStatus.FAILED)
    errors = sum(1 for r in results if r.status == TestStatus.ERROR)
    return 0 if (failed + errors) == 0 else 1


if __name__ == '__main__':
    exit(main())
