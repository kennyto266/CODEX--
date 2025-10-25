# Specification: Result Validation and Authenticity Verification

## Purpose

Verify that strategy optimization results represent genuine backtest computations with authentic data and diverse parameter impact, rather than cached or placeholder values.

## ADDED Requirements

### Requirement: Result Diversity Analysis

The system SHALL analyze diversity of optimization results to detect caching or placeholder data.

#### Scenario: Measure Sharpe ratio diversity
- **WHEN** strategy optimization completes
- **THEN** analyze Sharpe ratio distribution:
  - Extract sharpe_ratio from each result
  - Count unique values (numerical precision: 3 decimal places)
  - Calculate diversity ratio: unique_count / total_count
  - Threshold: diversity_ratio MUST be > 0.5 (> 50% unique)

#### Scenario: Sharpe ratio diversity validation
- **WHEN** diversity ratio is calculated
- **THEN** log analysis:
  ```
  ✅ Sharpe Ratio Diversity: 487/502 unique (97.0%)
  ✓ PASSED: > 50% threshold
  ```
- OR if failed:
  ```
  ⚠️ Sharpe Ratio Diversity: 5/502 unique (1.0%)
  ✗ FAILED: Likely cached or placeholder data
  ```

#### Scenario: Root cause analysis for low diversity
- **WHEN** diversity check fails
- **THEN** investigate:
  - Are results identical? → Likely cached or placeholder
  - Do results vary by only parameter? → Calculation might be working
  - Are all results valid dict objects? → Data format issue
  - Log findings for debugging

### Requirement: Return and Drawdown Diversity

The system SHALL verify diversity in performance metrics beyond Sharpe ratio.

#### Scenario: Measure return distribution diversity
- **WHEN** results are available
- **THEN** analyze total_return field:
  - Extract all total_return values
  - Round to 0.1% precision for grouping
  - Count unique rounded values
  - Threshold: > 2 unique values (indicates real variation)

#### Scenario: Measure drawdown distribution diversity
- **WHEN** results are available
- **THEN** analyze max_drawdown field:
  - Extract all max_drawdown values
  - Round to 0.1% precision for grouping
  - Count unique rounded values
  - Threshold: > 2 unique values

#### Scenario: Return diversity log
- **WHEN** return analysis completes
- **THEN** log:
  ```
  📊 Return Distribution: 89 unique values (range: -2.5% to 45.8%)
  ✓ PASSED: > 2 unique values
  ```

### Requirement: Statistical Distribution Validation

The system SHALL verify results follow reasonable statistical distributions.

#### Scenario: Sharpe ratio statistics
- **WHEN** results are analyzed
- **THEN** calculate:
  - Mean (average) Sharpe ratio
  - Standard deviation
  - Min and max values
  - Expected: std_dev > 0.1 (indicates variation)

#### Scenario: Validate statistical parameters
- **WHEN** statistics are calculated
- **THEN** verify:
  - Mean is between min and max (sanity check)
  - std_dev > 0 (not all identical)
  - std_dev < mean * 2 (no extreme outliers suggesting errors)

#### Scenario: Statistical distribution log
- **WHEN** distribution analysis completes
- **THEN** log:
  ```
  📈 Sharpe Ratio Distribution:
     Mean: 1.23, Std Dev: 0.38
     Range: [0.15 - 2.87]
     ✓ PASSED: std_dev indicates real variation
  ```

### Requirement: Parameter Impact Verification

The system SHALL verify that parameter changes produce measurable differences in results.

#### Scenario: Verify parameter correlation
- **WHEN** multiple results exist for same strategy type with different parameters
- **THEN** verify:
  - Results with different parameters have different metrics
  - Top performing parameters show measurable Sharpe improvement
  - Sample: MA strategy with short=5 vs short=45 should differ significantly

#### Scenario: Correlation check example
- **WHEN** analyzing MA strategy results (1,104 combinations)
- **THEN** verify:
  - MA with short=3, long=10: Sharpe = 0.45
  - MA with short=25, long=50: Sharpe = 1.82
  - Difference = 1.37 Sharpe points (measurable parameter impact)

