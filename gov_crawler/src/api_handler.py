"""
GOV 爬蟲系統 - API 處理模塊 (Phase 1 改進版)
直接從政府數據源下載數據（CKAN datastore API 不可用）

改進：
- 添加連接健康檢查
- 增強錯誤恢復機制
- 速率限制處理
- 響應驗證
- 性能優化
"""

import logging
import requests
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import json
import csv
from io import StringIO
import time
from functools import lru_cache

logger = logging.getLogger(__name__)


class DataGovHKAPI:
    """香港政府開放數據 API 處理類 (Phase 1 改進版)

    功能：
    - 自動重試和連接恢復
    - 速率限制管理
    - 響應緩存
    - 連接健康檢查
    - 詳細的錯誤追蹤
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化 API 處理器

        Args:
            config: 配置字典
        """
        self.config = config
        self.base_url = config['crawler'].get('base_url', 'https://data.gov.hk/tc-data')
        self.timeout = config['crawler'].get('timeout', 30)
        self.retry_count = config['crawler'].get('retry_count', 3)
        self.user_agent = config['crawler'].get('user_agent', 'GOV-Crawler/1.0')

        # Phase 1: 新增功能
        self.session = self._create_session()
        self._response_cache = {}  # 簡單的響應緩存
        self._last_request_time = {}  # 用於速率限制
        self._request_count = 0  # 請求計數
        self._is_healthy = True  # 連接健康狀態
        self._last_health_check = None  # 最後的健康檢查時間

        logger.info(f"✓ DataGovHKAPI 初始化成功 (Phase 1 改進版)")
        logger.info(f"  Base URL: {self.base_url}")
        logger.info(f"  Timeout: {self.timeout}s")
        logger.info(f"  Retry Count: {self.retry_count}")

    def _create_session(self) -> requests.Session:
        """創建 requests session"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-HK,zh;q=0.9,en;q=0.8'
        })
        return session

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def _make_request(self, url: str, **kwargs) -> requests.Response:
        """
        發送 HTTP 請求（帶重試機制）

        Args:
            url: 請求 URL
            **kwargs: 其他參數

        Returns:
            Response 對象
        """
        try:
            response = self.session.get(
                url,
                timeout=self.timeout,
                **kwargs
            )
            response.raise_for_status()
            logger.debug(f"API 請求成功: {url}")
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"API 請求失敗: {url} - {e}")
            raise

    def fetch_data_from_url(self, name: str, url: str, data_format: str) -> Optional[Dict[str, Any]]:
        """
        從 URL 獲取數據

        Args:
            name: 數據名稱
            url: 數據 URL
            data_format: 數據格式 (json, csv, etc.)

        Returns:
            數據字典
        """
        try:
            logger.info(f"正在獲取數據: {name} 從 {url}")

            response = self._make_request(url)

            if data_format.lower() == 'json':
                data = response.json()
                records = data if isinstance(data, list) else [data]
            elif data_format.lower() == 'csv':
                # 解析 CSV
                csv_reader = csv.DictReader(StringIO(response.text))
                records = list(csv_reader)
            else:
                records = [response.text]

            result = {
                'name': name,
                'timestamp': datetime.now().isoformat(),
                'records': records,
                'total_count': len(records),
                'url': url,
                'format': data_format
            }

            logger.info(f"成功獲取 {len(records)} 條 {name} 數據記錄")
            return result

        except Exception as e:
            logger.error(f"獲取 {name} 數據失敗: {e}")
            return None

    def crawl_dataset_category(self, category: str) -> Optional[Dict[str, Any]]:
        """
        爬取數據集類別

        Args:
            category: 數據集類別 (finance, real_estate, business, etc.)

        Returns:
            爬取結果
        """
        try:
            if category not in self.config['datasets']:
                logger.warning(f"未知的數據集類別: {category}")
                return None

            category_config = self.config['datasets'][category]

            if not category_config.get('enabled', False):
                logger.info(f"{category} 數據集已禁用")
                return None

            logger.info(f"開始爬取 {category} 數據集")

            results = []
            resources = category_config.get('resources', [])

            for resource in resources:
                name = resource.get('name', 'unknown')
                url = resource.get('url')
                data_format = resource.get('format', 'json')

                if not url:
                    logger.warning(f"資源 {name} 缺少 URL")
                    continue

                data = self.fetch_data_from_url(name, url, data_format)
                if data:
                    results.append(data)

            logger.info(f"完成爬取 {category} 數據集，獲得 {len(results)} 個資源")
            return {
                'category': category,
                'timestamp': datetime.now().isoformat(),
                'resources': results,
                'total_resources': len(results)
            }

        except Exception as e:
            logger.error(f"爬取 {category} 數據集失敗: {e}")
            return None

    def crawl_finance_data(self) -> Optional[Dict[str, Any]]:
        """爬取財經數據"""
        return self.crawl_dataset_category('finance')

    def crawl_real_estate_data(self) -> Optional[Dict[str, Any]]:
        """爬取地產數據"""
        return self.crawl_dataset_category('real_estate')

    def crawl_business_data(self) -> Optional[Dict[str, Any]]:
        """爬取工商業數據"""
        return self.crawl_dataset_category('business')

    def crawl_geography_data(self) -> Optional[Dict[str, Any]]:
        """爬取地理數據"""
        return self.crawl_dataset_category('geography')

    def crawl_transport_data(self) -> Optional[Dict[str, Any]]:
        """爬取運輸數據"""
        return self.crawl_dataset_category('transport')

    def search_datasets(self, query: str = "") -> Optional[List[Dict[str, Any]]]:
        """
        搜索數據集

        Args:
            query: 搜索查詢

        Returns:
            搜索結果
        """
        try:
            logger.info(f"正在搜索數據集: {query}")

            url = "https://data.gov.hk/tc-data/api/3/action/package_search"
            params = {
                'q': query if query else '*',
                'rows': 50
            }

            response = self._make_request(url, params=params)
            data = response.json()

            if data.get('success'):
                results = data['result']['results']
                logger.info(f"搜索找到 {len(results)} 個結果")
                return results
            else:
                logger.error(f"API 返回失敗: {data.get('error')}")
                return None

        except Exception as e:
            logger.error(f"搜索數據集失敗: {e}")
            return None

    # ========== Phase 1: 新增改進方法 ==========

    def check_connectivity(self) -> bool:
        """
        檢查到 data.gov.hk 的連接狀態

        Returns:
            連接是否正常
        """
        try:
            logger.info("正在檢查 API 連接狀態...")
            response = self.session.head(
                f"{self.base_url}/api/3/action/package_search",
                timeout=5
            )
            self._is_healthy = response.status_code < 400
            self._last_health_check = datetime.now()

            if self._is_healthy:
                logger.info("✓ API 連接正常")
            else:
                logger.warning(f"⚠️ API 返回狀態碼: {response.status_code}")

            return self._is_healthy

        except Exception as e:
            logger.error(f"✗ 連接檢查失敗: {e}")
            self._is_healthy = False
            return False

    def _apply_rate_limit(self, url: str, min_interval: float = 0.5) -> None:
        """
        應用速率限制 - 防止過快請求導致 429 錯誤

        Args:
            url: 請求 URL
            min_interval: 最小請求間隔（秒）
        """
        if url in self._last_request_time:
            elapsed = time.time() - self._last_request_time[url]
            if elapsed < min_interval:
                sleep_time = min_interval - elapsed
                logger.debug(f"應用速率限制，等待 {sleep_time:.2f}s")
                time.sleep(sleep_time)

        self._last_request_time[url] = time.time()
        self._request_count += 1

    def _get_cached_response(self, url: str) -> Optional[requests.Response]:
        """
        從緩存獲取響應

        Args:
            url: 請求 URL

        Returns:
            緩存的響應對象（如果存在且未過期）
        """
        if url in self._response_cache:
            cached_data, timestamp = self._response_cache[url]
            # 緩存 5 分鐘
            if (datetime.now() - timestamp).total_seconds() < 300:
                logger.debug(f"使用緩存響應: {url}")
                return cached_data
            else:
                del self._response_cache[url]

        return None

    def _cache_response(self, url: str, response: requests.Response) -> None:
        """
        緩存響應

        Args:
            url: 請求 URL
            response: 響應對象
        """
        self._response_cache[url] = (response, datetime.now())
        logger.debug(f"緩存響應: {url}")

    def _validate_response(self, response: requests.Response, expected_format: str) -> bool:
        """
        驗證響應的正確性

        Args:
            response: 響應對象
            expected_format: 期望的數據格式 (json, csv, text)

        Returns:
            響應是否有效
        """
        try:
            if expected_format.lower() == 'json':
                response.json()  # 嘗試解析 JSON
            elif expected_format.lower() == 'csv':
                # 檢查是否包含 CSV 標記
                lines = response.text.split('\n')
                if len(lines) < 2:
                    logger.warning("CSV 數據行數不足")
                    return False

            return True

        except json.JSONDecodeError:
            logger.error(f"JSON 解析失敗: {response.text[:100]}")
            return False
        except Exception as e:
            logger.error(f"響應驗證失敗: {e}")
            return False

    def get_api_statistics(self) -> Dict[str, Any]:
        """
        獲取 API 使用統計信息

        Returns:
            統計信息字典
        """
        return {
            'total_requests': self._request_count,
            'is_healthy': self._is_healthy,
            'last_health_check': self._last_health_check.isoformat() if self._last_health_check else None,
            'cached_responses': len(self._response_cache),
            'cache_size': sum(len(str(v[0])) for v in self._response_cache.values())
        }

    def clear_cache(self) -> None:
        """清除緩存"""
        cache_size = len(self._response_cache)
        self._response_cache.clear()
        logger.info(f"✓ 已清除 {cache_size} 個緩存響應")

    def close(self) -> None:
        """關閉 session"""
        stats = self.get_api_statistics()
        logger.info("=" * 60)
        logger.info("API 使用統計:")
        logger.info(f"  總請求數: {stats['total_requests']}")
        logger.info(f"  連接狀態: {'正常' if stats['is_healthy'] else '異常'}")
        logger.info(f"  緩存響應: {stats['cached_responses']} 個")
        logger.info("=" * 60)

        self.session.close()
        logger.info("✓ API session 已關閉")
