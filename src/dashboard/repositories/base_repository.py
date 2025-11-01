"""
Repository基類 - 統一的數據訪問接口
實現CRUD操作、分頁、排序、過濾等常見功能
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional, Dict, Any, Union, Callable
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """
    Repository基類

    提供統一的數據訪問接口，支持：
    - 基本CRUD操作
    - 分頁查詢
    - 排序
    - 過濾
    - 聚合操作
    - 事務支持
    """

    def __init__(self, cache_manager=None):
        """初始化Repository

        Args:
            cache_manager: 緩存管理器實例
        """
        self.cache_manager = cache_manager
        self.table_name = self.__class__.__name__.replace('Repository', '').lower()
        self.default_cache_ttl = 300  # 5分鐘默認緩存時間

    # ==================== 抽象方法 ====================

    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[T]:
        """根據ID獲取單條記錄

        Args:
            id: 記錄ID

        Returns:
            記錄對象，如果不存在返回None
        """
        pass

    @abstractmethod
    async def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0
    ) -> List[T]:
        """獲取記錄列表

        Args:
            filters: 過濾條件
            sort_by: 排序字段
            sort_order: 排序方向 (asc/desc)
            limit: 限制數量
            offset: 偏移量

        Returns:
            記錄列表
        """
        pass

    @abstractmethod
    async def create(self, data: Dict[str, Any]) -> T:
        """創建新記錄

        Args:
            data: 記錄數據

        Returns:
            創建的記錄對象
        """
        pass

    @abstractmethod
    async def update(self, id: str, data: Dict[str, Any]) -> T:
        """更新記錄

        Args:
            id: 記錄ID
            data: 更新數據

        Returns:
            更新後的記錄對象
        """
        pass

    @abstractmethod
    async def delete(self, id: str) -> bool:
        """刪除記錄

        Args:
            id: 記錄ID

        Returns:
            是否刪除成功
        """
        pass

    # ==================== 默認實現方法 ====================

    async def get_many(self, ids: List[str]) -> List[T]:
        """批量獲取記錄

        Args:
            ids: ID列表

        Returns:
            記錄列表
        """
        results = []
        for id in ids:
            result = await self.get_by_id(id)
            if result:
                results.append(result)
        return results

    async def create_many(self, data_list: List[Dict[str, Any]]) -> List[T]:
        """批量創建記錄

        Args:
            data_list: 記錄數據列表

        Returns:
            創建的記錄列表
        """
        results = []
        for data in data_list:
            result = await self.create(data)
            results.append(result)
        return results

    async def update_many(
        self,
        ids: List[str],
        data: Dict[str, Any]
    ) -> List[T]:
        """批量更新記錄

        Args:
            ids: ID列表
            data: 更新數據

        Returns:
            更新後的記錄列表
        """
        results = []
        for id in ids:
            result = await self.update(id, data)
            results.append(result)
        return results

    async def delete_many(self, ids: List[str]) -> int:
        """批量刪除記錄

        Args:
            ids: ID列表

        Returns:
            刪除的記錄數量
        """
        count = 0
        for id in ids:
            if await self.delete(id):
                count += 1
        return count

    async def count(
        self,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """統計記錄數量

        Args:
            filters: 過濾條件

        Returns:
            記錄數量
        """
        # 默認實現：獲取所有記錄並計數
        # 子類可以優化為直接COUNT查詢
        results = await self.list(filters=filters, limit=100000)
        return len(results)

    async def exists(self, id: str) -> bool:
        """檢查記錄是否存在

        Args:
            id: 記錄ID

        Returns:
            是否存在
        """
        result = await self.get_by_id(id)
        return result is not None

    async def paginate(
        self,
        page: int = 1,
        size: int = 50,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """
        分頁查詢

        Args:
            page: 頁碼（從1開始）
            size: 每頁數量
            filters: 過濾條件
            sort_by: 排序字段
            sort_order: 排序方向

        Returns:
            分頁結果字典
        """
        # 計算偏移量
        offset = (page - 1) * size

        # 獲取總數
        total = await self.count(filters=filters)

        # 獲取分頁數據
        items = await self.list(
            filters=filters,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=size,
            offset=offset
        )

        # 計算頁數
        pages = (total + size - 1) // size

        return {
            "items": items,
            "total": total,
            "page": page,
            "size": size,
            "pages": pages,
            "has_next": page < pages,
            "has_prev": page > 1,
            "next_page": page + 1 if page < pages else None,
            "prev_page": page - 1 if page > 1 else None
        }

    def build_cache_key(
        self,
        operation: str,
        **kwargs
    ) -> str:
        """
        構建緩存鍵

        Args:
            operation: 操作名稱
            **kwargs: 參數

        Returns:
            緩存鍵字符串
        """
        if self.cache_manager:
            return self.cache_manager.generate_cache_key(
                f"{self.table_name}:{operation}",
                **kwargs
            )
        return None

    async def get_cached(
        self,
        cache_key: str,
        fetch_func: Callable,
        ttl: Optional[int] = None
    ) -> Any:
        """
        獲取緩存或執行查詢

        Args:
            cache_key: 緩存鍵
            fetch_func: 查詢函數
            ttl: 緩存時間

        Returns:
            查詢結果
        """
        if not self.cache_manager:
            return await fetch_func()

        ttl = ttl or self.default_cache_ttl
        return await self.cache_manager.get_or_set(cache_key, fetch_func, ttl)

    async def invalidate_cache(
        self,
        operation: str,
        **kwargs
    ) -> int:
        """
        失效緩存

        Args:
            operation: 操作名稱
            **kwargs: 參數

        Returns:
            失效的鍵數量
        """
        if not self.cache_manager:
            return 0

        cache_key = self.build_cache_key(operation, **kwargs)
        if cache_key:
            pattern = f"{cache_key}*"
            return await self.cache_manager.clear_pattern(pattern)
        return 0

    async def invalidate_all(self) -> int:
        """
        失效所有相關緩存

        Returns:
            失效的鍵數量
        """
        if not self.cache_manager:
            return 0

        pattern = f"{self.table_name}:*"
        return await self.cache_manager.clear_pattern(pattern)

    def validate_sort_params(
        self,
        sort_by: Optional[str],
        sort_order: str
    ) -> tuple:
        """
        驗證排序參數

        Args:
            sort_by: 排序字段
            sort_order: 排序方向

        Returns:
            驗證後的排序參數
        """
        allowed_orders = ["asc", "desc"]
        if sort_order not in allowed_orders:
            logger.warning(f"無效的排序方向: {sort_order}，使用默認: desc")
            sort_order = "desc"

        return sort_by, sort_order.lower()

    def validate_pagination_params(
        self,
        page: int,
        size: int,
        max_size: int = 100
    ) -> tuple:
        """
        驗證分頁參數

        Args:
            page: 頁碼
            size: 每頁數量
            max_size: 最大每頁數量

        Returns:
            驗證後的分頁參數
        """
        if page < 1:
            logger.warning(f"無效的頁碼: {page}，使用默認: 1")
            page = 1

        if size < 1:
            logger.warning(f"無效的每頁數量: {size}，使用默認: 50")
            size = 50

        if size > max_size:
            logger.warning(f"每頁數量過大: {size}，限制為: {max_size}")
            size = max_size

        return page, size


class InMemoryRepository(BaseRepository[T]):
    """
    基於內存的Repository實現
    用於測試和演示
    """

    def __init__(self, cache_manager=None):
        super().__init__(cache_manager)
        self._data: Dict[str, T] = {}
        self._sequence = 1

    async def get_by_id(self, id: str) -> Optional[T]:
        return self._data.get(id)

    async def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0
    ) -> List[T]:
        results = list(self._data.values())

        # 應用過濾器
        if filters:
            for key, value in filters.items():
                results = [item for item in results if getattr(item, key, None) == value]

        # 應用排序
        if sort_by:
            results.sort(
                key=lambda x: getattr(x, sort_by, None),
                reverse=(sort_order.lower() == "desc")
            )

        # 應用分頁
        return results[offset:offset + limit]

    async def create(self, data: Dict[str, Any]) -> T:
        # 簡單實現：假設數據是字典
        id = str(self._sequence)
        self._sequence += 1
        item = {**data, "id": id, "created_at": datetime.utcnow()}
        self._data[id] = item
        return item

    async def update(self, id: str, data: Dict[str, Any]) -> T:
        if id not in self._data:
            raise ValueError(f"記錄不存在: {id}")

        updated = {**self._data[id], **data, "updated_at": datetime.utcnow()}
        self._data[id] = updated
        return updated

    async def delete(self, id: str) -> bool:
        if id in self._data:
            del self._data[id]
            return True
        return False
