# HKEX Market Correlation Analysis Report
## Comprehensive Statistical Analysis

**Analysis Date:** 2025-10-21
**Data Period:** 2025-09-01 to 2025-10-17
**Sample Size:** 32 trading days

---

## Executive Summary

This report presents a comprehensive correlation analysis of HKEX market data, focusing on identifying relationships between market metrics and daily returns for trading signal generation.

### Key Findings

1. **Market Breadth is the strongest predictor** of daily returns (r = 0.947, p < 0.001)
2. **Advanced/Declined stocks** show exceptionally high correlation with returns (r > 0.92)
3. **NO statistically significant 1-day ahead predictive indicators** found (all p > 0.05)
4. **Warning:** Small sample size (32 days) limits reliability of conclusions

---

## 1. Correlation Matrix Analysis

### Full Correlation Matrix with Daily_Return

| Metric | Correlation | P-value | Significance |
|--------|------------|---------|--------------|
| **Market_Breadth** | **0.9469** | **0.000000** | *** |
| **Advanced_Stocks** | **0.9236** | **0.000000** | *** |
| **AD_Ratio** | **0.9180** | **0.000000** | *** |
| RSI_14 | 0.3742 | 0.034879 | * |
| Afternoon_Close | 0.3228 | 0.071566 | NS |
| MACD | 0.0149 | 0.935570 | NS |
| Turnover_Per_Deal | -0.0110 | 0.952668 | NS |
| Volatility_20D | -0.1275 | 0.487823 | NS |
| Deals | -0.1697 | 0.360027 | NS |
| Turnover_HKD | -0.1739 | 0.347844 | NS |
| Volume_Ratio | -0.1886 | 0.305136 | NS |
| Trading_Volume | -0.2699 | 0.137884 | NS |
| Declined_Stocks | **-0.9505** | **0.000000** | *** |

**Legend:**
- `***` p < 0.001 (highly significant)
- `**` p < 0.01 (very significant)
- `*` p < 0.05 (significant)
- `NS` = Not significant

---

## 2. Strong Correlations (|r| > 0.7)

### Pairs with Absolute Correlation > 0.7

| Metric 1 | Metric 2 | Correlation | P-value |
|----------|----------|-------------|---------|
| Afternoon_Close | MACD | **0.8994** | 0.000000 |
| Volatility_20D | RSI_14 | **-0.8882** | 0.000000 |
| Daily_Return | Declined_Stocks | **-0.9505** | 0.000000 |
| Daily_Return | Market_Breadth | **0.9469** | 0.000000 |
| Daily_Return | Advanced_Stocks | **0.9236** | 0.000000 |
| Daily_Return | AD_Ratio | **0.9180** | 0.000000 |
| Advanced_Stocks | Declined_Stocks | **-0.9067** | 0.000000 |
| Advanced_Stocks | AD_Ratio | **0.9848** | 0.000000 |
| Advanced_Stocks | Market_Breadth | **0.9835** | 0.000000 |
| Declined_Stocks | AD_Ratio | **-0.9052** | 0.000000 |
| Declined_Stocks | Market_Breadth | **-0.9673** | 0.000000 |
| AD_Ratio | Market_Breadth | **0.9720** | 0.000000 |
| Volatility_20D | Afternoon_Close | **-0.7425** | 0.000001 |
| Volatility_20D | MACD | **-0.7267** | 0.000002 |
| Afternoon_Close | RSI_14 | **0.7370** | 0.000001 |

**Key Insight:** Market breadth indicators (Advanced/Declined stocks, AD Ratio) are highly intercorrelated and all strongly correlate with daily returns.

---

## 3. Moderate Correlations (0.4 < |r| < 0.7)

| Metric 1 | Metric 2 | Correlation | P-value |
|----------|----------|-------------|---------|
| Turnover_HKD | Deals | 0.9633 | 0.000000 |
| Trading_Volume | Volume_Ratio | 0.9402 | 0.000000 |
| RSI_14 | MACD | 0.6212 | 0.000155 |
| Volume_Ratio | Turnover_HKD | 0.6350 | 0.000094 |
| Volume_Ratio | Deals | 0.6053 | 0.000223 |
| Turnover_HKD | Turnover_Per_Deal | 0.5545 | 0.000977 |
| Trading_Volume | Turnover_HKD | 0.5251 | 0.002178 |
| Trading_Volume | Deals | 0.4763 | 0.006054 |

