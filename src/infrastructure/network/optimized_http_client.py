"""
优化的HTTP客户端

提供：
- 连接池管理
- 重试机制
- 请求缓存
- 超时控制
- 并发限制
"""

import asyncio
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime, timedelta

import aiohttp
from aiohttp import ClientTimeout, ClientError

from src.core.logging import get_logger

logger = get_logger("optimized_http_client")


@dataclass
class RequestConfig:
    """请求配置"""
    timeout: float = 10.0  # 请求超时（秒）
    max_retries: int = 3  # 最大重试次数
    retry_delay: float = 1.0  # 重试延迟（秒）
    retry_backoff: float = 2.0  # 重试退避因子
    enable_cache: bool = True  # 是否启用缓存
    cache_ttl: int = 300  # 缓存TTL（秒）
    max_concurrent: int = 100  # 最大并发数


class OptimizedHTTPClient:
    """优化的HTTP客户端"""

    def __init__(self, config: Optional[RequestConfig] = None):
        self.config = config or RequestConfig()

        # 连接池配置（延迟初始化）
        self._connector: Optional[aiohttp.TCPConnector] = None

        # 超时配置
        self._timeout = ClientTimeout(
            total=self.config.timeout,
            connect=5.0,
            sock_read=10.0
        )

        # 缓存管理器（简单内存缓存实现）
        self._cache = {} if self.config.enable_cache else None
        self._cache_lock = asyncio.Lock() if self.config.enable_cache else None

        # 统计信息
        self._stats = {
            'requests': 0,
            'successes': 0,
            'failures': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'retries': 0
        }

        # 限流器（延迟初始化）
        self._semaphore: Optional[asyncio.Semaphore] = None

    async def _ensure_resources(self):
        """确保资源已初始化"""
        if self._connector is None:
            self._connector = aiohttp.TCPConnector(
                limit=self.config.max_concurrent,
                limit_per_host=30,
                ttl_dns_cache=300,
                use_dns_cache=True,
                keepalive_timeout=60,
                enable_cleanup_closed=True
            )

        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self.config.max_concurrent)

    async def get(self, url: str, params: Optional[Dict[str, Any]] = None,
                  headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        GET请求（带缓存和重试）

        Args:
            url: 请求URL
            params: 查询参数
            headers: 请求头

        Returns:
            响应数据
        """
        # 确保资源已初始化
        await self._ensure_resources()

        cache_key = f"http_get:{url}:{hash(str(params))}" if params else f"http_get:{url}"

        # 检查缓存
        if self._cache and self.config.enable_cache:
            async with self._cache_lock:
                cached = self._cache.get(cache_key)
                if cached and cached.get('expires_at', 0) > time.time():
                    self._stats['cache_hits'] += 1
                    return cached['data']

            self._stats['cache_misses'] += 1

        # 执行请求
        result = await self._request_with_retry('GET', url, params=params, headers=headers)

        # 缓存结果
        if self._cache and self.config.enable_cache and result:
            async with self._cache_lock:
                self._cache[cache_key] = {
                    'data': result,
                    'expires_at': time.time() + self.config.cache_ttl
                }

        return result

    async def post(self, url: str, data: Optional[Dict[str, Any]] = None,
                   json: Optional[Dict[str, Any]] = None,
                   headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        POST请求（带重试）

        Args:
            url: 请求URL
            data: 表单数据
            json: JSON数据
            headers: 请求头

        Returns:
            响应数据
        """
        # 确保资源已初始化
        await self._ensure_resources()

        return await self._request_with_retry('POST', url, data=data, json=json, headers=headers)

    async def batch_get(self, urls: List[str],
                       params_list: Optional[List[Dict[str, Any]]] = None,
                       headers_list: Optional[List[Dict[str, str]]] = None,
                       max_concurrent: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        批量GET请求（并发执行）

        Args:
            urls: URL列表
            params_list: 参数列表
            headers_list: 请求头列表
            max_concurrent: 最大并发数

        Returns:
            响应数据列表
        """
        max_concurrent = max_concurrent or min(20, len(urls))

        semaphore = asyncio.Semaphore(max_concurrent)

        async def bounded_get(url, params, headers):
            async with semaphore:
                return await self.get(url, params, headers)

        # 创建任务
        tasks = []
        for i, url in enumerate(urls):
            params = params_list[i] if params_list and i < len(params_list) else None
            headers = headers_list[i] if headers_list and i < len(headers_list) else None
            tasks.append(bounded_get(url, params, headers))

        # 并发执行
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常
        return [
            result if not isinstance(result, Exception) else {'error': str(result)}
            for result in results
        ]

    async def _request_with_retry(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """带重试的请求"""
        last_exception = None

        for attempt in range(self.config.max_retries + 1):
            try:
                async with self._semaphore:
                    result = await self._do_request(method, url, **kwargs)

                    self._stats['requests'] += 1
                    self._stats['successes'] += 1

                    return result

            except (ClientError, asyncio.TimeoutError, aiohttp.ClientConnectorError) as e:
                last_exception = e
                self._stats['requests'] += 1
                self._stats['failures'] += 1

                if attempt < self.config.max_retries:
                    # 计算退避延迟
                    delay = self.config.retry_delay * (self.config.retry_backoff ** attempt)
                    self._stats['retries'] += 1

                    logger.warning(
                        f"Request failed (attempt {attempt + 1}/{self.config.max_retries + 1}): {url}. "
                        f"Retrying in {delay:.1f}s. Error: {str(e)[:100]}"
                    )

                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.error(f"Request failed after {attempt + 1} attempts: {url}. Error: {str(e)}")
                    break

        # 所有重试都失败
        raise last_exception or ClientError(f"Request failed: {url}")

    async def _do_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """执行HTTP请求"""
        async with aiohttp.ClientSession(
            connector=self._connector,
            timeout=self._timeout,
            headers={'User-Agent': 'CODEX-Quant-System/1.0'}
        ) as session:

            start_time = time.time()

            async with session.request(method, url, **kwargs) as response:
                elapsed = time.time() - start_time

                # 记录响应时间
                logger.debug(f"{method} {url} - {response.status} - {elapsed:.3f}s")

                # 检查响应状态
                if response.status >= 400:
                    text = await response.text()
                    raise ClientError(f"HTTP {response.status}: {text[:200]}")

                # 解析响应
                try:
                    data = await response.json()
                except Exception:
                    text = await response.text()
                    data = {'text': text, 'status': response.status}

                return {
                    'status': response.status,
                    'data': data,
                    'elapsed': elapsed,
                    'timestamp': datetime.now().isoformat()
                }

    async def clear_cache(self):
        """清空缓存"""
        if self._cache:
            async with self._cache_lock:
                self._cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = self._stats.copy()
        stats['cache_hit_ratio'] = (
            stats['cache_hits'] / (stats['cache_hits'] + stats['cache_misses'])
            if (stats['cache_hits'] + stats['cache_misses']) > 0 else 0
        )
        stats['success_rate'] = (
            stats['successes'] / stats['requests']
            if stats['requests'] > 0 else 0
        )
        return stats

    async def close(self):
        """关闭客户端"""
        if hasattr(self, '_connector') and self._connector:
            await self._connector.close()


# 全局HTTP客户端实例
_http_client: Optional[OptimizedHTTPClient] = None


def get_http_client(config: Optional[RequestConfig] = None) -> OptimizedHTTPClient:
    """获取全局HTTP客户端实例"""
    global _http_client
    if _http_client is None:
        _http_client = OptimizedHTTPClient(config)
    return _http_client


# 便捷函数
async def http_get(url: str, params: Optional[Dict[str, Any]] = None,
                   headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """GET请求便捷函数"""
    client = get_http_client()
    return await client.get(url, params, headers)


async def http_post(url: str, data: Optional[Dict[str, Any]] = None,
                    json: Optional[Dict[str, Any]] = None,
                    headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """POST请求便捷函数"""
    client = get_http_client()
    return await client.post(url, data, json, headers)


async def http_batch_get(urls: List[str],
                        params_list: Optional[List[Dict[str, Any]]] = None,
                        headers_list: Optional[List[Dict[str, str]]] = None,
                        max_concurrent: Optional[int] = None) -> List[Dict[str, Any]]:
    """批量GET请求便捷函数"""
    client = get_http_client()
    return await client.batch_get(urls, params_list, headers_list, max_concurrent)


async def close_http_client():
    """关闭全局HTTP客户端"""
    global _http_client
    if _http_client:
        await _http_client.close()
        _http_client = None
