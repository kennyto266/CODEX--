#!/usr/bin/env python3
"""
批量更新政府数据适配器使用真实数据
"""

import json
from pathlib import Path
import re

def update_adapter(adapter_file: str, source_id: str, data_field: str, quality_score: float = 0.95):
    """更新单个适配器文件"""
    try:
        with open(adapter_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 1. 添加必要的导入
        if 'import json' not in content:
            content = content.replace(
                'import asyncio\nimport logging',
                'import asyncio\nimport json\nimport logging'
            )

        if 'from pathlib import Path' not in content:
            content = content.replace(
                'from datetime import',
                'from pathlib import Path\nfrom datetime import'
            )

        # 2. 更新use_mock_data配置
        content = re.sub(
            r"'use_mock_data':\s*True,",
            "'use_mock_data': False,",
            content
        )

        # 3. 替换_fetch_real_data方法
        old_method = r'async def _fetch_real_data\(self.*?return await self\._fetch_mock_data\(start_date, end_date\)'
        new_method = f'''async def _fetch_real_data(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """获取真实{source_id}数据"""
        try:
            # 读取真实数据文件
            data_file = Path(__file__).parent.parent.parent.parent.parent / "data" / "real_gov_data" / "{source_id}_data_2025_11.json"

            if not data_file.exists():
                logger.warning(f"数据文件不存在: {{data_file}}, 使用模拟数据")
                return await self._fetch_mock_data(start_date, end_date)

            with open(data_file, 'r', encoding='utf-8') as f:
                real_data = json.load(f)

            # 过滤日期范围
            filtered_data = []
            for item in real_data:
                item_date = datetime.fromisoformat(item['timestamp']).date()
                if start_date <= item_date <= end_date:
                    filtered_data.append({{
                        'timestamp': datetime.fromisoformat(item['timestamp']),
                        'value': item['{data_field}'],
                        'quality_score': item.get('quality_score', {quality_score})
                    }})

            logger.info(f"成功加载 {{len(filtered_data)}} 条真实{source_id}数据")
            return filtered_data

        except Exception as e:
            logger.error(f"读取真实{source_id}数据失败: {{str(e)}}, 使用模拟数据")
            return await self._fetch_mock_data(start_date, end_date)'''

        content = re.sub(old_method, new_method, content, flags=re.DOTALL)

        # 写回文件
        with open(adapter_file, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✅ 更新 {source_id} 适配器成功")
        return True

    except Exception as e:
        print(f"❌ 更新 {source_id} 适配器失败: {str(e)}")
        return False

def main():
    """批量更新所有适配器"""
    base_path = Path("src/infrastructure/data_access/adapters/government")

    # 需要更新的适配器配置
    adapters = [
        ("property_adapter.py", "property", "price_index", 0.95),
        ("visitor_adapter.py", "visitor", "total_visitors", 0.94),
        ("retail_adapter.py", "retail", "retail_sales_hkd_millions", 0.96),
        ("trade_adapter.py", "trade", "total_exports_hkd_billions", 0.97),
        # 特殊处理hkex和banking (它们有多个数据字段)
    ]

    print("开始批量更新政府数据适配器...")

    success_count = 0
    for adapter_file, source_id, data_field, quality_score in adapters:
        if update_adapter(base_path / adapter_file, source_id, data_field, quality_score):
            success_count += 1

    print(f"\n更新完成: {success_count}/{len(adapters)} 个适配器成功更新")

if __name__ == "__main__":
    main()