"""
Phase 2 数据管道集成验证测试

验证替代数据框架 Phase 2 (数据管道和对齐) 的完整实现：
- 2.1 DataCleaner
- 2.2 TemporalAligner
- 2.3 DataNormalizer
- 2.4 QualityScorer
- 2.5 PipelineProcessor

运行: pytest tests/test_phase2_pipeline_integration.py -v -s
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, Any

# 导入数据管道组件
from src.data_pipeline.data_cleaner import DataCleaner
from src.data_pipeline.temporal_aligner import TemporalAligner
from src.data_pipeline.data_normalizer import DataNormalizer
from src.data_pipeline.quality_scorer import QualityScorer
from src.data_pipeline.pipeline_processor import PipelineProcessor


# ============================================================================
# 测试数据生成器
# ============================================================================

@pytest.fixture
def sample_alt_data():
    """生成示例替代数据（HIBOR + 访客数据）"""
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')

    data = pd.DataFrame({
        'date': dates,
        'hibor_overnight': np.random.normal(4.5, 0.5, len(dates)),
        'visitor_arrivals': np.random.normal(100000, 20000, len(dates)),
        'property_price': np.random.normal(50000, 5000, len(dates)),
    })

    # 添加一些缺失值
    data.loc[10:15, 'hibor_overnight'] = np.nan
    data.loc[50:55, 'visitor_arrivals'] = np.nan

    # 添加一些异常值
    data.loc[30, 'hibor_overnight'] = 100.0  # 明显的异常
    data.loc[100, 'visitor_arrivals'] = 500000  # 明显的异常

    return data.set_index('date')


@pytest.fixture
def sample_price_data():
    """生成示例价格数据"""
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')

    prices = 100 + np.random.randn(len(dates)).cumsum()
    volumes = np.random.randint(1000000, 10000000, len(dates))

    data = pd.DataFrame({
        'date': dates,
        'close': prices,
        'volume': volumes,
    })

    return data.set_index('date')


# ============================================================================
# 2.1 DataCleaner 单元测试
# ============================================================================

class TestDataCleaner:
    """DataCleaner 的单元测试"""

    def test_cleaner_initialization(self):
        """测试 DataCleaner 初始化"""
        cleaner = DataCleaner(strategy='balanced')
        assert cleaner.strategy == 'balanced'
        assert cleaner.report is None

    def test_missing_value_handling(self, sample_alt_data):
        """测试缺失值处理"""
        cleaner = DataCleaner(strategy='balanced')

        # 记录缺失值数量
        missing_before = sample_alt_data.isna().sum().sum()
        assert missing_before > 0, "示例数据应包含缺失值"

        # 清理数据
        cleaned = cleaner.clean(sample_alt_data)

        # 验证缺失值被处理
        missing_after = cleaned.isna().sum().sum()
        assert missing_after == 0, "清理后不应有缺失值"

        # 验证报告
        report = cleaner.get_report()
        assert report is not None
        assert report.missing_values_filled > 0
        assert report.missing_values_found == missing_before

    def test_outlier_detection(self, sample_alt_data):
        """测试异常值检测"""
        cleaner = DataCleaner(strategy='balanced', outlier_method='iqr')
        cleaned = cleaner.clean(sample_alt_data)

        report = cleaner.get_report()
        assert report.outliers_found > 0, "应检测到异常值"
        assert report.outliers_handled == report.outliers_found

    def test_cleaning_strategies(self, sample_alt_data):
        """测试不同的清理策略"""
        for strategy in ['conservative', 'balanced', 'aggressive']:
            cleaner = DataCleaner(strategy=strategy)
            cleaned = cleaner.clean(sample_alt_data)

            # 验证输出有效
            assert not cleaned.empty
            assert cleaned.shape[0] == sample_alt_data.shape[0]
            assert cleaned.isna().sum().sum() == 0


# ============================================================================
# 2.2 TemporalAligner 单元测试
# ============================================================================

class TestTemporalAligner:
    """TemporalAligner 的单元测试"""

    def test_aligner_initialization(self):
        """测试 TemporalAligner 初始化"""
        aligner = TemporalAligner()
        assert aligner.calendar is not None

    def test_trading_day_alignment(self, sample_alt_data):
        """测试交易日对齐"""
        aligner = TemporalAligner()

        # 原始数据可能包含周末
        original_dates = set(sample_alt_data.index.date)

        # 对齐到交易日
        aligned = aligner.align_to_trading_days(sample_alt_data)

        # 验证仅包含交易日
        aligned_dates = set(aligned.index.date)
        assert len(aligned_dates) <= len(original_dates)

    def test_frequency_conversion(self, sample_alt_data):
        """测试频率转换"""
        aligner = TemporalAligner()

        # 转换为周频率
        weekly = aligner.convert_frequency(sample_alt_data, 'W')

        # 验证周频率
        assert len(weekly) < len(sample_alt_data)
        assert isinstance(weekly.index[0], pd.Timestamp)

    def test_lagged_features(self, sample_alt_data):
        """测试滞后特征生成"""
        aligner = TemporalAligner()

        lagged = aligner.generate_lagged_features(
            sample_alt_data[['hibor_overnight']],
            lags=[1, 5, 20]
        )

        # 验证滞后列被添加
        assert 'hibor_overnight_lag1' in lagged.columns
        assert 'hibor_overnight_lag5' in lagged.columns
        assert 'hibor_overnight_lag20' in lagged.columns


# ============================================================================
# 2.3 DataNormalizer 单元测试
# ============================================================================

class TestDataNormalizer:
    """DataNormalizer 的单元测试"""

    def test_normalizer_initialization(self):
        """测试 DataNormalizer 初始化"""
        normalizer = DataNormalizer()
        assert normalizer is not None

    def test_zscore_normalization(self, sample_alt_data):
        """测试 Z-score 标准化"""
        normalizer = DataNormalizer()
        normalized = normalizer.zscore_normalize(sample_alt_data)

        # 验证均值接近0，标准差接近1
        for col in sample_alt_data.select_dtypes(include=[np.number]).columns:
            mean = normalized[col].mean()
            std = normalized[col].std()
            assert abs(mean) < 0.01, f"列 {col} 均值应接近 0"
            assert abs(std - 1.0) < 0.1, f"列 {col} 标准差应接近 1"

    def test_minmax_scaling(self, sample_alt_data):
        """测试 Min-Max 缩放"""
        normalizer = DataNormalizer()
        scaled = normalizer.minmax_scale(sample_alt_data)

        # 验证值在 [0, 1] 范围内
        numeric_data = scaled.select_dtypes(include=[np.number])
        assert (numeric_data >= 0).all().all()
        assert (numeric_data <= 1).all().all()

    def test_inverse_transform(self, sample_alt_data):
        """测试逆变换"""
        normalizer = DataNormalizer()

        # 标准化
        normalized = normalizer.zscore_normalize(sample_alt_data)

        # 逆变换
        restored = normalizer.inverse_zscore_normalize(normalized)

        # 验证恢复的数据接近原始数据
        pd.testing.assert_frame_equal(
            restored,
            sample_alt_data,
            atol=1e-10,
            check_dtype=False
        )


# ============================================================================
# 2.4 QualityScorer 单元测试
# ============================================================================

class TestQualityScorer:
    """QualityScorer 的单元测试"""

    def test_scorer_initialization(self):
        """测试 QualityScorer 初始化"""
        scorer = QualityScorer()
        assert scorer is not None

    def test_completeness_score(self):
        """测试完整性评分"""
        # 创建有缺失值的数据
        data = pd.DataFrame({
            'a': [1, 2, np.nan, 4, 5],
            'b': [1, 2, 3, 4, 5],  # 完整
        })

        scorer = QualityScorer()
        score_a = scorer.calculate_completeness_score(data['a'])
        score_b = scorer.calculate_completeness_score(data['b'])

        # b 列应得分更高（更完整）
        assert score_b > score_a
        assert 0 <= score_a <= 1
        assert 0 <= score_b <= 1

    def test_overall_quality_grade(self, sample_alt_data):
        """测试总体质量评级"""
        scorer = QualityScorer()
        grade = scorer.calculate_overall_grade(sample_alt_data)

        # 验证评级有效
        assert isinstance(grade, dict)
        assert 'score' in grade
        assert 'grade' in grade
        assert 0 <= grade['score'] <= 1
        assert grade['grade'] in ['POOR', 'FAIR', 'GOOD', 'EXCELLENT']


# ============================================================================
# 2.5 PipelineProcessor 集成测试
# ============================================================================

class TestPipelineProcessor:
    """PipelineProcessor 的集成测试"""

    def test_processor_initialization(self):
        """测试 PipelineProcessor 初始化"""
        processor = PipelineProcessor()
        assert processor is not None

    def test_full_pipeline_execution(self, sample_alt_data):
        """测试完整管道执行"""
        processor = PipelineProcessor()

        # 执行管道
        result = processor.process(sample_alt_data)

        # 验证输出
        assert not result.empty
        assert result.shape[0] == sample_alt_data.shape[0]
        assert result.isna().sum().sum() == 0

    def test_pipeline_with_config(self, sample_alt_data):
        """测试带配置的管道"""
        processor = PipelineProcessor()

        config = {
            'cleaning_strategy': 'balanced',
            'normalization_method': 'zscore',
            'generate_lagged_features': True,
            'lags': [1, 5],
        }

        result = processor.process(sample_alt_data, config)

        # 验证滞后特征被生成
        assert any('lag' in col for col in result.columns)


# ============================================================================
# 跨组件集成测试
# ============================================================================

class TestCrossComponentIntegration:
    """跨数据管道组件的集成测试"""

    def test_alt_data_to_price_alignment(self, sample_alt_data, sample_price_data):
        """测试替代数据与价格数据对齐"""
        # 清理替代数据
        cleaner = DataCleaner()
        cleaned_alt = cleaner.clean(sample_alt_data)

        # 对齐到交易日
        aligner = TemporalAligner()
        aligned_alt = aligner.align_to_trading_days(cleaned_alt)
        aligned_price = aligner.align_to_trading_days(sample_price_data)

        # 验证对齐
        assert len(aligned_alt) == len(aligned_price)
        pd.testing.assert_index_equal(aligned_alt.index, aligned_price.index)

    def test_normalization_preserves_relationships(self, sample_alt_data):
        """测试标准化保留数据关系"""
        # 计算原始相关性
        original_corr = sample_alt_data.corr().iloc[0, 1]

        # 标准化并计算相关性
        normalizer = DataNormalizer()
        normalized = normalizer.zscore_normalize(sample_alt_data)
        normalized_corr = normalized.corr().iloc[0, 1]

        # 相关性应保留
        assert abs(original_corr - normalized_corr) < 0.01

    def test_pipeline_output_quality(self, sample_alt_data):
        """测试管道输出质量"""
        processor = PipelineProcessor()
        result = processor.process(sample_alt_data)

        # 评估质量
        scorer = QualityScorer()
        grade = scorer.calculate_overall_grade(result)

        # 处理后的数据应有良好质量
        assert grade['score'] > 0.8 or grade['grade'] in ['GOOD', 'EXCELLENT']


# ============================================================================
# 性能和边界情况测试
# ============================================================================

class TestEdgeCases:
    """边界情况和性能测试"""

    def test_empty_dataframe_handling(self):
        """测试空 DataFrame 处理"""
        empty_df = pd.DataFrame()

        cleaner = DataCleaner()
        result = cleaner.clean(empty_df)

        assert result.empty

    def test_single_row_handling(self):
        """测试单行 DataFrame 处理"""
        single_row = pd.DataFrame({
            'a': [1],
            'b': [2],
        })

        cleaner = DataCleaner()
        result = cleaner.clean(single_row)

        assert len(result) == 1

    def test_all_nan_column_handling(self):
        """测试全 NaN 列处理"""
        data = pd.DataFrame({
            'a': [1, 2, 3],
            'b': [np.nan, np.nan, np.nan],
        })

        cleaner = DataCleaner()
        result = cleaner.clean(data)

        # 列 b 应被跳过或填充
        assert not result.empty

    def test_large_dataset_performance(self):
        """测试大型数据集性能"""
        # 创建大型数据集（10,000 行）
        large_data = pd.DataFrame({
            'a': np.random.normal(0, 1, 10000),
            'b': np.random.normal(100, 10, 10000),
            'c': np.random.normal(50, 5, 10000),
        })

        processor = PipelineProcessor()

        # 应在合理时间内完成
        import time
        start = time.time()
        result = processor.process(large_data)
        elapsed = time.time() - start

        assert elapsed < 10.0, "处理 10,000 行应在 10 秒内完成"
        assert len(result) == len(large_data)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