**Warning:** High correlation between Turnover_HKD and Deals (0.963) indicates multicollinearity - avoid using both in same model.

---

## 4. Leading vs Lagging Indicators

### Lagged Correlation Analysis (Daily_Return as Target)

| Metric | Lag -2 | Lag -1 | Lag 0 | Lag +1 | Lag +2 |
|--------|--------|--------|-------|--------|--------|
| **Market_Breadth** | **0.9555** | **0.9551** | **0.9469** | 0.1065 | 0.0182 |
| **Advanced_Stocks** | **0.9386** | **0.9380** | **0.9236** | 0.1151 | 0.0069 |
| **Declined_Stocks** | **-0.9523** | **-0.9474** | **-0.9505** | -0.0822 | -0.0116 |
| **AD_Ratio** | **0.9347** | **0.9341** | **0.9180** | 0.1349 | -0.0082 |
| RSI_14 | 0.3479 | 0.3481 | 0.3742 | 0.0602 | -0.0685 |
| Afternoon_Close | 0.2358 | 0.2363 | 0.3228 | -0.2417 | -0.2937 |
| Trading_Volume | -0.1477 | -0.1488 | -0.2699 | -0.2959 | -0.1588 |
| MACD | -0.1304 | -0.1215 | 0.0149 | -0.2145 | -0.2641 |
| Volume_Ratio | -0.0900 | -0.0883 | -0.1886 | -0.2030 | -0.0354 |

**Interpretation:**

- **Lag -2/-1 (Leading):** Metric value 1-2 days AGO vs today's return
- **Lag 0 (Contemporaneous):** Same-day correlation
- **Lag +1/+2 (Lagging):** Today's metric vs returns 1-2 days in future

### Key Observations:

1. **Market breadth indicators maintain high correlation at Lag -2 and Lag -1**
   - This suggests they reflect market momentum that persists
   - However, this is NOT predictive in traditional sense (they measure same-day sentiment)

2. **Correlation drops dramatically at Lag +1/+2**
   - Market breadth at Lag +1: only 0.11 (vs 0.95 at Lag 0)
   - This indicates mean reversion after strong moves

3. **No strong leading indicators found**
   - All metrics show similar or stronger correlation at Lag 0 vs Lag -1
   - This suggests contemporaneous relationships, not predictive

---

## 5. Predictive Power Analysis (1-Day Ahead)

### Metrics Tested for Next-Day Return Prediction

| Metric | Correlation | P-value | Significant? |
|--------|-------------|---------|--------------|
| Trading_Volume | -0.2959 | 0.1060 | ❌ No |
| Afternoon_Close | -0.2417 | 0.1902 | ❌ No |
| Turnover_Per_Deal | -0.2304 | 0.2124 | ❌ No |
| MACD | -0.2145 | 0.2465 | ❌ No |
| Volume_Ratio | -0.2030 | 0.2734 | ❌ No |
| AD_Ratio | 0.1349 | 0.4693 | ❌ No |
| Advanced_Stocks | 0.1151 | 0.5376 | ❌ No |
| Market_Breadth | 0.1065 | 0.5685 | ❌ No |

### Critical Finding:

**🚨 NO statistically significant 1-day ahead predictors found (all p > 0.05)**

This means:
- None of these metrics reliably predict next day's returns
- High contemporaneous correlation (0.95) does NOT translate to predictive power
- Market appears efficient at short timescales (1-day)

---

## 6. Rolling Correlation Analysis

### 5-Day Rolling Window

| Metric | Mean | Std Dev | Min | Max |
|--------|------|---------|-----|-----|
| Trading_Volume | 0.1258 | 0.6267 | -0.9519 | 0.9659 |
| Afternoon_Close | 0.5121 | 0.3719 | -0.4796 | 0.9150 |
| Turnover_Per_Deal | 0.1251 | 0.4135 | -0.6134 | 0.9088 |

### 10-Day Rolling Window

