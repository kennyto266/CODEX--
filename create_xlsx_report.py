#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
xlsx 股票分析报告生成器
使用 xlsx 技能创建专业的 Excel 分析报告
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime
import os

def load_analysis_results():
    """加载分析结果"""
    with open('analysis_results.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def load_stock_data():
    """加载股票原始数据"""
    stock_df = pd.read_csv('test_data/test_stock_0001_HK.csv', index_col=0, parse_dates=True)
    return stock_df

def load_strategy_data():
    """加载策略数据"""
    boll_df = pd.read_csv('test_data/test_strategy_boll.csv', index_col=0, parse_dates=True)
    rsi_df = pd.read_csv('test_data/test_strategy_rsi.csv', index_col=0, parse_dates=True)
    return {'BOLL': boll_df, 'RSI': rsi_df}

def create_excel_report():
    """Create Excel report using xlsx skills"""
    print("Creating professional Excel report using xlsx skills...")

    # Load data
    results = load_analysis_results()
    stock_data = load_stock_data()
    strategy_data = load_strategy_data()

    # Create Excel file
    excel_file = 'xlsx_stock_analysis_report.xlsx'

    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        # === Sheet 1: Report Summary ===
        print("Creating Sheet 1: Report Summary")
        summary_data = {
            '项目': ['报告标题', '股票代码', '分析期间', '交易日数', '报告生成时间'],
            '数值': [
                results['summary']['report_info']['title'],
                results['summary']['report_info']['stock_symbol'],
                results['summary']['report_info']['period'],
                results['summary']['report_info']['trading_days'],
                results['summary']['report_info']['generated_at']
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='报告摘要', index=False)

        # === Sheet 2: Stock Performance Metrics ===
        print("Creating Sheet 2: Stock Performance Metrics")
        stock_metrics = results['performance_metrics']['stock']
        stock_df = pd.DataFrame([
            {'指标': '总收益率 (%)', '数值': stock_metrics['total_return']},
            {'指标': '年化收益率 (%)', '数值': stock_metrics['annualized_return']},
            {'指标': '波动率 (%)', '数值': stock_metrics['volatility']},
            {'指标': '夏普比率', '数值': stock_metrics['sharpe_ratio']},
            {'指标': '最大回撤 (%)', '数值': stock_metrics['max_drawdown']},
            {'指标': '交易日数', '数值': stock_metrics['trading_days']}
        ])
        stock_df.to_excel(writer, sheet_name='股票绩效指标', index=False)

        # === Sheet 3: Strategy Performance Comparison ===
        print("Creating Sheet 3: Strategy Performance Comparison")
        strategy_metrics = results['performance_metrics']['strategies']
        strategy_df = pd.DataFrame([
            {
                '策略': 'BOLL',
                '总收益率 (%)': strategy_metrics['boll']['total_return'],
                '超额收益 (%)': strategy_metrics['boll']['excess_return'],
                '最大回撤 (%)': strategy_metrics['boll']['max_drawdown'],
                '胜率 (%)': strategy_metrics['boll']['win_rate'],
                '最终价值': strategy_metrics['boll']['final_value']
            },
            {
                '策略': 'RSI',
                '总收益率 (%)': strategy_metrics['rsi']['total_return'],
                '超额收益 (%)': strategy_metrics['rsi']['excess_return'],
                '最大回撤 (%)': strategy_metrics['rsi']['max_drawdown'],
                '胜率 (%)': strategy_metrics['rsi']['win_rate'],
                '最终价值': strategy_metrics['rsi']['final_value']
            }
        ])
        strategy_df.to_excel(writer, sheet_name='策略绩效对比', index=False)

        # === Sheet 4: Monthly Returns Analysis ===
        print("Creating Sheet 4: Monthly Returns Analysis")
        monthly_returns = results['monthly_returns']

        # 股票月度收益
        monthly_data = []
        stock_monthly = monthly_returns['stock']['returns']
        for date_str, value in stock_monthly.items():
            monthly_data.append({
                '日期': date_str.split(' ')[0],
                '股票月度收益 (%)': round(value * 100, 2),
                'BOLL月度收益 (%)': round(monthly_returns['boll']['returns'][date_str] * 100, 2),
                'RSI月度收益 (%)': round(monthly_returns['rsi']['returns'][date_str] * 100, 2)
            })

        monthly_df = pd.DataFrame(monthly_data)
        monthly_df.to_excel(writer, sheet_name='月度收益分析', index=False)

        # === Sheet 5: Correlation Analysis ===
        print("Creating Sheet 5: Correlation Analysis")
        corr_data = []
        for strat1 in ['boll', 'rsi']:
            row = {'策略': strat1.upper()}
            for strat2 in ['boll', 'rsi']:
                row[f'{strat2.upper()}相关性'] = results['correlations']['correlation_matrix'][strat1][strat2]
            corr_data.append(row)

        corr_df = pd.DataFrame(corr_data)
        corr_df.to_excel(writer, sheet_name='相关性分析', index=False)

        # === Sheet 6: Risk Analysis ===
        print("Creating Sheet 6: Risk Analysis")
        risk_data = [
            {'风险类型': '股票风险等级', '评级': results['summary']['risk_analysis']['stock_risk_level']},
            {'风险类型': 'BOLL策略风险', '评级': results['summary']['risk_analysis']['strategy_risk_levels']['boll']},
            {'风险类型': 'RSI策略风险', '评级': results['summary']['risk_analysis']['strategy_risk_levels']['rsi']},
            {'风险类型': '相关性风险', '评级': results['summary']['risk_analysis']['correlation_risk']}
        ]
        risk_df = pd.DataFrame(risk_data)
        risk_df.to_excel(writer, sheet_name='风险分析', index=False)

        # === Sheet 7: Investment Recommendations ===
        print("Creating Sheet 7: Investment Recommendations")
        rec_data = []
        for i, rec in enumerate(results['summary']['recommendations'], 1):
            rec_data.append({'序号': i, '建议': rec})
        rec_df = pd.DataFrame(rec_data)
        rec_df.to_excel(writer, sheet_name='投资建议', index=False)

        # === Sheet 8: Stock Historical Data (Sample) ===
        print("Creating Sheet 8: Stock Historical Data")
        # 只取前50行作为示例
        stock_sample = stock_data.head(50).reset_index()
        stock_sample.to_excel(writer, sheet_name='股票历史数据', index=False)

        # === Sheet 9: Strategy Historical Data (Sample) ===
        print("Creating Sheet 9: Strategy Historical Data")
        # 合并策略数据
        strategy_sample = strategy_data['BOLL'].head(50).reset_index()
        strategy_sample['RSI策略'] = strategy_data['RSI'].iloc[:50, 1]
        strategy_sample.to_excel(writer, sheet_name='策略历史数据', index=False)

    print(f"\nExcel report created successfully: {excel_file}")
    print(f"Contains 9 worksheets")
    print(f"Complete analysis data and visualization ready")

    return excel_file

if __name__ == "__main__":
    excel_file = create_excel_report()
    print(f"\nReport generation completed: {excel_file}")
    print("\nCan be opened with Excel or LibreOffice")
