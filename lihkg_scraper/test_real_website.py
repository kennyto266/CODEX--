#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
測試真實可爬取的網站
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re

async def test_scrapable_website():
    """測試一個真正可以爬取的網站"""
    print("=" * 60)
    print("測試真實可爬取的網站")
    print("=" * 60)

    # 使用一個公開的測試網站
    test_urls = [
        "https://httpbin.org/html",
        "https://example.com",
        "https://www.w3schools.com/xml/xml_dom.asp",
    ]

    async with aiohttp.ClientSession() as session:
        for url in test_urls:
            print(f"\n[測試] {url}")
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')

                        # 提取基本信息
                        title = soup.title.string if soup.title else "無標題"
                        text_content = soup.get_text(strip=True)[:200]

                        print(f"  [OK] 狀態: {response.status}")
                        print(f"  [OK] 標題: {title}")
                        print(f"  [OK] 內容長度: {len(html)} 字節")
                        print(f"  [OK] 文本內容: {text_content[:100]}...")

                        # 如果是論壇類網站，嘗試提取帖子
                        posts = soup.find_all(['article', 'div', 'li'], class_=re.compile(r'post|thread|item'))
                        if posts:
                            print(f"  [OK] 找到 {len(posts)} 個可能的帖子")
                        else:
                            print(f"  [-] 未找到帖子結構")

                    else:
                        print(f"  [FAIL] HTTP {response.status}")

            except Exception as e:
                print(f"  [ERROR] 錯誤: {e}")

    print("\n" + "=" * 60)
    print("測試完成")
    print("=" * 60)

if __name__ == '__main__':
    asyncio.run(test_scrapable_website())
