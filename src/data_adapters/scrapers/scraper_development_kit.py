"""
爬虫开发工具包 - 使用 Chrome DevTools 加速开发

工作流程：
1. 打开网站
2. 检查页面结构 → 找到数据容器
3. 生成爬虫代码框架
4. 集成到适配器
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import re

logger = logging.getLogger(__name__)


@dataclass
class ScraperTarget:
    """爬虫目标定义"""
    name: str  # 如: "HKEX Futures"
    url: str  # 目标URL
    data_selectors: Dict[str, str]  # CSS选择器: {'volume': '.data-volume', ...}
    extraction_rules: Dict[str, str]  # 提取规则: {'volume': 'text', 'price': 'data-price'}
    update_frequency: str  # 更新频率: 'daily', 'hourly'
    description: str


class ScraperDevKit:
    """爬虫开发工具包"""

    def __init__(self):
        self.targets: Dict[str, ScraperTarget] = {}
        self.chrome_sessions: Dict[str, Any] = {}

    def register_target(self, target: ScraperTarget) -> None:
        """注册爬虫目标"""
        self.targets[target.name] = target
        logger.info(f"✓ 已注册爬虫目标: {target.name}")

    def generate_scraper_code(self, target: ScraperTarget) -> str:
        """生成爬虫代码框架

        使用chrome-devtools分析后，生成可用的爬虫代码模板
        """
        selectors_str = json.dumps(target.data_selectors, indent=2, ensure_ascii=False)
        rules_str = json.dumps(target.extraction_rules, indent=2, ensure_ascii=False)

        code = f'''"""
爬虫: {target.name}
URL: {target.url}
更新频率: {target.update_frequency}
说明: {target.description}

开发步骤:
1. 使用chrome-devtools打开{target.url}
2. 使用DevTools的选择器工具验证以下选择器
3. 测试数据提取逻辑
4. 集成到适配器并测试缓存
"""

import asyncio
from bs4 import BeautifulSoup
import httpx
from datetime import datetime, timedelta
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class {target.name.replace(" ", "")}Scraper:
    """
    {target.name} 爬虫

    选择器:
    {selectors_str}

    提取规则:
    {rules_str}
    """

    def __init__(self, cache_ttl: int = 3600):
        self.url = "{target.url}"
        self.cache_ttl = cache_ttl
        self.cache: Dict[str, Any] = {{}}
        self.last_update = None
        self.selectors = {selectors_str}
        self.extraction_rules = {rules_str}

    async def fetch_data(self) -> Dict[str, Any]:
        """获取数据并缓存"""
        now = datetime.now()

        # 检查缓存
        if self.cache and self.last_update:
            age = (now - self.last_update).total_seconds()
            if age < self.cache_ttl:
                logger.info(f"使用缓存数据 (年龄: {{age:.0f}}秒)")
                return self.cache

        try:
            logger.info(f"正在获取数据: {{self.url}}")
            async with httpx.AsyncClient() as client:
                response = await client.get(self.url, timeout=30)
                response.raise_for_status()

            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # 提取数据
            data = self._extract_data(soup)

            # 更新缓存
            self.cache = data
            self.last_update = now

            logger.info(f"✓ 成功获取数据 ({{len(data)}} 项)")
            return data

        except Exception as e:
            logger.error(f"获取数据失败: {{e}}")
            # 如果有旧缓存，返回旧缓存
            if self.cache:
                logger.warning("使用过期缓存作为后备")
                return self.cache
            raise

    def _extract_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """从BeautifulSoup对象提取数据

        使用chrome-devtools找到的选择器
        """
        data = {{}}

        for field_name, selector in self.selectors.items():
            try:
                element = soup.select_one(selector)
                if element:
                    extraction_rule = self.extraction_rules.get(field_name, 'text')

                    if extraction_rule == 'text':
                        data[field_name] = element.get_text(strip=True)
                    elif extraction_rule.startswith('data-'):
                        attr_name = extraction_rule.split('-', 1)[1]
                        data[field_name] = element.get(attr_name)
                    elif extraction_rule.startswith('attr:'):
                        attr_name = extraction_rule.split(':')[1]
                        data[field_name] = element.get(attr_name)
                    else:
                        data[field_name] = element.get_text(strip=True)

                    logger.debug(f"✓ 提取 {{field_name}}: {{data[field_name]}}")
                else:
                    logger.warning(f"✗ 找不到选择器: {{selector}} (字段: {{field_name}})")

            except Exception as e:
                logger.error(f"提取 {{field_name}} 失败: {{e}}")

        return data

    async def test_extraction(self) -> bool:
        """测试数据提取逻辑

        运行此方法验证选择器是否正确
        """
        try:
            data = await self.fetch_data()
            print(f"\\n✓ 成功提取数据:")
            for key, value in data.items():
                print(f"  {{key}}: {{value}}")
            return True
        except Exception as e:
            print(f"✗ 提取失败: {{e}}")
            return False


# 使用示例
async def main():
    scraper = {target.name.replace(" ", "")}Scraper()
    success = await scraper.test_extraction()
    if success:
        print("\\n爬虫就绪，可以集成到适配器!")
    else:
        print("\\n请检查选择器和提取规则")


if __name__ == "__main__":
    asyncio.run(main())
'''
        return code

    def print_devtools_workflow(self, target: ScraperTarget) -> str:
        """输出chrome-devtools工作流指南"""
        guide = f"""
