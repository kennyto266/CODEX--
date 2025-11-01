"""
ORM查詢優化器

提供：
- N+1查詢檢測
- 預取（prefetch）建議
- 查詢優化策略
- 批量操作
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Set, Tuple, Type, Union

from src.core.logging import get_logger

logger = get_logger("orm_optimizer")


class ORMSelectOptimizer:
    """ORM查詢選擇優化器"""

    def __init__(self):
        self.logger = get_logger("orm_optimizer")
        self._query_cache: Dict[str, Any] = {}
        self._prefetch_cache: Dict[str, List[str]] = {}
        self._batch_cache: Dict[str, List[Any]] = {}

    async def optimize_select_query(
        self,
        model_class: Type,
        query_filters: Optional[Dict] = None,
        select_related: Optional[List[str]] = None,
        prefetch_related: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        優化SELECT查詢

        Args:
            model_class: 模型類
            query_filters: 查詢過濾器
            select_related: 關聯查詢
            prefetch_related: 預取查詢

        Returns:
            優化建議
        """
        optimization = {
            "model": model_class.__name__,
            "filters": query_filters,
            "original_strategy": "sequential",
            "optimized_strategy": "batch",
            "estimated_queries": {
                "original": 1 + len(select_related or []),
                "optimized": 1  # 使用JOIN或子查詢
            },
            "suggestions": []
        }

        # 檢查N+1問題
        if select_related:
            optimization["original_strategy"] = "select_related"
            optimization["optimized_strategy"] = "prefetch_related"
            optimization["estimated_queries"]["original"] = 1 + len(select_related)
            optimization["estimated_queries"]["optimized"] = 1 + len(select_related)

            optimization["suggestions"].append(
                "Consider using prefetch_related for many-to-many relationships"
            )

        # 檢查批量查詢建議
        if not query_filters:
            optimization["suggestions"].append(
                "Consider adding filters to limit result set"
            )

        return optimization

    async def detect_n_plus_one(self, queries: List[Dict]) -> Dict[str, Any]:
        """
        檢測N+1查詢問題

        Args:
            queries: 查詢列表

        Returns:
            檢測結果
        """
        detection = {
            "n_plus_one_detected": False,
            "patterns": [],
            "suggestions": []
        }

        # 簡化實現：查找重複的表查詢
        table_queries: Dict[str, List[Dict]] = {}

        for query_info in queries:
            table = query_info.get("table", "unknown")
            if table not in table_queries:
                table_queries[table] = []
            table_queries[table].append(query_info)

        # 檢測重複查詢
        for table, queries in table_queries.items():
            if len(queries) > 1:
                detection["n_plus_one_detected"] = True
                detection["patterns"].append({
                    "table": table,
                    "query_count": len(queries),
                    "queries": [q.get("query", "")[:100] for q in queries]
                })

        if detection["n_plus_one_detected"]:
            detection["suggestions"].append(
                "Use select_related() or prefetch_related() to reduce queries"
            )
            detection["suggestions"].append(
                "Consider batching queries with a single query and processing in memory"
            )

        return detection

    async def suggest_prefetch(
        self,
        model_class: Type,
        related_fields: List[str]
    ) -> List[Dict[str, str]]:
        """建議預取策略"""
        suggestions = []

        for field in related_fields:
            suggestions.append({
                "field": field,
                "strategy": "prefetch_related",
                "query_type": "separate_query",
                "reason": "Reduces N+1 queries for related objects"
            })

        return suggestions

    def get_cache_key(self, model_class: Type, filters: Dict, fields: Optional[List[str]] = None) -> str:
        """生成查詢緩存鍵"""
        key_parts = [model_class.__name__]

        if filters:
            key_parts.append(str(sorted(filters.items())))

        if fields:
            key_parts.append(str(sorted(fields)))

        return ":".join(key_parts)

    async def get_cached_result(
        self,
        model_class: Type,
        filters: Dict,
        fields: Optional[List[str]] = None
    ) -> Optional[Any]:
        """從緩存獲取結果"""
        cache_key = self.get_cache_key(model_class, filters, fields)
        return self._query_cache.get(cache_key)

    async def cache_result(
        self,
        model_class: Type,
        filters: Dict,
        result: Any,
        fields: Optional[List[str]] = None,
        ttl: int = 300
    ) -> None:
        """緩存查詢結果"""
        cache_key = self.get_cache_key(model_class, filters, fields)
        # 注意：實際應用中需要實現TTL
        self._query_cache[cache_key] = {
            "result": result,
            "timestamp": time.time(),
            "ttl": ttl
        }

    async def batch_queries(self, queries: List[Tuple]) -> List[Any]:
        """批量執行查詢"""
        self.logger.info(f"Batch executing {len(queries)} queries")

        # 簡化實現：實際應用中需要連接數據庫
        results = []
        for query_info in queries:
            # 執行查詢
            result = await self._execute_query(query_info)
            results.append(result)

        return results

    async def _execute_query(self, query_info: Tuple) -> Any:
        """執行單個查詢"""
        # 簡化實現
        return {"result": "mock_result"}


