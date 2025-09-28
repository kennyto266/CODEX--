#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
港股情绪分析代理 (HK Stock Sentiment Analyst)
专注高Sharpe Ratio交易策略的量化情绪分析
"""

import json
import re
import math
from datetime import datetime
from typing import Dict, List, Tuple, Any

class HKSentimentAnalyzer:
    """港股情绪分析代理"""
    
    def __init__(self):
        # 港股情绪关键词词典
        self.positive_keywords = {
            '涨': 0.8, '升': 0.7, '强劲': 0.9, '看好': 0.8, '突破': 0.8,
            '买入': 0.9, '牛市': 1.0, '上涨': 0.8, '利好': 0.9, '增长': 0.7,
            '收益': 0.6, '盈利': 0.8, '成长': 0.7, '机会': 0.6, '推荐': 0.8,
            '腾讯强劲': 0.9, '港股通': 0.6, '北水': 0.7, '资金流入': 0.8
        }
        
        self.negative_keywords = {
            '跌': -0.8, '下跌': -0.8, '暴跌': -1.0, '恐慌': -0.9, '抛售': -0.8,
            '卖出': -0.9, '熊市': -1.0, '亏损': -0.8, '风险': -0.6, '警告': -0.7,
            '贸易战': -0.9, '制裁': -1.0, '地缘': -0.7, '衰退': -0.9, '崩盘': -1.0,
            '资金外流': -0.8, '南水': -0.5, '监管': -0.6, '调整': -0.4
        }
        
        # 港股特定股票代码权重
        self.hk_stock_weights = {
            '0700': 1.2,  # 腾讯
            '0939': 1.1,  # 建设银行  
            '0941': 1.1,  # 中国移动
            '0388': 1.0,  # 港交所
            '2318': 1.1,  # 平安保险
            '1299': 1.0,  # 友邦保险
            '0005': 1.0,  # 汇丰控股
        }
    
    def extract_sentiment_score(self, text: str) -> float:
        """提取单条文本的情绪分数 (-1 to 1)"""
        if not text:
            return 0.0
            
        # 简化的中文分词 (使用字符级别匹配)
        sentiment_score = 0.0
        word_count = 0
        
        # 检查正面关键词
        for keyword, score in self.positive_keywords.items():
            if keyword in text:
                sentiment_score += score
                word_count += 1
                
        # 检查负面关键词  
        for keyword, score in self.negative_keywords.items():
            if keyword in text:
                sentiment_score += score
                word_count += 1
        
        # 标准化分数
        if word_count > 0:
            sentiment_score = sentiment_score / word_count
            
        # 限制在 [-1, 1] 范围内
        return max(-1.0, min(1.0, sentiment_score))
    
    def calculate_volume_weighted_sentiment(self, posts: List[str], volumes: List[float]) -> List[float]:
        """计算成交量加权情绪分数"""
        sentiment_scores = []
        
        for i, post in enumerate(posts):
            base_sentiment = self.extract_sentiment_score(post)
            
            # 成交量权重 (标准化到0.5-1.5倍数)
            if i < len(volumes) and volumes:
                volume_weight = 0.5 + (volumes[i] / max(volumes)) if max(volumes) > 0 else 1.0
                weighted_sentiment = base_sentiment * volume_weight
            else:
                weighted_sentiment = base_sentiment
                
            sentiment_scores.append(max(-1.0, min(1.0, weighted_sentiment)))
            
        return sentiment_scores
    
    def detect_sentiment_bias(self, sentiment_scores: List[float]) -> Dict[str, Any]:
        """识别情绪偏差和异常值"""
        if not sentiment_scores:
            return {"bias_type": "neutral", "extreme_count": 0, "volatility": 0.0}
            
        # 使用纯Python计算统计值
        mean_sentiment = sum(sentiment_scores) / len(sentiment_scores)
        variance = sum((x - mean_sentiment) ** 2 for x in sentiment_scores) / len(sentiment_scores)
        std_sentiment = math.sqrt(variance)
        
        # 识别极端情绪 (< -0.5 或 > 0.8)
        extreme_negative = sum(1 for score in sentiment_scores if score < -0.5)
        extreme_positive = sum(1 for score in sentiment_scores if score > 0.8)
        
        bias_type = "neutral"
        if mean_sentiment > 0.3:
            bias_type = "bullish"
        elif mean_sentiment < -0.3:
            bias_type = "bearish"
            
        return {
            "bias_type": bias_type,
            "extreme_negative": int(extreme_negative),
            "extreme_positive": int(extreme_positive), 
            "volatility": float(std_sentiment),
            "mean_sentiment": float(mean_sentiment)
        }
    
    def calculate_sharpe_contribution(self, sentiment_scores: List[float], volatility: float) -> float:
        """计算情绪对Sharpe Ratio的贡献 (-1 to 1)"""
        if not sentiment_scores:
            return 0.0
            
        mean_sentiment = sum(sentiment_scores) / len(sentiment_scores)
        
        # 情绪稳定性贡献 (低波动率 = 正贡献)
        stability_contribution = max(0, (0.5 - volatility) / 0.5) * 0.4
        
        # 情绪方向贡献 (正面情绪 = 正贡献)
        direction_contribution = mean_sentiment * 0.6
        
        total_contribution = stability_contribution + direction_contribution
        
        return max(-1.0, min(1.0, total_contribution))
    
    def generate_trading_recommendations(self, analysis_result: Dict[str, Any]) -> List[str]:
        """生成交易建议"""
        recommendations = []
        
        avg_score = analysis_result['avg_score']
        bias = analysis_result['sentiment_bias']
        sharpe_contrib = analysis_result['sharpe_contribution']
        
        # 买入建议
        if avg_score > 0.5 and bias['extreme_negative'] == 0:
            recommendations.append("🟢 买入信号：情绪持续正面，建议逐步建仓优质港股")
            
        if sharpe_contrib > 0.3:
            recommendations.append("📈 风险调整收益良好：情绪稳定支撑高Sharpe策略")
            
        # 卖出/规避建议
        if avg_score < -0.5 or bias['extreme_negative'] > 2:
            recommendations.append("🔴 规避信号：负面情绪浓厚，建议减仓或观望")
            
        if bias['volatility'] > 0.6:
            recommendations.append("⚠️ 情绪波动风险：建议降低仓位控制回撤")
            
        # 中性建议
        if -0.2 <= avg_score <= 0.2:
            recommendations.append("🟡 中性观望：情绪分歧明显，等待明确信号")
            
        # 特殊情况
        if bias['extreme_positive'] > 3:
            recommendations.append("⚡ 情绪过热警告：注意追涨风险，考虑分批获利了结")
            
        return recommendations[:5]  # 限制在5条以内
    
    def analyze_hk_stock_sentiment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """主分析函数"""
        
        # 提取输入数据
        stock_code = data.get('stock', '')
        posts = data.get('posts', [])
        volumes = data.get('volumes', [])
        dates = data.get('dates', [f"2024-09-{28-i}" for i in range(len(posts))])
        
        # 1. 计算情绪分数
        sentiment_scores = self.calculate_volume_weighted_sentiment(posts, volumes)
        
        # 2. 识别情绪偏差
        sentiment_bias = self.detect_sentiment_bias(sentiment_scores)
        
        # 3. 计算平均情绪
        avg_score = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
        
        # 4. 评估Sharpe贡献
        sharpe_contribution = self.calculate_sharpe_contribution(
            sentiment_scores, sentiment_bias['volatility']
        )
        
        # 5. 生成分析结果
        analysis_result = {
            'avg_score': avg_score,
            'sentiment_bias': sentiment_bias,
            'sharpe_contribution': sharpe_contribution
        }
        
        # 6. 生成交易建议
        recommendations = self.generate_trading_recommendations(analysis_result)
        
        # 构建最终输出
        result = {
            "stock_code": stock_code,
            "analysis_date": datetime.now().strftime("%Y-%m-%d"),
            "sentiment_scores": [
                {"date": dates[i] if i < len(dates) else f"day_{i}", 
                 "score": round(score, 3)} 
                for i, score in enumerate(sentiment_scores)
            ],
            "avg_score": round(avg_score, 3),
            "sentiment_bias": {
                "type": sentiment_bias['bias_type'],
                "volatility": round(sentiment_bias['volatility'], 3),
                "extreme_negative_count": sentiment_bias['extreme_negative'],
                "extreme_positive_count": sentiment_bias['extreme_positive']
            },
            "sharpe_contribution": round(sharpe_contribution, 3),
            "recommendations": recommendations,
            "risk_assessment": {
                "overall_risk": "HIGH" if sentiment_bias['volatility'] > 0.6 else "MEDIUM" if sentiment_bias['volatility'] > 0.3 else "LOW",
                "sentiment_contagion_risk": "HIGH" if abs(avg_score) > 0.7 else "MEDIUM",
                "drawdown_risk": "HIGH" if sentiment_bias['extreme_negative'] > 2 else "LOW"
            }
        }
        
        return result

def main():
    """示例运行"""
    analyzer = HKSentimentAnalyzer()
    
    # 示例数据
    sample_data = {
        "stock": "0700.HK",
        "posts": [
            "腾讯强劲成长！Q3业绩超预期，游戏收入大涨",
            "港股通资金大幅流入腾讯，北水看好科技股",
            "市场恐慌情绪蔓延，科技股全线下跌", 
            "腾讯云业务增长强劲，AI概念持续发酵",
            "美股科技股暴跌，港股科技股承压"
        ],
        "volumes": [15000000, 12000000, 8000000, 18000000, 6000000],
        "dates": ["2024-09-24", "2024-09-25", "2024-09-26", "2024-09-27", "2024-09-28"]
    }
    
    result = analyzer.analyze_hk_stock_sentiment(sample_data)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()