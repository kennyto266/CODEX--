"""
数据格式化模块
提供数据验证、清洗和转换功能
"""

from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DataFormatter:
    """数据格式化器"""
    
    @staticmethod
    def validate_stock_data(data: List[Dict[str, Any]]) -> bool:
        """
        验证股票数据格式
        
        Args:
            data: 股票数据列表
            
        Returns:
            数据是否有效
        """
        if not data or not isinstance(data, list):
            return False
        
        required_fields = ['symbol', 'timestamp', 'open', 'high', 'low', 'close', 'volume']
        
        for item in data:
            if not isinstance(item, dict):
                return False
            
            for field in required_fields:
                if field not in item:
                    return False
            
            # 验证数值字段
            numeric_fields = ['open', 'high', 'low', 'close', 'volume']
            for field in numeric_fields:
                if not isinstance(item[field], (int, float)) or item[field] < 0:
                    return False
        
        return True
    
    @staticmethod
    def clean_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        清洗数据，移除异常值
        
        Args:
            data: 原始数据列表
            
        Returns:
            清洗后的数据列表
        """
        cleaned_data = []
        
        for item in data:
            # 检查价格合理性
            if (item['high'] >= item['low'] and 
                item['open'] >= 0 and 
                item['close'] >= 0 and
                item['volume'] >= 0):
                cleaned_data.append(item)
            else:
                logger.warning(f"跳过异常数据: {item}")
        
        return cleaned_data
    
    @staticmethod
    def calculate_technical_indicators(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        计算技术指标
        
        Args:
            data: 股票数据列表
            
        Returns:
            包含技术指标的数据列表
        """
        if len(data) < 2:
            return data
        
        # 计算移动平均线
        for i, item in enumerate(data):
            if i >= 4:  # 5日移动平均线
                ma5 = sum(data[i-4:i+1][j]['close'] for j in range(5)) / 5
                item['ma5'] = round(ma5, 2)
            
            if i >= 9:  # 10日移动平均线
                ma10 = sum(data[i-9:i+1][j]['close'] for j in range(10)) / 10
                item['ma10'] = round(ma10, 2)
            
            # 计算RSI (简化版)
            if i >= 13:  # 14日RSI
                gains = []
                losses = []
                for j in range(i-13, i+1):
                    if j > 0:
                        change = data[j]['close'] - data[j-1]['close']
                        if change > 0:
                            gains.append(change)
                            losses.append(0)
                        else:
                            gains.append(0)
                            losses.append(abs(change))
                
                avg_gain = sum(gains) / len(gains) if gains else 0
                avg_loss = sum(losses) / len(losses) if losses else 0
                
                if avg_loss == 0:
                    rsi = 100
                else:
                    rs = avg_gain / avg_loss
                    rsi = 100 - (100 / (1 + rs))
                
                item['rsi'] = round(rsi, 2)
        
        return data
    
    @staticmethod
    def get_summary_stats(data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        获取数据摘要统计
        
        Args:
            data: 股票数据列表
            
        Returns:
            摘要统计信息
        """
        if not data:
            return {}
        
        prices = [item['close'] for item in data]
        volumes = [item['volume'] for item in data]
        
        return {
            "total_days": len(data),
            "current_price": prices[-1],
            "price_change": prices[-1] - prices[0] if len(prices) > 1 else 0,
            "price_change_pct": ((prices[-1] - prices[0]) / prices[0] * 100) if len(prices) > 1 and prices[0] != 0 else 0,
            "highest_price": max(prices),
            "lowest_price": min(prices),
            "avg_volume": sum(volumes) / len(volumes),
            "total_volume": sum(volumes),
            "symbol": data[0]['symbol'] if data else None,
            "date_range": {
                "start": data[0]['timestamp'] if data else None,
                "end": data[-1]['timestamp'] if data else None
            }
        }