╔════════════════════════════════════════════════════════════════╗
║  Chrome DevTools 爬虫开发工作流                                ║
╚════════════════════════════════════════════════════════════════╝

目标: {target.name}
URL: {target.url}

【步骤 1】打开网站
────────────────────────────────────────────────────────────────
1. 使用chrome-devtools打开: {target.url}
2. 在浏览器中检查页面是否正确加载

【步骤 2】查找数据容器
────────────────────────────────────────────────────────────────
1. 打开DevTools (F12)
2. 使用 Inspector 工具 (Ctrl+Shift+C)
3. 点击页面上的数据元素
4. 在Elements标签中查看HTML结构
5. 记录CSS选择器:

需要找的数据字段:
{json.dumps(target.data_selectors, indent=2, ensure_ascii=False)}

【步骤 3】验证选择器
────────────────────────────────────────────────────────────────
1. 在Console标签运行测试:
   document.querySelectorAll('YOUR_SELECTOR').length

2. 验证返回正确的元素个数

【步骤 4】生成爬虫代码
────────────────────────────────────────────────────────────────
1. 将找到的选择器更新到代码中
2. 运行 test_extraction() 验证
3. 调整选择器直到数据正确提取

【步骤 5】集成到适配器
────────────────────────────────────────────────────────────────
1. 将生成的爬虫类复制到适配器
2. 实现 fetch_data() 方法
3. 添加到AlternativeDataAdapter
4. 运行单元测试

╚════════════════════════════════════════════════════════════════╝
"""
        return guide


# 预定义的爬虫目标
def create_hkex_scraper_target() -> ScraperTarget:
    """HKEX期货数据爬虫目标"""
    return ScraperTarget(
        name="HKEX Futures",
        url="https://www.hkex.com.hk/",
        data_selectors={
            "hsi_volume": ".futures-data-hsi .volume",
            "hsi_price": ".futures-data-hsi .last-price",
            "mhi_volume": ".futures-data-mhi .volume",
            "mhi_price": ".futures-data-mhi .last-price",
            "timestamp": ".market-time",
        },
        extraction_rules={
            "hsi_volume": "text",
            "hsi_price": "text",
            "mhi_volume": "text",
            "mhi_price": "text",
            "timestamp": "text",
        },
        update_frequency="daily",
        description="香港交易所期货合约数据 (HSI, MHI)"
    )


def create_gov_scraper_target() -> ScraperTarget:
    """政府数据爬虫目标"""
    return ScraperTarget(
        name="HK Government Data",
        url="https://data.gov.hk/",
        data_selectors={
            "hibor_on": ".indicator-hibor-on .value",
            "hibor_1m": ".indicator-hibor-1m .value",
            "visitor_arrivals": ".indicator-visitors .value",
            "trade_balance": ".indicator-trade .value",
            "last_update": ".data-timestamp",
        },
        extraction_rules={
            "hibor_on": "text",
            "hibor_1m": "text",
            "visitor_arrivals": "text",
            "trade_balance": "text",
            "last_update": "text",
        },
        update_frequency="daily",
        description="香港政府经济数据 (HIBOR, 访客人数)"
    )


if __name__ == "__main__":
    # 初始化工具包
    kit = ScraperDevKit()

    # 注册爬虫目标
    kit.register_target(create_hkex_scraper_target())
    kit.register_target(create_gov_scraper_target())

    # 输出工作流指南
    print(kit.print_devtools_workflow(create_hkex_scraper_target()))

    # 生成爬虫代码
    code = kit.generate_scraper_code(create_hkex_scraper_target())
    print("\n已生成爬虫代码框架 - 保存到文件...")
    with open("hkex_scraper.py", "w", encoding="utf-8") as f:
        f.write(code)
    print("✓ 已保存到 hkex_scraper.py")
