#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
xlsx Stock Analysis - Data Preprocessing Module
數據預處理模組，用於讀取、驗證、清洗和整合股票數據
"""

import pandas as pd
import numpy as np
import os
import glob
import json
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import warnings

warnings.filterwarnings('ignore')

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StockDataPreprocessor:
    """股票數據預處理器"""

    def __init__(self, data_dir: str = "."):
        """初始化預處理器

        Args:
            data_dir: 數據目錄路徑
        """
        self.data_dir = data_dir
        self.stock_dir = os.path.join(data_dir, "hk-stock-quant-system/data_output/csv")
        self.analysis_dir = os.path.join(data_dir, "analysis_output")
        self.portfolio_file = os.path.join(data_dir, "data/portfolio_12345.json")
        self.raw_data = {}
        self.cleaned_data = {}
        self.validation_report = {}

    def read_csv_data(self, file_patterns: List[str]) -> Dict[str, pd.DataFrame]:
        """讀取CSV數據文件

        Args:
            file_patterns: 文件路徑模式列表

        Returns:
            Dict[str, pd.DataFrame]: 數據字典，key為文件名，value為DataFrame
        """
        data_dict = {}
        logger.info(f"開始讀取CSV數據文件...")

        for pattern in file_patterns:
            # 擴展glob模式
            files = glob.glob(pattern)
            if not files:
                logger.warning(f"未找到匹配的文件: {pattern}")
                continue

            for file_path in files:
                try:
                    # 讀取文件
                    df = pd.read_csv(file_path, index_col=0, parse_dates=True)
                    file_key = os.path.basename(file_path).replace('.csv', '')
                    data_dict[file_key] = df
                    logger.info(f"成功讀取: {file_path}, 記錄數: {len(df)}")
                except Exception as e:
                    logger.error(f"讀取文件失敗 {file_path}: {str(e)}")

        logger.info(f"完成數據讀取，總共讀取 {len(data_dict)} 個文件")
        self.raw_data = data_dict
        return data_dict

    def validate_data(self, data_dict: Dict[str, pd.DataFrame]) -> Dict[str, Dict]:
        """驗證數據質量

        Args:
            data_dict: 數據字典

        Returns:
            Dict[str, Dict]: 驗證報告
        """
        logger.info("開始數據驗證...")

        validation_report = {}
        total_files = len(data_dict)
        passed_files = 0

        for file_key, df in data_dict.items():
            file_report = {
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'missing_values': df.isnull().sum().to_dict(),
                'missing_percentage': (df.isnull().sum() / len(df) * 100).to_dict(),
                'data_types': df.dtypes.to_dict(),
                'date_range': None,
                'numeric_columns': [],
                'issues': [],
                'score': 0
            }

            # 檢查日期範圍
            if df.index.dtype == 'datetime64[ns]':
                file_report['date_range'] = {
                    'start': df.index.min().strftime('%Y-%m-%d'),
                    'end': df.index.max().strftime('%Y-%m-%d'),
                    'trading_days': len(df)
                }

            # 檢查數值列
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            file_report['numeric_columns'] = numeric_cols

            # 檢查數據質量問題
            issues = []

            # 檢查空值
            if df.isnull().any().any():
                issues.append(f"發現空值: {df.isnull().sum().sum()} 個")

            # 檢查重複日期
            if df.index.has_duplicates:
                issues.append(f"發現重複日期: {df.index.duplicated().sum()} 個")

            # 檢查數值範圍（對價格數據）
            if 'close' in df.columns or 'Close' in df.columns:
                price_col = 'close' if 'close' in df.columns else 'Close'
                if (df[price_col] <= 0).any():
                    issues.append(f"發現無效價格 (<= 0): {(df[price_col] <= 0).sum()} 個")

            # 檢查交易量
            if 'volume' in df.columns or 'Volume' in df.columns:
                vol_col = 'volume' if 'volume' in df.columns else 'Volume'
                if (df[vol_col] < 0).any():
                    issues.append(f"發現無效交易量 (< 0): {(df[vol_col] < 0).sum()} 個")

            file_report['issues'] = issues

            # 計算質量評分
            score = 100
            if df.isnull().any().sum() > 0:
                score -= 20
            if df.index.has_duplicates:
                score -= 20
            if 'close' in df.columns and (df['close'] <= 0).any():
                score -= 30
            file_report['score'] = max(0, score)

            validation_report[file_key] = file_report

            if score >= 80:
                passed_files += 1

        self.validation_report = validation_report

        logger.info(f"數據驗證完成: {passed_files}/{total_files} 文件通過檢查")
        return validation_report

    def clean_data(self, data_dict: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """清洗數據

        Args:
            data_dict: 原始數據字典

        Returns:
            Dict[str, pd.DataFrame]: 清洗後的數據字典
        """
        logger.info("開始數據清洗...")

        cleaned_data = {}
        total_processed = 0

        for file_key, df in data_dict.items():
            try:
                # 創建副本
                cleaned_df = df.copy()

                # 移除重複的日期索引
                if cleaned_df.index.has_duplicates:
                    initial_len = len(cleaned_df)
                    cleaned_df = cleaned_df[~cleaned_df.index.duplicated(keep='first')]
                    removed = initial_len - len(cleaned_df)
                    if removed > 0:
                        logger.info(f"{file_key}: 移除 {removed} 個重複日期")

                # 處理缺失值
                numeric_cols = cleaned_df.select_dtypes(include=[np.number]).columns
                if len(numeric_cols) > 0:
                    # 對於價格數據，使用前向填充
                    for col in numeric_cols:
                        if 'close' in col.lower() or 'price' in col.lower():
                            cleaned_df[col] = cleaned_df[col].fillna(method='ffill')
                        # 對於其他數值，使用前向填充然後後向填充
                        cleaned_df[col] = cleaned_df[col].fillna(method='ffill').fillna(method='bfill')

                # 檢查並處理異常值（簡單的3-sigma規則）
                for col in numeric_cols:
                    if col in cleaned_df.columns:
                        Q1 = cleaned_df[col].quantile(0.25)
                        Q3 = cleaned_df[col].quantile(0.75)
                        IQR = Q3 - Q1
                        lower_bound = Q1 - 3 * IQR
                        upper_bound = Q3 + 3 * IQR

                        outliers = cleaned_df[(cleaned_df[col] < lower_bound) |
                                             (cleaned_df[col] > upper_bound)]
                        if len(outliers) > 0:
                            logger.info(f"{file_key}.{col}: 發現 {len(outliers)} 個異常值")

                # 統一數據類型
                cleaned_df = cleaned_df.astype({
                    col: 'float64' for col in cleaned_df.select_dtypes(include=[np.number]).columns
                })

                cleaned_data[file_key] = cleaned_df
                total_processed += 1
                logger.info(f"完成清洗: {file_key}, 記錄數: {len(cleaned_df)}")

            except Exception as e:
                logger.error(f"清洗數據失敗 {file_key}: {str(e)}")
                cleaned_data[file_key] = df  # 使用原始數據

        self.cleaned_data = cleaned_data
        logger.info(f"數據清洗完成，總共處理 {total_processed} 個文件")
        return cleaned_data

    def merge_data(self, cleaned_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """整合數據為統一格式

        Args:
            cleaned_data: 清洗後的數據字典

        Returns:
            pd.DataFrame: 整合後的DataFrame
        """
        logger.info("開始數據整合...")

        # 分離股票數據和策略數據
        stock_data = {}
        strategy_data = {}

        for file_key, df in cleaned_data.items():
            if '_vs_stock' in file_key:
                # 這是策略回測數據
                strategy_data[file_key] = df
            elif 'HK_' in file_key and not any(s in file_key for s in ['boll', 'kd', 'macd', 'momentum', 'rsi', 'smaema']):
                # 這是股票價格數據
                stock_data[file_key] = df

        # 創建主數據集（股票價格）
        if stock_data:
            main_df = list(stock_data.values())[0].copy()
            logger.info(f"主數據集基於: {list(stock_data.keys())[0]}")
        else:
            logger.warning("未找到股票價格數據")
            return pd.DataFrame()

        # 如果有多個股票數據，合併它們
        if len(stock_data) > 1:
            for key, df in list(stock_data.items())[1:]:
                main_df = main_df.join(df, rsuffix=f'_{key}', how='outer')
                logger.info(f"合併股票數據: {key}")

        # 添加策略數據
        strategy_summary = {}
        for key, df in strategy_data.items():
            # 提取策略名稱和股票代碼
            parts = key.split('_')
            if len(parts) >= 3:
                stock_code = parts[0]
                strategy_name = parts[1] if parts[1] != 'vs' else parts[2]
                strategy_name = strategy_name.replace('_vs_stock', '')

                if strategy_name not in strategy_summary:
                    strategy_summary[strategy_name] = {}

                strategy_summary[strategy_name][stock_code] = {
                    'final_return': df.iloc[-1, 1] if len(df) > 1 else 1.0,  # 假設第二列是累積收益
                    'total_return': (df.iloc[-1, 1] - 1.0) * 100 if len(df) > 1 else 0,
                    'trading_days': len(df)
                }

        # 創建策略表現摘要
        if strategy_summary:
            strategy_df = pd.DataFrame(strategy_summary).T
            strategy_df.index.name = 'Strategy'
            logger.info(f"創建策略表現摘要，包含 {len(strategy_summary)} 種策略")

        # 保存整合結果
        self.merged_data = main_df
        self.strategy_summary = strategy_summary

        logger.info(f"數據整合完成，主數據集形狀: {main_df.shape}")
        return main_df

    def generate_validation_report(self) -> str:
        """生成驗證報告

        Returns:
            str: 驗證報告文本
        """
        if not self.validation_report:
            return "無驗證報告數據"

        report_lines = ["=" * 60, "數據驗證報告", "=" * 60, ""]

        for file_key, report in self.validation_report.items():
            report_lines.append(f"文件: {file_key}")
            report_lines.append(f"  記錄數: {report['total_rows']}")
            report_lines.append(f"  評分: {report['score']}/100")

            if report['date_range']:
                report_lines.append(f"  日期範圍: {report['date_range']['start']} 到 {report['date_range']['end']}")
                report_lines.append(f"  交易日數: {report['date_range']['trading_days']}")

            if report['issues']:
                report_lines.append("  問題:")
                for issue in report['issues']:
                    report_lines.append(f"    - {issue}")
            else:
                report_lines.append("  無問題")

            report_lines.append("")

        report_text = "\n".join(report_lines)
        return report_text

    def save_processed_data(self, output_dir: str = "processed_data"):
        """保存處理後的數據

        Args:
            output_dir: 輸出目錄
        """
        os.makedirs(output_dir, exist_ok=True)

        # 保存清洗後的數據
        if self.cleaned_data:
            for file_key, df in self.cleaned_data.items():
                output_path = os.path.join(output_dir, f"{file_key}_clean.csv")
                df.to_csv(output_path)
                logger.info(f"保存清洗數據: {output_path}")

        # 保存整合數據
        if hasattr(self, 'merged_data') and not self.merged_data.empty:
            output_path = os.path.join(output_dir, "merged_stock_data.csv")
            self.merged_data.to_csv(output_path)
            logger.info(f"保存整合數據: {output_path}")

        # 保存策略摘要
        if hasattr(self, 'strategy_summary') and self.strategy_summary:
            output_path = os.path.join(output_dir, "strategy_summary.json")
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.strategy_summary, f, indent=2, ensure_ascii=False)
            logger.info(f"保存策略摘要: {output_path}")

        # 保存驗證報告
        report_text = self.generate_validation_report()
        output_path = os.path.join(output_dir, "validation_report.txt")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
        logger.info(f"保存驗證報告: {output_path}")


def main():
    """主函數 - 用於測試"""
    preprocessor = StockDataPreprocessor()

    # 定義要讀取的文件模式
    file_patterns = [
        "hk-stock-quant-system/data_output/csv/0001_HK_*.csv",
        "hk-stock-quant-system/data_output/csv/0700_HK_*.csv",
        "analysis_output/*.csv"
    ]

    # 執行預處理流程
    print("開始數據預處理流程...")

    # 1. 讀取數據
    raw_data = preprocessor.read_csv_data(file_patterns)
    if not raw_data:
        print("錯誤：未能讀取任何數據")
        return

    # 2. 驗證數據
    validation_report = preprocessor.validate_data(raw_data)

    # 3. 清洗數據
    cleaned_data = preprocessor.clean_data(raw_data)

    # 4. 整合數據
    merged_data = preprocessor.merge_data(cleaned_data)

    # 5. 保存處理結果
    preprocessor.save_processed_data()

    # 6. 輸出摘要
    print("\n" + "=" * 60)
    print("數據預處理完成")
    print("=" * 60)
    print(f"原始數據文件數: {len(raw_data)}")
    print(f"清洗後數據文件數: {len(cleaned_data)}")
    if not merged_data.empty:
        print(f"整合數據形狀: {merged_data.shape}")
    if hasattr(preprocessor, 'strategy_summary'):
        print(f"策略數量: {len(preprocessor.strategy_summary)}")

    # 打印驗證摘要
    print("\n" + preprocessor.generate_validation_report())

    print("\n處理後的數據已保存到 'processed_data' 目錄")


if __name__ == "__main__":
    main()