class ORMBatchOptimizer:
    """ORM批量操作優化器"""

    def __init__(self):
        self.logger = get_logger("orm_batch_optimizer")
        self._batch_size = 100

    async def optimize_batch_insert(
        self,
        model_class: Type,
        objects: List[Any]
    ) -> Dict[str, Any]:
        """優化批量插入"""
        optimization = {
            "operation": "batch_insert",
            "object_count": len(objects),
            "original_queries": len(objects),  # 每個對象一個INSERT
            "optimized_queries": (len(objects) + self._batch_size - 1) // self._batch_size,
            "suggestions": [
                f"Use bulk_create() with batch_size={self._batch_size}",
                "Consider transaction wrapping for atomicity"
            ]
        }

        return optimization

    async def optimize_batch_update(
        self,
        model_class: Type,
        objects: List[Any]
    ) -> Dict[str, Any]:
        """優化批量更新"""
        optimization = {
            "operation": "batch_update",
            "object_count": len(objects),
            "original_queries": len(objects),  # 每個對象一個UPDATE
            "optimized_queries": 1,  # 使用WHERE IN
            "suggestions": [
                "Use filter().update() with specific values",
                "Consider using bulk_update() if available"
            ]
        }

        return optimization

    async def optimize_batch_delete(
        self,
        model_class: Type,
        filters: Dict
    ) -> Dict[str, Any]:
        """優化批量刪除"""
        optimization = {
            "operation": "batch_delete",
            "filters": filters,
            "original_queries": 1,  # 通常已經是批量的
            "optimized_queries": 1,
            "suggestions": [
                "Use filter().delete() for batch deletion",
                "Ensure proper WHERE clause to limit scope"
            ]
        }

        return optimization


class ORMQueryAnalyzer:
    """ORM查詢分析器"""

    def __init__(self):
        self.logger = get_logger("orm_query_analyzer")
        self._query_history: List[Dict] = []

    def record_query(self, query_info: Dict):
        """記錄查詢"""
        query_info["timestamp"] = time.time()
        self._query_history.append(query_info)

        # 保持最近1000個查詢
        if len(self._query_history) > 1000:
            self._query_history.pop(0)

    def analyze_query_patterns(self) -> Dict[str, Any]:
        """分析查詢模式"""
        if not self._query_history:
            return {}

        # 統計表使用頻率
        table_frequency: Dict[str, int] = {}
        for query_info in self._query_history:
            table = query_info.get("table", "unknown")
            table_frequency[table] = table_frequency.get(table, 0) + 1

        # 查找重複查詢
        duplicate_queries: Dict[str, int] = {}
        for query_info in self._query_history:
            query = query_info.get("query", "")
            duplicate_queries[query] = duplicate_queries.get(query, 0) + 1

        frequent_queries = {
            query: count
            for query, count in duplicate_queries.items()
            if count > 1
        }

        return {
            "total_queries": len(self._query_history),
            "table_frequency": table_frequency,
            "frequent_queries": frequent_queries,
            "cache_opportunities": len(frequent_queries),
            "recommendations": [
                "Enable query caching for repeated queries",
                "Consider database-level query caching",
                "Use connection pooling for repeated queries"
            ]
        }


# 全局ORM優化器實例
_global_select_optimizer: Optional[ORMSelectOptimizer] = None
_global_batch_optimizer: Optional[ORMBatchOptimizer] = None
_global_query_analyzer: Optional[ORMQueryAnalyzer] = None


def get_select_optimizer() -> ORMSelectOptimizer:
    """獲取選擇優化器"""
    global _global_select_optimizer
    if _global_select_optimizer is None:
        _global_select_optimizer = ORMSelectOptimizer()
    return _global_select_optimizer


def get_batch_optimizer() -> ORMBatchOptimizer:
    """獲取批量優化器"""
    global _global_batch_optimizer
    if _global_batch_optimizer is None:
        _global_batch_optimizer = ORMBatchOptimizer()
    return _global_batch_optimizer


def get_query_analyzer() -> ORMQueryAnalyzer:
    """獲取查詢分析器"""
    global _global_query_analyzer
    if _global_query_analyzer is None:
        _global_query_analyzer = ORMQueryAnalyzer()
    return _global_query_analyzer


# 便捷函數
async def optimize_select_query(
    model_class: Type,
    filters: Optional[Dict] = None,
    select_related: Optional[List[str]] = None,
    prefetch_related: Optional[List[str]] = None
) -> Dict[str, Any]:
    """優化選擇查詢"""
    return await get_select_optimizer().optimize_select_query(
        model_class, filters, select_related, prefetch_related
    )


async def detect_n_plus_one(queries: List[Dict]) -> Dict[str, Any]:
    """檢測N+1查詢"""
    return await get_select_optimizer().detect_n_plus_one(queries)


async def optimize_batch_insert(model_class: Type, objects: List[Any]) -> Dict[str, Any]:
    """優化批量插入"""
    return await get_batch_optimizer().optimize_batch_insert(model_class, objects)


def record_orm_query(query_info: Dict):
    """記錄ORM查詢"""
    get_query_analyzer().record_query(query_info)


def analyze_orm_queries() -> Dict[str, Any]:
    """分析ORM查詢"""
    return get_query_analyzer().analyze_query_patterns()
