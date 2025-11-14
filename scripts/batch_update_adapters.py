#!/usr/bin/env python3
"""
快速批量更新所有政府数据适配器以使用真实数据
"""

import os
from pathlib import Path

def update_adapter_template(adapter_name, config_name, data_file_name, data_field, provider, quality_score=0.95):
    """更新适配器模板"""
    adapter_file = f"src/infrastructure/data_access/adapters/government/{adapter_name}"

    # 读取文件内容
    with open(adapter_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. 添加导入
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

    # 2. 更新配置
    content = content.replace(
        "'use_mock_data': True,",
        "'use_mock_data': False,"
    )

    # 3. 替换真实数据方法
    real_data_method = f'''    async def _fetch_real_data(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """获取真实{config_name}数据"""
        try:
            # 读取真实数据文件
            data_file = Path(__file__).parent.parent.parent.parent.parent / "data" / "real_gov_data" / "{data_file_name}"

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

            logger.info(f"成功加载 {{len(filtered_data)}} 条真实{config_name}数据")
            return filtered_data

        except Exception as e:
            logger.error(f"读取真实{config_name}数据失败: {{str(e)}}, 使用模拟数据")
            return await self._fetch_mock_data(start_date, end_date)'''

    # 查找并替换旧方法
    import re
    pattern = r'async def _fetch_real_data\(self.*?return await self\._fetch_mock_data\(start_date, end_date\)'
    content = re.sub(pattern, real_data_method, content, flags=re.DOTALL)

    # 写回文件
    with open(adapter_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ 更新 {adapter_name} 成功")

def main():
    """批量更新所有适配器"""
    print("开始批量更新政府数据适配器...")

    adapters = [
        ("visitor_adapter.py", "访客", "visitor_data_2025_11.json", "total_visitors", "Tourism Board", 0.94),
        ("retail_adapter.py", "零售销售", "retail_data_2025_11.json", "retail_sales_hkd_millions", "C&SD", 0.96),
        ("trade_adapter.py", "对外贸易", "trade_data_2025_11.json", "total_exports_hkd_billions", "C&SD", 0.97),
    ]

    # 特殊处理hkex和banking适配器（需要特殊字段）
    special_adapters = [
        ("hkex_adapter.py", "港交所交易量", "hkex_data_2025_11.json", "daily_turnover_hkd_billions", "HKEX", 0.98),
        ("banking_adapter.py", "银行利率", "banking_data_2025_11.json", "hibor_overnight", "HKMA", 0.98),
        ("fiscal_adapter.py", "财政收支", "fiscal_data_2025_11.json", "total_revenue_hkd_billions", "HKMA", 0.96),
    ]

    # 首先更新标准适配器
    for adapter_file, config_name, data_file, data_field, provider, quality_score in adapters:
        try:
            update_adapter_template(adapter_file, config_name, data_file, data_field, provider, quality_score)
        except Exception as e:
            print(f"❌ 更新 {adapter_file} 失败: {str(e)}")

    print("\n标准适配器更新完成，开始处理特殊适配器...")

    # 手动更新hkma适配器（适配器文件可能不同名称）
    hkma_files = [
        ("hkma_adapter.py", "hkma_data_2025_11.json", "banking"),
    ]

    for hkma_file, data_file, data_type in hkma_files:
        try:
            hkma_path = f"src/infrastructure/data_access/adapters/government/{hkma_file}"
            if os.path.exists(hkma_path):
                update_adapter_template(hkma_file, "HKMA数据", data_file, "hibor_overnight", "HKMA", 0.98)
            else:
                print(f"⚠️  {hkma_file} 不存在，跳过")
        except Exception as e:
            print(f"❌ 更新 {hkma_file} 失败: {str(e)}")

    print("\n批量更新完成！")

if __name__ == "__main__":
    main()