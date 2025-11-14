#!/usr/bin/env python3
"""
Phase 4 性能優化工具 - 懶加載系統
減少啟動時間，通過按需加載模組和資源
"""

import sys
import importlib
import functools
from typing import Any, Dict, Optional, Callable, Type
from importlib import import_module


class LazyLoader:
    """
    懶加載器 - 按需加載模組和資源

    Example:
        # 替代:
        # import pandas as pd
        # import numpy as np
        # import matplotlib.pyplot as plt

        # 使用:
        pd = LazyLoader('pandas')
        np = LazyLoader('numpy')
        plt = LazyLoader('matplotlib.pyplot')

        # 實際使用時才加載
        df = pd.DataFrame({'a': [1, 2, 3]})
    """

    _instance: Optional['LazyLoader'] = None
    _cache: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, module_name: str, *args, **kwargs):
        self.module_name = module_name
        self.args = args
        self.kwargs = kwargs
        self._loaded = False
        self._module = None

    def __getattr__(self, name: str) -> Any:
        """動態加載模組中的屬性"""
        if not self._loaded:
            self._load_module()

        return getattr(self._module, name)

    def __repr__(self) -> str:
        return f"LazyLoader({self.module_name})"

    def __dir__(self):
        """支援dir()函數"""
        if not self._loaded:
            self._load_module()
        return dir(self._module)

    def _load_module(self):
        """加載模組"""
        if self.module_name in LazyLoader._cache:
            self._module = LazyLoader._cache[self.module_name]
            self._loaded = True
        else:
            try:
                self._module = import_module(self.module_name, *self.args, **self.kwargs)
                LazyLoader._cache[self.module_name] = self._module
                self._loaded = True
            except ImportError as e:
                raise ImportError(f"無法加載模組 {self.module_name}: {e}")

    @classmethod
    def preload(cls, module_names: list):
        """預加載模組（可選）"""
        for name in module_names:
            if name not in cls._cache:
                try:
                    module = import_module(name)
                    cls._cache[name] = module
                except ImportError as e:
                    print(f"Warning: 無法預加載 {name}: {e}")

    @classmethod
    def clear_cache(cls):
        """清空緩存"""
        cls._cache.clear()


def lazy_import(module_name: str, *args, **kwargs) -> LazyLoader:
    """
    懶導入函數

    Args:
        module_name: 模組名稱
        *args, **kwargs: 其他導入參數

    Returns:
        懶加載器實例

    Example:
        # 替代:
        # import pandas as pd
        # import numpy as np

        # 使用:
        pd = lazy_import('pandas')
        np = lazy_import('numpy')
    """
    return LazyLoader(module_name, *args, **kwargs)


def lazy_property(func: Callable) -> property:
    """
    懶屬性裝飾器

    Args:
        func: 要轉換的函數

    Returns:
        屬性描述符

    Example:
        class MyClass:
            @lazy_property
            def expensive_property(self):
                # 計算昂貴的屬性
                return result

            # 只在第一次訪問時計算，後續訪問使用緩存
    """
    attr_name = f'_lazy_{func.__name__}'

    @functools.wraps(func)
    def wrapper(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, func(self))
        return getattr(self, attr_name)

    return property(wrapper)


class ResourceLoader:
    """
    資源加載器 - 懶加載文件、配置等資源
    """

    _resource_cache: Dict[str, Any] = {}

    @classmethod
    def load_json(cls, file_path: str, use_cache: bool = True) -> Dict:
        """
        懶加載JSON文件

        Args:
            file_path: JSON文件路徑
            use_cache: 是否使用緩存

        Returns:
            JSON數據
        """
        if use_cache and file_path in cls._resource_cache:
            return cls._resource_cache[file_path]

        import json
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if use_cache:
            cls._resource_cache[file_path] = data

        return data

    @classmethod
    def load_csv(cls, file_path: str, use_cache: bool = True, **kwargs) -> Any:
        """
        懶加載CSV文件

        Args:
            file_path: CSV文件路徑
            use_cache: 是否使用緩存
            **kwargs: pandas.read_csv的參數

        Returns:
            DataFrame
        """
        if use_cache and file_path in cls._resource_cache:
            return cls._resource_cache[file_path]

        import pandas as pd
        data = pd.read_csv(file_path, **kwargs)

        if use_cache:
            cls._resource_cache[file_path] = data

        return data

    @classmethod
    def load_config(cls, config_path: str, config_type: str = 'yaml', use_cache: bool = True) -> Dict:
        """
        懶加載配置文件

        Args:
            config_path: 配置文件路徑
            config_type: 配置文件類型 (yaml, json, toml)
            use_cache: 是否使用緩存

        Returns:
            配置數據
        """
        if use_cache and config_path in cls._resource_cache:
            return cls._resource_cache[config_path]

        import os
        ext = os.path.splitext(config_path)[1].lower()

        if ext in ['.yaml', '.yml']:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        elif ext == '.json':
            import json
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        elif ext == '.toml':
            import tomli
            with open(config_path, 'rb') as f:
                data = tomli.load(f).decode('utf-8')
        else:
            raise ValueError(f"不支持的配置文件類型: {ext}")

        if use_cache:
            cls._resource_cache[config_path] = data

        return data

    @classmethod
    def clear_cache(cls):
        """清空資源緩存"""
        cls._resource_cache.clear()


