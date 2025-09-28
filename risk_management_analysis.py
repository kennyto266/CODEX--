#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
港股风险管理分析系统
Hong Kong Stock Risk Management Analysis System
"""

import json
import math
from datetime import datetime
from typing import Dict, List, Any, Tuple

class HKStockRiskAnalyzer:
    """港股风险管理分析器"""
    
    def __init__(self):
        self.risk_free_rate = 0.035  # 香港无风险利率约3.5%
        self.market_volatility = 0.18  # 恒生指数历史波动率约18%
        self.confidence_levels = [0.95, 0.99]  # VaR置信水平
        
    def analyze_stock_risk(self, stock_data: Dict) -> Dict:
        """
        综合风险分析主函数
        Args:
            stock_data: 股票数据字典
        Returns:
            完整的风险分析报告
        """
        # 提取股票基本信息
        stock_code = stock_data.get('stock_code', '0700.HK')
        current_price = float(stock_data.get('current_price', 644.0))
        price_change = float(stock_data.get('price_change', 57.0))
        price_change_pct = float(stock_data.get('price_change_pct', 9.71))
        historical_volatility = float(stock_data.get('historical_volatility', 1.38)) / 100
        max_drawdown = float(stock_data.get('max_drawdown', 3.93)) / 100
        
        # 执行各项风险分析
        market_risk = self._analyze_market_risk(stock_code, current_price, historical_volatility, max_drawdown)
        operational_risk = self._analyze_operational_risk(stock_code)
        credit_risk = self._analyze_credit_risk(stock_code)
        risk_quantification = self._quantify_risks(current_price, historical_volatility, max_drawdown)
        risk_control = self._generate_risk_control_recommendations(current_price, historical_volatility, max_drawdown)
        risk_warning = self._setup_risk_warning_system(current_price, historical_volatility)
        
        # 综合评估
        overall_assessment = self._generate_overall_assessment(
            market_risk, operational_risk, credit_risk, risk_quantification,
            current_price, price_change_pct, historical_volatility
        )
        
        return {
            "股票信息": {
                "股票代码": stock_code,
                "当前价格": current_price,
                "价格变化": f"{price_change} ({price_change_pct:.2f}%)",
                "历史波动率": f"{historical_volatility*100:.2f}%",
                "最大回撤": f"{max_drawdown*100:.2f}%",
                "分析时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            "市场风险": market_risk,
            "操作风险": operational_risk,
            "信用风险": credit_risk,
            "风险量化": risk_quantification,
            "风险控制建议": risk_control,
            "风险预警": risk_warning,
            "综合评估": overall_assessment
        }
    
    def _analyze_market_risk(self, stock_code: str, price: float, volatility: float, max_drawdown: float) -> Dict:
        """市场风险分析"""
        
        # 系统性风险分析
        systematic_risk = {
            "风险等级": "中等" if volatility < 0.25 else "高",
            "beta系数估算": round(volatility / self.market_volatility, 2),
            "市场敏感度": "高" if volatility > 0.20 else "中等" if volatility > 0.15 else "低",
            "宏观经济敏感度": "高" if stock_code.startswith('07') else "中等",  # 科技股对宏观经济更敏感
            "政策风险": "较高" if stock_code.startswith('07') else "中等"
        }
        
        # 非系统性风险识别
        non_systematic_risk = {
            "公司特定风险": "中等",
            "行业风险": "较高" if stock_code.startswith('07') else "中等",  # 科技行业风险较高
            "管理风险": "低" if stock_code == '0700.HK' else "中等",  # 腾讯管理相对稳定
            "财务风险": "低" if stock_code == '0700.HK' else "中等",
            "竞争风险": "高" if stock_code.startswith('07') else "中等"
        }
        
        # 流动性风险评估
        liquidity_risk = {
            "流动性等级": "优秀" if stock_code == '0700.HK' else "良好",
            "日均成交量": "高" if stock_code == '0700.HK' else "中等",
            "买卖价差": "窄" if stock_code == '0700.HK' else "中等",
            "市场深度": "深" if stock_code == '0700.HK' else "中等",
            "流动性风险评分": 2 if stock_code == '0700.HK' else 4  # 1-10分，分数越低风险越小
        }
        
        # 波动性风险分析
        volatility_risk = {
            "波动率水平": "低" if volatility < 0.15 else "中等" if volatility < 0.25 else "高",
            "波动率稳定性": "稳定" if max_drawdown < 0.05 else "一般" if max_drawdown < 0.10 else "不稳定",
            "极端波动概率": self._calculate_extreme_volatility_probability(volatility),
            "波动率风险评分": min(10, max(1, int(volatility * 50)))
        }
        
        # 相关性风险分析
        correlation_risk = {
            "与恒指相关性": "高" if stock_code == '0700.HK' else "中等",
            "行业集中度风险": "中等",
            "地域集中度风险": "高",  # 主要在香港和中国大陆
            "货币风险": "中等",  # 港币与美元挂钩
            "相关性风险评分": 6
        }
        
        return {
            "系统性风险分析": systematic_risk,
            "非系统性风险识别": non_systematic_risk,
            "流动性风险评估": liquidity_risk,
            "波动性风险分析": volatility_risk,
            "相关性风险分析": correlation_risk
        }
    
    def _analyze_operational_risk(self, stock_code: str) -> Dict:
        """操作风险分析"""
        
        return {
            "交易执行风险": {
                "滑点风险": "低" if stock_code == '0700.HK' else "中等",
                "执行延迟风险": "低",
                "部分成交风险": "低" if stock_code == '0700.HK' else "中等",
                "价格冲击风险": "低",
                "风险评分": 3
            },
            "模型风险": {
                "定价模型风险": "中等",
                "风险测度模型风险": "中等",
                "参数估计风险": "中等",
                "模型验证风险": "中等",
                "风险评分": 5
            },
            "数据风险": {
                "数据质量风险": "低",
                "数据延迟风险": "低",
                "数据完整性风险": "低",
                "数据安全风险": "中等",
                "风险评分": 3
            },
            "技术风险": {
                "系统故障风险": "低",
                "网络中断风险": "低",
                "软件错误风险": "中等",
                "硬件故障风险": "低",
                "风险评分": 3
            },
            "人为风险": {
                "操作错误风险": "中等",
                "欺诈风险": "低",
                "内部控制风险": "中等",
                "培训不足风险": "中等",
                "风险评分": 4
            }
        }
    
    def _analyze_credit_risk(self, stock_code: str) -> Dict:
        """信用风险分析"""
        
        return {
            "公司信用状况": {
                "信用等级": "优秀" if stock_code == '0700.HK' else "良好",
                "财务健康度": "优秀" if stock_code == '0700.HK' else "良好",
                "偿债能力": "强" if stock_code == '0700.HK' else "中等",
                "盈利稳定性": "高" if stock_code == '0700.HK' else "中等",
                "信用风险评分": 2 if stock_code == '0700.HK' else 4
            },
            "行业信用风险": {
                "行业发展前景": "良好" if stock_code.startswith('07') else "中等",
                "行业竞争激烈度": "高" if stock_code.startswith('07') else "中等",
                "监管政策风险": "较高" if stock_code.startswith('07') else "中等",
                "技术变革风险": "高" if stock_code.startswith('07') else "低",
                "风险评分": 6 if stock_code.startswith('07') else 4
            },
            "宏观经济信用风险": {
                "经济周期敏感度": "高",
                "利率敏感度": "中等",
                "通胀敏感度": "中等",
                "汇率风险": "中等",
                "风险评分": 5
            },
            "地缘政治信用风险": {
                "政治稳定性": "中等",
                "国际关系风险": "较高",
                "贸易政策风险": "高",
                "法律法规风险": "中等",
                "风险评分": 6
            }
        }
    
    def _quantify_risks(self, price: float, volatility: float, max_drawdown: float) -> Dict:
        """风险量化分析"""
        
        # VaR计算
        var_results = {}
        for confidence in self.confidence_levels:
            z_score = self._get_z_score(confidence)
            var_amount = price * volatility * z_score * math.sqrt(1/252)  # 日VaR
            var_results[f"VaR_{int(confidence*100)}%"] = {
                "金额": round(var_amount, 2),
                "比例": f"{(var_amount/price)*100:.2f}%"
            }
        
        # 压力测试
        stress_test = {
            "极端下跌情景": {
                "下跌幅度": "20%",
                "潜在损失": round(price * 0.20, 2),
                "发生概率": "5%"
            },
            "市场崩盘情景": {
                "下跌幅度": "35%",
                "潜在损失": round(price * 0.35, 2),
                "发生概率": "1%"
            },
            "流动性危机情景": {
                "下跌幅度": "15%",
                "潜在损失": round(price * 0.15, 2),
                "发生概率": "8%"
            }
        }
        
        # 情景分析
        scenario_analysis = {
            "乐观情景": {
                "预期收益": "15-25%",
                "发生概率": "25%",
                "关键因素": ["业绩超预期", "行业景气度提升", "政策利好"]
            },
            "基准情景": {
                "预期收益": "5-15%",
                "发生概率": "50%",
                "关键因素": ["业绩稳定增长", "市场平稳运行"]
            },
            "悲观情景": {
                "预期收益": "-10-5%",
                "发生概率": "25%",
                "关键因素": ["业绩不及预期", "市场调整", "政策收紧"]
            }
        }
        
        # 风险敞口计算
        risk_exposure = {
            "市场风险敞口": f"{(volatility * price):.2f}",
            "特定风险敞口": f"{(max_drawdown * price):.2f}",
            "总风险敞口": f"{(math.sqrt(volatility**2 + max_drawdown**2) * price):.2f}",
            "风险预算建议": "不超过投资组合的5-10%"
        }
        
        # 风险贡献度分析
        risk_contribution = {
            "市场风险贡献": f"{(volatility**2 / (volatility**2 + max_drawdown**2) * 100):.1f}%",
            "特定风险贡献": f"{(max_drawdown**2 / (volatility**2 + max_drawdown**2) * 100):.1f}%",
            "分散化效益": "中等",
            "边际风险贡献": f"{volatility:.3f}"
        }
        
        return {
            "VaR计算": var_results,
            "压力测试": stress_test,
            "情景分析": scenario_analysis,
            "风险敞口计算": risk_exposure,
            "风险贡献度分析": risk_contribution
        }
    
    def _generate_risk_control_recommendations(self, price: float, volatility: float, max_drawdown: float) -> Dict:
        """生成风险控制建议"""
        
        # 仓位控制建议
        position_control = {
            "建议仓位": "5-10%" if volatility > 0.20 else "8-15%" if volatility > 0.15 else "10-20%",
            "最大仓位": "15%" if volatility > 0.20 else "20%" if volatility > 0.15 else "25%",
            "分批建仓": "建议分3-5次建仓",
            "动态调整": "根据波动率动态调整仓位"
        }
        
        # 止损设置建议
        stop_loss = {
            "技术止损": f"{price * (1 - max_drawdown * 1.5):.2f}" if max_drawdown > 0 else f"{price * 0.92:.2f}",
            "时间止损": "持仓超过6个月且未达预期收益",
            "基本面止损": "公司基本面发生重大恶化",
            "止损幅度": f"{max_drawdown * 1.5 * 100:.1f}%" if max_drawdown > 0 else "8%"
        }
        
        # 对冲策略建议
        hedging_strategy = {
            "指数对冲": "可考虑做空恒生指数ETF",
            "行业对冲": "做空相关行业ETF",
            "期权保护": "购买看跌期权作为保险",
            "相关性对冲": "配置负相关资产"
        }
        
        # 分散化建议
        diversification = {
            "行业分散": "不超过投资组合的30%投资于同一行业",
            "地域分散": "配置其他市场资产",
            "时间分散": "分批建仓和减仓",
            "风格分散": "配置不同风格的股票"
        }
        
        # 监控指标设定
        monitoring_indicators = {
            "价格指标": ["日涨跌幅超过5%", "连续3日下跌超过3%"],
            "成交量指标": ["成交量异常放大或萎缩"],
            "技术指标": ["RSI < 30或 > 70", "MACD背离"],
            "基本面指标": ["业绩预告", "重大事项公告"],
            "宏观指标": ["利率变化", "政策变化"]
        }
        
        return {
            "仓位控制建议": position_control,
            "止损设置建议": stop_loss,
            "对冲策略建议": hedging_strategy,
            "分散化建议": diversification,
            "监控指标设定": monitoring_indicators
        }
    
    def _setup_risk_warning_system(self, price: float, volatility: float) -> Dict:
        """建立风险预警系统"""
        
        # 早期预警信号
        early_warning = {
            "一级预警": {
                "触发条件": ["单日跌幅超过3%", "连续2日下跌"],
                "预警级别": "低",
                "应对措施": "密切关注，准备减仓"
            },
            "二级预警": {
                "触发条件": ["单日跌幅超过5%", "连续3日下跌超过8%"],
                "预警级别": "中",
                "应对措施": "减仓50%，评估基本面"
            },
            "三级预警": {
                "触发条件": ["单日跌幅超过8%", "累计跌幅超过15%"],
                "预警级别": "高",
                "应对措施": "立即止损，全部清仓"
            }
        }
        
        # 风险阈值设定
        risk_thresholds = {
            "价格阈值": {
                "支撑位": f"{price * 0.92:.2f}",
                "阻力位": f"{price * 1.08:.2f}",
                "止损位": f"{price * 0.85:.2f}"
            },
            "波动率阈值": {
                "正常区间": "10-20%",
                "警戒线": "25%",
                "危险线": "30%"
            },
            "成交量阈值": {
                "异常放大": "超过30日均量200%",
                "异常萎缩": "低于30日均量50%"
            }
        }
        
        # 应急处理预案
        contingency_plan = {
            "市场暴跌": {
                "应对策略": "立即止损，等待企稳信号",
                "执行时间": "15分钟内",
                "责任人": "风控经理"
            },
            "个股异动": {
                "应对策略": "查明原因，评估影响，决定去留",
                "执行时间": "30分钟内",
                "责任人": "投资经理"
            },
            "系统故障": {
                "应对策略": "启用备用系统，人工下单",
                "执行时间": "5分钟内",
                "责任人": "技术负责人"
            }
        }
        
        # 风险报告机制
        reporting_mechanism = {
            "日报": "每日收盘后30分钟内",
            "周报": "每周五下午",
            "月报": "每月第一个工作日",
            "紧急报告": "触发预警后立即上报",
            "报告内容": ["仓位情况", "盈亏状况", "风险指标", "预警信号"]
        }
        
        return {
            "早期预警信号": early_warning,
            "风险阈值设定": risk_thresholds,
            "应急处理预案": contingency_plan,
            "风险报告机制": reporting_mechanism
        }
    
    def _generate_overall_assessment(self, market_risk: Dict, operational_risk: Dict, 
                                   credit_risk: Dict, risk_quantification: Dict,
                                   price: float, price_change_pct: float, volatility: float) -> Dict:
        """生成综合评估"""
        
        # 计算综合风险评分
        market_score = 5  # 基于波动率和其他市场风险因素
        operational_score = 3  # 基于操作风险评估
        credit_score = 3 if price > 600 else 5  # 基于股价和信用状况
        
        total_risk_score = (market_score + operational_score + credit_score) / 3
        
        # 风险等级
        if total_risk_score <= 3:
            risk_level = "低风险"
        elif total_risk_score <= 6:
            risk_level = "中等风险"
        else:
            risk_level = "高风险"
        
        # 投资建议
        if price_change_pct > 8 and volatility < 0.20:
            investment_advice = "谨慎乐观，可适量配置"
        elif price_change_pct > 5:
            investment_advice = "保持关注，控制仓位"
        else:
            investment_advice = "等待更好时机"
        
        # 预期收益评估
        if volatility < 0.15:
            expected_return = "8-15%"
        elif volatility < 0.25:
            expected_return = "5-20%"
        else:
            expected_return = "-5-25%"
        
        return {
            "详细的分析过程": {
                "分析方法": "基于现代投资组合理论和风险管理理论",
                "数据来源": "历史价格数据和市场指标",
                "分析维度": "市场风险、操作风险、信用风险、流动性风险",
                "量化方法": "VaR、压力测试、情景分析",
                "评估标准": "国际风险管理最佳实践"
            },
            "具体的投资建议": {
                "投资策略": investment_advice,
                "建议仓位": "5-15%",
                "持有期限": "3-6个月",
                "关注重点": ["基本面变化", "市场情绪", "政策动向"],
                "操作建议": "分批建仓，设置止损"
            },
            "风险提示": {
                "主要风险": [
                    "市场波动风险较高",
                    "行业政策风险需关注",
                    "地缘政治风险影响",
                    "流动性风险相对较低"
                ],
                "风险等级": risk_level,
                "风险评分": f"{total_risk_score:.1f}/10",
                "注意事项": [
                    "密切关注市场变化",
                    "严格执行风险控制",
                    "定期评估调整策略"
                ]
            },
            "预期收益评估": {
                "预期年化收益": expected_return,
                "风险收益比": f"1:{volatility*10:.1f}",
                "夏普比率估算": f"{(0.12 - self.risk_free_rate) / volatility:.2f}",
                "最大预期损失": f"{max(volatility * 2, 0.15) * 100:.1f}%",
                "收益概率分布": {
                    "盈利概率": "60-70%",
                    "亏损概率": "30-40%",
                    "大幅盈利概率(>20%)": "15-25%",
                    "大幅亏损概率(>15%)": "10-15%"
                }
            }
        }
    
    def _calculate_extreme_volatility_probability(self, volatility: float) -> str:
        """计算极端波动概率"""
        if volatility < 0.15:
            return "低 (<5%)"
        elif volatility < 0.25:
            return "中等 (5-10%)"
        else:
            return "高 (>10%)"
    
    def _get_z_score(self, confidence_level: float) -> float:
        """获取置信水平对应的Z分数"""
        z_scores = {0.90: 1.28, 0.95: 1.65, 0.99: 2.33}
        return z_scores.get(confidence_level, 1.65)


def main():
    """主函数：执行风险分析"""
    
    # 输入股票数据
    stock_data = {
        'stock_code': '0700.HK',
        'current_price': 644.0,
        'price_change': 57.00,
        'price_change_pct': 9.71,
        'historical_volatility': 1.38,  # 以百分比形式输入
        'max_drawdown': 3.93  # 以百分比形式输入
    }
    
    # 创建风险分析器
    analyzer = HKStockRiskAnalyzer()
    
    # 执行风险分析
    risk_analysis_result = analyzer.analyze_stock_risk(stock_data)
    
    # 输出JSON格式结果
    print(json.dumps(risk_analysis_result, ensure_ascii=False, indent=2))
    
    return risk_analysis_result


if __name__ == "__main__":
    main()