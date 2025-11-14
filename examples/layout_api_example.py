"""
Layout API Usage Example
布局API使用示例
演示如何使用LayoutConfig CRUD API
"""

import requests
import json
from typing import Dict, Any

# API基础URL
BASE_URL = "http://localhost:8001/api/v1"


def create_layout_example():
    """创建布局示例"""
    print("\n" + "="*60)
    print("1. 创建布局示例")
    print("="*60)

    layout_data = {
        "name": "我的自定义布局",
        "description": "包含价格图表、技术指标和投资组合的布局",
        "version": "1.0.0",
        "components": [
            {
                "id": "price_chart",
                "type": "price_chart",
                "title": "股价走势图",
                "position": {
                    "x": 0,
                    "y": 0,
                    "w": 6,
                    "h": 4
                },
                "properties": {
                    "symbol": "0700.HK",
                    "period": "1d",
                    "show_ma": True
                }
            },
            {
                "id": "technical_indicators",
                "type": "technical_indicators",
                "title": "技术指标",
                "position": {
                    "x": 6,
                    "y": 0,
                    "w": 6,
                    "h": 4
                },
                "properties": {
                    "indicators": ["kdj", "rsi", "macd"],
                    "period": 14
                }
            },
            {
                "id": "portfolio_summary",
                "type": "portfolio_summary",
                "title": "投资组合概览",
                "position": {
                    "x": 0,
                    "y": 4,
                    "w": 4,
                    "h": 3
                },
                "properties": {
                    "show_pnl": True,
                    "show_allocation": True
                }
            },
            {
                "id": "recent_trades",
                "type": "recent_trades",
                "title": "最近交易",
                "position": {
                    "x": 4,
                    "y": 4,
                    "w": 4,
                    "h": 3
                },
                "properties": {
                    "limit": 10,
                    "show_details": True
                }
            },
            {
                "id": "performance_chart",
                "type": "performance_chart",
                "title": "策略绩效",
                "position": {
                    "x": 8,
                    "y": 4,
                    "w": 4,
                    "h": 3
                },
                "properties": {
                    "metrics": ["return", "sharpe", "drawdown"],
                    "period": "1y"
                }
            }
        ],
        "theme": {
            "primary_color": "#1976d2",
            "background_color": "#ffffff",
            "text_color": "#333333",
            "grid_color": "#e0e0e0"
        },
        "is_default": False,
        "user_id": "user123"
    }

    try:
        response = requests.post(
            f"{BASE_URL}/layout",
            json=layout_data,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 201:
            result = response.json()
            print(f"✓ 布局创建成功!")
            print(f"  布局ID: {result['id']}")
            print(f"  布局名称: {result['name']}")
            print(f"  组件数量: {len(result['components'])}")
            print(f"  版本: {result['version']}")
            return result['id']
        else:
            print(f"✗ 布局创建失败: {response.status_code}")
            print(f"  错误信息: {response.text}")
            return None
    except Exception as e:
        print(f"✗ 请求异常: {str(e)}")
        return None


def get_all_layouts_example():
    """获取所有布局示例"""
    print("\n" + "="*60)
    print("2. 获取所有布局示例")
    print("="*60)

    try:
        response = requests.get(
            f"{BASE_URL}/layout",
            params={
                "page": 1,
                "size": 10,
                "sort_by": "created_at",
                "sort_order": "desc"
            }
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✓ 获取布局列表成功!")
            print(f"  总数: {result['total']}")
            print(f"  当前页: {result['page']}")
            print(f"  每页数量: {result['size']}")
            print(f"  当前页布局数量: {len(result['items'])}")
            print("\n布局列表:")
            for item in result['items']:
                print(f"  - {item['name']} (ID: {item['id'][:8]}...)")
                print(f"    版本: {item['version']}, 默认: {item['is_default']}")
            return result['items']
        else:
            print(f"✗ 获取布局列表失败: {response.status_code}")
            print(f"  错误信息: {response.text}")
            return []
    except Exception as e:
        print(f"✗ 请求异常: {str(e)}")
        return []


def get_layout_by_id_example(layout_id: str):
    """获取指定布局示例"""
    print("\n" + "="*60)
    print("3. 获取指定布局示例")
    print("="*60)

    if not layout_id:
        print("✗ 无效的布局ID")
        return None

    try:
        response = requests.get(f"{BASE_URL}/layout/{layout_id}")

        if response.status_code == 200:
            result = response.json()
            print(f"✓ 获取布局成功!")
            print(f"  布局ID: {result['id']}")
            print(f"  布局名称: {result['name']}")
            print(f"  描述: {result['description']}")
            print(f"  版本: {result['version']}")
            print(f"  是否默认: {result['is_default']}")
            print(f"  是否激活: {result['is_active']}")
            print(f"  使用次数: {result['usage_count']}")
            print(f"  创建时间: {result['created_at']}")
            print(f"  更新时间: {result['updated_at']}")
            print(f"\n组件列表 ({len(result['components'])}个):")
            for comp in result['components']:
                print(f"  - {comp['title']} ({comp['type']})")
                print(f"    位置: x={comp['position']['x']}, y={comp['position']['y']}, "
                      f"w={comp['position']['w']}, h={comp['position']['h']}")
            print(f"\n主题配置:")
            for key, value in result['theme'].items():
                print(f"  - {key}: {value}")
            return result
        else:
            print(f"✗ 获取布局失败: {response.status_code}")
            print(f"  错误信息: {response.text}")
            return None
    except Exception as e:
        print(f"✗ 请求异常: {str(e)}")
        return None


def update_layout_example(layout_id: str):
    """更新布局示例"""
    print("\n" + "="*60)
    print("4. 更新布局示例")
    print("="*60)

    if not layout_id:
        print("✗ 无效的布局ID")
        return None

    update_data = {
        "name": "更新后的布局名称",
        "description": "更新后的布局描述",
        "version": "1.1.0",
        "is_default": True
    }

    try:
        response = requests.put(
            f"{BASE_URL}/layout/{layout_id}",
            json=update_data
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✓ 布局更新成功!")
            print(f"  布局ID: {result['id']}")
            print(f"  新名称: {result['name']}")
            print(f"  新描述: {result['description']}")
            print(f"  新版本: {result['version']}")
            print(f"  是否默认: {result['is_default']}")
            return result
        else:
            print(f"✗ 布局更新失败: {response.status_code}")
            print(f"  错误信息: {response.text}")
            return None
    except Exception as e:
        print(f"✗ 请求异常: {str(e)}")
        return None


def apply_layout_example(layout_id: str):
    """应用布局示例"""
    print("\n" + "="*60)
    print("5. 应用布局示例")
    print("="*60)

    if not layout_id:
        print("✗ 无效的布局ID")
        return None

    try:
        response = requests.post(f"{BASE_URL}/layout/{layout_id}/apply")

        if response.status_code == 200:
            result = response.json()
            print(f"✓ 布局应用成功!")
            print(f"  布局ID: {result['layout_id']}")
            print(f"  消息: {result['message']}")
            print(f"  当前使用次数: {result['usage_count']}")
            return result
        else:
            print(f"✗ 布局应用失败: {response.status_code}")
            print(f"  错误信息: {response.text}")
            return None
    except Exception as e:
        print(f"✗ 请求异常: {str(e)}")
        return None


def delete_layout_example(layout_id: str):
    """删除布局示例"""
    print("\n" + "="*60)
    print("6. 删除布局示例")
    print("="*60)

    if not layout_id:
        print("✗ 无效的布局ID")
        return False

    try:
        response = requests.delete(f"{BASE_URL}/layout/{layout_id}")

        if response.status_code == 200:
            result = response.json()
            print(f"✓ 布局删除成功!")
            print(f"  消息: {result['message']}")
            return True
        else:
            print(f"✗ 布局删除失败: {response.status_code}")
            print(f"  错误信息: {response.text}")
            return False
    except Exception as e:
        print(f"✗ 请求异常: {str(e)}")
        return False


def main():
    """主函数"""
    print("\n" + "="*60)
    print("LayoutConfig API CRUD 操作示例")
    print("="*60)

    # 检查API服务是否运行
    print("\n检查API服务...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code == 200:
            print("✓ API服务运行正常")
        else:
            print("✗ API服务状态异常")
            return
    except requests.exceptions.RequestException:
        print("✗ 无法连接到API服务 (http://localhost:8001)")
        print("  请确保API服务已启动")
        return

    # 1. 创建布局
    layout_id = create_layout_example()

    # 2. 获取所有布局
    layouts = get_all_layouts_example()

    # 3. 获取指定布局
    if layout_id:
        get_layout_by_id_example(layout_id)

    # 4. 更新布局
    if layout_id:
        update_layout_example(layout_id)

    # 5. 应用布局
    if layout_id:
        apply_layout_example(layout_id)

    # 6. 删除布局
    # 注意：不要删除默认布局
    if layout_id:
        # 先确保不是默认布局
        get_response = requests.get(f"{BASE_URL}/layout/{layout_id}")
        if get_response.status_code == 200:
            layout = get_response.json()
            if not layout['is_default']:
                delete_layout_example(layout_id)
            else:
                print("\n" + "="*60)
                print("6. 删除布局示例")
                print("="*60)
                print("⚠ 跳过删除：当前布局是默认布局，不能删除")

    print("\n" + "="*60)
    print("示例演示完成!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
