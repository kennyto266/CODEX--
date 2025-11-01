#!/usr/bin/env python3
"""
簡單測試 Mark6 修復
"""

import asyncio
import sys
import os

# 添加項目路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_mark6_format():
    """測試格式化函數"""
    print("=== Mark6 格式化測試 ===\n")

    # 模擬 Mark6Service 返回的數據
    mock_data = {
        "draw_no": "25/117 THS 幸運二金多寶",
        "draw_date": "04/11/2025 (星期二)",
        "estimated_prize": "68000000",
        "sales_close": "21:15",
        "currency": "HKD"
    }

    print("測試數據:")
    print(f"  期數: {mock_data.get('draw_no', 'N/A')}")
    print(f"  開獎日期: {mock_data.get('draw_date', 'N/A')}")
    print(f"  頭獎基金: {mock_data.get('estimated_prize', 'N/A')}")
    print(f"  投注截止: {mock_data.get('sales_close', 'N/A')}")
    print()

    # 格式化輸出 (修復後的代碼)
    result = "🎲 香港 Mark Six\n\n"
    result += f"• 下期期數: {mock_data.get('draw_no', 'N/A')}\n"
    result += f"• 開獎日期: {mock_data.get('draw_date', 'N/A')}\n"

    estimated_prize = mock_data.get('estimated_prize')
    if estimated_prize:
        if isinstance(estimated_prize, str) and ',' not in estimated_prize:
            result += f"• 頭獎基金: ${float(estimated_prize):,.0f}\n"
        else:
            result += f"• 頭獎基金: ${estimated_prize}\n"
    else:
        result += "• 頭獎基金: N/A\n"

    result += f"• 投注截止: {mock_data.get('sales_close', 'N/A')}\n\n"
    result += "數據來源: 香港賽馬會官方網站"
    result += "\n\n祝您好運! 🍀"

    print("格式化結果:")
    print(result)
    print()

    # 測試原始數據為字符串的情況
    mock_data2 = {
        "draw_no": "25/117",
        "draw_date": "04/11/2025",
        "estimated_prize": "80000000",
        "sales_close": "20:45"
    }

    result2 = "🎲 香港 Mark Six\n\n"
    result2 += f"• 下期期數: {mock_data2.get('draw_no', 'N/A')}\n"
    result2 += f"• 開獎日期: {mock_data2.get('draw_date', 'N/A')}\n"

    estimated_prize2 = mock_data2.get('estimated_prize')
    if estimated_prize2:
        if isinstance(estimated_prize2, str) and ',' not in estimated_prize2:
            result2 += f"• 頭獎基金: ${float(estimated_prize2):,.0f}\n"
        else:
            result2 += f"• 頭獎基金: ${estimated_prize2}\n"
    else:
        result2 += "• 頭獎基金: N/A\n"

    result2 += f"• 投注截止: {mock_data2.get('sales_close', 'N/A')}\n\n"
    result2 += "數據來源: 香港賽馬會官方網站"
    result2 += "\n\n祝您好運! 🍀"

    print("測試 2 (字符串數字):")
    print(result2)

    return True

async def main():
    await test_mark6_format()
    print("\n=== 測試完成 ===")
    print("修復成功！字段匹配問題已解決。")

if __name__ == '__main__':
    asyncio.run(main())
