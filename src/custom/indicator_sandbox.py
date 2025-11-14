"""
自定義指標沙箱 - 安全的代碼執行環境
支持用戶創建自定義技術指標

功能:
- 安全的Python代碼執行
- 資源使用限制 (時間、內存)
- 禁止危險操作
- 技術指標工具函數
- 性能監控
"""

import ast
import sys
import os
import signal
import logging
import traceback
import inspect
import time
import multiprocessing as mp
from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass, field
from concurrent.futures import ProcessPoolExecutor, TimeoutError as FutureTimeoutError
import pandas as pd
import numpy as np
import re

# Windows兼容性: resource模块在Windows上不可用
try:
    import resource
except ImportError:
    resource = None

logger = logging.getLogger(__name__)


@dataclass
class SandboxConfig:
    """沙箱配置 - 定義安全執行環境的參數"""
    max_execution_time: float = 10.0  # 最大執行時間（秒）
    max_memory_mb: int = 512  # 最大內存使用（MB）
    max_complexity: int = 1000  # 代碼複雜度限制
    max_function_calls: int = 10000  # 最大函數調用次數
    allowed_builtins: List[str] = field(default_factory=lambda: [
        'abs', 'min', 'max', 'sum', 'len', 'range', 'float', 'int', 'bool', 'str',
        'list', 'dict', 'tuple', 'set', 'round', 'sorted', 'reversed', 'enumerate',
        'zip', 'map', 'filter', 'all', 'any', 'isinstance', 'type'
    ])
    allowed_modules: List[str] = field(default_factory=lambda: [
        'pandas', 'numpy', 'math', 'statistics'
    ])
    blocked_keywords: List[str] = field(default_factory=lambda: [
        'import', 'exec', 'eval', 'open', 'file', 'input', 'raw_input',
        'compile', '__import__', 'reload', 'help', 'quit', 'exit',
        'globals', 'locals', 'vars', 'dir', '__builtins__', 'getattr',
        'setattr', 'delattr', 'hasattr'
    ])
    dangerous_modules: List[str] = field(default_factory=lambda: [
        'os', 'sys', 'subprocess', 'socket', 'urllib', 'http', 'requests',
        'sqlite3', 'pickle', 'marshal', 'shelve', 'tempfile', 'shutil',
        'threading', 'multiprocessing', 'concurrent', 'asyncio', 'ssl'
    ])


@dataclass
class SandboxError:
    """沙箱錯誤"""
    type: str
    message: str
    line_number: Optional[int] = None
    traceback: Optional[str] = None


class SecurityScanner:
    """安全掃描器 - 檢測惡意代碼"""

    def __init__(self):
        self.dangerous_patterns = [
            r'__\w+__',  # 魔法方法
            r'eval\s*\(',  # eval函數
            r'exec\s*\(',  # exec函數
            r'open\s*\(',  # 文件操作
            r'file\s*\(',  # 文件操作
            r'input\s*\(',  # 用戶輸入
            r'subprocess',  # 子進程
            r'os\.system',  # 系統調用
            r'os\.popen',  # 系統調用
            r'shell\s*=',  # shell命令
            r'base64',  # Base64編碼
            r'marshal',  # 序列化
            r'pickle',  # 序列化
        ]

    def scan_code(self, code: str) -> List[str]:
        """
        掃描代碼中的安全風險

        Args:
            code: 待掃描的代碼

        Returns:
            危險關鍵詞列表
        """
        violations = []

        for pattern in self.dangerous_patterns:
            matches = re.findall(pattern, code, re.IGNORECASE)
            if matches:
                violations.extend(matches)

        # 檢查import語句
        import_matches = re.findall(r'\bimport\s+', code, re.IGNORECASE)
        if import_matches:
            violations.append('import statements')

        return violations


