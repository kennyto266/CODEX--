#!/usr/bin/env python3
"""
港股新闻分析代理 (Hong Kong Stock News Analyst Agent)
专注于高Sharpe Ratio交易策略的量化分析
"""

import json
import re
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import math

@dataclass
class NewsEvent:
    """新闻事件数据结构"""
    description: str
    impact_score: float  # -0.1 到 0.1
    confidence: float    # 0 到 1
    category: str       # 监管、并购、业绩等
    affected_stocks: List[str]

@dataclass 
class AnalysisResult:
    """分析结果数据结构"""
    key_events: List[Dict[str, Any]]
    event_count: int
    sharpe_contribution: float  # -1 到 1
    recommendations: List[str]

class HKStockNewsAnalyzer:
    """港股新闻分析代理"""
    
    def __init__(self):
        # 关键词权重映射
        self.event_keywords = {
            # 正面事件
            "并购": 0.08, "收购": 0.08, "合并": 0.06,
            "业绩超预期": 0.09, "盈利增长": 0.07, "分红": 0.05,
            "新产品": 0.06, "扩张": 0.05, "合作": 0.04,
            "获批": 0.07, "牌照": 0.08, "政策支持": 0.09,
            
            # 负面事件  
            "监管": -0.07, "调查": -0.08, "罚款": -0.09,
            "亏损": -0.08, "下调": -0.06, "风险": -0.05,
            "制裁": -0.09, "禁令": -0.08, "暂停": -0.07,
            "违规": -0.08, "诉讼": -0.06, "退市": -0.10
        }
        
        # 行业敏感度系数
        self.sector_sensitivity = {
            "科技": 1.2, "金融": 1.0, "地产": 1.1,
            "消费": 0.9, "能源": 1.0, "医药": 1.1
        }
        
    def extract_events(self, news_items: List[str]) -> List[NewsEvent]:
        """从新闻中提取关键事件"""
        events = []
        
        for news in news_items:
            impact_score = 0.0
            confidence = 0.5
            category = "其他"
            
            # 关键词匹配和影响评分
            for keyword, weight in self.event_keywords.items():
                if keyword in news:
                    impact_score += weight
                    confidence += 0.2
                    
                    # 确定事件类别
                    if keyword in ["并购", "收购", "合并"]:
                        category = "并购"
                    elif keyword in ["监管", "调查", "罚款"]:
                        category = "监管"
                    elif keyword in ["业绩超预期", "盈利增长"]:
                        category = "业绩"
            
            # 限制影响分数范围
            impact_score = max(-0.1, min(0.1, impact_score))
            confidence = min(1.0, confidence)
            
            # 提取相关股票代码
            stock_pattern = r'\d{4}\.HK'
            affected_stocks = re.findall(stock_pattern, news)
            
            events.append(NewsEvent(
                description=news,
                impact_score=impact_score,
                confidence=confidence,
                category=category,
                affected_stocks=affected_stocks
            ))
            
        return events
    
    def calculate_sharpe_contribution(self, events: List[NewsEvent]) -> float:
        """计算事件对Sharpe Ratio的贡献"""
        total_impact = 0.0
        risk_adjustment = 0.0
        
        for event in events:
            # 基础影响
            weighted_impact = event.impact_score * event.confidence
            total_impact += weighted_impact
            
            # 风险调整：负面事件增加波动性惩罚
            if event.impact_score < 0:
                risk_adjustment += abs(event.impact_score) * 0.5
        
        # 计算Sharpe贡献 (考虑风险调整)
        sharpe_contribution = total_impact - risk_adjustment
        
        # 限制在 -1 到 1 范围内
        return max(-1.0, min(1.0, sharpe_contribution))
    
    def generate_recommendations(self, events: List[NewsEvent], 
                               sharpe_contribution: float) -> List[str]:
        """生成交易建议"""
        recommendations = []
        
        # 筛选正面和负面事件
        positive_events = [e for e in events if e.impact_score > 0.05]
        negative_events = [e for e in events if e.impact_score < -0.05]
        
        # 买入建议
        if positive_events:
            stocks = set()
            for event in positive_events:
                stocks.update(event.affected_stocks)
            if stocks:
                recommendations.append(
                    f"买入建议: {', '.join(list(stocks)[:3])} - "
                    f"基于{len(positive_events)}个正面事件"
                )
        
        # 风险警示
        if negative_events:
            high_risk_stocks = set()
            for event in negative_events:
                if event.impact_score < -0.07:
                    high_risk_stocks.update(event.affected_stocks)
            if high_risk_stocks:
                recommendations.append(
                    f"风险警示: 避免 {', '.join(list(high_risk_stocks)[:3])} - "
                    f"重大负面事件影响"
                )
        
        # Sharpe策略建议
        if sharpe_contribution > 0.3:
            recommendations.append(
                "策略建议: 增加仓位配置，预期Sharpe Ratio提升"
            )
        elif sharpe_contribution < -0.3:
            recommendations.append(
                "策略建议: 降低仓位或启动对冲，保护Sharpe Ratio"
            )
        else:
            recommendations.append(
                "策略建议: 维持当前仓位，市场中性信号"
            )
        
        # 风险管理建议
        if len(negative_events) > len(positive_events):
            recommendations.append(
                "风险管理: 考虑购买看跌期权或恒指期货对冲"
            )
        
        return recommendations[:5]  # 限制在5条以内
    
    def analyze(self, data: Dict[str, Any]) -> str:
        """
        主分析函数
        
        Args:
            data: 包含news_items和stock的字典
            
        Returns:
            JSON格式的分析结果
        """
        # 提取输入数据
        news_items = data.get("news_items", [])
        target_stock = data.get("stock", "")
        
        # 步骤1: 提取事件
        events = self.extract_events(news_items)
        
        # 步骤2: 计算Sharpe贡献
        sharpe_contribution = self.calculate_sharpe_contribution(events)
        
        # 步骤3: 生成建议
        recommendations = self.generate_recommendations(events, sharpe_contribution)
        
        # 构建输出结果
        key_events = []
        for event in events:
            key_events.append({
                "description": event.description,
                "impact_score": round(event.impact_score, 3),
                "confidence": round(event.confidence, 2),
                "category": event.category,
                "affected_stocks": event.affected_stocks
            })
        
        result = {
            "key_events": key_events,
            "event_count": len(events),
            "sharpe_contribution": round(sharpe_contribution, 3),
            "recommendations": recommendations,
            "analysis_timestamp": datetime.now().isoformat(),
            "target_stock": target_stock
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)

def main():
    """演示分析功能"""
    analyzer = HKStockNewsAnalyzer()
    
    # 示例数据
    sample_data = {
        "news_items": [
            "腾讯(0700.HK)宣布收购游戏公司，预期业绩增长20%",
            "港股监管机构对科技股展开新一轮调查",
            "阿里巴巴(9988.HK)获得新的支付牌照批准",
            "恒生指数成分股面临地缘政治风险",
            "比亚迪(1211.HK)新能源汽车销量超预期，股价大涨"
        ],
        "stock": "0700.HK"
    }
    
    # 执行分析
    result = analyzer.analyze(sample_data)
    print("=== 港股新闻分析结果 ===")
    print(result)
    
    # 解析并显示关键洞见
    result_dict = json.loads(result)
    print(f"\n=== 关键洞见 ===")
    print(f"检测到 {result_dict['event_count']} 个关键事件")
    print(f"Sharpe Ratio预期贡献: {result_dict['sharpe_contribution']}")
    
    if result_dict['sharpe_contribution'] > 0:
        print("✅ 整体市场情绪偏正面，建议适度增加仓位")
    else:
        print("⚠️  市场存在风险因素，建议谨慎操作并考虑对冲")

if __name__ == "__main__":
    main()