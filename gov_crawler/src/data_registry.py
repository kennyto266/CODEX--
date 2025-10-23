"""
GOV 爬蟲系統 - 數據註冊表 (Phase 1 新增)
自動發現和管理 data.gov.hk 上的所有數據資源

功能：
- 自動掃描 data.gov.hk 上的所有數據集
- 資源元數據管理
- 資源可用性監控
- 資源索引和搜索
"""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import requests
from dataclasses import dataclass, asdict
from functools import lru_cache

logger = logging.getLogger(__name__)


@dataclass
class Resource:
    """數據資源元數據"""
    id: str
    name: str
    title: str
    package_id: str
    package_name: str
    url: str
    format: str
    description: str = ""
    last_modified: str = ""
    size: Optional[int] = None
    hash: str = ""
    mimetype: str = ""
    discovered_at: str = ""
    last_checked: str = ""
    is_accessible: bool = True


class DataRegistry:
    """數據註冊表 - 管理 data.gov.hk 上的所有資源"""

    def __init__(self, base_url: str = "https://data.gov.hk/tc-data", registry_path: str = "data/registry"):
        """
        初始化數據註冊表

        Args:
            base_url: data.gov.hk 基礎 URL
            registry_path: 註冊表保存路徑
        """
        self.base_url = base_url
        self.api_url = f"{base_url}/api/3/action"
        self.registry_path = Path(registry_path)
        self.registry_path.mkdir(parents=True, exist_ok=True)

        self.resources: Dict[str, Resource] = {}
        self.packages: Dict[str, Dict[str, Any]] = {}

        logger.info(f"✓ 數據註冊表初始化成功")
        logger.info(f"  Base URL: {base_url}")
        logger.info(f"  Registry Path: {registry_path}")

        # 加載已有的註冊表
        self._load_registry()

    def _load_registry(self) -> None:
        """加載已有的註冊表"""
        registry_file = self.registry_path / "registry.json"
        if registry_file.exists():
            try:
                with open(registry_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.resources = {
                        rid: Resource(**rdata)
                        for rid, rdata in data.get('resources', {}).items()
                    }
                    self.packages = data.get('packages', {})
                logger.info(f"✓ 已加載 {len(self.resources)} 個資源")
            except Exception as e:
                logger.error(f"✗ 加載註冊表失敗: {e}")

    def save_registry(self) -> None:
        """保存註冊表到文件"""
        try:
            registry_file = self.registry_path / "registry.json"
            registry_data = {
                'last_updated': datetime.now().isoformat(),
                'resources': {rid: asdict(r) for rid, r in self.resources.items()},
                'packages': self.packages
            }

            with open(registry_file, 'w', encoding='utf-8') as f:
                json.dump(registry_data, f, ensure_ascii=False, indent=2)

            logger.info(f"✓ 已保存 {len(self.resources)} 個資源到註冊表")

        except Exception as e:
            logger.error(f"✗ 保存註冊表失敗: {e}")

    def discover_all_datasets(self, max_rows: int = 1000) -> int:
        """
        發現所有數據集

        Args:
            max_rows: 最大行數

        Returns:
            發現的資源數
        """
        logger.info(f"開始發現所有數據集 (最多 {max_rows} 個)...")

        try:
            url = f"{self.api_url}/package_search"
            params = {'rows': max_rows}

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            if not data.get('success'):
                logger.error(f"API 返回失敗: {data.get('error')}")
                return 0

            packages = data['result']['results']
            logger.info(f"找到 {len(packages)} 個數據集")

            discovered = 0
            for pkg in packages:
                pkg_id = pkg.get('id', '')
                pkg_name = pkg.get('name', '')

                # 保存包元數據
                self.packages[pkg_id] = {
                    'id': pkg_id,
                    'name': pkg_name,
                    'title': pkg.get('title', ''),
                    'notes': pkg.get('notes', ''),
                    'tags': [t.get('name', '') for t in pkg.get('tags', [])],
                    'discovered_at': datetime.now().isoformat()
                }

                # 處理資源
                for resource in pkg.get('resources', []):
                    res_id = resource.get('id', '')
                    if res_id not in self.resources:
                        res = Resource(
                            id=res_id,
                            name=resource.get('name', ''),
                            title=resource.get('name', ''),
                            package_id=pkg_id,
                            package_name=pkg_name,
                            url=resource.get('url', ''),
                            format=resource.get('format', '').upper(),
                            description=resource.get('description', ''),
                            last_modified=resource.get('last_modified', ''),
                            size=resource.get('size'),
                            hash=resource.get('hash', ''),
                            mimetype=resource.get('mimetype', ''),
                            discovered_at=datetime.now().isoformat(),
                            last_checked=datetime.now().isoformat()
                        )
                        self.resources[res_id] = res
                        discovered += 1

            logger.info(f"✓ 發現 {discovered} 個新資源")
            self.save_registry()
            return discovered

        except Exception as e:
            logger.error(f"✗ 發現數據集失敗: {e}")
            return 0

    def check_resource_availability(self, limit: int = 50) -> Dict[str, bool]:
        """
        檢查資源的可用性

        Args:
            limit: 檢查的最大資源數

        Returns:
            資源 ID 和可用性的映射
        """
        logger.info(f"檢查資源可用性 (最多 {limit} 個)...")

        results = {}
        checked_count = 0

        for res_id, resource in list(self.resources.items())[:limit]:
            if not resource.url:
                results[res_id] = False
                continue

            try:
                response = requests.head(
                    resource.url,
                    timeout=10,
                    allow_redirects=True
                )
                is_available = response.status_code < 400
                resource.is_accessible = is_available
                resource.last_checked = datetime.now().isoformat()
                results[res_id] = is_available
                checked_count += 1

                if is_available:
                    logger.debug(f"✓ {resource.name}: 可用")
                else:
                    logger.warning(f"⚠️ {resource.name}: 不可用 ({response.status_code})")

            except Exception as e:
                logger.warning(f"✗ {resource.name}: 檢查失敗 ({e})")
                resource.is_accessible = False
                resource.last_checked = datetime.now().isoformat()
                results[res_id] = False

        logger.info(f"✓ 已檢查 {checked_count} 個資源")
        self.save_registry()
        return results

    def search_resources(self, query: str, by_field: str = "name") -> List[Resource]:
        """
        搜索資源

        Args:
            query: 搜索查詢
            by_field: 搜索字段 (name, title, description, format, package_name)

        Returns:
            匹配的資源列表
        """
        logger.debug(f"搜索資源: {query} (字段: {by_field})")

        results = []
        query_lower = query.lower()

        for resource in self.resources.values():
            field_value = getattr(resource, by_field, "").lower()
            if query_lower in field_value:
                results.append(resource)

        return results

    def get_resources_by_format(self, format_type: str) -> List[Resource]:
        """
        按格式獲取資源

        Args:
            format_type: 格式類型 (JSON, CSV, XML, etc.)

        Returns:
            該格式的資源列表
        """
        format_upper = format_type.upper()
        return [
            r for r in self.resources.values()
            if r.format == format_upper
        ]

    def get_accessible_resources(self) -> List[Resource]:
        """獲取所有可訪問的資源"""
        return [r for r in self.resources.values() if r.is_accessible]

    def get_registry_statistics(self) -> Dict[str, Any]:
        """獲取註冊表統計信息"""
        resources_list = list(self.resources.values())

        formats = {}
        for res in resources_list:
            fmt = res.format or "UNKNOWN"
            formats[fmt] = formats.get(fmt, 0) + 1

        return {
            'total_resources': len(self.resources),
            'total_packages': len(self.packages),
            'accessible_resources': sum(1 for r in resources_list if r.is_accessible),
            'formats': formats,
            'last_updated': self.packages and max(
                (p.get('discovered_at', '') for p in self.packages.values()),
                default=None
            )
        }

    def export_registry(self, output_path: str = None) -> str:
        """
        導出註冊表

        Args:
            output_path: 導出路徑 (預設: registry_export.json)

        Returns:
            導出文件路徑
        """
        output_file = Path(output_path or self.registry_path / "registry_export.json")

        try:
            export_data = {
                'export_time': datetime.now().isoformat(),
                'statistics': self.get_registry_statistics(),
                'resources': [asdict(r) for r in self.resources.values()],
                'packages': self.packages
            }

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            logger.info(f"✓ 已導出註冊表到 {output_file}")
            return str(output_file)

        except Exception as e:
            logger.error(f"✗ 導出註冊表失敗: {e}")
            return ""


# 使用示例
if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)

    registry = DataRegistry()

    print("=" * 60)
    print("發現所有數據集...")
    print("=" * 60)
    discovered = registry.discover_all_datasets()
    print(f"發現: {discovered} 個新資源\n")

    print("=" * 60)
    print("檢查資源可用性...")
    print("=" * 60)
    availability = registry.check_resource_availability(limit=20)
    print(f"可用: {sum(availability.values())} / {len(availability)}\n")

    print("=" * 60)
    print("註冊表統計:")
    print("=" * 60)
    stats = registry.get_registry_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\n" + "=" * 60)
    print("搜索範例 - CSV 資源:")
    print("=" * 60)
    csv_resources = registry.get_resources_by_format("CSV")
    for res in csv_resources[:5]:
        print(f"  - {res.name} ({res.package_name})")

    registry.export_registry()
