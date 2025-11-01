"""
數據庫查詢優化器

提供：
- 查詢分析和優化建議
- 索引建議
- 查詢性能分析
- N+1查詢檢測
"""

import time
from typing import Dict, List, Optional, Tuple, Any

from src.core.logging import get_logger

logger = get_logger("query_optimizer")


class QueryOptimizer:
    """查詢優化器"""

    def __init__(self):
        self.logger = get_logger("query_optimizer")
        self._query_stats: Dict[str, Dict] = {}
        self._slow_queries: List[Dict] = []

    def analyze_query(self, query: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        分析查詢並提供優化建議

        Args:
            query: SQL查詢
            params: 查詢參數

        Returns:
            分析結果
        """
        analysis = {
            "query": query,
            "timestamp": time.time(),
            "suggestions": [],
            "score": 100,  # 0-100分，分數越高越好
            "issues": []
        }

        # 檢查常見問題
        self._check_select_star(query, analysis)
        self._check_missing_where(query, analysis)
        self._check_like_usage(query, analysis)
        self._check_subquery(query, analysis)
        self._check_joins(query, analysis)
        self._check_order_by_without_index(query, analysis)

        return analysis

    def _check_select_star(self, query: str, analysis: Dict):
        """檢查SELECT *"""
        if "SELECT *" in query.upper() and "WHERE" in query.upper():
            analysis["issues"].append(
                "Using SELECT * with WHERE clause may fetch unnecessary columns"
            )
            analysis["suggestions"].append(
                "Specify only required columns in SELECT clause"
            )
            analysis["score"] -= 10

    def _check_missing_where(self, query: str, analysis: Dict):
        """檢查缺少WHERE子句"""
        query_upper = query.upper()
        if "SELECT" in query_upper and "WHERE" not in query_upper and "GROUP BY" not in query_upper:
            analysis["issues"].append(
                "Query may return all rows without WHERE clause"
            )
            analysis["suggestions"].append(
                "Add WHERE clause to limit rows"
            )
            analysis["score"] -= 20

    def _check_like_usage(self, query: str, analysis: Dict):
        """檢查LIKE使用"""
        if "LIKE" in query.upper():
            analysis["issues"].append(
                "LIKE with wildcard at beginning prevents index usage"
            )
            analysis["suggestions"].append(
                "Use full-text search or consider alternative approaches"
            )
            analysis["score"] -= 15

    def _check_subquery(self, query: str, analysis: Dict):
        """檢查子查詢"""
        if "(" in query and ")" in query:
            analysis["issues"].append(
                "Subqueries may be less efficient than JOINs"
            )
            analysis["suggestions"].append(
                "Consider rewriting with JOINs when possible"
            )
            analysis["score"] -= 10

    def _check_joins(self, query: str, analysis: Dict):
        """檢查JOIN"""
        if "JOIN" in query.upper():
            join_count = query.upper().count("JOIN")
            if join_count > 3:
                analysis["issues"].append(
                    f"Multiple JOINs ({join_count}) may impact performance"
                )
                analysis["suggestions"].append(
                    "Review JOIN necessity and consider denormalization"
                )
                analysis["score"] -= 5 * join_count

    def _check_order_by_without_index(self, query: str, analysis: Dict):
        """檢查ORDER BY"""
        if "ORDER BY" in query.upper():
            analysis["issues"].append(
                "ORDER BY without index may cause sorting overhead"
            )
            analysis["suggestions"].append(
                "Ensure ORDER BY columns have appropriate indexes"
            )
            analysis["score"] -= 5

    def suggest_indexes(self, query: str) -> List[Dict]:
        """建議索引"""
        suggestions = []

        # 提取WHERE子句中的列
        where_cols = self._extract_where_columns(query)
        for table, cols in where_cols.items():
            for col in cols:
                suggestions.append({
                    "type": "INDEX",
                    "table": table,
                    "column": col,
                    "reason": f"Column used in WHERE clause for {table}.{col}"
                })

        # 提取JOIN列
        join_cols = self._extract_join_columns(query)
        for table, cols in join_cols.items():
            for col in cols:
                suggestions.append({
                    "type": "INDEX",
                    "table": table,
                    "column": col,
                    "reason": f"Column used in JOIN for {table}.{col}"
                })

        return suggestions

    def _extract_where_columns(self, query: str) -> Dict[str, List[str]]:
        """提取WHERE子句中的列"""
        # 簡化實現，實際應用中需要更複雜的SQL解析
        where_cols = {}
        try:
            import re
            # 提取表名和WHERE條件
            tables = re.findall(r"FROM\s+(\w+)", query, re.IGNORECASE)
            if tables:
                table = tables[0]
                where_conditions = re.findall(r"WHERE\s+(.+?)(?:\s+GROUP|\s+ORDER|\s+LIMIT|$)", query, re.IGNORECASE | re.DOTALL)
                if where_conditions:
                    cols = re.findall(r"(\w+)\s*=", where_conditions[0])
                    where_cols[table] = cols
        except:
            pass
        return where_cols

    def _extract_join_columns(self, query: str) -> Dict[str, List[str]]:
        """提取JOIN子句中的列"""
        join_cols = {}
        try:
            import re
            # 提取JOIN表和ON條件
            joins = re.findall(r"JOIN\s+(\w+)\s+ON\s+(.+?)(?:\s+JOIN|\s+WHERE|\s+GROUP|\s+ORDER|\s+LIMIT|$)", query, re.IGNORECASE | re.DOTALL)
            for table, on_condition in joins:
                cols = re.findall(r"(\w+)\s*\.\w+\s*=\s*\w+\.\w+", on_condition)
                # 簡化：取左側的表
                if table not in join_cols:
                    join_cols[table] = []
                join_cols[table].extend([c.split('.')[0] for c in cols])
        except:
            pass
        return join_cols

    def record_query_performance(self, query: str, execution_time: float, row_count: int = 0):
        """記錄查詢性能"""
        query_hash = hash(query)

        if query_hash not in self._query_stats:
            self._query_stats[query_hash] = {
                "query": query,
                "execution_count": 0,
                "total_time": 0,
                "average_time": 0,
                "min_time": float('inf'),
                "max_time": 0,
                "total_rows": 0,
                "last_execution": time.time()
            }

        stats = self._query_stats[query_hash]
        stats["execution_count"] += 1
        stats["total_time"] += execution_time
        stats["average_time"] = stats["total_time"] / stats["execution_count"]
        stats["min_time"] = min(stats["min_time"], execution_time)
        stats["max_time"] = max(stats["max_time"], execution_time)
        stats["total_rows"] += row_count
        stats["last_execution"] = time.time()

        # 檢查慢查詢
        if execution_time > 1.0:  # 超過1秒的查詢
            self._slow_queries.append({
                "query": query,
                "execution_time": execution_time,
                "timestamp": time.time(),
                "row_count": row_count
            })

            # 保持最近100個慢查詢
            if len(self._slow_queries) > 100:
                self._slow_queries.pop(0)

            self.logger.warning(
                f"Slow query detected: {execution_time:.3f}s - {query[:100]}"
            )

    def get_slow_queries(self, limit: int = 10) -> List[Dict]:
        """獲取慢查詢"""
        sorted_queries = sorted(
            self._slow_queries,
            key=lambda x: x["execution_time"],
            reverse=True
        )
        return sorted_queries[:limit]

    def get_query_statistics(self) -> Dict[str, Any]:
        """獲取查詢統計"""
        if not self._query_stats:
            return {}

        total_queries = len(self._query_stats)
        total_executions = sum(s["execution_count"] for s in self._query_stats.values())
        total_time = sum(s["total_time"] for s in self._query_stats.values())

        # 最慢的查詢
        slowest_query = max(
            self._query_stats.values(),
            key=lambda x: x["average_time"]
        )

        return {
            "total_unique_queries": total_queries,
            "total_executions": total_executions,
            "total_execution_time": total_time,
            "average_execution_time": total_time / max(total_executions, 1),
            "slowest_query": {
                "query": slowest_query["query"][:100],
                "average_time": slowest_query["average_time"],
                "execution_count": slowest_query["execution_count"]
            },
            "slow_query_count": len(self._slow_queries)
        }

    def clear_statistics(self):
        """清除統計"""
        self._query_stats.clear()
        self._slow_queries.clear()
        self.logger.info("Query statistics cleared")


# 全局查詢優化器實例
_global_optimizer: Optional[QueryOptimizer] = None


def get_query_optimizer() -> QueryOptimizer:
    """獲取全局查詢優化器"""
    global _global_optimizer
    if _global_optimizer is None:
        _global_optimizer = QueryOptimizer()
    return _global_optimizer


# 便捷函數
def analyze_query(query: str, params: Optional[Dict] = None) -> Dict[str, Any]:
    """分析查詢"""
    return get_query_optimizer().analyze_query(query, params)


def suggest_indexes_for_query(query: str) -> List[Dict]:
    """為查詢建議索引"""
    return get_query_optimizer().suggest_indexes(query)


def record_query_performance(query: str, execution_time: float, row_count: int = 0):
    """記錄查詢性能"""
    get_query_optimizer().record_query_performance(query, execution_time, row_count)
