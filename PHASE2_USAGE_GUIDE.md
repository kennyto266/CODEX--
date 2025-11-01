# Phase 2 Data Pipeline - Quick Reference Guide

## Overview

The Phase 2 data pipeline provides a complete framework for data cleaning, alignment, normalization, and quality scoring. Use it to prepare alternative data for quantitative analysis.

---

## Quick Start

### Basic Usage (Complete Pipeline)

```python
from src.data_pipeline.pipeline_processor import PipelineProcessor
import pandas as pd

# Load your data
df = pd.read_csv("your_data.csv")

# Create pipeline with all steps
processor = PipelineProcessor(verbose=True)

# Add default steps: clean → align → normalize → score
processor.add_step("clean", "clean",
    config={"missing_value_strategy": "interpolate"})
processor.add_step("align", "align",
    config={"align_to_trading_days": True})
processor.add_step("normalize", "normalize",
    config={"method": "zscore"})
processor.add_step("score", "score")

# Process data
result = processor.process(df, date_column="date", numeric_columns=["volume", "price"])

# Get report
processor.print_report()
```

---

## Module Reference

### 1. DataCleaner

**Purpose**: Handle missing values and outliers

**Example**:
```python
from src.data_pipeline.data_cleaner import DataCleaner

cleaner = DataCleaner(
    missing_value_strategy="interpolate",  # or "forward_fill", "mean", etc.
    outlier_strategy="cap",               # or "remove", "zscore_cap", etc.
    z_score_threshold=3.0,
    iqr_multiplier=1.5
)

cleaned_df = cleaner.clean(df, numeric_columns=["volume", "price"])
```

**Strategies**:
- Missing: drop, forward_fill, backward_fill, interpolate, mean, median, hybrid
- Outliers: remove, cap, zscore_cap, flag, keep

---

### 2. TemporalAligner

**Purpose**: Align time-series data to trading days and generate features

**Example**:
```python
from src.data_pipeline.temporal_aligner import TemporalAligner

aligner = TemporalAligner()

# Align to trading days
aligned_df = aligner.align_to_trading_days(df, date_column="date")

# Generate lagged features
lagged_df = aligner.generate_lagged_features(
    aligned_df,
    columns=["volume", "price"],
    lags=[1, 5, 20]
)

# Generate rolling features
rolling_df = aligner.generate_rolling_features(
    lagged_df,
    columns=["volume"],
    windows=[5, 20],
    functions=["mean", "std"]
)

# Compute returns
returns_df = aligner.compute_returns(
    rolling_df,
    price_columns=["price"],
    return_type="log",
    periods=[1, 5]
)
```

**Features Generated**:
- Lagged: `{col}_lag_{n}` (e.g., volume_lag_5)
- Rolling: `{col}_roll_{window}d_{func}` (e.g., price_roll_20d_mean)
- Returns: `{col}_return_{n}d` (e.g., price_return_5d)

---

### 3. DataNormalizer

**Purpose**: Normalize data for ML models

**Example**:
```python
from src.data_pipeline.data_normalizer import DataNormalizer

# Z-score normalization
normalizer = DataNormalizer(method="zscore")
normalized_df = normalizer.fit_transform(df, columns=["volume", "price"])

# Reverse normalization
original_df = normalizer.inverse_transform(normalized_df, columns=["volume", "price"])
```

**Methods**:
- zscore: (x - mean) / std
- minmax: (x - min) / (max - min)
- log: log(x)
- robust: (x - median) / IQR

**Pipeline**:
```python
from src.data_pipeline.data_normalizer import DataNormalizerPipeline

pipeline = DataNormalizerPipeline()
pipeline.add_normalizer("volume_zscore", ["volume"], method="zscore")
pipeline.add_normalizer("price_minmax", ["price"], method="minmax")

result = pipeline.fit_transform(df)
```

---

### 4. QualityScorer

**Purpose**: Assess data quality across multiple dimensions

**Example**:
```python
from src.data_pipeline.quality_scorer import QualityScorer

scorer = QualityScorer(
    completeness_weight=0.5,
    freshness_weight=0.3,
    consistency_weight=0.2,
    max_age_hours=24
)

# Calculate quality
score = scorer.calculate_quality(df, date_column="date")

# Get grade
grade = scorer.get_grade()  # Returns "A", "B", "C", "D", or "F"

# Print report
print(scorer.generate_quality_report_text())

# Check if acceptable
is_acceptable = scorer.is_quality_acceptable(min_grade="B")
```

**Quality Dimensions**:
- Completeness: % of non-null values
- Freshness: Recency of data (based on date_column)
- Consistency: Uniformity and stability (via coefficient of variation)

**Grades**:
- A (0.9-1.0): Excellent
- B (0.8-0.9): Good
- C (0.7-0.8): Fair
- D (0.6-0.7): Poor
- F (0.0-0.6): Very Poor