| Metric | Mean | Std Dev | Min | Max |
|--------|------|---------|-----|-----|
| Trading_Volume | 0.1609 | 0.3174 | -0.4608 | 0.6421 |
| Afternoon_Close | 0.4261 | 0.2402 | -0.1908 | 0.7299 |
| Turnover_Per_Deal | 0.0767 | 0.2634 | -0.2492 | 0.5940 |

**Key Observations:**

1. **High volatility in rolling correlations** (especially Trading_Volume: range -0.95 to +0.97)
2. **Correlations are NOT stable over time** - they change sign and magnitude
3. **This instability undermines trading strategy reliability**

---

## 7. Confidence Intervals (95%)

| Metric | Correlation | 95% CI Lower | 95% CI Upper |
|--------|-------------|--------------|--------------|
| Market_Breadth | 0.9469 | 0.8930 | 0.9740 |
| Advanced_Stocks | 0.9236 | 0.8481 | 0.9624 |
| AD_Ratio | 0.9180 | 0.8373 | 0.9595 |
| RSI_14 | 0.3742 | 0.0293 | 0.6394 |
| Afternoon_Close | 0.3228 | -0.0292 | 0.6036 |

**Note:** Wide confidence intervals (especially for weaker correlations) due to small sample size.

---

## 8. Actionable Insights

### 🎯 Best Single Predictor

**Metric:** Trading_Volume
**1-Day Ahead Correlation:** -0.2959
**Statistical Significance:** p = 0.1060 (NOT significant)

⚠️ **WARNING:** This metric does NOT meet statistical significance threshold (p < 0.05)

### 📊 Strongest Contemporaneous Correlations

1. **Market_Breadth:** r = 0.9469 (p < 0.001) ✅
2. **Advanced_Stocks:** r = 0.9236 (p < 0.001) ✅
3. **AD_Ratio:** r = 0.9180 (p < 0.001) ✅

These are **reactive indicators** (same-day), not **predictive**.

### 🔍 Reliability Assessment

**Sample Size:** 32 trading days
**Status:** ⚠️ CAUTION - Moderate sample size, use with care

**Recommendations:**
- Collect at least 100+ trading days for reliable estimates
- Current correlations may be unstable and sample-specific
- Do NOT base production strategies on 32-day sample

### ⚠️ Multicollinearity Check

**Found 15 pairs of non-return metrics with |r| > 0.7**

High correlation pairs to AVOID using together:
- Turnover_HKD + Deals (r = 0.963)
- Trading_Volume + Volume_Ratio (r = 0.940)
- Advanced_Stocks + Market_Breadth (r = 0.984)
- Declined_Stocks + Market_Breadth (r = -0.967)
- AD_Ratio + Market_Breadth (r = 0.972)

### 📈 Trading Signal Recommendations

**Status:** ❌ No statistically significant predictive metrics found

**Implications:**
1. **Market appears efficient at 1-day horizon** - past data doesn't predict next day
2. **High contemporaneous correlation ≠ predictive power**
3. **Need longer time horizons or alternative approaches:**
   - Multi-day prediction windows (2-5 days)
   - Regime-based models (bull/bear market states)
   - Alternative data sources (sentiment, options flow)
   - Machine learning for non-linear patterns

---

## 9. Statistical Test Results

### Pearson Correlation Significance Tests

**Statistically Significant Correlations (p < 0.05) with Daily_Return:**

| Metric | Correlation | P-value | Interpretation |
|--------|-------------|---------|----------------|
| Market_Breadth | 0.9469 | < 0.001 | Extremely strong positive |
| Advanced_Stocks | 0.9236 | < 0.001 | Extremely strong positive |
| AD_Ratio | 0.9180 | < 0.001 | Extremely strong positive |
| Declined_Stocks | -0.9505 | < 0.001 | Extremely strong negative |
| RSI_14 | 0.3742 | 0.0349 | Moderate positive |

All other metrics: p > 0.05 (not statistically significant)

---

## 10. Causality and Interpretation

### What Drives What?

#### ✅ **Established Relationships:**

1. **Daily_Return → Market_Breadth** (CAUSAL)
   - When prices go up, more stocks advance
   - This is definitional, not predictive