#### Scenario: Parameter impact validation
- **WHEN** parameter impact is verified
- **THEN** log findings:
  ```
  🔍 Parameter Impact Analysis:
     Strategy: MA (1,104 combinations)
     ✓ Parameter changes produce different Sharpe ratios
     ✓ Top performers (Sharpe > 2.0): 12 combinations
     ✓ Worst performers (Sharpe < 0.5): 45 combinations
     ✓ PASSED: Real parameter impact detected
  ```

### Requirement: Benchmark Comparison

The system SHALL verify results are within expected ranges for authentic backtests.

#### Scenario: Sharpe ratio reasonableness check
- **WHEN** results are available
- **THEN** verify ranges are reasonable:
  - Sharpe ratio typically: -2 to +3 for stocks
  - If all Sharpe > 3: Likely unrealistic or data issue
  - If all Sharpe < -1: Likely all losing strategies
  - Log warning if outside typical ranges

#### Scenario: Return range validation
- **WHEN** total_return field is available
- **THEN** verify ranges:
  - Typical range: -50% to +200% for annual backtests
  - Single day data: -10% to +10%
  - If outliers detected: log with strategy details

#### Scenario: Benchmark validation log
- **WHEN** benchmark check completes
- **THEN** log:
  ```
  ✅ Result Reasonableness Check:
     Sharpe range: [-0.23 to 2.87] (NORMAL)
     Return range: [-8.2% to 42.5%] (NORMAL)
     ✓ PASSED: Results within expected ranges
  ```

### Requirement: Data Completeness Check

The system SHALL verify all results contain required fields.

#### Scenario: Validate result structure
- **WHEN** results are collected
- **THEN** for each result, verify presence of:
  - strategy_name (string)
  - total_return (float)
  - annual_return (float)
  - volatility (float)
  - sharpe_ratio (float)
  - max_drawdown (float)
  - win_rate (float)
  - trade_count (int)
  - final_value (float)

#### Scenario: Invalid result handling
- **WHEN** result is missing required fields
- **THEN**:
  - Skip result in validation
  - Log warning with strategy name
  - Do NOT crash or fail validation entirely

#### Scenario: Data completeness log
- **WHEN** completeness check completes
- **THEN** log:
  ```
  ✓ Result completeness: 2,297/2,297 (100%) valid
  ```

### Requirement: Validation Report Generation

The system SHALL generate comprehensive validation report summarizing all checks.

#### Scenario: Generate validation report
- **WHEN** all validations complete
- **THEN** create report structure:
  ```python
  validation_report = {
    'status': 'PASSED' or 'FAILED',  # Overall result
    'total_results': int,             # Total results analyzed
    'checks': {
      'result_count': bool,            # > 0 results
      'sharpe_diversity': bool,        # > 50% unique
      'return_diversity': bool,        # > 2 unique values
      'drawdown_diversity': bool,      # > 2 unique values
      'statistical_variation': bool,   # std_dev > 0
      'parameter_impact': bool,        # Parameters matter
      'reasonableness': bool,          # Within expected ranges
      'data_completeness': bool,       # All fields present
    },
    'diversity_metrics': {
      'sharpe_ratio_unique': int,      # Unique values
      'sharpe_ratio_diversity': float, # Percentage
      'return_unique': int,
      'drawdown_unique': int,
    },
    'statistics': {
      'sharpe_mean': float,
      'sharpe_std': float,
      'sharpe_range': [float, float],
      'return_range': [float, float],
    },
    'anomalies': [                     # Any unusual patterns
      'All Sharpe > 2.5 (check for overfitting)',
      'No losing strategies (suspicious)',
    ],
  }
  ```

#### Scenario: Validation report export
- **WHEN** report is generated
- **THEN** include in API response:
  ```json
  {
    "success": true,
    "data": { ... strategy results ... },
    "diagnostics": {
      "validation_report": { ... report structure ... },
      "cpu_monitoring": { ... },
      "execution_time_seconds": 31.5
    }
  }
  ```

