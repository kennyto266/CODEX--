"""
受控本地代码执行工具。
仅允许使用 numpy/pandas/math/random 进行小规模计算（如Sharpe回测）。
阻止危险内置与文件/网络操作。
"""

from typing import Any, Dict
import math
import random


ALLOWED_GLOBALS: Dict[str, Any] = {
    "__builtins__": {
        "abs": abs,
        "min": min,
        "max": max,
        "sum": sum,
        "len": len,
        "range": range,
        "enumerate": enumerate,
        "map": map,
        "filter": filter,
        "list": list,
        "dict": dict,
        "float": float,
        "int": int,
        "print": print,
    },
    "math": math,
    "random": random,
}


def execute_python(code: str, local_vars: Dict[str, Any]) -> Dict[str, Any]:
    """在受限环境中执行代码，返回 {ok, result|error}."""
    try:
        safe_locals = dict(local_vars or {})
        exec(code, ALLOWED_GLOBALS, safe_locals)
        return {"ok": True, "result": safe_locals}
    except Exception as e:
        return {"ok": False, "error": str(e)}


