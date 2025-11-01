"""
LIHKG 爬蟲系統演示運行
"""
import asyncio
import sys
sys.path.append('.')

from core.parser import PostParser
from core.sentiment import SentimentAnalyzer
from core.storage import LIHKGDataStore

async def demo_run():
    print("\n" + "="*70)
    print("LIHKG 財經台爬蟲與散戶情緒分析 - 演示運行")
    print("="*70)
    
    # 初始化組件
    print("\n[初始化組件]")
    parser = PostParser()
    analyzer = SentimentAnalyzer()
    store = LIHKGDataStore('data/demo_run.db')
    print("+ 帖子解析器: 初始化完成")
    print("+ 情緒分析器: 初始化完成")
    print("+ 數據存儲: 初始化完成")
    
    # 模擬從 LIHKG 爬取的帖子
    print("\n[模擬爬取數據]")
    lihkg_posts = [
        {
            'title': '討論 0700.HK 騰訊 突破新高',
            'content': '騰訊股價今日大漲，突破歷史新高，基本面強勁，建議持續買入，未來還有上漲空間',
            'replies': '128',
            'views': '8650',
            'author': '投資達人2025',
            'time': '2025-10-27 20:15:00',
            'url': 'https://lihkg.com/thread/cat2_001'
        },
        {
            'title': '0388.HK 港交所 最新消息',
            'content': '港交所宣佈新政策，對金融市場有正面影響，短期看好，技術面向好',
            'replies': '65',
            'views': '4320',
            'author': '市場觀察者',
            'time': '2025-10-27 20:10:00',
            'url': 'https://lihkg.com/thread/cat2_002'
        },
        {
            'title': '0939.HK 建設銀行 持續下跌',
            'content': '建行股價持續下跌，市場情緒低迷，建議謹慎操作，或考慮止損',
            'replies': '42',
            'views': '2180',
            'author': '風險管理者',
            'time': '2025-10-27 20:05:00',
            'url': 'https://lihkg.com/thread/cat2_003'
        },
        {
            'title': 'HSI 期貨 今日操作策略',
            'content': '恆生指數期貨震盪整理，等待方向突破，建議觀望或輕倉操作',
            'replies': '28',
            'views': '1650',
            'author': '期貨專家',
            'time': '2025-10-27 20:00:00',
            'url': 'https://lihkg.com/thread/cat15_001'
        }
    ]
    
    print(f"+ 模擬從 category/2 (股票) 爬取: 3 個帖子")
    print(f"+ 模擬從 category/15 (期貨) 爬取: 1 個帖子")
    print(f"+ 總計: {len(lihkg_posts)} 個帖子")
    
    # 解析帖子
    print("\n[解析帖子數據]")
    parsed_posts = []
    for i, raw_post in enumerate(lihkg_posts, 1):
        post = await parser.parse(raw_post)
        parsed_posts.append(post)
        print(f"+ 帖子 {i}: {post['post_id'][:8]}... - 股票: {post['stock_mentions']}")
    
    # 情緒分析
    print("\n[情緒分析]")
    sentiment_results = []
    for i, post in enumerate(parsed_posts, 1):
        sentiment = await analyzer.analyze_post(post)
        sentiment_results.append(sentiment)
        score = sentiment['sentiment_score']
        label = sentiment['sentiment_label']
        intensity = sentiment['intensity']
        print(f"+ 帖子 {i}: {label:8s} (分數: {score:+.3f}, 強度: {intensity:.3f})")
    
    # 保存到資料庫
    print("\n[保存到資料庫]")
    for post, sentiment in zip(parsed_posts, sentiment_results):
        await store.save_post(post, sentiment)
    print(f"+ 成功保存 {len(parsed_posts)} 個帖子到資料庫")
    
    # 查詢統計
    print("\n[統計查詢]")
    stats = await store.get_statistics()
    print(f"+ 總帖子數: {stats['total_posts']}")
    print(f"+ 平均情緒: {stats['average_sentiment']:+.3f}")
    
    sentiment_dist = stats['sentiment_distribution']
    print(f"+ 情緒分佈:")
    print(f"  - 正面: {sentiment_dist.get('positive', 0)} 個")
    print(f"  - 負面: {sentiment_dist.get('negative', 0)} 個")
    print(f"  - 中性: {sentiment_dist.get('neutral', 0)} 個")
    
    # 熱門股票
    print("\n[熱門股票排行]")
    trending = await store.get_trending_stocks(limit=10)
    for i, stock in enumerate(trending, 1):
        code = stock['stock_code']
        mentions = stock['mentions']
        avg_sent = stock['avg_sentiment']
        print(f"+ {i}. {code}: {mentions} 次提及, 平均情緒 {avg_sent:+.3f}")
    
    # 查詢特定股票
    print("\n[查詢特定股票 - 0700.HK]")
    tencent_posts = await store.get_stock_sentiment('0700.HK', days=7)
    print(f"+ 找到 {len(tencent_posts)} 個相關討論")
    if tencent_posts:
        post = tencent_posts[0]
        print(f"  標題: {post['title']}")
        print(f"  情緒: {post['sentiment_label']} ({post['sentiment_score']:+.3f})")
    
    # 總結
    print("\n" + "="*70)
    print("演示運行完成")
    print("="*70)
    print("\n處理流程:")
    print("  [1] 初始化系統組件")
    print("  [2] 爬取 LIHKG 帖子數據")
    print("  [3] 解析帖子內容")
    print("  [4] 進行情緒分析")
    print("  [5] 保存到資料庫")
    print("  [6] 查詢和統計")
    print("\n處理結果:")
    print(f"  + 解析帖子: {len(parsed_posts)} 個")
    print(f"  + 情緒分析: {len(sentiment_results)} 個")
    print(f"  + 數據存儲: {len(parsed_posts)} 條記錄")
    print(f"  + 股票追蹤: {len(trending)} 個股票")
    print("\n系統運行正常，所有功能工作正常！\n")

if __name__ == '__main__':
    asyncio.run(demo_run())