### Requirement: Validation Logging

The system SHALL emit detailed logs for all validation activities.

#### Scenario: Log validation start
- **WHEN** validation begins
- **THEN** log at INFO:
  ```
  🔍 Validating 2,297 strategy results...
  ```

#### Scenario: Log each validation check
- **WHEN** each check completes
- **THEN** log at INFO with result:
  ```
  ✓ Sharpe diversity check: 487/502 unique (97.0%)
  ✓ Return diversity check: 89 unique values
  ✓ Parameter impact check: Verified
  ⚠️ Reasonableness check: Some Sharpe > 3.0 (investigate)
  ```

#### Scenario: Final validation summary
- **WHEN** all checks complete
- **THEN** log at INFO:
  ```
  ✅ VALIDATION PASSED (8/8 checks)
  ```
  OR
  ```
  ❌ VALIDATION FAILED (5/8 checks)
  ```

### Requirement: False Positive Prevention

The system SHALL avoid incorrectly flagging valid results as suspicious.

#### Scenario: Handle known diversity variations
- **WHEN** validating results
- **THEN** accept as valid:
  - Fixed-parameter strategies (Ichimoku, Parabolic SAR) with identical values
  - Small strategy sets (< 10 combinations) with duplicate values
  - High-performing strategies with similar Sharpe ratios (real clusters)

#### Scenario: Ichimoku and Parabolic SAR exception
- **WHEN** validating Ichimoku or Parabolic SAR results
- **THEN** do NOT require:
  - Sharpe diversity > 50%
  - Multiple unique parameters (only 1 combination each)
- **BUT** do verify:
  - Results are present
  - Metrics are within reasonable ranges
  - Data is complete

#### Scenario: Small sample exception
- **WHEN** validating < 20 results
- **THEN** adjust diversity threshold:
  - Sharpe diversity: > 30% instead of 50%
  - Return diversity: > 1 unique value instead of 2

### Requirement: Remediation Guidance

The system SHALL provide actionable guidance when validation fails.

#### Scenario: Low diversity failure
- **WHEN** sharpe_diversity check fails
- **THEN** log:
  ```
  ❌ Low Sharpe ratio diversity detected
  Possible causes:
    1. Results are cached or placeholder values
    2. Strategy calculations are not running
    3. All parameters converge to same result
  Recommendations:
    1. Verify DataFrame.copy() is used in task wrapper
    2. Inspect per-task timing in diagnostics
    3. Run single strategy manually to verify computation
  Debug: Check complete_project_system.py:2684
  ```

#### Scenario: Reasonableness failure
- **WHEN** benchmark check detects outliers
- **THEN** log:
  ```
  ⚠️ Unusual result ranges detected
  Sharpe ratio max: 15.2 (typically < 3.0)
  Possible causes:
    1. Data quality issue or penny stocks
    2. Extreme volatility periods
    3. Insufficient data for annualization
  Recommendations:
    1. Verify data source quality
    2. Check for data gaps or errors
    3. Consider longer lookback period
  ```

---

## Related Specifications

- **CPU Monitoring**: System resource verification (spec/cpu-monitoring/)
- **Task Timing**: Per-task computation verification (spec/task-timing/)

## Implementation Notes

- Use Sharpe ratio precision of 3 decimal places for uniqueness
- Round performance metrics to 0.1% for distribution grouping
- Typical strategy backtests: Sharpe -1 to +3
- Small dataset warning if < 100 rows
- Parameter impact: Compare top 10% vs bottom 10% performers

## Success Criteria

- ✅ Sharpe diversity > 50% or identified exception
- ✅ Return diversity > 2 unique values
- ✅ Drawdown diversity > 2 unique values
- ✅ Statistical std_dev > 0
- ✅ Results within reasonable ranges
- ✅ All required fields present
- ✅ Validation report complete and logged
- ✅ Clear remediation guidance when checks fail