---

### 5. PipelineProcessor

**Purpose**: Orchestrate the complete pipeline

**Example**:
```python
from src.data_pipeline.pipeline_processor import PipelineProcessor

# Create processor
processor = PipelineProcessor(checkpoint_enabled=True, verbose=True)

# Add steps
processor.add_step("clean", "clean", config={
    "missing_value_strategy": "mean",
    "outlier_strategy": "cap"
})

processor.add_step("align", "align", config={
    "align_to_trading_days": True,
    "generate_lags": True,
    "lag_columns": ["volume", "price"],
    "lags": [1, 5]
})

processor.add_step("normalize", "normalize", config={
    "method": "zscore"
})

processor.add_step("score", "score")

# Process
result = processor.process(df, date_column="date", numeric_columns=["volume", "price"])

# Get report
report = processor.get_report()
print(f"Execution time: {report['execution']['duration_seconds']:.2f}s")
print(f"Quality score: {report['statistics']['quality_score']:.1%}")
```

---

## Advanced Use Cases

### Use Case 1: Custom Pipeline for Specific Data Type

```python
processor = PipelineProcessor()

# For financial data with extreme values
processor.add_step("clean", "clean", config={
    "missing_value_strategy": "interpolate",
    "outlier_strategy": "zscore_cap",
    "z_score_threshold": 2.5  # More sensitive
})

processor.add_step("normalize", "normalize", config={
    "method": "robust"  # Resistant to remaining outliers
})

result = processor.process(df)
```

### Use Case 2: Feature Engineering Pipeline

```python
processor = PipelineProcessor()

processor.add_step("align", "align", config={
    "align_to_trading_days": True,
    "generate_lags": True,
    "lag_columns": ["volume", "price"],
    "lags": [1, 5, 10, 20, 60],
    "generate_rolling": True,
    "rolling_columns": ["volume", "price"],
    "windows": [5, 20, 60],
    "functions": ["mean", "std", "min", "max"],
    "compute_returns": True,
    "price_columns": ["price"],
    "return_type": "log",
    "return_periods": [1, 5, 20]
})

result = processor.process(df)
# Result will have 100+ features
```

### Use Case 3: Quality-First Pipeline

```python
processor = PipelineProcessor()

# Check quality first
processor.add_step("score", "score", config={
    "completeness_weight": 0.6,
    "freshness_weight": 0.3,
    "consistency_weight": 0.1
})

processor.add_step("clean", "clean", config={
    "missing_value_strategy": "drop",  # Remove any missing
    "outlier_strategy": "remove"        # Remove any outliers
})

processor.add_step("normalize", "normalize")

result = processor.process(df)
quality_report = processor.statistics
if quality_report["quality_score"] >= 0.9:
    print("Data is excellent quality!")
else:
    print("Warning: Data quality concerns")
```

### Use Case 4: Integration with AlternativeDataService

```python
from src.data_adapters.alternative_data_service import AlternativeDataService

service = AlternativeDataService()

# Configure pipeline
service.configure_pipeline([
    ("clean", "clean", {"missing_value_strategy": "interpolate"}),
    ("align", "align", {"align_to_trading_days": True}),
    ("normalize", "normalize", {"method": "zscore"}),
    ("score", "score", {})
])

# Get and process data in one call
aligned_data = service.get_aligned_data(
    adapter_name="hkex",
    indicator_code="HSI",
    start_date="2025-01-01",
    end_date="2025-10-31",
    apply_pipeline=True,
    date_column="date"
)

# Get report
report = service.get_pipeline_report()
```

---

## Configuration Examples

### Conservative Cleaning (Quality-First)
```python
config = {
    "missing_value_strategy": "drop",
    "outlier_strategy": "remove",
    "z_score_threshold": 2.0,  # More sensitive
    "iqr_multiplier": 1.5
}
```

### Aggressive Cleaning (Preserve Data)
```python
config = {
    "missing_value_strategy": "hybrid",
    "outlier_strategy": "cap",
    "z_score_threshold": 4.0,  # Less sensitive
    "iqr_multiplier": 2.0
}
```

### Trading Calendar with Features
```python
config = {
    "align_to_trading_days": True,
    "generate_lags": True,
    "lag_columns": ["volume", "price"],
    "lags": [1, 5, 20],
    "generate_rolling": True,
    "rolling_columns": ["volume"],
    "windows": [20],
    "functions": ["mean", "std"],
    "compute_returns": True,
    "price_columns": ["price"],
    "return_type": "log",
    "return_periods": [1, 5]
}
```

---

## Error Handling

### Handle Missing Data

```python
try:
    processor = PipelineProcessor()
    processor.add_step("clean", "clean")
    result = processor.process(df)

    if processor.has_errors():
        print("Errors during processing:")
        for error in processor.execution_log["errors"]:
            print(f"  - {error}")
except Exception as e:
    print(f"Fatal error: {e}")
```

