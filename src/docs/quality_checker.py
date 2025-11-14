"""
文档质量检查器 (T599)

负责验证文档的完整性、链接有效性、拼写语法和覆盖率统计。
支持 Markdown、reStructuredText 和 API 文档的检查。
"""

import os
import re
import ast
import json
import yaml
import requests
import logging
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from datetime import datetime
from urllib.parse import urljoin, urlparse
from collections import defaultdict
import subprocess


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentationQualityChecker:
    """文档质量检查器主类"""

    # 支持的文档格式
    SUPPORTED_FORMATS = {'.md', '.rst', '.txt'}

    # 需要检查的文件类型
    CHECK_TYPES = {
        'links': '链接有效性',
        'spelling': '拼写检查',
        'grammar': '语法检查',
        'completeness': '完整性',
        'coverage': '覆盖率',
        'consistency': '一致性'
    }

    def __init__(self, project_root: str, docs_path: str, src_path: str):
        """
        初始化质量检查器

        Args:
            project_root: 项目根目录
            docs_path: 文档目录路径
            src_path: 源代码目录路径
        """
        self.project_root = Path(project_root)
        self.docs_path = Path(docs_path)
        self.src_path = Path(src_path)
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'summary': {},
            'details': {},
            'issues': []
        }

    def check_all(self) -> Dict:
        """
        执行所有检查

        Returns:
            包含检查结果的字典
        """
        logger.info("开始文档质量检查...")

        # 1. 检查文档完整性
        self._check_completeness()

        # 2. 验证链接有效性
        self._check_links()

        # 3. 检查拼写和语法
        self._check_spelling()

        # 4. 统计文档覆盖率
        self._check_coverage()

        # 5. 验证代码与文档一致性
        self._check_consistency()

        # 生成摘要
        self._generate_summary()

        logger.info("文档质量检查完成")
        return self.results

    def _check_completeness(self):
        """检查文档完整性"""
        logger.info("检查文档完整性...")

        completeness_results = {
            'total_files': 0,
            'checked_files': 0,
            'missing_files': [],
            'incomplete_files': []
        }

        # 定义必要的文档文件
        required_files = {
            'README.md': '项目主说明文档',
            'api/': 'API文档目录',
            'guides/': '使用指南目录',
            'architecture/': '架构文档目录',
            'developer-guide/': '开发者指南目录'
        }

        for req_path, desc in required_files.items():
            full_path = self.docs_path / req_path
            if full_path.exists():
                completeness_results['checked_files'] += 1
            else:
                completeness_results['missing_files'].append({
                    'file': req_path,
                    'description': desc
                })

        # 检查所有文档文件
        for file_path in self.docs_path.rglob('*'):
            if file_path.suffix in self.SUPPORTED_FORMATS:
                completeness_results['total_files'] += 1

                # 检查文件是否为空或过小
                if file_path.stat().st_size < 100:
                    completeness_results['incomplete_files'].append(str(file_path))

        self.results['details']['completeness'] = completeness_results

    def _check_links(self) -> Dict[str, List[Dict]]:
        """
        验证链接有效性

        Returns:
            链接检查结果
        """
        logger.info("验证链接有效性...")

        link_results = {
            'total_links': 0,
            'valid_links': 0,
            'broken_links': [],
            'relative_links': [],
            'external_links': []
        }

        # 链接模式
        link_patterns = [
            r'\[([^\]]+)\]\(([^)]+)\)',  # Markdown链接
            r'`([^`]+)`',  # 内联代码
            r'.. \w+:: ([^\n]+)',  # reStructuredText 指令
        ]

        for file_path in self.docs_path.rglob('*'):
            if file_path.suffix in self.SUPPORTED_FORMATS:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    for pattern in link_patterns:
                        for match in re.finditer(pattern, content):
                            link = match.group(2) if len(match.groups()) > 1 else match.group(1)
                            link_results['total_links'] += 1

                            # 分类链接
                            if link.startswith(('http://', 'https://')):
                                # 外部链接
                                link_info = {
                                    'file': str(file_path.relative_to(self.docs_path)),
                                    'link': link,
                                    'type': 'external'
                                }
                                link_results['external_links'].append(link_info)

                                # 检查外部链接有效性（限制数量避免超时）
                                if len(link_results['external_links']) <= 50:
                                    if not self._check_external_link(link):
                                        link_results['broken_links'].append({
                                            **link_info,
                                            'error': 'Unreachable'
                                        })
                                        link_results['valid_links'] -= 1
                                    else:
                                        link_results['valid_links'] += 1
                            else:
                                # 相对链接
                                link_info = {
                                    'file': str(file_path.relative_to(self.docs_path)),
                                    'link': link,
                                    'type': 'relative'
                                }
                                link_results['relative_links'].append(link_info)

                                # 检查相对链接是否存在
                                target = (file_path.parent / link).resolve()
                                if not target.exists():
                                    link_results['broken_links'].append({
                                        **link_info,
                                        'error': 'File not found'
                                    })

                except Exception as e:
                    logger.error(f"处理文件 {file_path} 时出错: {e}")

        self.results['details']['links'] = link_results
        return link_results

    def _check_external_link(self, url: str, timeout: int = 5) -> bool:
        """
        检查外部链接是否可访问

        Args:
            url: URL地址
            timeout: 超时时间（秒）

        Returns:
            True if accessible, False otherwise
        """
        try:
            response = requests.head(url, timeout=timeout, allow_redirects=True)
            return response.status_code < 400
        except:
            try:
                response = requests.get(url, timeout=timeout, stream=True)
                return response.status_code < 400
            except:
                return False

    def _check_spelling(self):
        """检查拼写和语法"""
        logger.info("检查拼写和语法...")

        spelling_results = {
            'files_checked': 0,
            'errors': [],
            'warnings': [],
            'common_misspellings': []
        }

        # 常见拼写错误
        common_errors = {
            'teh': 'the',
            'recieve': 'receive',
            'seperate': 'separate',
            'definately': 'definitely',
            'occured': 'occurred',
            'writen': 'written',
            'buisness': 'business',
            'accross': 'across',
            'begining': 'beginning'
        }

        for file_path in self.docs_path.rglob('*'):
            if file_path.suffix in self.SUPPORTED_FORMATS:
                spelling_results['files_checked'] += 1

                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # 检查常见拼写错误
                    for error, correction in common_errors.items():
                        if re.search(r'\b' + error + r'\b', content, re.IGNORECASE):
                            spelling_results['common_misspellings'].append({
                                'file': str(file_path.relative_to(self.docs_path)),
                                'error': error,
                                'correction': correction
                            })

                    # 检查大写问题（简单检查）
                    lines = content.split('\n')
                    for i, line in enumerate(lines, 1):
                        # 检查句子是否以大写字母开头（跳过代码块）
                        if line.strip() and not line.strip().startswith(('```', '.. code-block', '    ')):
                            if re.match(r'^[a-z]', line.strip()):
                                spelling_results['warnings'].append({
                                    'file': str(file_path.relative_to(self.docs_path)),
                                    'line': i,
                                    'message': 'Sentence may need capitalization'
                                })

                except Exception as e:
                    logger.error(f"检查文件 {file_path} 时出错: {e}")

        self.results['details']['spelling'] = spelling_results

    def _check_coverage(self):
        """统计文档覆盖率"""
        logger.info("统计文档覆盖率...")

        coverage_results = {
            'code_files': 0,
            'documented_files': 0,
            'undocumented_files': [],
            'documentation_percentage': 0,
            'by_module': {}
        }

        # 计算代码文件数
        for py_file in self.src_path.rglob('*.py'):
            coverage_results['code_files'] += 1

            # 检查是否有相应的文档
            doc_path = self.docs_path / f"{py_file.stem}.md"
            if doc_path.exists():
                coverage_results['documented_files'] += 1
            else:
                coverage_results['undocumented_files'].append(
                    str(py_file.relative_to(self.src_path))
                )

        # 计算覆盖率百分比
        if coverage_results['code_files'] > 0:
            coverage_results['documentation_percentage'] = (
                coverage_results['documented_files'] / coverage_results['code_files'] * 100
            )

        self.results['details']['coverage'] = coverage_results

    def _check_consistency(self):
        """验证代码与文档一致性"""
        logger.info("检查代码与文档一致性...")

        consistency_results = {
            'api_consistency': [],
            'version_consistency': [],
            'example_validation': []
        }

        # 1. 检查API文档一致性
        self._check_api_consistency(consistency_results)

        # 2. 检查版本号一致性
        self._check_version_consistency(consistency_results)

        # 3. 验证示例代码
        self._validate_code_examples(consistency_results)

        self.results['details']['consistency'] = consistency_results

    def _check_api_consistency(self, results: Dict):
        """检查API文档与代码一致性"""
        # 解析FastAPI路由
        api_pattern = re.compile(r'@app\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']')

        # 从源代码提取API路径
        api_routes = set()
        for py_file in self.src_path.rglob('*.py'):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    for match in api_pattern.finditer(content):
                        method = match.group(1).upper()
                        path = match.group(2)
                        api_routes.add(f"{method} {path}")
            except:
                continue

        # 从文档提取API路径
        doc_api_routes = set()
        for doc_file in self.docs_path.rglob('*.md'):
            try:
                with open(doc_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 寻找API路径模式
                    for match in re.finditer(r'<(?:code|`)([A-Z]+)\s+([^>]+)>(?:</code>|`)', content):
                        doc_api_routes.add(f"{match.group(1)} {match.group(2)}")
            except:
                continue

        # 比较差异
        missing_in_docs = api_routes - doc_api_routes
        missing_in_code = doc_api_routes - api_routes

        if missing_in_docs:
            results['api_consistency'].append({
                'type': 'missing_in_docs',
                'routes': list(missing_in_docs)
            })

        if missing_in_code:
            results['api_consistency'].append({
                'type': 'missing_in_code',
                'routes': list(missing_in_code)
            })

    def _check_version_consistency(self, results: Dict):
        """检查版本号一致性"""
        # 从setup.py/pyproject.toml提取版本
        version_files = [
            self.project_root / 'setup.py',
            self.project_root / 'pyproject.toml',
            self.project_root / '__init__.py'
        ]

        versions = {}
        for vfile in version_files:
            if vfile.exists():
                try:
                    with open(vfile, 'r', encoding='utf-8') as f:
                        content = f.read()
                        version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
                        if version_match:
                            versions[vfile.name] = version_match.group(1)
                except:
                    continue

        # 检查文档中的版本
        doc_version = None
        for doc_file in self.docs_path.rglob('*.md'):
            try:
                with open(doc_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    version_match = re.search(r'(?:version|Version)\s*[:#]\s*([\d.]+)', content)
                    if version_match:
                        doc_version = version_match.group(1)
                        break
            except:
                continue

        # 验证一致性
        if len(versions) > 1 and len(set(versions.values())) > 1:
            results['version_consistency'].append({
                'type': 'inconsistent',
                'versions': versions
            })

        if doc_version and versions:
            code_version = list(versions.values())[0]
            if code_version != doc_version:
                results['version_consistency'].append({
                    'type': 'doc_mismatch',
                    'code_version': code_version,
                    'doc_version': doc_version
                })

    def _validate_code_examples(self, results: Dict):
        """验证文档中的代码示例"""
        code_block_pattern = re.compile(r'```(\w+)?\n(.*?)\n```', re.DOTALL)

        for doc_file in self.docs_path.rglob('*.md'):
            try:
                with open(doc_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                for match in code_block_pattern.finditer(content):
                    lang = match.group(1) or ''
                    code = match.group(2)

                    if lang.lower() in ('python', 'py'):
                        # 验证Python代码
                        try:
                            ast.parse(code)
                            results['example_validation'].append({
                                'file': str(doc_file.relative_to(self.docs_path)),
                                'status': 'valid',
                                'language': 'python'
                            })
                        except SyntaxError as e:
                            results['example_validation'].append({
                                'file': str(doc_file.relative_to(self.docs_path)),
                                'status': 'invalid',
                                'language': 'python',
                                'error': str(e)
                            })

            except Exception as e:
                logger.error(f"验证文档 {doc_file} 中的代码示例时出错: {e}")

    def _generate_summary(self):
        """生成检查摘要"""
        summary = {
            'total_issues': 0,
            'critical_issues': 0,
            'warnings': 0,
            'categories': {}
        }

        # 统计各类问题
        for category, details in self.results['details'].items():
            count = 0
            if category == 'links':
                count = len(details.get('broken_links', []))
                if count > 0:
                    summary['critical_issues'] += count
            elif category == 'spelling':
                count = len(details.get('common_misspellings', []))
                summary['warnings'] += count
            elif category == 'completeness':
                count = len(details.get('missing_files', []))
                if count > 0:
                    summary['critical_issues'] += count
            elif category == 'consistency':
                count = sum(len(item.get('routes', [])) for item in details.get('api_consistency', []))
                if count > 0:
                    summary['critical_issues'] += count

            summary['categories'][category] = count
            summary['total_issues'] += count

        self.results['summary'] = summary

    def save_results(self, output_path: str):
        """
        保存检查结果到文件

        Args:
            output_path: 输出文件路径
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        logger.info(f"检查结果已保存到: {output_path}")

    def print_report(self):
        """打印检查报告"""
        print("\n" + "="*80)
        print("文档质量检查报告".center(80))
        print("="*80)
        print(f"\n检查时间: {self.results['timestamp']}")

        # 摘要
        summary = self.results['summary']
        print(f"\n【摘要】")
        print(f"  总问题数: {summary['total_issues']}")
        print(f"  严重问题: {summary['critical_issues']}")
        print(f"  警告: {summary['warnings']}")

        # 各类别统计
        print(f"\n【分类统计】")
        for category, count in summary['categories'].items():
            print(f"  {self.CHECK_TYPES.get(category, category)}: {count}")

        # 严重问题详情
        if summary['critical_issues'] > 0:
            print(f"\n【严重问题详情】")

            # 链接问题
            if 'links' in self.results['details']:
                broken = self.results['details']['links'].get('broken_links', [])
                if broken:
                    print(f"\n  断开的链接 ({len(broken)}):")
                    for link in broken[:5]:  # 只显示前5个
                        print(f"    - {link['file']}: {link['link']} ({link.get('error', 'Unknown')})")
                    if len(broken) > 5:
                        print(f"    ... 还有 {len(broken) - 5} 个")

            # 缺失文件
            if 'completeness' in self.results['details']:
                missing = self.results['details']['completeness'].get('missing_files', [])
                if missing:
                    print(f"\n  缺失文件 ({len(missing)}):")
                    for mfile in missing[:5]:
                        print(f"    - {mfile['file']}: {mfile['description']}")
                    if len(missing) > 5:
                        print(f"    ... 还有 {len(missing) - 5} 个")

        # 覆盖率
        if 'coverage' in self.results['details']:
            cov = self.results['details']['coverage']
            print(f"\n【文档覆盖率】")
            print(f"  代码文件: {cov['code_files']}")
            print(f"  已文档化: {cov['documented_files']}")
            print(f"  覆盖率: {cov['documentation_percentage']:.1f}%")

        print("\n" + "="*80)


def main():
    """主函数"""
    import sys

    project_root = sys.argv[1] if len(sys.argv) > 1 else '.'
    docs_path = sys.argv[2] if len(sys.argv) > 2 else './docs'
    src_path = sys.argv[3] if len(sys.argv) > 3 else './src'
    output_path = sys.argv[4] if len(sys.argv) > 4 else './docs_quality_report.json'

    checker = DocumentationQualityChecker(project_root, docs_path, src_path)
    results = checker.check_all()
    checker.print_report()
    checker.save_results(output_path)

    # 返回退出码
    return 0 if results['summary']['total_issues'] == 0 else 1


if __name__ == '__main__':
    exit(main())