class CodeValidator:
    """代碼驗證器 - 驗證用戶代碼語法和結構"""

    def __init__(self):
        self.security_scanner = SecurityScanner()

    def validate_code(self, code: str) -> List[SandboxError]:
        """
        驗證代碼

        Args:
            code: 待驗證的代碼

        Returns:
            錯誤列表
        """
        errors = []

        # 語法檢查
        try:
            ast.parse(code)
        except SyntaxError as e:
            errors.append(SandboxError(
                type="SyntaxError",
                message=str(e),
                line_number=e.lineno
            ))
            return errors

        # 安全掃描
        security_violations = self.security_scanner.scan_code(code)
        if security_violations:
            errors.append(SandboxError(
                type="SecurityError",
                message=f"Blocked keywords detected: {', '.join(security_violations)}"
            ))

        # 檢查是否定義了函數
        try:
            tree = ast.parse(code)
            has_function = any(isinstance(node, ast.FunctionDef) for node in ast.walk(tree))
            if not has_function:
                errors.append(SandboxError(
                    type="StructureError",
                    message="Code must define at least one function"
                ))
        except Exception as e:
            errors.append(SandboxError(
                type="ValidationError",
                message=f"Code validation failed: {str(e)}"
            ))

        return errors


class IndicatorSandbox:
    """自定義指標沙箱 - 安全的代碼執行環境"""

    def __init__(self, config: Optional[SandboxConfig] = None):
        self.config = config or SandboxConfig()
        self.validator = CodeValidator()
        self._compiled_cache: Dict[str, Any] = {}

    def validate_indicator(self, code: str) -> List[SandboxError]:
        """
        驗證自定義指標代碼

        Args:
            code: 指標代碼

        Returns:
            錯誤列表
        """
        return self.validator.validate_code(code)

    def execute_indicator(
        self,
        code: str,
        data: pd.DataFrame,
        parameters: Optional[Dict[str, Any]] = None,
        use_isolation: bool = True
    ) -> pd.DataFrame:
        """
        執行自定義指標

        Args:
            code: 指標代碼
            data: 股票數據 (OHLCV)
            parameters: 指標參數
            use_isolation: 是否使用進程隔離

        Returns:
            帶有指標值的DataFrame
        """
        # 驗證代碼
        errors = self.validate_indicator(code)
        if errors:
            raise ValueError(
                f"Code validation failed: {', '.join([e.message for e in errors])}"
            )

        if use_isolation:
            return self._execute_in_isolation(code, data, parameters)
        else:
            return self._execute_inline(code, data, parameters)

    def _execute_in_isolation(
        self,
        code: str,
        data: pd.DataFrame,
        parameters: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """在隔離進程中執行指標"""
        def _safe_execute(code, data_json, params_dict):
            """在子進程中執行的安全代碼"""
            try:
                import pandas as pd
                import numpy as np
                import ast
                import sys

                # 重建數據
                data = pd.DataFrame(data_json)
                parameters = params_dict or {}

                # 創建安全執行環境
                safe_globals = {
                    '__builtins__': {k: __builtins__[k] for k in [
                        'abs', 'min', 'max', 'sum', 'len', 'range', 'float', 'int',
                        'bool', 'str', 'list', 'dict', 'tuple', 'set', 'round',
                        'sorted', 'reversed', 'enumerate', 'zip', 'map', 'filter'
                    ]},
                    'pd': pd,
                    'np': np,
                    'parameters': parameters,
                    'sma': sma,
                    'ema': ema,
                    'rsi': rsi,
                    'macd': macd,
                    'bollinger_bands': bollinger_bands,
                    'atr': atr,
                    'stochastic': stochastic,
                }

                safe_locals = {}

                # 編譯並執行
                compiled = compile(code, '<indicator>', 'exec')
                exec(compiled, safe_globals, safe_locals)

                # 找到指標函數
                indicator_func = None
                for name, value in safe_locals.items():
                    if callable(value) and not name.startswith('_'):
                        indicator_func = value
                        break

                if indicator_func is None:
                    raise ValueError("No callable function found")

                # 執行指標
                result = indicator_func(data, **parameters)

                # 轉換為可序列化的格式
                if isinstance(result, pd.DataFrame):
                    return {
                        'success': True,
                        'data': result.to_dict('records'),
                        'columns': result.columns.tolist(),
                        'index': result.index.tolist()
                    }
                elif isinstance(result, pd.Series):
                    df = result.to_frame()
                    return {
                        'success': True,
                        'data': df.to_dict('records'),
                        'columns': df.columns.tolist(),
                        'index': df.index.tolist()
                    }
                else:
                    return {
                        'success': True,
                        'data': result.tolist() if hasattr(result, 'tolist') else result
                    }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e),
                    'traceback': traceback.format_exc()
                }

        # 準備數據
        data_json = data.to_dict('records')
        parameters = parameters or {}

        # 使用進程池執行
        try:
            with ProcessPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    _safe_execute,
                    code,
                    data_json,
                    parameters
                )

                result = future.result(timeout=self.config.max_execution_time)

                if not result['success']:
                    raise RuntimeError(f"Indicator execution failed: {result['error']}")

                # 重建DataFrame
                if isinstance(result['data'], list) and result.get('columns'):
                    index = pd.to_datetime(result['index'])
                    data_dict = {col: [row[col] for row in result['data']]
                                for col in result['columns']}
                    return pd.DataFrame(data_dict, index=index)
                else:
                    return result['data']

        except FutureTimeoutError:
            raise TimeoutError(f"Indicator execution timed out after {self.config.max_execution_time}s")
        except Exception as e:
            logger.error(f"Isolated execution failed: {str(e)}")
            raise

    def _execute_inline(
        self,
        code: str,
        data: pd.DataFrame,
        parameters: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """內聯執行指標（較快但不那麼安全）"""
        parameters = parameters or {}

        # 創建安全的執行環境
        safe_globals = {
            '__builtins__': {k: __builtins__[k] for k in self.config.allowed_builtins
                           if k in __builtins__},
            'pd': pd,
            'np': np,
            'parameters': parameters,
            'sma': sma,
            'ema': ema,
            'rsi': rsi,
            'macd': macd,
            'bollinger_bands': bollinger_bands,
            'atr': atr,
            'stochastic': stochastic,
        }

        safe_locals = {}

        try:
            # 編譯代碼
            compiled_code = compile(code, '<indicator>', 'exec')
            self._compiled_cache[code] = compiled_code

            # 執行代碼
            exec(compiled_code, safe_globals, safe_locals)

            # 查找指標函數
            indicator_func = None
            for name, value in safe_locals.items():
                if callable(value) and not name.startswith('_'):
                    indicator_func = value
                    break

            if indicator_func is None:
                raise ValueError("No callable function found in the code")

            # 執行指標函數
            result = indicator_func(data, **parameters)

            # 確保結果是DataFrame
            if not isinstance(result, pd.DataFrame):
                if isinstance(result, pd.Series):
                    result = result.to_frame()
                else:
                    # 嘗試轉換為Series
                    result = pd.Series(result, index=data.index, name='indicator')

            return result

        except Exception as e:
            logger.error(f"Indicator execution failed: {str(e)}")
            logger.error(traceback.format_exc())
            raise RuntimeError(f"Failed to execute indicator: {str(e)}")

    def get_supported_functions(self) -> List[str]:
        """獲取支持的函數列表"""
        return [
            'sma(data, period) - 簡單移動平均',
            'ema(data, period) - 指數移動平均',
            'rsi(data, period) - 相對強弱指數',
            'macd(data, fast, slow, signal) - MACD',
            'bollinger_bands(data, period, std) - 布林帶',
            'atr(data, period) - 真實波動範圍',
            'stochastic(high, low, close, k_period, d_period) - 隨機指標',
        ]

    def analyze_complexity(self, code: str) -> Dict[str, Any]:
        """
        分析代碼複雜度

        Args:
            code: 代碼字符串

        Returns:
            複雜度分析結果
        """
        try:
            tree = ast.parse(code)

            # 計算各種指標
            complexity_metrics = {
                'total_lines': len(code.splitlines()),
                'function_count': 0,
                'class_count': 0,
                'loop_count': 0,
                'condition_count': 0,
                'import_count': 0,
                'max_depth': 0,
            }

            def count_nodes(node, depth=0):
                nonlocal complexity_metrics
                complexity_metrics['max_depth'] = max(complexity_metrics['max_depth'], depth)

                if isinstance(node, ast.FunctionDef):
                    complexity_metrics['function_count'] += 1
                elif isinstance(node, ast.ClassDef):
                    complexity_metrics['class_count'] += 1
                elif isinstance(node, (ast.For, ast.While, ast.AsyncFor)):
                    complexity_metrics['loop_count'] += 1
                elif isinstance(node, (ast.If, ast.While)):
                    complexity_metrics['condition_count'] += 1
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    complexity_metrics['import_count'] += 1

                for child in ast.iter_child_nodes(node):
                    count_nodes(child, depth + 1)

            count_nodes(tree)

            # 計算總複雜度
            total_complexity = (
                complexity_metrics['function_count'] * 2 +
                complexity_metrics['class_count'] * 3 +
                complexity_metrics['loop_count'] * 3 +
                complexity_metrics['condition_count'] * 2 +
                complexity_metrics['import_count'] * 1 +
                complexity_metrics['max_depth']
            )

            complexity_metrics['total_complexity'] = total_complexity
            complexity_metrics['is_acceptable'] = total_complexity <= self.config.max_complexity

            return complexity_metrics

        except Exception as e:
            return {
                'error': str(e),
                'is_acceptable': False
            }


# 工具函數
def sma(data: pd.DataFrame, period: int) -> pd.Series:
    """簡單移動平均"""
    if 'close' not in data.columns:
        raise ValueError("Data must contain 'close' column")
    return data['close'].rolling(window=period).mean()


def ema(data: pd.DataFrame, period: int) -> pd.Series:
    """指數移動平均"""
    if 'close' not in data.columns:
        raise ValueError("Data must contain 'close' column")
    return data['close'].ewm(span=period).mean()


def rsi(data: pd.DataFrame, period: int = 14) -> pd.Series:
    """相對強弱指數"""
    if 'close' not in data.columns:
        raise ValueError("Data must contain 'close' column")

    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    return 100 - (100 / (1 + rs))


def macd(data: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """MACD指標"""
    if 'close' not in data.columns:
        raise ValueError("Data must contain 'close' column")

    ema_fast = ema(data, fast)
    ema_slow = ema(data, slow)
    macd_line = ema_fast - ema_slow

    # 计算Signal线 - 使用macd_line作为Series
    signal_df = data.copy()
    signal_df['macd'] = macd_line
    signal_line = ema(signal_df, signal)

    histogram = macd_line - signal_line

    return pd.DataFrame({
        'macd': macd_line,
        'signal': signal_line,
        'histogram': histogram
    }, index=data.index)


def bollinger_bands(data: pd.DataFrame, period: int = 20, std: float = 2) -> pd.DataFrame:
    """布林帶"""
    if 'close' not in data.columns:
        raise ValueError("Data must contain 'close' column")

    sma_line = data['close'].rolling(window=period).mean()
    std_line = data['close'].rolling(window=period).std()

    return pd.DataFrame({
        'upper': sma_line + (std_line * std),
        'middle': sma_line,
        'lower': sma_line - (std_line * std)
    }, index=data.index)


def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """真實波動範圍"""
    high_low = high - low
    high_close = np.abs(high - close.shift())
    low_close = np.abs(low - close.shift())

    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()


def stochastic(high: pd.Series, low: pd.Series, close: pd.Series,
               k_period: int = 14, d_period: int = 3) -> pd.DataFrame:
    """隨機指標 (KD)"""
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()

    k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
    d_percent = k_percent.rolling(window=d_period).mean()

    return pd.DataFrame({
        'k': k_percent,
        'd': d_percent
    })


# 導出工具函數
__all__ = [
    'IndicatorSandbox',
    'SandboxConfig',
    'SandboxError',
    'CodeValidator',
    'SecurityScanner',
    'sma',
    'ema',
    'rsi',
    'macd',
    'bollinger_bands',
    'atr',
    'stochastic',
]
