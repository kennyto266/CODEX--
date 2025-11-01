#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
富途API连接测试 - 编码修复版
解决Windows环境下Unicode字符显示问题
"""

import asyncio
import sys
import os

# 设置UTF-8编码
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from src.trading.futu_trading_api import create_futu_trading_api


async def test_futu_connection():
    """测试富途API连接 - 修复编码问题"""
    print("=" * 60)
    print("富途API连接测试 - 编码修复版")
    print("=" * 60)
    print()

    try:
        # 创建API实例
        futu_api = create_futu_trading_api(
            host='127.0.0.1',
            port=11111,
            trade_password='677750',
            market='HK'
        )
        print(f"[INFO] 正在连接到富途API: {futu_api.host}:{futu_api.port}")

        # 测试连接
        connected = await futu_api.connect()
        if connected:
            print("[SUCCESS] 连接成功!")
            print()

            # 测试身份验证
            print("[INFO] 正在验证交易密码...")
            auth_result = await futu_api.authenticate({'trade_password': '677750'})
            if auth_result:
                print("[SUCCESS] 交易密码验证成功!")
                print()

                # 测试获取账户信息
                print("[INFO] 正在获取账户信息...")
                account = await futu_api.get_account_info()
                if account:
                    print("[SUCCESS] 账户信息获取成功!")
                    print(f"  账户ID: {account.account_id}")
                    print(f"  账户类型: {account.account_type}")
                    print(f"  现金: {account.cash}")
                    print(f"  权益: {account.equity}")
                else:
                    print("[ERROR] 账户信息获取失败!")
            else:
                print("[ERROR] 交易密码验证失败!")
        else:
            print("[ERROR] 连接失败!")

        # 断开连接
        await futu_api.disconnect()
        print()
        print("[INFO] 已断开连接")

    except Exception as e:
        print(f"[ERROR] 发生异常: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Windows控制台编码设置
    if os.name == 'nt':
        os.system('chcp 65001 > nul 2>&1')

    asyncio.run(test_futu_connection())
