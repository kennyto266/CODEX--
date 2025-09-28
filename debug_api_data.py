"""
调试API数据格式
"""

import asyncio
import aiohttp
import json

async def debug_api_data():
    """调试API数据格式"""
    print("🔍 调试API数据格式...")
    
    # 你的股票数据API
    stock_api_url = "http://18.180.162.113:9191/inst/getInst"
    symbol = "0700.hk"
    duration = 1825
    
    try:
        url = f"{stock_api_url}?symbol={symbol}&duration={duration}"
        print(f"📡 请求URL: {url}")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                print(f"📊 响应状态: {response.status}")
                print(f"📊 响应头: {dict(response.headers)}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ 数据获取成功")
                    print(f"📊 数据类型: {type(data)}")
                    print(f"📊 数据长度: {len(str(data))}")
                    print(f"📊 数据内容:")
                    print(json.dumps(data, indent=2, ensure_ascii=False)[:1000] + "..." if len(str(data)) > 1000 else json.dumps(data, indent=2, ensure_ascii=False))
                    
                    # 检查数据结构
                    if isinstance(data, dict):
                        print(f"\n🔍 字典键: {list(data.keys())}")
                        if 'data' in data:
                            print(f"📊 data字段类型: {type(data['data'])}")
                            print(f"📊 data字段长度: {len(data['data']) if isinstance(data['data'], list) else 'N/A'}")
                            if isinstance(data['data'], list) and len(data['data']) > 0:
                                print(f"📊 第一条数据: {data['data'][0]}")
                                print(f"📊 第一条数据类型: {type(data['data'][0])}")
                                if isinstance(data['data'][0], dict):
                                    print(f"📊 第一条数据键: {list(data['data'][0].keys())}")
                else:
                    print(f"❌ 请求失败: HTTP {response.status}")
                    text = await response.text()
                    print(f"📊 错误内容: {text}")
                    
    except Exception as e:
        print(f"❌ 调试出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_api_data())
