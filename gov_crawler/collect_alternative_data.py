#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
香港替代數據收集脚本
收集 HIBOR、訪港旅客、貿易數據等替代數據源
"""

import sys
import os
import json
import logging
from pathlib import Path
from datetime import datetime, date, timedelta
import pandas as pd
from typing import Dict, List, Any

# 添加項目路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 設置日誌
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / f"collect_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("alternative_data_collector")

# 數據保存目錄
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)


class AlternativeDataCollector:
    """替代數據收集器"""

    def __init__(self):
        self.data_dir = DATA_DIR
        self.collected_data = {}
        logger.info(f"初始化數據收集器，數據目錄: {self.data_dir}")

    def collect_hibor_data(self, days=365) -> Dict[str, List[float]]:
        """收集 HIBOR 數據"""
        logger.info("=" * 60)
        logger.info("開始收集 HIBOR 數據")
        logger.info("=" * 60)

        try:
            from src.data_adapters.gov_data_collector import GovDataCollector

            collector = GovDataCollector(mode="mock")
            logger.info("✓ GovDataCollector 初始化成功")

            # 生成日期範圍
            end_date = date.today()
            start_date = end_date - timedelta(days=days)

            hibor_indicators = [
                "hibor_overnight",
                "hibor_1m",
                "hibor_3m",
                "hibor_6m",
                "hibor_12m"
            ]

            hibor_data = {}

            for indicator in hibor_indicators:
                try:
                    logger.info(f"獲取 {indicator}...")
                    # 使用 mock 模式生成數據
                    df = collector._generate_mock_data(indicator, start_date, end_date)

                    if df is not None and len(df) > 0:
                        hibor_data[indicator] = {
                            "values": df['value'].tolist(),
                            "dates": df['timestamp'].astype(str).tolist(),
                            "count": len(df),
                            "min": float(df['value'].min()),
                            "max": float(df['value'].max()),
                            "mean": float(df['value'].mean()),
                        }
                        logger.info(f"✓ {indicator}: {len(df)} 筆數據，範圍 {hibor_data[indicator]['min']:.2f}% - {hibor_data[indicator]['max']:.2f}%")
                    else:
                        logger.warning(f"⚠ {indicator}: 未獲得數據")

                except Exception as e:
                    logger.error(f"✗ {indicator} 失敗: {e}")

            self.collected_data['hibor'] = hibor_data
            return hibor_data

        except Exception as e:
            logger.error(f"✗ HIBOR 數據收集失敗: {e}")
            return {}

    def collect_visitor_data(self, months=12) -> Dict[str, Any]:
        """收集訪港旅客數據"""
        logger.info("\n" + "=" * 60)
        logger.info("開始收集訪港旅客數據")
        logger.info("=" * 60)

        try:
            from src.data_adapters.gov_data_collector import GovDataCollector

            collector = GovDataCollector(mode="mock")

            end_date = date.today()
            start_date = end_date - timedelta(days=30*months)

            visitor_indicators = [
                "visitor_arrivals_total",
                "visitor_arrivals_mainland",
                "visitor_arrivals_growth"
            ]

            visitor_data = {}

            for indicator in visitor_indicators:
                try:
                    logger.info(f"獲取 {indicator}...")
                    df = collector._generate_mock_data(indicator, start_date, end_date)

                    if df is not None and len(df) > 0:
                        visitor_data[indicator] = {
                            "values": df['value'].tolist(),
                            "dates": df['timestamp'].astype(str).tolist(),
                            "count": len(df),
                            "min": float(df['value'].min()),
                            "max": float(df['value'].max()),
                            "mean": float(df['value'].mean()),
                            "latest": float(df['value'].iloc[-1]) if len(df) > 0 else 0,
                        }
                        logger.info(f"✓ {indicator}: {len(df)} 筆數據，最新值 {visitor_data[indicator]['latest']:,.0f}")
                    else:
                        logger.warning(f"⚠ {indicator}: 未獲得數據")

                except Exception as e:
                    logger.error(f"✗ {indicator} 失敗: {e}")

            self.collected_data['visitors'] = visitor_data
            return visitor_data

        except Exception as e:
            logger.error(f"✗ 訪港旅客數據收集失敗: {e}")
            return {}

    def collect_trade_data(self, months=12) -> Dict[str, Any]:
        """收集貿易數據"""
        logger.info("\n" + "=" * 60)
        logger.info("開始收集貿易數據")
        logger.info("=" * 60)

        try:
            from src.data_adapters.gov_data_collector import GovDataCollector

            collector = GovDataCollector(mode="mock")

            end_date = date.today()
            start_date = end_date - timedelta(days=30*months)

            trade_indicators = [
                "trade_export",
                "trade_import",
                "trade_balance"
            ]

            trade_data = {}

            for indicator in trade_indicators:
                try:
                    logger.info(f"獲取 {indicator}...")
                    df = collector._generate_mock_data(indicator, start_date, end_date)

                    if df is not None and len(df) > 0:
                        trade_data[indicator] = {
                            "values": df['value'].tolist(),
                            "dates": df['timestamp'].astype(str).tolist(),
                            "count": len(df),
                            "min": float(df['value'].min()),
                            "max": float(df['value'].max()),
                            "mean": float(df['value'].mean()),
                            "latest": float(df['value'].iloc[-1]) if len(df) > 0 else 0,
                        }
                        logger.info(f"✓ {indicator}: {len(df)} 筆數據，最新值 HK${trade_data[indicator]['latest']:,.0f}")
                    else:
                        logger.warning(f"⚠ {indicator}: 未獲得數據")

                except Exception as e:
                    logger.error(f"✗ {indicator} 失敗: {e}")

            self.collected_data['trade'] = trade_data
            return trade_data

        except Exception as e:
            logger.error(f"✗ 貿易數據收集失敗: {e}")
            return {}

    def collect_economic_indicators(self, months=12) -> Dict[str, Any]:
        """收集經濟指標"""
        logger.info("\n" + "=" * 60)
        logger.info("開始收集經濟指標")
        logger.info("=" * 60)

        try:
            from src.data_adapters.gov_data_collector import GovDataCollector

            collector = GovDataCollector(mode="mock")

            end_date = date.today()
            start_date = end_date - timedelta(days=30*months)

            econ_indicators = [
                "unemployment_rate",
                "cpi"
            ]

            econ_data = {}

            for indicator in econ_indicators:
                try:
                    logger.info(f"獲取 {indicator}...")
                    df = collector._generate_mock_data(indicator, start_date, end_date)

                    if df is not None and len(df) > 0:
                        econ_data[indicator] = {
                            "values": df['value'].tolist(),
                            "dates": df['timestamp'].astype(str).tolist(),
                            "count": len(df),
                            "min": float(df['value'].min()),
                            "max": float(df['value'].max()),
                            "mean": float(df['value'].mean()),
                            "latest": float(df['value'].iloc[-1]) if len(df) > 0 else 0,
                        }
                        logger.info(f"✓ {indicator}: {len(df)} 筆數據，最新值 {econ_data[indicator]['latest']:.2f}")
                    else:
                        logger.warning(f"⚠ {indicator}: 未獲得數據")

                except Exception as e:
                    logger.error(f"✗ {indicator} 失敗: {e}")

            self.collected_data['economic'] = econ_data
            return econ_data

        except Exception as e:
            logger.error(f"✗ 經濟指標收集失敗: {e}")
            return {}

    def collect_from_http_api(self, symbol="0700.hk", duration=365) -> Dict[str, Any]:
        """從中心化 HTTP API 收集數據"""
        logger.info("\n" + "=" * 60)
        logger.info(f"從 HTTP API 收集 {symbol} 數據")
        logger.info("=" * 60)

        try:
            import requests
            from src.data_adapters.http_api_adapter import HTTPAPIAdapter

            api_url = "http://18.180.162.113:9191/inst/getInst"
            logger.info(f"API 端點: {api_url}")
            logger.info(f"符號: {symbol}, 期限: {duration} 天")

            try:
                response = requests.get(
                    api_url,
                    params={"symbol": symbol.lower(), "duration": duration},
                    timeout=30
                )

                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✓ API 返回數據成功")

                    # 提取基本信息
                    if isinstance(data, dict):
                        logger.info(f"  數據類型: {type(data)}")
                        logger.info(f"  包含鍵: {list(data.keys())[:5]}...")
                        if len(data) > 0:
                            logger.info(f"  數據條數: {len(data)}")

                    self.collected_data['http_api'] = {
                        "symbol": symbol,
                        "duration": duration,
                        "data_count": len(data) if isinstance(data, (list, dict)) else 0,
                        "status": "success",
                        "timestamp": datetime.now().isoformat(),
                    }

                    return self.collected_data['http_api']
                else:
                    logger.error(f"✗ API 返回狀態碼 {response.status_code}")
                    return {}

            except requests.Timeout:
                logger.warning("⚠ API 連接超時")
                return {}
            except requests.ConnectionError as e:
                logger.warning(f"⚠ 無法連接到 API: {e}")
                return {}

        except Exception as e:
            logger.error(f"✗ HTTP API 數據收集失敗: {e}")
            return {}

    def save_data(self):
        """保存所有收集的數據"""
        logger.info("\n" + "=" * 60)
        logger.info("保存收集的數據")
        logger.info("=" * 60)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 保存為 JSON
        json_file = self.data_dir / f"alternative_data_{timestamp}.json"
        try:
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(self.collected_data, f, ensure_ascii=False, indent=2)
            logger.info(f"✓ JSON 文件已保存: {json_file}")
        except Exception as e:
            logger.error(f"✗ JSON 保存失敗: {e}")

        # 保存為 CSV（HIBOR 數據）
        if 'hibor' in self.collected_data and self.collected_data['hibor']:
            try:
                hibor_df = pd.DataFrame()
                for indicator, data in self.collected_data['hibor'].items():
                    if 'dates' in data and 'values' in data:
                        temp_df = pd.DataFrame({
                            'date': pd.to_datetime(data['dates']),
                            indicator: data['values']
                        })
                        if len(hibor_df) == 0:
                            hibor_df = temp_df
                        else:
                            hibor_df = hibor_df.merge(temp_df, on='date', how='outer')

                if len(hibor_df) > 0:
                    hibor_df = hibor_df.set_index('date')
                    hibor_df = hibor_df.sort_index()
                    csv_file = self.data_dir / f"hibor_data_{timestamp}.csv"
                    hibor_df.to_csv(csv_file)
                    logger.info(f"✓ HIBOR CSV 文件已保存: {csv_file}")
            except Exception as e:
                logger.error(f"✗ HIBOR CSV 保存失敗: {e}")

        # 保存為 CSV（訪港旅客數據）
        if 'visitors' in self.collected_data and self.collected_data['visitors']:
            try:
                visitor_df = pd.DataFrame()
                for indicator, data in self.collected_data['visitors'].items():
                    if 'dates' in data and 'values' in data:
                        temp_df = pd.DataFrame({
                            'date': pd.to_datetime(data['dates']),
                            indicator: data['values']
                        })
                        if len(visitor_df) == 0:
                            visitor_df = temp_df
                        else:
                            visitor_df = visitor_df.merge(temp_df, on='date', how='outer')

                if len(visitor_df) > 0:
                    visitor_df = visitor_df.set_index('date')
                    visitor_df = visitor_df.sort_index()
                    csv_file = self.data_dir / f"visitor_data_{timestamp}.csv"
                    visitor_df.to_csv(csv_file)
                    logger.info(f"✓ 訪客 CSV 文件已保存: {csv_file}")
            except Exception as e:
                logger.error(f"✗ 訪客 CSV 保存失敗: {e}")

        # 保存摘要
        summary = {
            "collection_time": datetime.now().isoformat(),
            "data_sources": list(self.collected_data.keys()),
            "summary": {
                key: {
                    "count": len(value) if isinstance(value, dict) else 0,
                    "indicators": list(value.keys()) if isinstance(value, dict) else []
                }
                for key, value in self.collected_data.items()
            }
        }

        summary_file = self.data_dir / f"summary_{timestamp}.json"
        try:
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            logger.info(f"✓ 摘要文件已保存: {summary_file}")
        except Exception as e:
            logger.error(f"✗ 摘要保存失敗: {e}")

        logger.info(f"✓ 所有數據已保存到: {self.data_dir}")
        return json_file, summary_file

    def run(self):
        """運行完整的數據收集流程"""
        logger.info("\n")
        logger.info("╔" + "=" * 58 + "╗")
        logger.info("║  香港替代數據收集器 - 完整數據收集             ║")
        logger.info("╚" + "=" * 58 + "╝")

        try:
            # 收集各類數據
            self.collect_hibor_data(days=365)
            self.collect_visitor_data(months=12)
            self.collect_trade_data(months=12)
            self.collect_economic_indicators(months=12)

            # 嘗試從 HTTP API 收集
            self.collect_from_http_api(symbol="0700.hk", duration=365)

            # 保存數據
            json_file, summary_file = self.save_data()

            # 最終統計
            logger.info("\n" + "=" * 60)
            logger.info("數據收集完成統計")
            logger.info("=" * 60)
            logger.info(f"✓ 總共收集 {len(self.collected_data)} 個數據源")
            logger.info(f"✓ 數據保存位置:")
            logger.info(f"  - 主數據文件: {json_file}")
            logger.info(f"  - 摘要文件: {summary_file}")
            logger.info(f"  - 數據目錄: {self.data_dir}")

            # 列出數據目錄中的文件
            logger.info(f"\n✓ {self.data_dir} 中的文件:")
            for file in sorted(self.data_dir.glob("*"))[-5:]:
                size = file.stat().st_size if file.is_file() else 0
                logger.info(f"  - {file.name} ({size:,} bytes)")

            logger.info("=" * 60)
            return True

        except Exception as e:
            logger.error(f"\n✗ 數據收集過程出錯: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    collector = AlternativeDataCollector()
    success = collector.run()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