class ModelLoader:
    """
    模型加載器 - 懶加載機器學習模型
    """

    _model_cache: Dict[str, Any] = {}

    @classmethod
    def load_sklearn_model(cls, model_path: str, use_cache: bool = True) -> Any:
        """
        懶加載scikit-learn模型

        Args:
            model_path: 模型文件路徑
            use_cache: 是否使用緩存

        Returns:
            加載的模型
        """
        if use_cache and model_path in cls._model_cache:
            return cls._model_cache[model_path]

        from sklearn.externals import joblib
        model = joblib.load(model_path)

        if use_cache:
            cls._model_cache[model_path] = model

        return model

    @classmethod
    def load_tensorflow_model(cls, model_path: str, use_cache: bool = True) -> Any:
        """
        懶加載TensorFlow模型

        Args:
            model_path: 模型文件路徑
            use_cache: 是否使用緩存

        Returns:
            加載的模型
        """
        if use_cache and model_path in cls._model_cache:
            return cls._model_cache[model_path]

        import tensorflow as tf
        model = tf.keras.models.load_model(model_path)

        if use_cache:
            cls._model_cache[model_path] = model

        return model

    @classmethod
    def load_pytorch_model(cls, model_path: str, use_cache: bool = True, **kwargs) -> Any:
        """
        懶加載PyTorch模型

        Args:
            model_path: 模型文件路徑
            use_cache: 是否使用緩存
            **kwargs: torch.load的參數

        Returns:
            加載的模型
        """
        if use_cache and model_path in cls._model_cache:
            return cls._model_cache[model_path]

        import torch
        model = torch.load(model_path, **kwargs)

        if use_cache:
            cls._model_cache[model_path] = model

        return model

    @classmethod
    def clear_cache(cls):
        """清空模型緩存"""
        cls._model_cache.clear()


class DatabaseConnector:
    """
    數據庫連接器 - 懶加載數據庫連接
    """

    _connections: Dict[str, Any] = {}

    @classmethod
    def get_connection(cls, connection_string: str, **kwargs) -> Any:
        """
        獲取數據庫連接

        Args:
            connection_string: 連接字符串
            **kwargs: 連接參數

        Returns:
            數據庫連接
        """
        if connection_string in cls._connections:
            return cls._connections[connection_string]

        # 這裡需要根據具體數據庫類型實現
        # 例如: PostgreSQL, MySQL, MongoDB等
        raise NotImplementedError("需要根據具體數據庫類型實現")

    @classmethod
    def close_all(cls):
        """關閉所有連接"""
        for conn in cls._connections.values():
            try:
                conn.close()
            except:
                pass
        cls._connections.clear()


def measure_import_time():
    """
    測量模組導入時間

    Returns:
        導入時間報告
    """
    import time

    modules = [
        'pandas',
        'numpy',
        'matplotlib.pyplot',
        'sklearn',
        'tensorflow',
        'torch'
    ]

    results = {}

    for module in modules:
        start = time.time()
        try:
            __import__(module)
            elapsed = time.time() - start
            results[module] = elapsed
        except ImportError as e:
            results[module] = f"Failed: {e}"

    return results


def main():
    """主函數 - 演示用法"""
    print("=" * 80)
    print("Phase 4: Lazy Loading System Demo")
    print("=" * 80)

    # 演示1: 測量導入時間
    print("\n[1] 模組導入時間測試")
    import_time = measure_import_time()
    for module, time_taken in import_time.items():
        if isinstance(time_taken, float):
            print(f"  {module:20s}: {time_taken*1000:6.1f} ms")
        else:
            print(f"  {module:20s}: {time_taken}")

    # 演示2: 懶加載模組
    print("\n[2] 懶加載模組")
    print("  創建懶加載器...")
    pd = lazy_import('pandas')
    np = lazy_import('numpy')
    print(f"  pd: {pd}")
    print(f"  np: {np}")

    print("\n  首次使用（加載模組）...")
    import time
    start = time.time()
    # 模擬使用
    array = np.array([1, 2, 3])
    df = pd.DataFrame({'a': [1, 2, 3]})
    load_time = time.time() - start
    print(f"  加載時間: {load_time*1000:.1f} ms")

    # 演示3: 資源加載
    print("\n[3] 資源緩存")
    test_data = {'key1': 'value1', 'key2': 'value2'}
    import json
    with open('/tmp/test_config.json', 'w') as f:
        json.dump(test_data, f)

    # 首次加載
    start = time.time()
    config1 = ResourceLoader.load_json('/tmp/test_config.json')
    time1 = time.time() - start

    # 緩存讀取
    start = time.time()
    config2 = ResourceLoader.load_json('/tmp/test_config.json')
    time2 = time.time() - start

    print(f"  首次加載: {time1*1000:.1f} ms")
    print(f"  緩存讀取: {time2*1000:.1f} ms")
    print(f"  提升: {time1/time2:.1f}x")

    print("\n" + "=" * 80)
    print("Lazy loading system ready!")
    print("=" * 80)
    print("\n使用指南:")
    print("1. 將昂貴的導入改為懶加載:")
    print("   pd = lazy_import('pandas')")
    print("2. 使用懶屬性:")
    print("   @lazy_property")
    print("   def expensive_calculation(self):")
    print("       return result")
    print("3. 緩存資源:")
    print("   data = ResourceLoader.load_json('config.json')")


if __name__ == '__main__':
    main()
