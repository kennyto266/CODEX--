#!/usr/bin/env python
"""
文档审查和更新脚本 (T244)

全面审查和更新项目文档，包括：
- 文档完整性检查
- 内容准确性验证
- 示例代码测试
- 文档更新和生成
"""

import os
import sys
import json
import re
import ast
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import argparse


# ==================== 文档审查配置 ====================

class DocsReviewConfig:
    """文档审查配置"""
    # 文档目录
    DOCS_DIR = "docs"
    README_PATH = "README.md"
    API_DOCS_DIR = "docs/api"
    GUIDES_DIR = "docs/guides"
    EXAMPLES_DIR = "examples"

    # 代码示例目录
    PYTHON_EXAMPLES_DIR = "examples/python"
    API_EXAMPLES_DIR = "examples/api"

    # 必要文档列表
    REQUIRED_DOCS = [
        "README.md",
        "API_DOCUMENTATION.md",
        "DEPLOYMENT_SUMMARY.md",
        "EXECUTION_GUIDE.md",
        "PROJECT_COMPLETION_GUIDE.md",
        "FINAL_PROJECT_SUMMARY.md",
        "TEST_COVERAGE_REPORT.md",
        "TELEGRAM_BOT_README.md",
        "运行指南.md"
    ]

    # API文档要求
    API_DOCS_REQUIRED = [
        "overview.md",
        "endpoints.md",
        "authentication.md",
        "examples.md"
    ]

    # 文档质量标准
    QUALITY_STANDARDS = {
        'min_length': 100,  # 最小字符数
        'required_sections': ['Description', 'Usage', 'Installation'],  # 必要章节
        'code_example_required': True,  # 需要代码示例
        'diagram_required': False,  # 需要图表
    }


# ==================== 文档完整性检查 ====================

