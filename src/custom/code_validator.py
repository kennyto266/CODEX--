"""
代碼驗證器和安全掃描器
用於驗證自定義指標代碼的安全性和正確性

功能:
- 語法檢查
- 安全掃描
- 惡意代碼檢測
- 代碼複雜度分析
- 模塊導入驗證
"""

import ast
import re
import sys
import importlib.util
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ValidationError:
    """驗證錯誤"""
    type: str
    message: str
    line_number: Optional[int] = None
    column: Optional[int] = None
    severity: str = 'error'  # error, warning, info
    code: Optional[str] = None  # 錯誤代碼


class SecurityScanner:
    """安全掃描器 - 檢測危險代碼"""

    def __init__(self):
        # 危險關鍵詞模式
        self.dangerous_keywords = {
            'file_operations': ['open', 'file', 'read', 'write', 'readlines', 'writelines'],
            'system_operations': ['exec', 'eval', 'compile', 'globals', 'locals', 'vars', 'dir'],
            'import_operations': ['__import__', 'importlib', 'reload'],
            'network_operations': ['socket', 'urllib', 'http', 'requests', 'urllib2', 'httplib'],
            'subprocess': ['subprocess', 'os.system', 'os.popen', 'shell', 'popen'],
            'serialization': ['pickle', 'marshal', 'shelve', 'dill', 'cloudpickle'],
            'threading': ['threading', 'multiprocessing', 'concurrent', 'asyncio'],
            'database': ['sqlite3', 'sqlite', 'database', 'db'],
            'os_access': ['os.path', 'os.listdir', 'os.remove', 'os.unlink', 'os.rename'],
            'dangerous_builtins': ['help', 'quit', 'exit', '__builtins__', 'input', 'raw_input'],
            'meta_programming': ['getattr', 'setattr', 'delattr', 'hasattr', 'delattr'],
        }

        # 危險的正則表達式模式
        self.dangerous_patterns = [
            (r'__\w+__', 'Magic methods', 'high'),
            (r'eval\s*\(', 'eval() function', 'high'),
            (r'exec\s*\(', 'exec() function', 'high'),
            (r'compile\s*\(', 'compile() function', 'medium'),
            (r'globals\(\)', 'globals() call', 'high'),
            (r'locals\(\)', 'locals() call', 'high'),
            (r'vars\(\)', 'vars() call', 'high'),
            (r'dir\s*\(', 'dir() call', 'medium'),
            (r'getattr\s*\(', 'getattr() call', 'high'),
            (r'setattr\s*\(', 'setattr() call', 'high'),
            (r'delattr\s*\(', 'delattr() call', 'high'),
            (r'hasattr\s*\(', 'hasattr() call', 'medium'),
            (r'open\s*\(', 'file operations', 'high'),
            (r'file\s*\(', 'file operations', 'high'),
            (r'input\s*\(', 'user input', 'high'),
            (r'raw_input\s*\(', 'user input', 'high'),
            (r'subprocess', 'subprocess module', 'high'),
            (r'os\.system', 'os.system call', 'high'),
            (r'os\.popen', 'os.popen call', 'high'),
            (r'shell\s*=', 'shell command', 'high'),
            (r'base64', 'base64 encoding', 'medium'),
            (r'marshal', 'marshal serialization', 'high'),
            (r'pickle', 'pickle serialization', 'high'),
            (r'ssl', 'SSL operations', 'medium'),
            (r'socket', 'socket operations', 'high'),
        ]

        # 允許的模塊
        self.allowed_modules = {
            'pandas', 'numpy', 'math', 'statistics', 'datetime', 'itertools',
            'collections', 'functools', 'operator', 'random'
        }

        # 禁止的模塊
        self.blocked_modules = {
            'os', 'sys', 'subprocess', 'socket', 'urllib', 'http', 'requests',
            'sqlite3', 'pickle', 'marshal', 'shelve', 'tempfile', 'shutil',
            'threading', 'multiprocessing', 'concurrent', 'asyncio', 'ssl',
            'imaplib', 'poplib', 'smtplib', 'ftp', 'telnet', 'hashlib',
            'cryptography', 'pycryptodome', 'Crypto'
        }

    def scan_code(self, code: str) -> List[ValidationError]:
        """
        掃描代碼中的安全風險

        Args:
            code: 待掃描的代碼

        Returns:
            安全錯誤列表
        """
        errors = []

        # 1. 檢查危險關鍵詞
        code_lower = code.lower()
        for category, keywords in self.dangerous_keywords.items():
            for keyword in keywords:
                if keyword in code_lower:
                    errors.append(ValidationError(
                        type='SecurityError',
                        message=f'Forbidden {category}: {keyword}',
                        severity='high',
                        code='SEC_001'
                    ))

        # 2. 檢查危險模式
        for pattern, description, severity in self.dangerous_patterns:
            matches = re.finditer(pattern, code, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                errors.append(ValidationError(
                    type='SecurityError',
                    message=f'{description} detected',
                    severity=severity,
                    code='SEC_002'
                ))

        # 3. 檢查import語句
        import_errors = self._check_imports(code)
        errors.extend(import_errors)

        # 4. 檢查函數定義
        function_errors = self._check_function_definitions(code)
        errors.extend(function_errors)

        return errors

    def _check_imports(self, code: str) -> List[ValidationError]:
        """檢查導入語句"""
        errors = []

        # 查找import語句
        import_patterns = [
            r'^\s*import\s+(\w+)',
            r'^\s*from\s+(\w+)\s+import',
        ]

        for pattern in import_patterns:
            matches = re.finditer(pattern, code, re.MULTILINE)
            for match in matches:
                module = match.group(1)
                if module in self.blocked_modules:
                    errors.append(ValidationError(
                        type='ImportError',
                        message=f'Blocked module: {module}',
                        line_number=code[:match.start()].count('\n') + 1,
                        severity='high',
                        code='IMP_001'
                    ))
                elif module not in self.allowed_modules:
                    # 檢查是否為子模塊
                    if any(module.startswith(blocked) for blocked in self.blocked_modules):
                        errors.append(ValidationError(
                            type='ImportError',
                            message=f'Blocked submodule: {module}',
                            line_number=code[:match.start()].count('\n') + 1,
                            severity='high',
                            code='IMP_002'
                        ))

        return errors

    def _check_function_definitions(self, code: str) -> List[ValidationError]:
        """檢查函數定義"""
        errors = []

        try:
            tree = ast.parse(code)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # 檢查函數名
                    if node.name.startswith('_'):
                        errors.append(ValidationError(
                            type='NamingError',
                            message=f'Function name starts with underscore: {node.name}',
                            line_number=node.lineno,
                            severity='warning',
                            code='NAM_001'
                        ))

                    # 檢查參數數量
                    if len(node.args.args) > 10:
                        errors.append(ValidationError(
                            type='ComplexityWarning',
                            message=f'Too many parameters: {node.name} has {len(node.args.args)} parameters',
                            line_number=node.lineno,
                            severity='warning',
                            code='CPL_001'
                        ))

        except SyntaxError as e:
            errors.append(ValidationError(
                type='SyntaxError',
                message=f'Syntax error: {str(e)}',
                line_number=e.lineno,
                severity='error',
                code='SYN_001'
            ))

        return errors


class CodeValidator:
    """代碼驗證器 - 驗證代碼語法和結構"""

    def __init__(self):
        self.security_scanner = SecurityScanner()

    def validate_code(
        self,
        code: str,
        check_security: bool = True,
        check_complexity: bool = True,
        max_complexity: int = 1000
    ) -> Dict[str, Any]:
        """
        驗證代碼

        Args:
            code: 待驗證的代碼
            check_security: 是否檢查安全性
            check_complexity: 是否檢查複雜度
            max_complexity: 最大複雜度

        Returns:
            驗證結果
        """
        result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'info': [],
            'metrics': {}
        }

        # 1. 語法檢查
        syntax_errors = self._check_syntax(code)
        if syntax_errors:
            result['errors'].extend(syntax_errors)
            result['is_valid'] = False

        # 2. 結構檢查
        structure_errors = self._check_structure(code)
        result['errors'].extend(structure_errors)
        if structure_errors:
            result['is_valid'] = False

        # 3. 安全掃描
        if check_security:
            security_errors = self.security_scanner.scan_code(code)
            result['errors'].extend(security_errors)
            if any(e.severity == 'high' for e in security_errors):
                result['is_valid'] = False

        # 4. 複雜度分析
        if check_complexity:
            complexity_info = self._analyze_complexity(code, max_complexity)
            result['metrics']['complexity'] = complexity_info

            if not complexity_info.get('is_acceptable', True):
                result['warnings'].append(ValidationError(
                    type='ComplexityWarning',
                    message=f'Code complexity too high: {complexity_info.get("total", 0)} > {max_complexity}',
                    severity='warning',
                    code='CPL_002'
                ))

        # 5. 代碼質量檢查
        quality_info = self._check_code_quality(code)
        result['metrics']['quality'] = quality_info

        # 6. 總結
        result['summary'] = {
            'total_errors': len(result['errors']),
            'total_warnings': len(result['warnings']),
            'total_info': len(result['info']),
            'error_rate': len(result['errors']) / max(1, len(code.splitlines())),
        }

        return result

    def _check_syntax(self, code: str) -> List[ValidationError]:
        """語法檢查"""
        errors = []

        try:
            ast.parse(code)
        except SyntaxError as e:
            errors.append(ValidationError(
                type='SyntaxError',
                message=str(e),
                line_number=e.lineno,
                column=e.offset,
                severity='error',
                code='SYN_001'
            ))
        except Exception as e:
            errors.append(ValidationError(
                type='ParseError',
                message=f'Parse error: {str(e)}',
                severity='error',
                code='SYN_002'
            ))

        return errors

    def _check_structure(self, code: str) -> List[ValidationError]:
        """結構檢查"""
        errors = []

        try:
            tree = ast.parse(code)

            # 檢查是否有函數定義
            has_function = any(isinstance(node, ast.FunctionDef) for node in ast.walk(tree))

            if not has_function:
                errors.append(ValidationError(
                    type='StructureError',
                    message='Code must define at least one function',
                    severity='error',
                    code='STR_001'
                ))

            # 檢查函數返回值
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if not any(isinstance(n, (ast.Return, ast.Yield)) for n in ast.walk(node)):
                        errors.append(ValidationError(
                            type='StructureWarning',
                            message=f'Function {node.name} has no return statement',
                            line_number=node.lineno,
                            severity='warning',
                            code='STR_002'
                        ))

        except Exception as e:
            errors.append(ValidationError(
                type='ValidationError',
                message=f'Structure validation failed: {str(e)}',
                severity='error',
                code='STR_003'
            ))

        return errors

    def _analyze_complexity(self, code: str, max_complexity: int) -> Dict[str, Any]:
        """複雜度分析"""
        try:
            tree = ast.parse(code)

            metrics = {
                'lines': len(code.splitlines()),
                'functions': 0,
                'classes': 0,
                'loops': 0,
                'conditions': 0,
                'imports': 0,
                'max_depth': 0,
            }

            def count_nodes(node, depth=0):
                nonlocal metrics
                metrics['max_depth'] = max(metrics['max_depth'], depth)

                if isinstance(node, ast.FunctionDef):
                    metrics['functions'] += 1
                elif isinstance(node, ast.ClassDef):
                    metrics['classes'] += 1
                elif isinstance(node, (ast.For, ast.While, ast.AsyncFor)):
                    metrics['loops'] += 1
                elif isinstance(node, (ast.If, ast.While, ast.Try)):
                    metrics['conditions'] += 1
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    metrics['imports'] += 1

                for child in ast.iter_child_nodes(node):
                    count_nodes(child, depth + 1)

            count_nodes(tree)

            # 計算總複雜度
            total = (
                metrics['functions'] * 2 +
                metrics['classes'] * 3 +
                metrics['loops'] * 3 +
                metrics['conditions'] * 2 +
                metrics['imports'] * 1 +
                metrics['max_depth']
            )

            metrics['total'] = total
            metrics['is_acceptable'] = total <= max_complexity

            return metrics

        except Exception as e:
            return {
                'error': str(e),
                'is_acceptable': False
            }

    def _check_code_quality(self, code: str) -> Dict[str, Any]:
        """代碼質量檢查"""
        lines = code.splitlines()
        total_lines = len(lines)
        non_empty_lines = len([l for l in lines if l.strip()])
        comment_lines = len([l for l in lines if l.strip().startswith('#')])

        # 檢查docstring
        has_docstring = False
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and ast.get_docstring(node):
                    has_docstring = True
                    break
        except:
            pass

        # 檢查變量命名
        problematic_names = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                    if len(node.id) == 1 or node.id.isupper():
                        problematic_names.append(node.id)
        except:
            pass

        return {
            'total_lines': total_lines,
            'non_empty_lines': non_empty_lines,
            'comment_lines': comment_lines,
            'comment_ratio': comment_lines / max(1, non_empty_lines),
            'has_docstring': has_docstring,
            'problematic_names': list(set(problematic_names)),
            'quality_score': self._calculate_quality_score(
                comment_lines, non_empty_lines, has_docstring, len(problematic_names)
            )
        }

    def _calculate_quality_score(
        self,
        comment_lines: int,
        code_lines: int,
        has_docstring: bool,
        problematic_names: int
    ) -> float:
        """計算代碼質量分數 (0-100)"""
        score = 100.0

        # 註釋比率 (理想: 20-40%)
        comment_ratio = comment_lines / max(1, code_lines)
        if comment_ratio < 0.1:
            score -= 10
        elif comment_ratio > 0.5:
            score -= 5

        # Docstring
        if not has_docstring:
            score -= 5

        # 變量命名
        score -= min(20, problematic_names * 2)

        return max(0, score)


# 導出
__all__ = [
    'ValidationError',
    'SecurityScanner',
    'CodeValidator',
]
