#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
分析真實爬蟲結果
"""

import json
import os
from datetime import datetime
from collections import Counter

def analyze_data(file_path):
    """分析數據文件"""
    print("=" * 70)
    print("LIHKG 真實爬蟲數據分析報告")
    print("=" * 70)

    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"\n[1] 基本統計")
    print(f"  總帖子數: {len(data)}")

    # 按板塊分類
    categories = {}
    for post in data:
        cat = post['category']
        categories[cat] = categories.get(cat, 0) + 1

    print(f"  板塊分佈:")
    for cat, count in sorted(categories.items()):
        cat_name = "股票" if cat == 2 else "期貨" if cat == 15 else f"板塊{cat}"
        print(f"    - {cat_name} (category/{cat}): {count} 個")

    print(f"\n[2] 情緒分析")
    sentiments = [p['sentiment_score'] for p in data]
    avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0

    sentiment_dist = Counter([p['sentiment_label'] for p in data])

    print(f"  平均情緒分數: {avg_sentiment:+.3f}")
    print(f"  情緒分佈:")
    for label, count in sentiment_dist.items():
        pct = (count / len(data)) * 100
        label_cn = {"positive": "正面", "negative": "負面", "neutral": "中性"}
        print(f"    - {label_cn.get(label, label)}: {count} 個 ({pct:.1f}%)")

    # 情緒強度排序
    print(f"\n  情緒強度排序:")
    sorted_by_sentiment = sorted(data, key=lambda x: x['sentiment_score'], reverse=True)
    for i, post in enumerate(sorted_by_sentiment[:5], 1):
        print(f"    {i}. {post['post_id']}: {post['sentiment_score']:+.3f} ({post['sentiment_label']})")

    print(f"\n[3] 股票提及統計")
    all_stocks = []
    for post in data:
        all_stocks.extend(post['stock_mentions'])

    stock_counts = Counter(all_stocks)

    if stock_counts:
        print(f"  熱門股票排名:")
        for i, (stock, count) in enumerate(stock_counts.most_common(10), 1):
            # 計算該股票的平均情緒
            stock_sentiments = [p['sentiment_score'] for p in data if stock in p['stock_mentions']]
            avg_stock_sentiment = sum(stock_sentiments) / len(stock_sentiments) if stock_sentiments else 0
            print(f"    {i}. {stock}: {count} 次提及, 平均情緒 {avg_stock_sentiment:+.3f}")
    else:
        print(f"  無股票提及")

    print(f"\n[4] 帖子熱度統計")
    # 按回復數排序
    sorted_by_replies = sorted(data, key=lambda x: x['replies'], reverse=True)
    print(f"  最熱門帖子 (按回復數):")
    for i, post in enumerate(sorted_by_replies[:3], 1):
        print(f"    {i}. {post['post_id']}: {post['replies']} 回復, {post['views']:,} 查閱")

    # 按查閱數排序
    sorted_by_views = sorted(data, key=lambda x: x['views'], reverse=True)
    print(f"  最受關注帖子 (按查閱數):")
    for i, post in enumerate(sorted_by_views[:3], 1):
        print(f"    {i}. {post['post_id']}: {post['views']:,} 查閱, {post['replies']} 回復")

    print(f"\n[5] 關鍵詞分析")
    all_keywords = []
    for post in data:
        all_keywords.extend(post['keywords'])

    keyword_counts = Counter(all_keywords)
    if keyword_counts:
        print(f"  高頻關鍵詞:")
        for i, (keyword, count) in enumerate(keyword_counts.most_common(10), 1):
            print(f"    {i}. {keyword}: {count} 次")

    print(f"\n[6] 板塊對比")
    stock_data = [p for p in data if p['category'] == 2]
    futures_data = [p for p in data if p['category'] == 15]

    if stock_data:
        stock_sentiment = sum(p['sentiment_score'] for p in stock_data) / len(stock_data)
        print(f"  股票板塊:")
        print(f"    - 平均情緒: {stock_sentiment:+.3f}")
        print(f"    - 帖子數: {len(stock_data)}")

    if futures_data:
        futures_sentiment = sum(p['sentiment_score'] for p in futures_data) / len(futures_data)
        print(f"  期貨板塊:")
        print(f"    - 平均情緒: {futures_sentiment:+.3f}")
        print(f"    - 帖子數: {len(futures_data)}")

    print(f"\n[7] 詳細帖子列表")
    print(f"-" * 70)
    for i, post in enumerate(data, 1):
        print(f"\n[{i}] 帖子ID: {post['post_id']}")
        print(f"    板塊: category/{post['category']}")
        print(f"    標題: {post['title']}")
        print(f"    作者: {post['author']}")
        print(f"    回復: {post['replies']} | 查閱: {post['views']:,} | 點讚: {post['likes']}")
        print(f"    股票: {', '.join(post['stock_mentions']) if post['stock_mentions'] else '無'}")
        print(f"    情緒: {post['sentiment_score']:+.3f} ({post['sentiment_label']})")
        print(f"    關鍵詞: {', '.join(post['keywords']) if post['keywords'] else '無'}")

    print(f"\n" + "=" * 70)
    print("分析完成")
    print("=" * 70)


if __name__ == '__main__':
    import glob
    json_files = glob.glob('data/real_lihkg_posts_*.json')
    if json_files:
        latest_file = max(json_files, key=os.path.getctime)
        print(f"分析文件: {latest_file}\n")
        analyze_data(latest_file)
    else:
        print("未找到數據文件")