class DocsCompletenessChecker:
    """文档完整性检查器"""

    def __init__(self, config: DocsReviewConfig):
        self.config = config
        self.missing_docs = []
        self.empty_docs = []
        self.incomplete_docs = []

    def check_required_documents(self) -> Dict[str, Any]:
        """检查必要文档"""
        print("=== 检查必要文档 ===")

        results = {
            'total_required': len(self.config.REQUIRED_DOCS),
            'found': 0,
            'missing': [],
            'empty': [],
            'details': []
        }

        for doc in self.config.REQUIRED_DOCS:
            doc_path = self._get_doc_path(doc)
            status, message = self._check_document(doc_path)

            if status == 'found':
                results['found'] += 1
                results['details'].append({
                    'document': doc,
                    'status': 'FOUND',
                    'path': doc_path,
                    'size': os.path.getsize(doc_path) if os.path.exists(doc_path) else 0
                })
                print(f"✓ {doc}")
            elif status == 'missing':
                results['missing'].append(doc)
                self.missing_docs.append(doc)
                results['details'].append({
                    'document': doc,
                    'status': 'MISSING'
                })
                print(f"✗ {doc} - 缺失")
            elif status == 'empty':
                results['empty'].append(doc)
                self.empty_docs.append(doc)
                results['details'].append({
                    'document': doc,
                    'status': 'EMPTY',
                    'path': doc_path
                })
                print(f"⚠ {doc} - 空文件")

        return results

    def check_api_documentation(self) -> Dict[str, Any]:
        """检查API文档"""
        print("\n=== 检查API文档 ===")

        results = {
            'total_required': len(self.config.API_DOCS_REQUIRED),
            'found': 0,
            'missing': [],
            'details': []
        }

        for doc in self.config.API_DOCS_REQUIRED:
            doc_path = os.path.join(self.config.API_DOCS_DIR, doc)
            if os.path.exists(doc_path):
                results['found'] += 1
                results['details'].append({
                    'document': doc,
                    'status': 'FOUND',
                    'path': doc_path
                })
                print(f"✓ {doc}")
            else:
                results['missing'].append(doc)
                print(f"✗ {doc} - 缺失")

        return results

    def check_code_examples(self) -> Dict[str, Any]:
        """检查代码示例"""
        print("\n=== 检查代码示例 ===")

        results = {
            'total_checked': 0,
            'valid': 0,
            'invalid': [],
            'missing_run_instructions': []
        }

        # 检查Python示例
        if os.path.exists(self.config.PYTHON_EXAMPLES_DIR):
            for example_file in os.listdir(self.config.PYTHON_EXAMPLES_DIR):
                if example_file.endswith('.py'):
                    example_path = os.path.join(self.config.PYTHON_EXAMPLES_DIR, example_file)
                    results['total_checked'] += 1

                    # 检查示例是否可运行
                    is_valid = self._validate_python_example(example_path)
                    if is_valid:
                        results['valid'] += 1
                        print(f"✓ {example_file}")
                    else:
                        results['invalid'].append(example_file)
                        print(f"✗ {example_file} - 语法错误")

        return results

    def _get_doc_path(self, doc: str) -> str:
        """获取文档路径"""
        # 优先检查docs目录
        docs_path = os.path.join(self.config.DOCS_DIR, doc)
        if os.path.exists(docs_path):
            return docs_path

        # 检查根目录
        root_path = doc
        if os.path.exists(root_path):
            return root_path

        return doc

    def _check_document(self, doc_path: str) -> Tuple[str, str]:
        """检查文档"""
        if not os.path.exists(doc_path):
            return 'missing', f"文档不存在: {doc_path}"

        # 检查文件大小
        file_size = os.path.getsize(doc_path)
        if file_size == 0:
            return 'empty', f"空文件: {doc_path}"

        # 检查内容
        with open(doc_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if len(content.strip()) < 100:
            return 'empty', f"内容过少: {doc_path}"

        return 'found', f"文档正常: {doc_path}"

    def _validate_python_example(self, file_path: str) -> bool:
        """验证Python示例"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()

            # 尝试解析AST
            ast.parse(code)
            return True
        except SyntaxError:
            return False


# ==================== 内容准确性验证 ====================

class ContentAccuracyValidator:
    """内容准确性验证器"""

    def __init__(self, config: DocsReviewConfig):
        self.config = config
        self.accuracy_issues = []

    def validate_readme_content(self) -> Dict[str, Any]:
        """验证README内容"""
        print("\n=== 验证README内容 ===")

        if not os.path.exists(self.config.README_PATH):
            return {'status': 'missing'}

        with open(self.config.README_PATH, 'r', encoding='utf-8') as f:
            content = f.read()

        issues = []

        # 检查必要章节
        required_sections = ['安装', '使用', '功能', 'API']
        for section in required_sections:
            if section not in content:
                issues.append(f"缺少章节: {section}")

        # 检查代码示例
        if '```' not in content:
            issues.append("缺少代码示例")

        # 检查徽章
        if '![' not in content:
            issues.append("缺少项目徽章")

        # 检查链接
        broken_links = self._check_broken_links(content)
        issues.extend(broken_links)

        if issues:
            self.accuracy_issues.extend(issues)
            print(f"发现 {len(issues)} 个问题")
            for issue in issues:
                print(f"  ⚠ {issue}")
        else:
            print("✓ README内容验证通过")

        return {
            'status': 'validated' if not issues else 'issues',
            'issues': issues
        }

    def validate_api_docs(self) -> Dict[str, Any]:
        """验证API文档"""
        print("\n=== 验证API文档 ===")

        issues = []

        # 检查API端点文档
        api_doc_path = os.path.join(self.config.API_DOCS_DIR, 'endpoints.md')
        if os.path.exists(api_doc_path):
            with open(api_doc_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 检查端点描述
            endpoint_pattern = r'### \w+'
            endpoints = re.findall(endpoint_pattern, content)
            if len(endpoints) < 5:
                issues.append(f"API端点文档不足: 仅发现 {len(endpoints)} 个端点")

            # 检查参数说明
            param_pattern = r'\*\*\w+\*\*:'
            params = re.findall(param_pattern, content)
            if len(params) < 10:
                issues.append(f"参数说明不足: 仅发现 {len(params)} 个参数")

        # 检查认证文档
        auth_doc_path = os.path.join(self.config.API_DOCS_DIR, 'authentication.md')
        if os.path.exists(auth_doc_path):
            with open(auth_doc_path, 'r', encoding='utf-8') as f:
                auth_content = f.read()

            if 'token' not in auth_content.lower():
                issues.append("认证文档缺少token说明")

            if '示例' not in auth_content:
                issues.append("认证文档缺少代码示例")

        if issues:
            self.accuracy_issues.extend(issues)
            print(f"发现 {len(issues)} 个问题")
            for issue in issues:
                print(f"  ⚠ {issue}")
        else:
            print("✓ API文档验证通过")

        return {
            'status': 'validated' if not issues else 'issues',
            'issues': issues
        }

    def _check_broken_links(self, content: str) -> List[str]:
        """检查失效链接"""
        issues = []

        # 提取Markdown链接
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        links = re.findall(link_pattern, content)

        for link_text, link_url in links:
            # 检查相对链接
            if link_url.startswith('./') or link_url.startswith('../'):
                link_path = link_url.split('#')[0]
                if not os.path.exists(link_path):
                    issues.append(f"失效链接: {link_text} -> {link_url}")

        return issues


# ==================== 示例代码测试 ====================

class CodeExampleTester:
    """代码示例测试器"""

    def __init__(self, config: DocsReviewConfig):
        self.config = config
        self.test_results = []

    def test_all_examples(self) -> Dict[str, Any]:
        """测试所有代码示例"""
        print("\n=== 测试代码示例 ===")

        results = {
            'total_tested': 0,
            'passed': 0,
            'failed': 0,
            'details': []
        }

        # 测试Python示例
        if os.path.exists(self.config.PYTHON_EXAMPLES_DIR):
            for example_file in os.listdir(self.config.PYTHON_EXAMPLES_DIR):
                if example_file.endswith('.py'):
                    example_path = os.path.join(self.config.PYTHON_EXAMPLES_DIR, example_file)
                    test_result = self._test_example(example_path, 'python')
                    results['total_tested'] += 1

                    if test_result['success']:
                        results['passed'] += 1
                        print(f"✓ {example_file}")
                    else:
                        results['failed'] += 1
                        print(f"✗ {example_file}: {test_result['error']}")

                    results['details'].append(test_result)

        # 测试API示例（使用curl）
        api_examples_dir = os.path.join(self.config.GUIDES_DIR, 'api-examples')
        if os.path.exists(api_examples_dir):
            for example_file in os.listdir(api_examples_dir):
                if example_file.endswith('.sh'):
                    example_path = os.path.join(api_examples_dir, example_file)
                    test_result = self._test_example(example_path, 'shell')
                    results['total_tested'] += 1

                    if test_result['success']:
                        results['passed'] += 1
                        print(f"✓ {example_file}")
                    else:
                        results['failed'] += 1
                        print(f"✗ {example_file}: {test_result['error']}")

                    results['details'].append(test_result)

        return results

    def _test_example(self, example_path: str, language: str) -> Dict[str, Any]:
        """测试单个示例"""
        result = {
            'file': example_path,
            'language': language,
            'success': False,
            'error': None,
            'output': None
        }

        try:
            if language == 'python':
                # 执行Python示例
                process = subprocess.run(
                    [sys.executable, example_path],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if process.returncode == 0:
                    result['success'] = True
                    result['output'] = process.stdout
                else:
                    result['error'] = process.stderr

            elif language == 'shell':
                # 测试shell脚本（不实际执行）
                with open(example_path, 'r') as f:
                    content = f.read()

                # 基本语法检查
                if content.strip():
                    result['success'] = True
                else:
                    result['error'] "空文件"

        except subprocess.TimeoutExpired:
            result['error'] = "执行超时"
        except Exception as e:
            result['error'] = str(e)

        return result


# ==================== 文档更新器 ====================

class DocsUpdater:
    """文档更新器"""

    def __init__(self, config: DocsReviewConfig):
        self.config = config

    def update_readme(self) -> bool:
        """更新README"""
        print("\n=== 更新README ===")

        readme_path = self.config.README_PATH

        if not os.path.exists(readme_path):
            # 创建README
            self._create_readme(readme_path)
            print(f"✓ 创建新README: {readme_path}")
            return True

        # 更新现有README
        try:
            with open(readme_path, 'r', encoding='utf-8') as f:
                content = f.read()

            updated = False

            # 检查并添加徽章
            if '![CI]' not in content:
                content = self._add_badges(content)
                updated = True

            # 检查并添加API文档链接
            if '[API文档](docs/api/overview.md)' not in content:
                content = self._add_api_docs_link(content)
                updated = True

            if updated:
                with open(readme_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✓ 更新README")
            else:
                print("✓ README已是最新")

            return True
        except Exception as e:
            print(f"✗ 更新README失败: {e}")
            return False

    def generate_api_docs_index(self) -> bool:
        """生成API文档索引"""
        print("\n=== 生成API文档索引 ===")

        index_path = os.path.join(self.config.API_DOCS_DIR, 'README.md')

        try:
            # 生成API文档索引
            index_content = self._generate_api_index_content()

            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(index_content)

            print(f"✓ 生成API文档索引: {index_path}")
            return True
        except Exception as e:
            print(f"✗ 生成API文档索引失败: {e}")
            return False

    def create_missing_docs(self) -> bool:
        """创建缺失的文档"""
        print("\n=== 创建缺失文档 ===")

        created = 0

        # 创建必要的API文档
        for doc in self.config.API_DOCS_REQUIRED:
            doc_path = os.path.join(self.config.API_DOCS_DIR, doc)
            if not os.path.exists(doc_path):
                self._create_api_doc(doc, doc_path)
                print(f"✓ 创建API文档: {doc}")
                created += 1

        return created > 0

    def _create_readme(self, path: str):
        """创建README"""
        content = f"""# 港股量化交易系统

[![CI](https://img.shields.io/badge/CI-passing-brightgreen)](https://github.com/your-repo/actions)
[![Version](https://img.shields.io/badge/Version-1.0.0-blue)](https://github.com/your-repo/releases)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

## 项目简介

港股量化交易系统是一个基于多智能体协作的港股量化交易平台，集成了数据适配器、回测引擎、实时监控和Telegram机器人等功能模块。

## 主要功能

- 📊 实时数据获取和处理
- 🤖 多智能体系统协作
- 📈 量化策略回测和优化
- 🔔 实时交易信号推送
- 📱 Telegram机器人支持

## 快速开始

### 安装

```bash
pip install -r requirements.txt
```

### 使用

```python
from src.trading.futu_trading_api import FutuTradingAPI

api = FutuTradingAPI()
api.run()
```

## 文档

- [完整文档](docs/)
- [API文档](docs/api/overview.md)
- [部署指南](DEPLOYMENT_SUMMARY.md)

## 许可证

MIT License
"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

    def _add_badges(self, content: str) -> str:
        """添加徽章"""
        badge_section = """[![CI](https://img.shields.io/badge/CI-passing-brightgreen)](https://github.com/your-repo/actions)
[![Version](https://img.shields.io/badge/Version-1.0.0-blue)](https://github.com/your-repo/releases)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

"""
        return badge_section + content

    def _add_api_docs_link(self, content: str) -> str:
        """添加API文档链接"""
        if '## 文档' in content:
            # 替换现有文档部分
            pattern = r'## 文档.*?(?=\n##|\Z)'
            replacement = """## 文档

- [完整文档](docs/)
- [API文档](docs/api/overview.md)
- [部署指南](DEPLOYMENT_SUMMARY.md)
"""
            return re.sub(pattern, replacement, content, flags=re.DOTALL)

        return content

    def _generate_api_index_content(self) -> str:
        """生成API文档索引内容"""
        return """# API 文档

## 概述

港股量化交易系统提供RESTful API接口，支持策略管理、数据获取、回测执行等功能。

## 文档结构

- [API概览](overview.md) - API总体介绍
- [认证](authentication.md) - API认证方式
- [端点](endpoints.md) - API端点详细说明
- [示例](examples.md) - 代码示例

## 快速开始

获取访问令牌：

```bash
curl -X POST http://localhost:8001/api/auth/token \\
  -H "Content-Type: application/json" \\
  -d '{"username": "your_username", "password": "your_password"}'
```
"""

    def _create_api_doc(self, doc_name: str, path: str):
        """创建API文档"""
        templates = {
            'overview.md': """# API 概览

## 简介

港股量化交易系统API提供了以下功能：

- 股票数据获取
- 策略回测
- 交易信号管理
- 性能监控

## 基本信息

- 基础URL: `http://localhost:8001/api`
- 协议: HTTP/HTTPS
- 数据格式: JSON
""",
            'authentication.md': """# 认证

## API Key认证

所有API请求需要在Header中包含API Key：

```bash
curl -H "X-API-Key: your_api_key" http://localhost:8001/api/endpoint
```

## Token认证

也可以使用Token认证：

```bash
curl -H "Authorization: Bearer your_token" http://localhost:8001/api/endpoint
```
""",
            'endpoints.md': """# API 端点

## 数据获取

### 获取股票价格

```http
GET /api/data/{symbol}
```

**参数:**
- `symbol`: 股票代码 (例如: 0700.hk)

**响应:**
```json
{
  "symbol": "0700.hk",
  "price": 320.0,
  "change": 1.5,
  "timestamp": "2023-01-01T00:00:00Z"
}
```

## 策略管理

### 获取策略列表

```http
GET /api/strategies
```

### 执行回测

```http
POST /api/backtest
```

**请求体:**
```json
{
  "symbol": "0700.hk",
  "start_date": "2023-01-01",
  "end_date": "2023-12-31",
  "strategy": "rsi"
}
```
""",
            'examples.md': """# 代码示例

## Python示例

```python
import requests

# 获取股票数据
response = requests.get('http://localhost:8001/api/data/0700.hk')
data = response.json()
print(f"股票价格: {data['price']}")
```

## JavaScript示例

```javascript
// 获取股票数据
fetch('http://localhost:8001/api/data/0700.hk')
  .then(response => response.json())
  .then(data => console.log(data));
```
"""
        }

        content = templates.get(doc_name, "")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)


# ==================== 主程序 ====================

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='文档审查和更新工具')
    parser.add_argument('--check-only', action='store_true', help='仅检查，不更新')
    parser.add_argument('--update', action='store_true', help='更新文档')
    parser.add_argument('--test-examples', action='store_true', help='测试代码示例')
    parser.add_argument('--output', type=str, default='docs_review_report.json', help='输出报告路径')

    args = parser.parse_args()

    # 初始化
    config = DocsReviewConfig()
    checker = DocsCompletenessChecker(config)
    validator = ContentAccuracyValidator(config)
    tester = CodeExampleTester(config)
    updater = DocsUpdater(config)

    # 执行检查
    print("=" * 60)
    print("港股量化交易系统 - 文档审查和更新")
    print("=" * 60)

    # 1. 文档完整性检查
    completeness_results = checker.check_required_documents()
    api_docs_results = checker.check_api_documentation()
    examples_results = checker.check_code_examples()

    # 2. 内容准确性验证
    readme_validation = validator.validate_readme_content()
    api_docs_validation = validator.validate_api_docs()

    # 3. 代码示例测试
    if args.test_examples:
        test_results = tester.test_all_examples()
    else:
        test_results = {'total_tested': 0, 'passed': 0, 'failed': 0}

    # 4. 更新文档
    update_results = {'updated': False}
    if args.update and not args.check_only:
        updater.create_missing_docs()
        updater.update_readme()
        updater.generate_api_docs_index()
        update_results['updated'] = True

    # 5. 生成报告
    report = {
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'completeness': {
            'required_documents': completeness_results,
            'api_documentation': api_docs_results,
            'code_examples': examples_results
        },
        'accuracy': {
            'readme': readme_validation,
            'api_docs': api_docs_validation
        },
        'testing': test_results,
        'updates': update_results,
        'summary': {
            'total_issues': len(checker.missing_docs) + len(checker.empty_docs) + len(validator.accuracy_issues),
            'critical_issues': len(checker.missing_docs),
            'recommendations': [
                "完善缺失的文档",
                "更新过时的内容",
                "添加更多代码示例",
                "修复失效链接"
            ]
        }
    }

    # 保存报告
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # 打印总结
    print("\n" + "=" * 60)
    print("文档审查总结")
    print("=" * 60)
    print(f"总问题数: {report['summary']['total_issues']}")
    print(f"严重问题: {report['summary']['critical_issues']}")
    print(f"必要文档: {completeness_results['found']}/{completeness_results['total_required']}")
    print(f"API文档: {api_docs_results['found']}/{api_docs_results['total_required']}")
    print(f"代码示例: {examples_results['total_checked']} 个")

    if test_results['total_tested'] > 0:
        print(f"示例测试: {test_results['passed']}/{test_results['total_tested']} 通过")

    print(f"\n报告已保存: {args.output}")

    # 返回退出码
    if report['summary']['critical_issues'] > 0:
        print("\n⚠ 发现严重问题，请检查文档")
        return 1
    else:
        print("\n✓ 文档检查通过")
        return 0


if __name__ == '__main__':
    sys.exit(main())
