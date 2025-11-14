#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CKAN API 集成
从 data.gov.hk 的 CKAN API 获取访客数据集信息并下载数据

Author: Claude Code
Version: 1.0.0
Date: 2025-11-10
"""

import asyncio
import json
import logging
import re
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, quote

import pandas as pd
import requests
from pydantic import BaseModel, Field


class CKANAPIConfig(BaseModel):
    """CKAN API 配置"""
    base_url: str = Field(default="https://data.gov.hk/api/3", description="CKAN API 基础URL")
    api_key: Optional[str] = Field(default=None, description="API 密钥")
    timeout: int = Field(default=30, description="请求超时（秒）")
    max_retries: int = Field(default=3, description="最大重试次数")
    retry_delay: float = Field(default=1.0, description="重试延迟（秒）")
    rate_limit: int = Field(default=100, description="速率限制（每分钟请求数）")


class CKANDataset(BaseModel):
    """CKAN 数据集"""
    id: str
    title: str
    name: str
    description: Optional[str] = None
    resources: List[Dict[str, Any]] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    metadata_modified: Optional[str] = None
    organization: Optional[str] = None


class CKANResource(BaseModel):
    """CKAN 资源"""
    id: str
    package_id: str
    name: str
    url: str
    format: str
    size: Optional[int] = None
    description: Optional[str] = None
    metadata_modified: Optional[str] = None


class CKANAPI:
    """
    CKAN API 客户端

    用于与 data.gov.hk 的 CKAN API 交互
    """

    def __init__(self, base_url: str, config: Optional[CKANAPIConfig] = None):
        """
        初始化 CKAN API 客户端

        Args:
            base_url: CKAN API 基础URL
            config: API 配置
        """
        self.base_url = base_url.rstrip('/')
        self.config = config or CKANAPIConfig()
        self.logger = logging.getLogger(f'{__name__}.{self.__class__.__name__}')

        # HTTP 会话
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'HK-Quant-System/1.0',
            'Accept': 'application/json'
        })

        if self.config.api_key:
            self.session.headers['Authorization'] = self.config.api_key

        # 速率限制
        self._last_request_time = 0
        self._request_count = 0
        self._request_window_start = time.time()

    def _check_rate_limit(self) -> None:
        """检查并应用速率限制"""
        current_time = time.time()

        # 重置窗口
        if current_time - self._request_window_start >= 60:
            self._request_window_start = current_time
            self._request_count = 0

        # 检查是否超过限制
        if self._request_count >= self.config.rate_limit:
            sleep_time = 60 - (current_time - self._request_window_start)
            if sleep_time > 0:
                self.logger.info(f"Rate limit reached, sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
                self._request_window_start = time.time()
                self._request_count = 0

    def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        发起 HTTP 请求

        Args:
            method: HTTP 方法
            endpoint: API 端点
            **kwargs: 其他参数

        Returns:
            Dict: 响应数据
        """
        url = urljoin(self.base_url + '/', endpoint)

        # 设置超时
        if 'timeout' not in kwargs:
            kwargs['timeout'] = self.config.timeout

        # 应用速率限制
        self._check_rate_limit()

        # 重试逻辑
        for attempt in range(self.config.max_retries):
            try:
                self.logger.debug(f"Making {method} request to {url} (attempt {attempt + 1})")

                response = self.session.request(method, url, **kwargs)
                response.raise_for_status()

                self._request_count += 1
                return response.json()

            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Request failed (attempt {attempt + 1}): {e}")

                if attempt < self.config.max_retries - 1:
                    sleep_time = self.config.retry_delay * (2 ** attempt)
                    self.logger.info(f"Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)
                else:
                    self.logger.error(f"All retry attempts failed: {e}")
                    raise

    async def search_datasets(
        self,
        query: str,
        rows: int = 100,
        start: int = 0
    ) -> Optional[Dict[str, Any]]:
        """
        搜索数据集

        Args:
            query: 搜索查询
            rows: 返回行数
            start: 起始位置

        Returns:
            Dict: 搜索结果
        """
        try:
            # 构建查询
            params = {
                'q': query,
                'rows': rows,
                'start': start,
                'sort': 'metadata_modified desc'
            }

            # 发起请求
            result = self._make_request('GET', 'action/package_search', params=params)

            if result and result.get('success'):
                return result

            return None

        except Exception as e:
            self.logger.error(f"Error searching datasets: {e}")
            return None

    async def get_dataset(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        """
        获取数据集详情

        Args:
            dataset_id: 数据集ID

        Returns:
            Dict: 数据集信息
        """
        try:
            result = self._make_request('GET', f'action/package_show', params={'id': dataset_id})

            if result and result.get('success'):
                return result

            return None

        except Exception as e:
            self.logger.error(f"Error getting dataset {dataset_id}: {e}")
            return None

    async def get_visitor_datasets(self) -> List[Dict[str, Any]]:
        """
        获取所有访客相关数据集

        Returns:
            List[Dict]: 数据集列表
        """
        try:
            # 搜索关键词
            search_queries = [
                'visitor arrivals',
                'tourist statistics',
                'tourism statistics',
                'visitor statistics',
                '入境旅客'
            ]

            all_datasets = []
            seen_ids = set()

            for query in search_queries:
                self.logger.info(f"Searching for datasets: {query}")

                result = await self.search_datasets(query, rows=50)

                if result and result.get('success'):
                    datasets = result.get('result', {}).get('results', [])

                    for dataset in datasets:
                        dataset_id = dataset.get('id')
                        if dataset_id and dataset_id not in seen_ids:
                            # 过滤访客相关数据集
                            if self._is_visitor_dataset(dataset):
                                all_datasets.append(dataset)
                                seen_ids.add(dataset_id)

            self.logger.info(f"Found {len(all_datasets)} visitor-related datasets")
            return all_datasets

        except Exception as e:
            self.logger.error(f"Error getting visitor datasets: {e}")
            return []

    def _is_visitor_dataset(self, dataset: Dict[str, Any]) -> bool:
        """
        检查数据集是否与访客相关

        Args:
            dataset: 数据集

        Returns:
            bool: 是否相关
        """
        # 检查标题
        title = dataset.get('title', '').lower()
        keywords = ['visitor', 'tourist', 'arrival', '入境', '旅客', '旅游']

        if any(keyword in title for keyword in keywords):
            return True

        # 检查标签
        tags = [tag.get('name', '').lower() for tag in dataset.get('tags', [])]
        if any(keyword in ' '.join(tags) for keyword in keywords):
            return True

        # 检查描述
        description = dataset.get('description', '').lower()
        if any(keyword in description for keyword in keywords):
            return True

        return False

    async def get_visitor_resources(self, dataset_id: str) -> List[Dict[str, Any]]:
        """
        获取数据集的资源

        Args:
            dataset_id: 数据集ID

        Returns:
            List[Dict]: 资源列表
        """
        try:
            dataset = await self.get_dataset(dataset_id)

            if not dataset:
                return []

            resources = dataset.get('result', {}).get('resources', [])

            # 过滤访客相关资源
            visitor_resources = []
            for resource in resources:
                if self._is_visitor_resource(resource):
                    visitor_resources.append(resource)

            return visitor_resources

        except Exception as e:
            self.logger.error(f"Error getting resources for dataset {dataset_id}: {e}")
            return []

    def _is_visitor_resource(self, resource: Dict[str, Any]) -> bool:
        """
        检查资源是否与访客相关

        Args:
            resource: 资源

        Returns:
            bool: 是否相关
        """
        # 检查格式（优先 CSV）
        format_lower = resource.get('format', '').lower()
        if format_lower in ['csv', 'xlsx', 'json']:
            return True

        # 检查名称
        name = resource.get('name', '').lower()
        if 'visitor' in name or 'tourist' in name:
            return True

        return False

    async def download_resource(self, url: str) -> Optional[bytes]:
        """
        下载资源

        Args:
            url: 资源 URL

        Returns:
            bytes: 数据
        """
        try:
            self.logger.info(f"Downloading resource: {url}")

            response = self.session.get(url, timeout=self.config.timeout)
            response.raise_for_status()

            return response.content

        except Exception as e:
            self.logger.error(f"Error downloading resource {url}: {e}")
            return None

    async def download_visitor_data(self) -> List[Dict[str, Any]]:
        """
        下载所有访客数据

        Returns:
            List[Dict]: 下载的数据列表
        """
        try:
            all_data = []

            # 获取访客数据集
            datasets = await self.get_visitor_datasets()

            for dataset in datasets:
                self.logger.info(f"Processing dataset: {dataset.get('title')}")

                # 获取资源
                resources = await self.get_visitor_resources(dataset.get('id'))

                for resource in resources:
                    # 下载数据
                    content = await self.download_resource(resource.get('url'))

                    if content:
                        # 解析数据
                        parsed_data = await self._parse_resource_data(
                            content,
                            resource.get('format', ''),
                            dataset,
                            resource
                        )

                        if parsed_data:
                            all_data.extend(parsed_data)

            self.logger.info(f"Downloaded {len(all_data)} data points")
            return all_data

        except Exception as e:
            self.logger.error(f"Error downloading visitor data: {e}")
            return []

    async def _parse_resource_data(
        self,
        content: bytes,
        format_type: str,
        dataset: Dict[str, Any],
        resource: Dict[str, Any]
    ) -> Optional[List[Dict[str, Any]]]:
        """
        解析资源数据

        Args:
            content: 原始数据
            format_type: 数据格式
            dataset: 数据集信息
            resource: 资源信息

        Returns:
            List[Dict]: 解析后的数据
        """
        try:
            format_lower = format_type.lower()

            if format_lower == 'csv':
                # 解析 CSV
                df = pd.read_csv(pd.io.common.BytesIO(content))

                # 转换为标准格式
                return self._convert_to_visitor_format(
                    df,
                    dataset,
                    resource
                )

            elif format_lower in ['xlsx', 'xls']:
                # 解析 Excel
                df = pd.read_excel(pd.io.common.BytesIO(content))

                return self._convert_to_visitor_format(
                    df,
                    dataset,
                    resource
                )

            elif format_lower == 'json':
                # 解析 JSON
                data = json.loads(content.decode('utf-8'))

                if isinstance(data, list):
                    df = pd.DataFrame(data)
                    return self._convert_to_visitor_format(
                        df,
                        dataset,
                        resource
                    )
                else:
                    return []

            return None

        except Exception as e:
            self.logger.error(f"Error parsing resource data: {e}")
            return None

    def _convert_to_visitor_format(
        self,
        df: pd.DataFrame,
        dataset: Dict[str, Any],
        resource: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        转换为访客数据标准格式

        Args:
            df: DataFrame
            dataset: 数据集信息
            resource: 资源信息

        Returns:
            List[Dict]: 标准格式数据
        """
        try:
            standardized_data = []

            for _, row in df.iterrows():
                # 尝试识别日期列
                date_value = self._find_date_column(row)
                if not date_value:
                    continue

                # 尝试识别访客数量列
                visitor_total = self._find_visitor_column(row, ['total', 'visitors', 'total_visitors'])
                if visitor_total is None:
                    continue

                # 尝试识别内地访客列
                visitor_mainland = self._find_visitor_column(row, ['mainland', 'china', 'mainland_china'])

                # 尝试识别增长率列
                visitor_growth = self._find_visitor_column(row, ['growth', 'growth_rate', 'yoy'])

                # 构建标准化记录
                record = {
                    'date': self._standardize_date(date_value),
                    'visitor_total': visitor_total,
                    'visitor_mainland': visitor_mainland,
                    'visitor_growth': visitor_growth,
                    'source': f"data.gov.hk/{dataset.get('id', '')}"
                }

                # 添加原始数据
                record['raw_data'] = row.to_dict()

                standardized_data.append(record)

            return standardized_data

        except Exception as e:
            self.logger.error(f"Error converting to visitor format: {e}")
            return []

    def _find_date_column(self, row: pd.Series) -> Optional[str]:
        """查找日期列"""
        for col in row.index:
            col_lower = str(col).lower()
            if 'date' in col_lower or 'time' in col_lower:
                return str(row[col])
        return None

    def _find_visitor_column(self, row: pd.Series, keywords: List[str]) -> Optional[float]:
        """查找访客数量列"""
        for col in row.index:
            col_lower = str(col).lower()
            for keyword in keywords:
                if keyword in col_lower:
                    try:
                        value = str(row[col]).replace(',', '').replace(' ', '')
                        return float(value)
                    except (ValueError, TypeError):
                        continue
        return None

    def _standardize_date(self, date_value: Any) -> Optional[str]:
        """标准化日期格式"""
        if pd.isna(date_value):
            return None

        try:
            # 尝试解析日期
            if isinstance(date_value, str):
                # 尝试不同格式
                formats = [
                    '%Y-%m-%d',
                    '%Y/%m/%d',
                    '%Y-%m',
                    '%Y/%m',
                    '%Y-%m-%d %H:%M:%S',
                    '%Y年%m月%d日',
                    '%Y年%m月'
                ]

                for fmt in formats:
                    try:
                        dt = datetime.strptime(date_value, fmt)
                        return dt.strftime('%Y-%m-%d')
                    except ValueError:
                        continue

            return None

        except Exception:
            return None

    def parse_csv_url(self, url: str) -> Dict[str, Any]:
        """
        解析 CSV URL

        Args:
            url: CSV URL

        Returns:
            Dict: 解析结果
        """
        parsed = {
            'url': url,
            'domain': '',
            'keywords': [],
            'is_data_gov_hk': False
        }

        # 提取域名
        if 'data.gov.hk' in url:
            parsed['is_data_gov_hk'] = True
            parsed['domain'] = 'data.gov.hk'

        # 提取关键词
        url_lower = url.lower()
        keywords = ['visitor', 'tourist', 'arrival', 'tourism']
        parsed['keywords'] = [k for k in keywords if k in url_lower]

        return parsed


# 便捷函数
async def get_visitor_data_from_ckan() -> List[Dict[str, Any]]:
    """
    从 CKAN 获取访客数据

    Returns:
        List[Dict]: 访客数据
    """
    api = CKANAPI(base_url="https://data.gov.hk/api/3")
    return await api.download_visitor_data()


if __name__ == '__main__':
    # 示例用法
    async def main():
        api = CKANAPI(base_url="https://data.gov.hk/api/3")

        # 搜索访客数据集
        datasets = await api.get_visitor_datasets()
        print(f"Found {len(datasets)} visitor datasets")

        # 下载数据
        data = await api.download_visitor_data()
        print(f"Downloaded {len(data)} data points")

    asyncio.run(main())
