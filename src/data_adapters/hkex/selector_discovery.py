#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HKEX 选择器自动发现模块

智能识别网页中的数据表格和结构，自动生成稳定的 CSS 选择器。

主要功能:
- 自动发现表格元素
- 生成稳定的 CSS 选择器
- 验证选择器有效性
- 支持多语言页面（中文/英文）
- 选择器优化和去重

作者: Claude Code
创建日期: 2025-10-27
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("hk_quant_system.hkex_selector_discovery")


class SelectorType(Enum):
    """选择器类型枚举"""
    CSS_CLASS = "css_class"
    CSS_ID = "css_id"
    CSS_TAG = "css_tag"
    CSS_ATTRIBUTE = "css_attribute"
    XPATH = "xpath"
    TEXT_PATTERN = "text_pattern"


@dataclass
class SelectorCandidate:
    """选择器候选"""
    selector: str
    selector_type: SelectorType
    confidence: float
    element_count: int
    uniqueness: float
    stability: float
    description: str


@dataclass
class DiscoveredElement:
    """发现的数据元素"""
    tag_name: str
    attributes: Dict[str, str]
    text_content: str
    xpath: str
    css_selector: str
    confidence: float
    is_table: bool = False
    is_data_container: bool = False
    language: str = "unknown"


class SelectorDiscoveryEngine:
    """选择器发现引擎

    分析页面结构，自动发现数据元素并生成稳定的选择器。
    """

    def __init__(self):
        """初始化发现引擎"""
        self.discovered_selectors = {}
        self.selector_history = {}
        self.element_patterns = {
            "table": ["table", "tbody", "thead", "tr", "td", "th"],
            "list": ["ul", "ol", "li"],
            "data_container": ["div", "span", "section"],
            "text": ["p", "h1", "h2", "h3", "h4", "h5", "h6"]
        }

        # 数据模式关键词
        self.data_keywords = {
            "index": ["指数", "index", "恒生", "HSI", "HSCEI", "HSTECH"],
            "price": ["价格", "price", "现价", "current"],
            "change": ["涨跌", "change", "变动"],
            "volume": ["成交量", "volume", "成交"],
            "turnover": ["成交额", "turnover", "成交金额"],
            "percentage": ["百分比", "%", "percent"],
            "date": ["日期", "date", "时间", "time"],
            "name": ["名称", "name", "名称"],
            "market": ["市场", "market", "交易所"]
        }

        logger.info("✓ SelectorDiscoveryEngine 初始化完成")

    async def discover_page_structure(
        self,
        page_id: str,
        controller: Any,
        min_confidence: float = 0.8
    ) -> Dict[str, List[DiscoveredElement]]:
        """发现页面结构

        Args:
            page_id: 页面 ID
            controller: Chrome 控制器实例
            min_confidence: 最低置信度

        Returns:
            按类型分组的数据元素字典

        Raises:
            Exception: 发现失败
        """
        try:
            logger.info(f"开始发现页面结构: {page_id}")

            # 1. 获取页面快照
            await self._analyze_page_snapshot(page_id, controller)

            # 2. 发现表格结构
            tables = await self._discover_tables(page_id, controller)

            # 3. 发现数据容器
            containers = await self._discover_data_containers(page_id, controller)

            # 4. 发现文本元素
            text_elements = await self._discover_text_elements(page_id, controller)

            # 5. 过滤低置信度元素
            all_elements = {
                "tables": self._filter_by_confidence(tables, min_confidence),
                "containers": self._filter_by_confidence(containers, min_confidence),
                "text_elements": self._filter_by_confidence(text_elements, min_confidence)
            }

            logger.info(
                f"✓ 页面结构发现完成: "
                f"表格={len(all_elements['tables'])}, "
                f"容器={len(all_elements['containers'])}, "
                f"文本={len(all_elements['text_elements'])}"
            )

            return all_elements

        except Exception as e:
            logger.error(f"✗ 页面结构发现失败: {e}")
            raise

    async def _analyze_page_snapshot(self, page_id: str, controller: Any):
        """分析页面快照"""
        try:
            # 执行分析脚本
            await controller.execute_script(
                page_id,
                """
                // 页面结构分析脚本
                const structure = {
                    tables: document.querySelectorAll('table').length,
                    divs: document.querySelectorAll('div').length,
                    spans: document.querySelectorAll('span').length,
                    language: document.documentElement.lang || 'unknown'
                };
                return structure;
                """
            )
            logger.debug(f"页面快照分析: {page_id}")

        except Exception as e:
            logger.error(f"页面快照分析失败: {e}")

    async def _discover_tables(
        self,
        page_id: str,
        controller: Any
    ) -> List[DiscoveredElement]:
        """发现表格结构"""
        try:
            # 查询所有表格
            tables = await controller.query_elements(
                page_id,
                ["table", "table[role='table']", ".data-table", "[data-table]"]
            )

            discovered_tables = []
            for i, table in enumerate(tables):
                if not table or not table.get("found"):
                    continue

                # 生成表格选择器
                selector = f"table:nth-of-type({i+1})"

                # 分析表格内容
                table_element = DiscoveredElement(
                    tag_name="table",
                    attributes=table.get("attributes", {}),
                    text_content=table.get("text", ""),
                    xpath=f"//table[{i+1}]",
                    css_selector=selector,
                    confidence=0.9,
                    is_table=True,
                    is_data_container=True,
                    language="zh" if "恒生" in table.get("text", "") else "unknown"
                )

                discovered_tables.append(table_element)

            logger.debug(f"发现表格: {len(discovered_tables)} 个")
            return discovered_tables

        except Exception as e:
            logger.error(f"表格发现失败: {e}")
            return []

    async def _discover_data_containers(
        self,
        page_id: str,
        controller: Any
    ) -> List[DiscoveredElement]:
        """发现数据容器"""
        try:
            # 常见数据容器选择器
            container_selectors = [
                "div[class*='data']",
                "div[class*='market']",
                "div[class*='index']",
                "div[class*='stock']",
                "span[class*='value']",
                "section[class*='content']"
            ]

            discovered_containers = []
            for selector in container_selectors:
                elements = await controller.query_elements(page_id, [selector])
                for element in elements:
                    if element and element.get("found"):
                        container = DiscoveredElement(
                            tag_name=element.get("tag_name", "div"),
                            attributes=element.get("attributes", {}),
                            text_content=element.get("text", "")[:100],
                            xpath=f"//{element.get('tag_name', 'div')}[@class*='data']",
                            css_selector=selector,
                            confidence=0.8,
                            is_table=False,
                            is_data_container=True,
                            language="unknown"
                        )
                        discovered_containers.append(container)

            logger.debug(f"发现数据容器: {len(discovered_containers)} 个")
            return discovered_containers

        except Exception as e:
            logger.error(f"数据容器发现失败: {e}")
            return []

    async def _discover_text_elements(
        self,
        page_id: str,
        controller: Any
    ) -> List[DiscoveredElement]:
        """发现文本元素"""
        try:
            # 文本元素选择器
            text_selectors = [
                "h1", "h2", "h3", "h4", "h5", "h6",
                "p", "span", "div"
            ]

            discovered_texts = []
            for selector in text_selectors:
                elements = await controller.query_elements(page_id, [selector])
                for element in elements:
                    if element and element.get("found"):
                        text = element.get("text", "").strip()
                        if len(text) < 5:  # 过滤太短的文本
                            continue

                        # 检查是否包含数据关键词
                        confidence = self._calculate_text_confidence(text)

                        text_element = DiscoveredElement(
                            tag_name=element.get("tag_name", "div"),
                            attributes=element.get("attributes", {}),
                            text_content=text[:200],
                            xpath=f"//{element.get('tag_name', 'div')}[text()='{text[:50]}']",
                            css_selector=f"{selector}:contains('{text[:20]}')",
                            confidence=confidence,
                            is_table=False,
                            is_data_container=False,
                            language="zh" if self._is_chinese_text(text) else "en"
                        )
                        discovered_texts.append(text_element)

            logger.debug(f"发现文本元素: {len(discovered_texts)} 个")
            return discovered_texts

        except Exception as e:
            logger.error(f"文本元素发现失败: {e}")
            return []

    def _filter_by_confidence(
        self,
        elements: List[DiscoveredElement],
        min_confidence: float
    ) -> List[DiscoveredElement]:
        """按置信度过滤元素"""
        return [e for e in elements if e.confidence >= min_confidence]

    def _calculate_text_confidence(self, text: str) -> float:
        """计算文本置信度"""
        confidence = 0.5  # 基础置信度

        # 检查关键词匹配
        for category, keywords in self.data_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text.lower():
                    confidence += 0.1

        # 文本长度加分
        if len(text) > 10:
            confidence += 0.1
        if len(text) > 50:
            confidence += 0.1

        # 包含数字加分
        if re.search(r'\d', text):
            confidence += 0.1

        # 包含特殊字符加分
        if re.search(r'[%,.$]', text):
            confidence += 0.1

        return min(confidence, 1.0)

    def _is_chinese_text(self, text: str) -> bool:
        """检查是否包含中文"""
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
        return len(chinese_chars) / len(text) > 0.3 if text else False

    async def generate_selector_candidates(
        self,
        element: DiscoveredElement,
        max_candidates: int = 5
    ) -> List[SelectorCandidate]:
        """为元素生成选择器候选

        Args:
            element: 发现的元素
            max_candidates: 最大候选数

        Returns:
            选择器候选列表
        """
        try:
            candidates = []

            # 1. 基于标签的选择器
            if element.attributes.get("id"):
                candidates.append(SelectorCandidate(
                    selector=f"#{element.attributes['id']}",
                    selector_type=SelectorType.CSS_ID,
                    confidence=1.0,
                    element_count=1,
                    uniqueness=1.0,
                    stability=0.9,
                    description="ID 选择器 (最高优先级)"
                ))

            # 2. 基于类的选择器
            if element.attributes.get("class"):
                classes = element.attributes["class"].split()
                for i, cls in enumerate(classes):
                    selector = ".".join(classes[:i+1])
                    candidates.append(SelectorCandidate(
                        selector=f".{selector}",
                        selector_type=SelectorType.CSS_CLASS,
                        confidence=0.9 - i * 0.1,
                        element_count=1,
                        uniqueness=0.9 - i * 0.1,
                        stability=0.8,
                        description=f"类选择器 ({i+1} 个类)"
                    ))

            # 3. 标签 + 属性选择器
            if element.attributes:
                for attr, value in element.attributes.items():
                    if value and len(value) < 50:
                        candidates.append(SelectorCandidate(
                            selector=f"{element.tag_name}[{attr}='{value}']",
                            selector_type=SelectorType.CSS_ATTRIBUTE,
                            confidence=0.8,
                            element_count=1,
                            uniqueness=0.85,
                            stability=0.8,
                            description=f"属性选择器 ({attr})"
                        ))

            # 4. 标签选择器
            candidates.append(SelectorCandidate(
                selector=element.tag_name,
                selector_type=SelectorType.CSS_TAG,
                confidence=0.6,
                element_count=1,
                uniqueness=0.5,
                stability=0.9,
                description="标签选择器"
            ))

            # 5. XPath 选择器
            candidates.append(SelectorCandidate(
                selector=element.xpath,
                selector_type=SelectorType.XPATH,
                confidence=0.85,
                element_count=1,
                uniqueness=0.9,
                stability=0.7,
                description="XPath 选择器"
            ))

            # 按置信度排序
            candidates.sort(key=lambda x: x.confidence, reverse=True)

            # 限制候选数量
            return candidates[:max_candidates]

        except Exception as e:
            logger.error(f"生成选择器候选失败: {e}")
            return []

    async def validate_selector(
        self,
        page_id: str,
        controller: Any,
        selector: str
    ) -> Dict[str, Any]:
        """验证选择器有效性

        Args:
            page_id: 页面 ID
            controller: Chrome 控制器
            selector: CSS 选择器

        Returns:
            验证结果字典
        """
        try:
            logger.debug(f"验证选择器: {selector}")

            # 执行验证脚本
            result = await controller.execute_script(
                page_id,
                f"""
                const elements = document.querySelectorAll('{selector}');
                return {{
                    count: elements.length,
                    firstElement: elements[0] ? {{
                        tagName: elements[0].tagName,
                        text: elements[0].textContent.substring(0, 100),
                        attributes: Object.keys(elements[0].attributes).length
                    }} : null,
                    isUnique: elements.length === 1,
                    isVisible: elements[0] ? elements[0].offsetParent !== null : false
                }};
                """
            )

            validation_result = {
                "selector": selector,
                "valid": result.get("count", 0) > 0,
                "element_count": result.get("count", 0),
                "unique": result.get("isUnique", False),
                "visible": result.get("isVisible", False),
                "sample": result.get("firstElement", {}),
                "confidence": 1.0 if result.get("isUnique") else 0.7
            }

            logger.debug(f"✓ 选择器验证: {selector} -> {validation_result['element_count']} 个元素")
            return validation_result

        except Exception as e:
            logger.error(f"✗ 选择器验证失败: {e}")
            return {
                "selector": selector,
                "valid": False,
                "error": str(e)
            }

    async def optimize_selectors(
        self,
        page_id: str,
        controller: Any,
        selectors: List[str]
    ) -> List[Dict[str, Any]]:
        """优化选择器列表

        Args:
            page_id: 页面 ID
            controller: Chrome 控制器
            selectors: 选择器列表

        Returns:
            优化后的选择器列表
        """
        try:
            validated_selectors = []

            for selector in selectors:
                validation = await self.validate_selector(
                    page_id, controller, selector
                )

                if validation["valid"]:
                    validated_selectors.append({
                        "selector": selector,
                        "element_count": validation["element_count"],
                        "unique": validation["unique"],
                        "confidence": validation["confidence"],
                        "priority": self._calculate_priority(validation)
                    })

            # 按优先级排序
            validated_selectors.sort(
                key=lambda x: (x["priority"], x["confidence"]),
                reverse=True
            )

            logger.info(f"✓ 选择器优化: {len(selectors)} -> {len(validated_selectors)}")
            return validated_selectors

        except Exception as e:
            logger.error(f"✗ 选择器优化失败: {e}")
            return []

    def _calculate_priority(self, validation: Dict[str, Any]) -> float:
        """计算选择器优先级"""
        priority = 0.0

        # 唯一性加分
        if validation["unique"]:
            priority += 10.0

        # 元素数量加分
        if validation["element_count"] == 1:
            priority += 5.0
        elif validation["element_count"] <= 5:
            priority += 3.0

        # 可见性加分
        if validation.get("visible", False):
            priority += 2.0

        return priority

    def save_discovery_results(
        self,
        page_url: str,
        discovered_elements: Dict[str, List[DiscoveredElement]],
        output_file: Optional[str] = None
    ):
        """保存发现结果

        Args:
            page_url: 页面 URL
            discovered_elements: 发现的数据元素
            output_file: 输出文件路径
        """
        try:
            results = {
                "url": page_url,
                "timestamp": datetime.now().isoformat(),
                "elements": {
                    category: [
                        {
                            "tag_name": e.tag_name,
                            "text": e.text_content[:100],
                            "xpath": e.xpath,
                            "css_selector": e.css_selector,
                            "confidence": e.confidence,
                            "is_table": e.is_table,
                            "is_data_container": e.is_data_container
                        }
                        for e in elements
                    ]
                    for category, elements in discovered_elements.items()
                }
            }

            if output_file:
                import json
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)
                logger.info(f"✓ 发现结果保存到: {output_file}")

            # 存储到内存
            self.discovered_selectors[page_url] = results

        except Exception as e:
            logger.error(f"保存发现结果失败: {e}")

    def get_best_selectors(
        self,
        page_url: str,
        element_type: str = "tables",
        top_n: int = 5
    ) -> List[str]:
        """获取最佳选择器

        Args:
            page_url: 页面 URL
            element_type: 元素类型
            top_n: 返回数量

        Returns:
            最佳选择器列表
        """
        try:
            if page_url not in self.discovered_selectors:
                logger.warning(f"未找到页面发现结果: {page_url}")
                return []

            elements = self.discovered_selectors[page_url]["elements"].get(
                element_type, []
            )

            # 按置信度排序
            sorted_elements = sorted(
                elements,
                key=lambda x: x["confidence"],
                reverse=True
            )

            # 返回前 N 个
            selectors = [
                e["css_selector"]
                for e in sorted_elements[:top_n]
            ]

            logger.info(f"✓ 获取最佳选择器: {len(selectors)} 个")
            return selectors

        except Exception as e:
            logger.error(f"获取最佳选择器失败: {e}")
            return []


