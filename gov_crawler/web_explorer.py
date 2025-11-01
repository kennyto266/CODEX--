#!/usr/bin/env python3
"""
Web Explorer for Gov Data Sources
探索香港政府數據源的腳本，使用網頁分析來發現可用的數據API和數據集
"""

import asyncio
import aiohttp
import json
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import logging

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gov_crawler/logs/web_exploration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WebExplorer:
    """Web exploration class for discovering data sources"""

    def __init__(self):
        self.session = None
        self.results = []
        self.target_sites = [
            {
                "name": "香港政府開放數據平台",
                "url": "https://data.gov.hk/tc-data/dataset",
                "priority": "HIGH",
                "category": "Portal",
                "expected_data": ["各種政府統計數據", "API接口", "CSV下載"]
            },
            {
                "name": "香港金融管理局 (HKMA)",
                "url": "https://www.hkma.gov.hk/eng/",
                "priority": "HIGH",
                "category": "Financial",
                "expected_data": ["HIBOR利率", "銀行統計", "外匯數據"]
            },
            {
                "name": "政府統計處 (C&SD)",
                "url": "https://www.censtatd.gov.hk/",
                "priority": "HIGH",
                "category": "Statistics",
                "expected_data": ["GDP", "人口統計", "零售銷售", "經濟指標"]
            },
            {
                "name": "入境事務處 (IMMD)",
                "url": "https://www.immd.gov.hk/",
                "priority": "MEDIUM",
                "category": "Immigration",
                "expected_data": ["入境人數", "訪客統計", "邊境數據"]
            },
            {
                "name": "香港旅遊發展局",
                "url": "https://www.discoverhongkong.com/",
                "priority": "MEDIUM",
                "category": "Tourism",
                "expected_data": ["訪客 arrivals", "酒店入住率", "旅遊統計"]
            },
            {
                "name": "港鐵公司 (MTR)",
                "url": "https://www.mtr.com.hk/",
                "priority": "MEDIUM",
                "category": "Transport",
                "expected_data": ["乘客量", "服務統計", "財務數據"]
            },
            {
                "name": "土地註冊處",
                "url": "https://www.landreg.gov.hk/",
                "priority": "MEDIUM",
                "category": "Property",
                "expected_data": ["物業交易", "樓價指數", "註冊統計"]
            },
            {
                "name": "社會福利署",
                "url": "https://www.swd.gov.hk/",
                "priority": "LOW",
                "category": "Social",
                "expected_data": ["社會指標", "福利統計", "服務數據"]
            },
            {
                "name": "庫務署",
                "url": "https://www.tib.gov.hk/",
                "priority": "MEDIUM",
                "category": "Fiscal",
                "expected_data": ["政府財政", "公共開支", "稅收數據"]
            }
        ]

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def explore_site(self, site: Dict[str, str]) -> Dict[str, Any]:
        """Explore a single website and analyze its structure"""
        logger.info(f"探索網站: {site['name']} - {site['url']}")

        result = {
            "site_name": site['name'],
            "url": site['url'],
            "priority": site['priority'],
            "category": site['category'],
            "exploration_time": datetime.now().isoformat(),
            "accessible": False,
            "apis_discovered": [],
            "data_formats": [],
            "download_links": [],
            "notes": [],
            "score": 0
        }

        try:
            async with self.session.get(site['url']) as response:
                if response.status == 200:
                    result["accessible"] = True
                    content = await response.text()

                    # 分析內容
                    await self.analyze_content(result, content, site)

                else:
                    result["notes"].append(f"HTTP {response.status}")
                    logger.warning(f"網站無法訪問: {site['url']} - {response.status}")

        except Exception as e:
            result["notes"].append(f"錯誤: {str(e)}")
            logger.error(f"探索網站時出錯: {site['url']} - {str(e)}")

        # 計算分數
        result["score"] = self.calculate_score(result)

        return result

    async def analyze_content(self, result: Dict[str, Any], content: str, site: Dict[str, str]):
        """Analyze the content of a webpage"""
        # 檢查常見的API關鍵詞
        api_keywords = ['api', 'API', 'endpoint', 'Endpoint', 'rest', 'REST', 'json', 'JSON']
        csv_keywords = ['csv', 'CSV', 'download', 'Download', 'data', 'Data']

        # 檢查API相關內容
        for keyword in api_keywords:
            if keyword in content:
                result["apis_discovered"].append(f"可能的API相關內容: {keyword}")
                result["score"] += 1

        # 檢查數據下載
        for keyword in csv_keywords:
            if keyword in content:
                result["data_formats"].append(f"發現數據格式: {keyword}")
                result["score"] += 1

        # 網站特定分析
        if 'data.gov.hk' in site['url']:
            await self.analyze_data_gov_hk(result, content)
        elif 'hkma.gov.hk' in site['url']:
            await self.analyze_hkma(result, content)
        elif 'censtatd.gov.hk' in site['url']:
            await self.analyze_censustd(result, content)

        # 檢查統計表或圖表
        if any(word in content.lower() for word in ['statistics', 'statistic', '數據', '統計']):
            result["notes"].append("發現統計相關內容")
            result["score"] += 2

    async def analyze_data_gov_hk(self, result: Dict[str, Any], content: str):
        """Specialized analysis for data.gov.hk"""
        result["notes"].append("香港政府開放數據平台 - 可能有API或數據集")

        # 檢查數據集頁面
        if 'dataset' in content.lower():
            result["apis_discovered"].append("數據集發現")

        # 檢查API文檔
        if 'api' in content.lower():
            result["apis_discovered"].append("API文檔可能存在")

    async def analyze_hkma(self, result: Dict[str, Any], content: str):
        """Specialized analysis for HKMA"""
        result["notes"].append("香港金融管理局 - HIBOR利率數據源")

        if 'hibor' in content.lower() or 'HIBOR' in content:
            result["apis_discovered"].append("HIBOR利率數據")
            result["score"] += 3

        if 'interest' in content.lower():
            result["apis_discovered"].append("利率相關數據")
            result["score"] += 2

    async def analyze_censustd(self, result: Dict[str, Any], content: str):
        """Specialized analysis for C&SD"""
        result["notes"].append("政府統計處 - 經濟和社會統計數據")

        keywords = ['gdp', 'GDP', 'retail', 'retail', 'population', '人口', 'GDP']
        for keyword in keywords:
            if keyword in content:
                result["apis_discovered"].append(f"統計數據: {keyword}")
                result["score"] += 2

    def calculate_score(self, result: Dict[str, Any]) -> int:
        """Calculate a relevance score for the data source"""
        score = 0

        # 基礎分數
        if result["accessible"]:
            score += 10

        # 優先級加權
        priority_weights = {"HIGH": 5, "MEDIUM": 3, "LOW": 1}
        score += priority_weights.get(result["priority"], 0)

        # API發現加分
        score += len(result["apis_discovered"]) * 2

        # 數據格式加分
        score += len(result["data_formats"])

        return min(score, 50)  # 最大50分

    async def explore_all_sites(self) -> List[Dict[str, Any]]:
        """探索所有目標網站"""
        logger.info(f"開始探索 {len(self.target_sites)} 個網站")

        tasks = [self.explore_site(site) for site in self.target_sites]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 過濾異常結果
        valid_results = [r for r in results if isinstance(r, dict)]

        # 按分數排序
        valid_results.sort(key=lambda x: x['score'], reverse=True)

        self.results = valid_results
        return valid_results

    def save_results(self, filename: str = None):
        """保存探索結果"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"gov_crawler/data/web_exploration_{timestamp}.json"

        Path(filename).parent.mkdir(parents=True, exist_ok=True)

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                "exploration_date": datetime.now().isoformat(),
                "total_sites": len(self.results),
                "accessible_sites": sum(1 for r in self.results if r.get("accessible")),
                "results": self.results
            }, f, ensure_ascii=False, indent=2)

        logger.info(f"結果已保存到: {filename}")

    def generate_report(self) -> str:
        """生成探索報告"""
        if not self.results:
            return "No exploration results available."

        report = []
        report.append("=" * 80)
        report.append("香港政府數據源探索報告")
        report.append("=" * 80)
        report.append(f"探索時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"總網站數: {len(self.results)}")
        report.append(f"可訪問網站: {sum(1 for r in self.results if r.get('accessible'))}")
        report.append("")

        report.append("按優先級排序的結果:")
        report.append("-" * 80)

        for i, result in enumerate(self.results, 1):
            report.append(f"\n{i}. {result['site_name']}")
            report.append(f"   URL: {result['url']}")
            report.append(f"   優先級: {result['priority']}")
            report.append(f"   分數: {result['score']}/50")
            report.append(f"   可訪問: {'是' if result['accessible'] else '否'}")

            if result.get('apis_discovered'):
                report.append(f"   發現的API/數據: {', '.join(result['apis_discovered'][:3])}")

            if result.get('notes'):
                report.append(f"   備註: {result['notes'][0]}")

        report.append("\n" + "=" * 80)
        report.append("推薦實施優先級:")
        report.append("=" * 80)

        high_priority = [r for r in self.results if r.get('priority') == 'HIGH' and r.get('accessible')]
        for result in high_priority[:3]:
            report.append(f"✓ {result['site_name']} (分數: {result['score']})")

        return "\n".join(report)

async def main():
    """主函數"""
    print("開始探索香港政府數據源...")
    print("=" * 80)

    async with WebExplorer() as explorer:
        results = await explorer.explore_all_sites()

        # 保存結果
        explorer.save_results()

        # 生成報告
        report = explorer.generate_report()
        print("\n" + report)

        # 保存報告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"gov_crawler/logs/web_exploration_report_{timestamp}.txt"
        Path(report_filename).parent.mkdir(parents=True, exist_ok=True)

        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"\n報告已保存到: {report_filename}")

if __name__ == "__main__":
    asyncio.run(main())
