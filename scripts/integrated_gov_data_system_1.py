#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成政府数据系统 - 终极自动化版本
Integrated Government Data System - Ultimate Automation

自动获取政府数据并集成到交易系统
"""

import os
import sys
import json
import csv
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

class IntegratedGovDataSystem:
    def __init__(self):
        self.data_dir = Path("integrated_gov_data")
        self.data_dir.mkdir(exist_ok=True)

    def update_all_gov_data(self):
        """更新所有政府数据"""
        print("\n" + "="*80)
        print("Updating All Government Data")
        print("="*80)

        # 运行自动下载器
        os.system("python simple_auto_downloader.py > /dev/null 2>&1")

        # 复制最新数据到集成目录
        source_dir = Path("auto_downloaded_gov_data")
        if source_dir.exists():
            for csv_file in source_dir.glob("*.csv"):
                # 获取文件修改时间
                mtime = csv_file.stat().st_mtime
                # 只有今天修改的文件才复制
                if datetime.fromtimestamp(mtime).date() == datetime.now().date():
                    dest = self.data_dir / csv_file.name
                    dest.write_bytes(csv_file.read_bytes())
                    print(f"Copied: {csv_file.name}")

        print(f"\nData updated in: {self.data_dir}")

    def get_latest_data(self, data_type: str) -> List[Dict]:
        """获取最新数据"""
        files = {
            "hibor": list(self.data_dir.glob("hibor_rates_*.csv")),
            "visitor": list(self.data_dir.glob("visitor_arrivals_*.csv")),
            "traffic": list(self.data_dir.glob("traffic_speed_*.csv")),
            "aqhi": list(self.data_dir.glob("aqhi_*.csv")),
            "mtr": list(self.data_dir.glob("mtr_passengers_*.csv"))
        }

        if data_type not in files:
            return []

        data_files = files[data_type]
        if not data_files:
            return []

        # 获取最新的文件
        latest_file = max(data_files, key=lambda x: x.stat().st_mtime)

        # 读取数据
        with open(latest_file, 'r') as f:
            reader = csv.DictReader(f)
            return list(reader)

    def calculate_economic_indicators(self):
        """计算经济指标"""
        print("\nCalculating Economic Indicators...")

        indicators = {}

        # 1. HIBOR利率指标
        hibor_data = self.get_latest_data("hibor")
        if hibor_data:
            overnight_rate = float(hibor_data[0]['Rate (%)'])
            one_month_rate = float(hibor_data[2]['Rate (%)'])
            indicators['hibor_overnight'] = overnight_rate
            indicators['hibor_spread'] = one_month_rate - overnight_rate
            print(f"  HIBOR Overnight: {overnight_rate:.2f}%")

        # 2. 访客指标
        visitor_data = self.get_latest_data("visitor")
        if visitor_data:
            latest_month = visitor_data[-1]
            total_visitors = int(latest_month['Total_Visitors'])
            indicators['total_visitors'] = total_visitors
            print(f"  Total Visitors: {total_visitors:,}")

        # 3. 交通指标
        traffic_data = self.get_latest_data("traffic")
        if traffic_data:
            avg_speed = sum(int(row['Speed_kmh']) for row in traffic_data) / len(traffic_data)
            indicators['avg_traffic_speed'] = avg_speed
            print(f"  Avg Traffic Speed: {avg_speed:.1f} km/h")

        # 4. 空气质量指标
        aqhi_data = self.get_latest_data("aqhi")
        if aqhi_data:
            avg_aqhi = sum(int(row['AQHI']) for row in aqhi_data) / len(aqhi_data)
            indicators['avg_aqhi'] = avg_aqhi
            print(f"  Average AQHI: {avg_aqhi:.1f}")

        # 保存指标
        indicators_file = self.data_dir / "economic_indicators.json"
        with open(indicators_file, 'w') as f:
            json.dump(indicators, f, indent=2)

        print(f"\nIndicators saved to: {indicators_file}")
        return indicators

    def generate_trading_signals(self):
        """生成交易信号"""
        print("\nGenerating Trading Signals...")

        indicators = self.calculate_economic_indicators()

        signals = {
            "bank_stocks": "HOLD",
            "retail_stocks": "HOLD",
            "transport_stocks": "HOLD",
            "healthcare_stocks": "HOLD"
        }

        # 基于HIBOR的银行股信号
        if 'hibor_overnight' in indicators:
            if indicators['hibor_overnight'] > 5.0:
                signals['bank_stocks'] = "BUY"
            elif indicators['hibor_overnight'] < 3.0:
                signals['bank_stocks'] = "SELL"

        # 基于访客的零售股信号
        if 'total_visitors' in indicators:
            if indicators['total_visitors'] > 220000:
                signals['retail_stocks'] = "BUY"
            elif indicators['total_visitors'] < 200000:
                signals['retail_stocks'] = "SELL"

        # 基于交通的运输股信号
        if 'avg_traffic_speed' in indicators:
            if indicators['avg_traffic_speed'] < 50:
                signals['transport_stocks'] = "SELL"

        # 保存信号
        signals_file = self.data_dir / "trading_signals.json"
        with open(signals_file, 'w') as f:
            json.dump(signals, f, indent=2)

        print("Trading Signals:")
        for sector, signal in signals.items():
            print(f"  {sector}: {signal}")

        print(f"\nSignals saved to: {signals_file}")
        return signals

    def combine_with_hkex_data(self):
        """与HKEX数据结合"""
        print("\nCombining with HKEX Data...")

        # 读取HKEX数据目录
        hkex_data_dir = Path("data")
        if not hkex_data_dir.exists():
            print("  HKEX data directory not found")
            return

        # 获取所有HKEX股票文件
        hkex_files = list(hkex_data_dir.glob("*.csv"))
        print(f"  Found {len(hkex_files)} HKEX files")

        # 合并数据 (示例)
        combined_file = self.data_dir / "combined_analysis.json"
        combined_data = {
            "hkex_stocks": len(hkex_files),
            "gov_data_updated": datetime.now().isoformat(),
            "status": "READY_FOR_ANALYSIS"
        }

        with open(combined_file, 'w') as f:
            json.dump(combined_data, f, indent=2)

        print(f"  Combined data: {combined_file}")

    def run_full_integration(self):
        """运行完整集成流程"""
        print("\n" + "="*80)
        print("FULL GOVERNMENT DATA INTEGRATION")
        print("="*80)

        # 1. 更新所有政府数据
        self.update_all_gov_data()

        # 2. 计算经济指标
        indicators = self.calculate_economic_indicators()

        # 3. 生成交易信号
        signals = self.generate_trading_signals()

        # 4. 与HKEX数据结合
        self.combine_with_hkex_data()

        # 5. 生成报告
        self.generate_daily_report()

        print("\n" + "="*80)
        print("INTEGRATION COMPLETE!")
        print("="*80)
        print(f"All data available in: {self.data_dir}")

    def generate_daily_report(self):
        """生成日报"""
        report_file = self.data_dir / "daily_report.json"

        # 读取最新指标
        indicators_file = self.data_dir / "economic_indicators.json"
        indicators = {}
        if indicators_file.exists():
            indicators = json.loads(indicators_file.read_text())

        # 读取最新信号
        signals_file = self.data_dir / "trading_signals.json"
        signals = {}
        if signals_file.exists():
            signals = json.loads(signals_file.read_text())

        report = {
            "date": datetime.now().strftime('%Y-%m-%d'),
            "time": datetime.now().strftime('%H:%M:%S'),
            "economic_indicators": indicators,
            "trading_signals": signals,
            "data_sources": ["HIBOR", "Visitor Arrivals", "Traffic Speed", "AQHI", "MTR Passengers"],
            "integration_status": "COMPLETE"
        }

        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\nDaily report: {report_file}")


def main():
    """主函数"""
    system = IntegratedGovDataSystem()

    if len(sys.argv) > 1 and sys.argv[1] == "--update":
        # 仅更新数据
        system.update_all_gov_data()
    elif len(sys.argv) > 1 and sys.argv[1] == "--signals":
        # 仅生成信号
        system.generate_trading_signals()
    else:
        # 完整集成
        system.run_full_integration()


if __name__ == "__main__":
    main()
