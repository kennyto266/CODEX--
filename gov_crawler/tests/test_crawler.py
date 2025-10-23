"""
GOV 爬蟲系統 - 單元測試
"""

import unittest
import os
import json
import tempfile
from pathlib import Path
import sys

# 添加源代碼路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils import load_config, ProgressTracker
from src.data_processor import DataProcessor
from src.storage_manager import StorageManager
import pandas as pd


class TestUtils(unittest.TestCase):
    """測試工具函數"""

    def test_load_config(self):
        """測試配置加載"""
        config = load_config('config.yaml')
        self.assertIsNotNone(config)
        self.assertIn('crawler', config)
        self.assertIn('datasets', config)
        self.assertIn('storage', config)

    def test_progress_tracker(self):
        """測試進度跟蹤器"""
        tracker = ProgressTracker(total=10, name="測試進度")
        tracker.update(5)
        tracker.update(5)
        elapsed = tracker.finish()
        self.assertGreater(elapsed, 0)


class TestDataProcessor(unittest.TestCase):
    """測試數據處理器"""

    def setUp(self):
        """設置測試環境"""
        self.processor = DataProcessor()

    def test_clean_dataframe(self):
        """測試 DataFrame 清理"""
        # 創建含有空值和重複的 DataFrame
        df = pd.DataFrame({
            'A': [1, 2, None, 2],
            'B': [4, None, None, 5],
            'C': [None, None, None, None]
        })

        cleaned = DataProcessor._clean_dataframe(df)
        self.assertLess(len(cleaned), len(df))
        self.assertNotIn('C', cleaned.columns)

    def test_calculate_statistics(self):
        """測試統計計算"""
        df = pd.DataFrame({
            'A': [1, 2, 3, 4, 5],
            'B': [10, 20, 30, 40, 50]
        })

        stats = self.processor.calculate_statistics(df)
        self.assertEqual(stats['row_count'], 5)
        self.assertEqual(stats['column_count'], 2)
        self.assertIn('A', stats['columns'])
        self.assertIn('B', stats['columns'])

    def test_validate_data_quality(self):
        """測試數據質量驗證"""
        # 創建高質量數據
        df_good = pd.DataFrame({
            'A': [1, 2, 3, 4, 5],
            'B': [10, 20, 30, 40, 50]
        })

        quality = self.processor.validate_data_quality(df_good)
        self.assertTrue(quality['is_valid'])
        self.assertEqual(quality['total_rows'], 5)

        # 創建低質量數據
        df_bad = pd.DataFrame({
            'A': [None, None, None, None, None],
            'B': [None, None, None, None, None]
        })

        quality = self.processor.validate_data_quality(df_bad)
        self.assertFalse(quality['is_valid'])

    def test_normalize_columns(self):
        """測試列名標準化"""
        df = pd.DataFrame({
            'Column A': [1, 2, 3],
            'Column-B': [4, 5, 6],
            'Column C': [7, 8, 9]
        })

        normalized = DataProcessor.normalize_columns(df)
        self.assertIn('column_a', normalized.columns)
        self.assertIn('column_b', normalized.columns)
        self.assertIn('column_c', normalized.columns)


class TestStorageManager(unittest.TestCase):
    """測試存儲管理器"""

    def setUp(self):
        """設置測試環境"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = {
            'storage': {
                'raw_data_dir': os.path.join(self.temp_dir, 'raw'),
                'processed_data_dir': os.path.join(self.temp_dir, 'processed'),
                'metadata_dir': os.path.join(self.temp_dir, 'metadata'),
                'archive_dir': os.path.join(self.temp_dir, 'archive'),
                'formats': ['csv', 'json']
            }
        }
        self.storage = StorageManager(self.config)

    def tearDown(self):
        """清理測試環境"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_save_raw_data(self):
        """測試保存原始數據"""
        data = {'test': 'data', 'value': 123}
        filepath = self.storage.save_raw_data('test_dataset', data)
        self.assertIsNotNone(filepath)
        self.assertTrue(os.path.exists(filepath))

    def test_save_processed_data_csv(self):
        """測試保存處理後的數據 (CSV)"""
        df = pd.DataFrame({
            'A': [1, 2, 3],
            'B': [4, 5, 6]
        })
        filepath = self.storage.save_processed_data('test_dataset', df, format='csv')
        self.assertIsNotNone(filepath)
        self.assertTrue(os.path.exists(filepath))

    def test_save_processed_data_json(self):
        """測試保存處理後的數據 (JSON)"""
        df = pd.DataFrame({
            'A': [1, 2, 3],
            'B': [4, 5, 6]
        })
        filepath = self.storage.save_processed_data('test_dataset', df, format='json')
        self.assertIsNotNone(filepath)
        self.assertTrue(os.path.exists(filepath))

    def test_save_metadata(self):
        """測試保存元信息"""
        metadata = {'key': 'value', 'count': 100}
        filepath = self.storage.save_metadata('test_dataset', metadata)
        self.assertIsNotNone(filepath)
        self.assertTrue(os.path.exists(filepath))

    def test_load_metadata(self):
        """測試加載元信息"""
        # 先保存
        metadata = {'key': 'value', 'count': 100}
        self.storage.save_metadata('test_dataset', metadata)

        # 再加載
        loaded = self.storage.load_metadata('test_dataset')
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded['key'], 'value')
        self.assertEqual(loaded['count'], 100)

    def test_list_files(self):
        """測試列出文件"""
        # 創建一些文件
        for i in range(3):
            df = pd.DataFrame({'A': [i, i+1, i+2]})
            self.storage.save_processed_data(f'dataset_{i}', df)

        files = self.storage.list_files('processed')
        self.assertGreater(len(files), 0)

    def test_get_storage_stats(self):
        """測試獲取存儲統計"""
        # 創建一些數據
        df = pd.DataFrame({'A': [1, 2, 3]})
        self.storage.save_processed_data('test', df)

        stats = self.storage.get_storage_stats()
        self.assertIn('raw_data_count', stats)
        self.assertIn('processed_data_count', stats)
        self.assertIn('total_size_bytes', stats)


def run_tests():
    """運行所有測試"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加測試
    suite.addTests(loader.loadTestsFromTestCase(TestUtils))
    suite.addTests(loader.loadTestsFromTestCase(TestDataProcessor))
    suite.addTests(loader.loadTestsFromTestCase(TestStorageManager))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
