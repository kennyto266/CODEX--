"""
統一基礎適配器
整合 BaseDataAdapter 和 AlternativeDataAdapter
提供統一的錯誤處理、快取和數據驗證機制
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union
import logging
import hashlib
import json
from datetime import datetime
import pandas as pd
import asyncio
from functools import wraps

logger = logging.getLogger(__name__)

class CacheManager:
    """統一快取管理器"""
    _cache = {}

    @classmethod
    def get(cls, key: str) -> Optional[Any]:
        """獲取快取數據"""
        if key in cls._cache:
            return cls._cache[key]
        return None

    @classmethod
    def set(cls, key: str, value: Any, ttl: int = 3600) -> None:
        """設置快取數據"""
        cls._cache[key] = {
            'data': value,
            'timestamp': datetime.now(),
            'ttl': ttl
        }

    @classmethod
    def is_valid(cls, key: str) -> bool:
        """檢查快取是否有效"""
        if key not in cls._cache:
            return False
        cache_entry = cls._cache[key]
        age = (datetime.now() - cache_entry['timestamp']).total_seconds()
        return age < cache_entry['ttl']

class ErrorHandler:
    """統一錯誤處理器"""

    @staticmethod
    def handle_error(error: Exception, context: str = "") -> Dict[str, Any]:
        """處理錯誤並返回標準化響應"""
        error_info = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context,
            'timestamp': datetime.now().isoformat()
        }

        logger.error(f"[{context}] {error_info['error_type']}: {error_info['error_message']}")
        return error_info

    @staticmethod
    def retry(max_retries: int = 3, delay: float = 1.0):
        """重試裝飾器"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                for attempt in range(max_retries):
                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        if attempt == max_retries - 1:
                            raise
                        await asyncio.sleep(delay * (2 ** attempt))
                return None
            return wrapper
        return decorator

class UnifiedBaseAdapter(ABC):
    """
    統一基礎適配器
    整合所有適配器的共同功能
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.cache = CacheManager()
        self.error_handler = ErrorHandler()

    def _generate_cache_key(self, data: Dict) -> str:
        """生成快取鍵"""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.md5(data_str.encode()).hexdigest()

    def _validate_data(self, data: Any, expected_type: type = pd.DataFrame) -> bool:
        """驗證數據"""
        if data is None:
            return False
        if expected_type == pd.DataFrame:
            return isinstance(data, pd.DataFrame) and not data.empty
        return isinstance(data, expected_type)

    @abstractmethod
    async def fetch_data(self, params: Dict[str, Any]) -> Any:
        """獲取數據（抽象方法）"""
        pass

    async def get_cached_data(self, params: Dict[str, Any]) -> Optional[Any]:
        """獲取快取數據"""
        cache_key = self._generate_cache_key(params)
        if self.cache.is_valid(cache_key):
            return self.cache.get(cache_key)['data']
        return None

    async def set_cached_data(self, params: Dict[str, Any], data: Any, ttl: int = 3600) -> None:
        """設置快取數據"""
        cache_key = self._generate_cache_key(params)
        self.cache.set(cache_key, data, ttl)

    async def safe_fetch(self, params: Dict[str, Any], use_cache: bool = True) -> Dict[str, Any]:
        """安全獲取數據（包含錯誤處理和快取）"""
        context = f"{self.__class__.__name__}.fetch_data"

        try:
            # 嘗試從快取獲取
            if use_cache:
                cached_data = await self.get_cached_data(params)
                if cached_data is not None:
                    return {
                        'success': True,
                        'data': cached_data,
                        'source': 'cache',
                        'timestamp': datetime.now().isoformat()
                    }

            # 獲取新數據
            data = await self.fetch_data(params)

            # 驗證數據
            if not self._validate_data(data):
                raise ValueError("Invalid data received")

            # 設置快取
            if use_cache:
                await self.set_cached_data(params, data)

            return {
                'success': True,
                'data': data,
                'source': 'api',
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            error_info = self.error_handler.handle_error(e, context)
            return {
                'success': False,
                'error': error_info,
                'data': None
            }

    def get_data_source_info(self) -> Dict[str, Any]:
        """獲取數據源信息"""
        return {
            'adapter_name': self.__class__.__name__,
            'config': self.config,
            'cache_enabled': True,
            'timestamp': datetime.now().isoformat()
        }