# 使用示例
async def main():
    """演示选择器发现功能"""

    print("\n" + "="*70)
    print("HKEX 选择器自动发现演示")
    print("="*70 + "\n")

    # 创建发现引擎
    engine = SelectorDiscoveryEngine()

    # 模拟发现结果
    discovered = {
        "tables": [
            {
                "tag_name": "table",
                "text": "恒生指数 26,433.70",
                "xpath": "//table[1]",
                "css_selector": "table:nth-of-type(1)",
                "confidence": 0.95,
                "is_table": True
            }
        ],
        "containers": [
            {
                "tag_name": "div",
                "text": "市场数据",
                "xpath": "//div[@class='market-data']",
                "css_selector": "div.market-data",
                "confidence": 0.85,
                "is_data_container": True
            }
        ]
    }

    # 保存发现结果
    engine.save_discovery_results(
        "https://www.hkex.com.hk",
        discovered,
        "discovery_results.json"
    )

    # 获取最佳选择器
    best_selectors = engine.get_best_selectors(
        "https://www.hkex.com.hk",
        "tables",
        top_n=3
    )

    print(f"最佳选择器:")
    for selector in best_selectors:
        print(f"  - {selector}")

    print("\n" + "="*70)
    print("演示完成")
    print("="*70)


if __name__ == "__main__":
    from datetime import datetime
    asyncio.run(main())