2. **Daily_Return → AD_Ratio** (CAUSAL)
   - Advance-Decline ratio is calculated FROM price movements
   - High correlation expected by construction

3. **Price → RSI** (CAUSAL with lag)
   - RSI is calculated from price changes
   - 14-day lookback creates weak predictive signal

#### ❌ **Non-Causal (Spurious) Relationships:**

1. **Turnover_HKD ↔ Daily_Return** (r = -0.17, NS)
   - No causal mechanism
   - Correlation not significant

2. **Trading_Volume ↔ Daily_Return** (r = -0.27, NS)
   - Weak negative correlation
   - Not statistically significant
   - Cannot be used for prediction

### 🔬 **True Predictive Indicators:** NONE FOUND

Based on this analysis:
- No metric shows statistically significant 1-day ahead predictive power
- High same-day correlations are **descriptive**, not **predictive**
- Market adjusts too quickly for simple lagged relationships

---

## 11. Visualization Data

### Files Generated:

1. **correlation_matrix.csv** - Full correlation matrix for heatmap
2. **scatter_data_1_Trading_Volume.csv** - Volume vs Return scatter plot
3. **scatter_data_2_Afternoon_Close.csv** - Price vs Return scatter plot
4. **scatter_data_3_Turnover_Per_Deal.csv** - Turnover/Deal vs Return
5. **rolling_corr_Trading_Volume.csv** - 5D/10D rolling correlations
6. **rolling_corr_Afternoon_Close.csv** - Price rolling correlations
7. **rolling_corr_Turnover_Per_Deal.csv** - Turnover rolling correlations

---

## 12. Conclusions and Recommendations

### 📌 Key Takeaways:

1. **Market breadth indicators perfectly capture same-day returns** (r > 0.9)
   - But this is by construction, not predictive
   - They measure what already happened

2. **NO reliable 1-day ahead predictors** in this dataset
   - All p-values > 0.05 for lagged correlations
   - Market is efficient at short timescales

3. **Sample size is too small** (32 days)
   - Need 100+ days for robust conclusions
   - Current findings may be period-specific

4. **High correlation volatility** in rolling windows
   - Relationships are unstable over time
   - Risk of overfitting to recent patterns

### ✅ Actionable Recommendations:

#### For Trading Strategy Development:

1. **DO NOT use simple lagged models** - no predictive power demonstrated
2. **Consider longer prediction horizons** (3-5 days) instead of 1-day
3. **Test regime-dependent models:**
   - Correlations may differ in bull vs bear markets
   - Volatility regimes (high vol vs low vol)
4. **Incorporate alternative data:**
   - News sentiment
   - Options implied volatility
   - Order flow imbalance
5. **Use machine learning for non-linear patterns:**
   - Random forests for feature interactions
   - LSTM for temporal dependencies

#### For Risk Management:

1. **Monitor market breadth as coincident indicator**
   - AD_Ratio crossing thresholds
   - Divergence between breadth and price
2. **Use RSI for overbought/oversold conditions**
   - Only weak correlation (r = 0.37) allows contrarian use
3. **Combine multiple uncorrelated indicators**
   - Avoid multicollinearity (many metrics highly correlated)
   - Use PCA or factor analysis to reduce dimensions

#### Next Steps:

1. **Collect more data** - target 100+ trading days minimum
2. **Test multi-day prediction windows** (2, 3, 5 days)
3. **Segment by market regime** (trending vs mean-reverting periods)
4. **Build ensemble models** combining multiple weak signals
5. **Implement walk-forward validation** to test out-of-sample performance

---

## Appendix: Technical Notes

### Data Quality Issues:

- Missing data for some dates (holidays)
- Only 32 complete observations
- No outlier removal performed (all data used as-is)

### Statistical Assumptions:

- Pearson correlation assumes linear relationships
- Normal distribution assumption NOT tested
- Independence assumption likely violated (time series autocorrelation)

### Limitations:

1. Small sample size reduces statistical power
2. Short time period may not capture different market regimes
3. Only tested linear relationships (non-linear patterns not explored)
4. Autocorrelation in time series violates independence assumption
5. Multiple testing problem (14 metrics = 91 correlation pairs) increases false positive risk

---

**Report End**
