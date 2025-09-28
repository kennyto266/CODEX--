#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
港股情绪分析代理 (HK Stock Sentiment Analyst)
专注于高Sharpe Ratio交易策略的量化情绪分析系统
"""

import json
import re
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Any
import jieba
import jieba.analyse


class HKSentimentAnalyzer:
    """港股情绪分析代理"""
    
    def __init__(self):
        """初始化情绪分析器"""
        # 港股相关正面关键词
        self.positive_keywords = {
            '涨': 0.8, '升': 0.7, '强劲': 0.9, '看好': 0.8, '突破': 0.8,
            '牛市': 1.0, '利好': 0.9, '增长': 0.7, '上涨': 0.8, '买入': 0.9,
            '腾讯': 0.6, '阿里': 0.6, '美团': 0.6, '建设银行': 0.5, '中移动': 0.5,
            '恒指': 0.5, '港股': 0.3, '成交量': 0.4, '资金': 0.4, '机构': 0.5
        }
        
        # 港股相关负面关键词
        self.negative_keywords = {
            '跌': -0.8, '跌停': -1.0, '暴跌': -1.0, '恐慌': -0.9, '抛售': -0.8,
            '熊市': -1.0, '利空': -0.9, '下跌': -0.8, '卖出': -0.9, '崩盘': -1.0,
            '贸易战': -0.7, '制裁': -0.8, '地缘': -0.6, '风险': -0.5, '担忧': -0.6,
            '调整': -0.4, '回调': -0.3, '震荡': -0.2, '不确定': -0.5
        }
        
        # 情绪波动权重（用于Sharpe Ratio计算）
        self.volatility_weights = {
            'extreme_positive': 0.3,  # 极端正面情绪增加波动
            'moderate_positive': 0.1,
            'neutral': 0.05,
            'moderate_negative': 0.2,
            'extreme_negative': 0.4   # 极端负面情绪大幅增加波动
        }
    
    def preprocess_text(self, text: str) -> List[str]:
        """文本预处理和分词"""
        # 清理文本
        text = re.sub(r'[^\u4e00-\u9fff\w\s]', '', text)
        # 使用jieba分词
        words = jieba.lcut(text)
        return [word for word in words if len(word) > 1]
    
    def calculate_sentiment_score(self, text: str) -> float:
        """计算单条文本的情绪分数 (-1 to 1)"""
        words = self.preprocess_text(text)
        total_score = 0.0
        word_count = 0
        
        for word in words:
            if word in self.positive_keywords:
                total_score += self.positive_keywords[word]
                word_count += 1
            elif word in self.negative_keywords:
                total_score += self.negative_keywords[word]
                word_count += 1
        
        if word_count == 0:
            return 0.0
        
        # 归一化到 [-1, 1] 区间
        avg_score = total_score / word_count
        return max(-1.0, min(1.0, avg_score))
    
    def categorize_sentiment(self, score: float) -> str:
        """情绪分类"""
        if score >= 0.7:
            return 'extreme_positive'
        elif score >= 0.3:
            return 'moderate_positive'
        elif score >= -0.3:
            return 'neutral'
        elif score >= -0.7:
            return 'moderate_negative'
        else:
            return 'extreme_negative'
    
    def calculate_sharpe_contribution(self, sentiment_scores: List[float], volumes: List[int]) -> float:
        """计算情绪对Sharpe Ratio的贡献 (-1 to 1)"""
        if not sentiment_scores or not volumes:
            return 0.0
        
        # 计算加权平均情绪（按成交量加权）
        total_volume = sum(volumes)
        if total_volume == 0:
            weighted_sentiment = np.mean(sentiment_scores)
        else:
            weighted_sentiment = sum(s * v for s, v in zip(sentiment_scores, volumes)) / total_volume
        
        # 计算情绪波动性
        sentiment_volatility = np.std(sentiment_scores) if len(sentiment_scores) > 1 else 0.0
        
        # 情绪一致性（减少波动）
        consistency_bonus = 1.0 - sentiment_volatility if sentiment_volatility < 1.0 else 0.0
        
        # 极端情绪惩罚
        extreme_penalty = 0.0
        for score in sentiment_scores:
            category = self.categorize_sentiment(score)
            if category in ['extreme_positive', 'extreme_negative']:
                extreme_penalty += self.volatility_weights[category]
        
        extreme_penalty = min(0.5, extreme_penalty / len(sentiment_scores))
        
        # 最终Sharpe贡献计算
        sharpe_contribution = weighted_sentiment * consistency_bonus - extreme_penalty
        return max(-1.0, min(1.0, sharpe_contribution))
    
    def generate_recommendations(self, sentiment_scores: List[float], avg_score: float, 
                               sharpe_contribution: float, stock_symbol: str) -> List[str]:
        """生成交易建议"""
        recommendations = []
        
        # 基于平均情绪的建议
        if avg_score > 0.5:
            recommendations.append(f"【买入信号】{stock_symbol} 情绪强烈正面(avg={avg_score:.2f})，建议逢低买入")
        elif avg_score > 0.2:
            recommendations.append(f"【谨慎看多】{stock_symbol} 情绪温和正面，可考虑小仓位建仓")
        elif avg_score < -0.5:
            recommendations.append(f"【避险警告】{stock_symbol} 情绪极度负面(avg={avg_score:.2f})，建议减仓或观望")
        elif avg_score < -0.2:
            recommendations.append(f"【风险提示】{stock_symbol} 情绪偏负面，注意止损设置")
        else:
            recommendations.append(f"【中性观望】{stock_symbol} 情绪中性，等待更明确信号")
        
        # 基于Sharpe贡献的建议
        if sharpe_contribution > 0.3:
            recommendations.append("【风险调整】当前情绪有利于提升风险调整回报，可适度加杠杆")
        elif sharpe_contribution < -0.3:
            recommendations.append("【波动警告】情绪波动较大，建议降低仓位规模控制风险")
        
        # 情绪波动性建议
        if len(sentiment_scores) > 1:
            volatility = np.std(sentiment_scores)
            if volatility > 0.6:
                recommendations.append("【情绪分歧】市场情绪分化严重，建议分批建仓降低择时风险")
        
        # 极端情绪警示
        extreme_count = sum(1 for score in sentiment_scores if abs(score) > 0.7)
        if extreme_count > len(sentiment_scores) * 0.3:
            recommendations.append("【极端情绪】超30%言论情绪极端，警惕情绪反转风险")
        
        return recommendations[:5]  # 最多返回5条建议
    
    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """主分析函数"""
        stock_symbol = data.get('stock', 'Unknown')
        posts = data.get('posts', [])
        volumes = data.get('volumes', [])
        dates = data.get('dates', [datetime.now().strftime('%Y-%m-%d')] * len(posts))
        
        # 计算每条帖子的情绪分数
        sentiment_scores = []
        detailed_scores = []
        
        for i, post in enumerate(posts):
            score = self.calculate_sentiment_score(post)
            sentiment_scores.append(score)
            
            detailed_scores.append({
                'date': dates[i] if i < len(dates) else datetime.now().strftime('%Y-%m-%d'),
                'text': post[:50] + '...' if len(post) > 50 else post,
                'score': round(score, 3),
                'volume': volumes[i] if i < len(volumes) else 0
            })
        
        # 计算统计指标
        avg_score = np.mean(sentiment_scores) if sentiment_scores else 0.0
        sharpe_contribution = self.calculate_sharpe_contribution(sentiment_scores, volumes)
        
        # 生成交易建议
        recommendations = self.generate_recommendations(
            sentiment_scores, avg_score, sharpe_contribution, stock_symbol
        )
        
        # 构建结果
        result = {
            'stock_symbol': stock_symbol,
            'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'sentiment_scores': detailed_scores,
            'avg_score': round(avg_score, 3),
            'sharpe_contribution': round(sharpe_contribution, 3),
            'volatility': round(np.std(sentiment_scores), 3) if len(sentiment_scores) > 1 else 0.0,
            'sample_size': len(posts),
            'recommendations': recommendations,
            'risk_assessment': {
                'extreme_sentiment_ratio': round(sum(1 for s in sentiment_scores if abs(s) > 0.7) / max(len(sentiment_scores), 1), 3),
                'sentiment_consistency': round(1 - np.std(sentiment_scores), 3) if sentiment_scores else 0.0,
                'expected_sharpe_impact': 'Positive' if sharpe_contribution > 0.1 else 'Negative' if sharpe_contribution < -0.1 else 'Neutral'
            }
        }
        
        return result


def main():
    """主函数 - 处理示例数据"""
    analyzer = HKSentimentAnalyzer()
    
    # 示例数据 - 腾讯(0700.HK)
    sample_data = {
        "stock": "0700.HK",
        "posts": [
            "腾讯强劲成长！游戏业务恢复，云计算增长迅速",
            "市场恐慌，腾讯也难逃一跌，建议谨慎",
            "腾讯Q3财报超预期，买入时机来了",
            "地缘风险加剧，港股全线下跌，腾讯跌破400",
            "机构大举买入腾讯，看好长期成长潜力",
            "贸易战影响持续，科技股承压，腾讯前景不明",
            "腾讯元宇宙布局领先，未来增长空间巨大"
        ],
        "volumes": [1200000, 800000, 1500000, 2000000, 1800000, 900000, 1100000],
        "dates": ["2024-01-15", "2024-01-16", "2024-01-17", "2024-01-18", "2024-01-19", "2024-01-20", "2024-01-21"]
    }
    
    # 执行分析
    result = analyzer.analyze(sample_data)
    
    # 输出JSON结果
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 简短解释
    print(f"\n=== 关键洞见 ===")
    print(f"腾讯(0700.HK)平均情绪分数{result['avg_score']:.2f}，属于温和正面区间。")
    print(f"Sharpe贡献度{result['sharpe_contribution']:.2f}，情绪波动对风险调整回报影响{'正面' if result['sharpe_contribution'] > 0 else '负面'}。")


if __name__ == "__main__":
    main()