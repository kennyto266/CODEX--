"""
简易网页搜索工具（无API key）。
实现 DuckDuckGo HTML 搜索的轻量抓取，返回标题与链接。
在网络不可用时，返回基于查询的占位建议。
"""

from typing import List, Dict
import re
import urllib.parse
import requests


def web_search(query: str, max_results: int = 5, timeout: int = 10) -> List[Dict[str, str]]:
    """执行简易搜索，返回[{title, url}]."""
    try:
        q = urllib.parse.quote_plus(query)
        url = f"https://duckduckgo.com/html/?q={q}"
        resp = requests.get(url, timeout=timeout, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        })
        if resp.status_code != 200:
            return _fallback(query)

        html = resp.text
        # 粗略解析结果：<a rel="nofollow" class="result__a" href="...">Title</a>
        items: List[Dict[str, str]] = []
        for m in re.finditer(r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html, re.I | re.S):
            url = re.sub(r"&amp;", "&", m.group(1))
            title = re.sub("<.*?>", "", m.group(2))
            title = re.sub(r"\s+", " ", title).strip()
            if title and url:
                items.append({"title": title, "url": url})
            if len(items) >= max_results:
                break
        return items or _fallback(query)
    except Exception:
        return _fallback(query)


def _fallback(query: str) -> List[Dict[str, str]]:
    return [
        {"title": f"Research idea for: {query}", "url": "https://scholar.google.com/"},
        {"title": "HKEX news", "url": "https://www.hkex.com.hk/News"},
    ]