### Check Quality After Processing

```python
processor = PipelineProcessor()
processor.add_step("clean", "clean")
processor.add_step("score", "score")

result = processor.process(df)

quality_score = processor.statistics["quality_score"]
if quality_score < 0.7:
    print(f"Warning: Low quality score {quality_score:.1%}")
elif quality_score < 0.9:
    print(f"Fair quality: {quality_score:.1%}")
else:
    print(f"Excellent quality: {quality_score:.1%}")
```

---

## Performance Tips

1. **Filter columns early**: Only process columns you need
   ```python
   numeric_cols = ["volume", "price"]
   result = processor.process(df, numeric_columns=numeric_cols)
   ```

2. **Use appropriate strategies**: More aggressive cleaning = faster
   ```python
   # Faster: drop strategy
   processor.add_step("clean", "clean", {"missing_value_strategy": "drop"})

   # Slower: interpolate strategy
   processor.add_step("clean", "clean", {"missing_value_strategy": "interpolate"})
   ```

3. **Limit feature generation**: Too many features slow down downstream
   ```python
   # Generate only essential features
   processor.add_step("align", "align", config={
       "generate_lags": True,
       "lags": [1, 5],  # Not [1, 5, 10, 20, 60]
   })
   ```

4. **Process in chunks for very large datasets**:
   ```python
   chunk_size = 100000
   for i in range(0, len(df), chunk_size):
       chunk = df.iloc[i:i+chunk_size]
       result = processor.process(chunk)
   ```

---

## Troubleshooting

### Issue: "DataFrame.fillna with 'method' deprecated"
**Fix**: Code already updated. Make sure you have latest version.

### Issue: Quality score too low
**Solution**:
```python
# Check what's causing low quality
scorer = QualityScorer()
scorer.calculate_quality(df, date_column="date")
print(scorer.generate_quality_report_text())

# Use gentler cleaning
processor.add_step("clean", "clean", {
    "missing_value_strategy": "hybrid",  # More aggressive filling
    "outlier_strategy": "cap"             # Don't remove outliers
})
```

### Issue: Pipeline too slow
**Solution**:
```python
# Profile individual steps
import time

for step in processor.steps:
    start = time.time()
    # Execute step
    elapsed = time.time() - start
    print(f"{step['name']}: {elapsed:.2f}s")

# Remove unnecessary steps or use faster strategies
```

### Issue: Data shape changed unexpectedly
**Solution**:
```python
# Check execution log
report = processor.get_report()
print(f"Initial rows: {report['statistics']['initial_rows']}")
print(f"Final rows: {report['statistics']['final_rows']}")

# Check which step caused change
for checkpoint in report['execution']['checkpoints']:
    print(f"{checkpoint['step']}: {checkpoint['rows']} rows")
```

---

## API Reference

### DataCleaner
- `clean(df, numeric_columns, date_column)`: Main cleaning method
- `get_quality_report()`: Get quality metrics

### TemporalAligner
- `align_to_trading_days(df, date_column, fill_method)`: Trading day alignment
- `generate_lagged_features(df, columns, lags, date_column)`: Lagged features
- `generate_rolling_features(df, columns, windows, functions)`: Rolling features
- `compute_returns(df, price_columns, return_type, periods)`: Returns
- `resample_data(df, date_column, target_frequency, agg_functions)`: Frequency conversion
- `is_trading_day(date)`: Check if date is trading day
- `get_trading_days_range(start_date, end_date)`: Get trading days in range

### DataNormalizer
- `fit(df, columns)`: Learn normalization parameters
- `transform(df, columns)`: Apply normalization
- `fit_transform(df, columns)`: One-step fit+transform
- `inverse_transform(df, columns)`: Reverse normalization
- `validate_normalization(df, columns)`: Validate results
- `get_params(column)`: Get normalization parameters

### QualityScorer
- `calculate_quality(df, date_column, numeric_columns)`: Calculate score
- `get_grade()`: Get letter grade
- `get_score()`: Get numeric score
- `get_report()`: Get detailed report
- `generate_quality_report_text()`: Human-readable report
- `is_quality_acceptable(min_grade)`: Check if acceptable

### PipelineProcessor
- `add_step(name, step_type, config)`: Add pipeline step
- `process(df, date_column, numeric_columns)`: Execute pipeline
- `get_report()`: Get execution report
- `print_report()`: Print formatted report
- `get_step_status(step_name)`: Get step status
- `has_errors()`: Check for errors

---

## Contact & Support

For issues or questions, refer to:
- `PHASE2_COMPLETION_SUMMARY.md` - Detailed completion report
- `PHASE2_TEST_REPORT.md` - Test results and coverage
- Module docstrings - Implementation details

---

**Last Updated**: 2025-10-18
**Version**: 1.0 (Production Ready)
