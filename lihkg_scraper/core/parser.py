"""
LIHKG 帖子解析器
解析帖子數據、提取股票代碼、標籤等
"""

import re
import logging
from typing import List, Dict
from datetime import datetime

logger = logging.getLogger('lihkg_scraper.parser')

class PostParser:
    """
    解析 LIHKG 帖子數據
    提取標題、內容、作者、回復等關鍵信息
    """
    
    def __init__(self):
        # 股票代碼正則表達式 (XXXX.HK)
        self.stock_code_pattern = re.compile(r'\b(\d{4})\.HK\b')
        
        # 標籤正則表達式 [標籤]
        self.tag_pattern = re.compile(r'\[(.*?)\]')
        
        # 數字提取正則
        self.number_pattern = re.compile(r'[\d,]+')
        
    async def parse(self, raw_data: Dict) -> Dict:
        """
        解析原始數據
        
        Args:
            raw_data: 從頁面提取的原始數據
            
        Returns:
            dict: 結構化的帖子數據
        """
        try:
            post = {
                'post_id': self.extract_post_id(raw_data),
                'title': self.clean_text(raw_data.get('title', '')),
                'content': self.clean_text(raw_data.get('content', '')),
                'author': raw_data.get('author', ''),
                'replies': self.extract_number(raw_data.get('replies', '0')),
                'views': self.extract_number(raw_data.get('views', '0')),
                'likes': self.extract_number(raw_data.get('likes', '0')),
                'post_time': self.parse_time(raw_data.get('time', '')),
                'tags': self.extract_tags(raw_data.get('title', '')),
                'stock_mentions': self.extract_stock_codes(raw_data),
                'created_at': datetime.now().isoformat()
            }
            
            logger.debug(f"解析帖子: {post['post_id']}")
            return post
            
        except Exception as e:
            logger.error(f"解析帖子失敗: {e}, 數據: {raw_data}")
            raise
    
    def extract_post_id(self, data: Dict) -> str:
        """
        提取帖子 ID
        
        Args:
            data: 原始數據
            
        Returns:
            str: 帖子 ID
        """
        # 嘗試從 URL 或數據中提取 ID
        url = data.get('url', '')
        if 'thread/' in url:
            return url.split('thread/')[-1].split('?')[0]
        
        return data.get('post_id', '')
    
    def clean_text(self, text: str) -> str:
        """
        清洗文本
        
        Args:
            text: 原始文本
            
        Returns:
            str: 清洗後的文本
        """
        if not text:
            return ''
        
        # 移除多餘空白
        text = re.sub(r'\s+', ' ', text.strip())
        
        # 移除特殊字符
        text = re.sub(r'[\x00-\x1F\x7F]', '', text)
        
        return text
    
    def extract_number(self, text: str) -> int:
        """
        提取數字
        
        Args:
            text: 包含數字的文本
            
        Returns:
            int: 數字值
        """
        if not text:
            return 0
        
        # 移除逗號並轉換為數字
        match = self.number_pattern.search(str(text))
        if match:
            return int(match.group().replace(',', ''))
        
        return 0
    
    def parse_time(self, time_str: str) -> str:
        """
        解析時間字符串
        
        Args:
            time_str: 時間字符串
            
        Returns:
            str: ISO 格式時間
        """
        if not time_str:
            return datetime.now().isoformat()
        
        try:
            # 這裡需要根據 LIHKG 的時間格式進行調整
            # 示例格式: "2025-10-27 19:30:00"
            dt = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
            return dt.isoformat()
        except Exception as e:
            logger.warning(f"時間解析失敗: {time_str}, 錯誤: {e}")
            return datetime.now().isoformat()
    
    def extract_stock_codes(self, data: Dict) -> List[str]:
        """
        提取股票代碼
        
        Args:
            data: 帖子數據
            
        Returns:
            list: 股票代碼列表
        """
        # 合併標題和內容進行匹配
        text = f"{data.get('title', '')} {data.get('content', '')}"
        
        # 查找所有股票代碼
        matches = self.stock_code_pattern.findall(text)
        
        # 添加 .HK 後綴
        stock_codes = [f"{match}.HK" for match in matches]
        
        logger.debug(f"提取股票代碼: {stock_codes}")
        return stock_codes
    
    def extract_tags(self, text: str) -> List[str]:
        """
        提取標籤
        
        Args:
            text: 文本內容
            
        Returns:
            list: 標籤列表
        """
        if not text:
            return []
        
        tags = self.tag_pattern.findall(text)
        
        logger.debug(f"提取標籤: {tags}")
        return tags
    
    def validate_post(self, post: Dict) -> bool:
        """
        驗證帖子數據
        
        Args:
            post: 帖子數據
            
        Returns:
            bool: 是否有效
        """
        required_fields = ['post_id', 'title']
        
        for field in required_fields:
            if not post.get(field):
                logger.warning(f"缺少必需字段: {field}")
                return False
        
        return True
