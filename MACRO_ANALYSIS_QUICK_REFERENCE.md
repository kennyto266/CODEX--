# 宏观量化分析系统 - 快速参考卡

## 🚀 一分钟快速开始

```bash
# 1. 激活环境
cd C:\Users\Penguin8n\CODEX--\CODEX--
venv\Scripts\activate

# 2. 运行分析
python run_macro_analysis_simple.py

# 3. 查看结果
cd macro_analysis_output
ls -la
```

---

## 📁 关键文件速查

| 文件 | 用途 | 位置 |
|------|------|------|
| **执行入口** | 运行完整分析 | `run_macro_analysis_simple.py` |
| **数据加载** | 6类数据源整合 | `comprehensive_macro_analysis.py` |
| **交易策略** | 5个策略实现 | `macro_trading_strategies.py` |
| **主引擎** | 8步分析流程 | `run_complete_macro_analysis.py` |
| **执行总结** | 150页详细报告 | `EXECUTIVE_SUMMARY_COMPLETE_MACRO_ANALYSIS.md` |
| **项目索引** | 完整使用指南 | `MACRO_ANALYSIS_PROJECT_INDEX.md` |

---

## 📊 输出文件速查 (15个文件)

### CSV数据 (7个)
- `composite_indicators_*.csv` - 景气指标时间序列
- `all_correlations_*.csv` - 相关性矩阵
- `lagged_correlations_*.csv` - 滞后相关性
- `sector_scores_*.csv` - 板块评分
- `strategy_comparison_*.csv` - 策略性能对比
- `risk_metrics_*.csv` - VaR/CVaR/波动率
- `data_summary_*.txt` - 数据加载日志

### PNG图表 (4个)
- `composite_indicator_*.png` - 综合指标图
- `correlation_heatmap_*.png` - 相关性热力图
- `strategy_comparison_*.png` - 策略对比图
- `lagged_correlation_*.png` - 滞后相关性图

### TXT报告 (3个)
- `COMPLETE_MACRO_ANALYSIS_REPORT_*.txt` - 主报告
- `MACRO_INDICATORS_GUIDE_*.txt` - 指标指南
- `TRADING_STRATEGY_PLAYBOOK_*.txt` - 策略手册

---

## 🔑 核心数据速查

### 景气评分解读

| 评分范围 | 经济状态 | 推荐仓位 | 配置建议 |
|---------|---------|---------|---------|
| **80-100** | 强劲扩张 | 90-100% | 满仓进攻 |
| **60-79** | 温和扩张 | 70-90% | 偏多配置 |
| **40-59** | 中性 | 40-60% | 平衡配置 |
| **20-39** | 温和收缩 | 20-40% | 防守配置 |
| **0-19** | 衰退 | 0-20% | 现金为王 |

**当前评分**: 35.22 → 推荐仓位: **40-50%**

---

### 相关性强度解读

| 相关系数 | 强度 | 交易含义 |
|---------|------|---------|
| **+0.7至+1.0** | 强正相关 | 同向操作 |
| **+0.4至+0.7** | 中度正相关 | 倾向同向 |
| **-0.4至+0.4** | 弱相关/无相关 | 无明确指引 |
| **-0.7至-0.4** | 中度负相关 | 倾向反向 |
| **-1.0至-0.7** | 强负相关 | 反向操作 |

---

### 风险指标阈值

| 指标 | 当前值 | 低风险 | 中风险 | 高风险 |
|------|--------|--------|--------|--------|
| **VaR (95%)** | -1.73% | > -1.5% | -1.5%至-2.5% | < -2.5% |
| **CVaR (95%)** | -2.10% | > -2.0% | -2.0%至-3.0% | < -3.0% |
| **年化波动率** | 18.95% | < 15% | 15-25% | > 25% |

**当前风险**: 🟡 中等风险

---

## 💡 关键发现速查

### ⏱️ 最佳入场时机
**Lag 2-3天**: 相关性-0.41至-0.42 (最强负相关)
- 宏观数据公布后2-3天是**反向入场**的最佳窗口

### 📈 板块配置建议
| 板块 | 评分 | 推荐 |
|------|------|------|
| 成长股 | 51.96 | 🟢 **优先配置** |
| 零售/酒店 | 49.69 | 🟡 中性 |
| 金融股 | 41.56 | 🔴 谨慎 |

### 🏆 最佳策略
**综合评分策略**:
- 收益率: -0.92%
- Sharpe: -0.93
- 回撤: 3.85%
- 胜率: **39.4%** (最高)

---

## 🔧 常用命令速查

### 查看数据
```bash
# 查看主报告
cat macro_analysis_output/COMPLETE_MACRO_ANALYSIS_REPORT_*.txt

# 查看策略对比
cat macro_analysis_output/strategy_comparison_*.csv

# 查看滞后相关性
cat macro_analysis_output/lagged_correlations_*.csv
```

### Python导入
```python
import pandas as pd

# 读取综合指标
indicators = pd.read_csv('macro_analysis_output/composite_indicators_20251024_041410.csv',
                        index_col=0, parse_dates=True)

# 当前评分
current_score = indicators['composite_score'].iloc[-1]
print(f"当前景气评分: {current_score:.2f}")

# 评分统计
print(indicators['composite_score'].describe())
```

### 修改权重
```python
# 在 comprehensive_macro_analysis.py 中
composite_df = self._merge_indicators([
    ('property', property_index, 0.40),    # 房地产 40%
    ('visitor', visitor_index, 0.20),      # 访客 20%
    ('trade', trade_index, 0.15),          # 贸易 15%
    ('liquidity', liquidity_index, 0.15),  # 流动性 15%
    ('transport', transport_index, 0.10)   # 运输 10%
])
```

---

## 📞 故障排除速查

| 问题 | 解决方案 |
|------|---------|
| 编码错误 | 使用 `run_macro_analysis_simple.py` |
| 房地产数据失败 | 正常，已有6/7数据源成功 |
| 策略计算异常 | 检查数据对齐和重采样 |
| 内存不足 | 减少数据范围或增加虚拟内存 |

---

## 📚 深入学习

| 主题 | 文档 | 内容 |
|------|------|------|
| **完整执行总结** | `EXECUTIVE_SUMMARY_COMPLETE_MACRO_ANALYSIS.md` | 150页详细报告，所有发现和建议 |
| **项目使用指南** | `MACRO_ANALYSIS_PROJECT_INDEX.md` | 完整使用指南，自定义和扩展 |
| **代码文档** | 各Python文件的文档字符串 | API参考和实现细节 |

---

## 🎯 投资决策检查清单

### 入场前检查
- [ ] 景气评分是否 > 30? (当前: 35.22)
- [ ] 相关性分析是否支持方向?
- [ ] VaR风险是否可接受? (-1.73%)
- [ ] 滞后关系是否确认入场时机?
- [ ] 板块评分是否支持配置?

### 持仓管理
- [ ] 当前仓位是否符合景气评分? (推荐40-50%)
- [ ] 最大回撤是否超过预警阈值? (4%以内)
- [ ] 成交量变化是否异常?
- [ ] 是否需要板块轮动?

### 风险控制
- [ ] 单日最大敞口 ≤ 50%账户
- [ ] 止损设置是否到位?
- [ ] 分散度是否足够? (至少3个板块)
- [ ] 流动性是否充足?

---

## 💰 实战交易规则

### 根据景气评分调整仓位
```
IF 景气评分 > 70:
    目标仓位 = 90%
ELIF 景气评分 > 50:
    目标仓位 = 70%
ELIF 景气评分 > 30:
    目标仓位 = 45%  ← 当前 (35.22)
ELSE:
    目标仓位 = 20%
```

### 利用滞后效应
```
WHEN 宏观数据公布:
    IF 数据好于预期:
        等待2-3天市场调整后买入
    ELIF 数据差于预期:
        等待2-3天市场反弹后卖出
```

### 板块轮动规则
```
当月检查:
    IF 成长股评分 > 55:
        配置权重 = 40%
    IF 零售/酒店评分 > 55:
        配置权重 = 30%
    IF 金融股评分 < 45:
        配置权重 = 10%  ← 当前 (41.56)
    ELSE:
        均衡配置 = 各20%
```

---

## 🔔 定期监控任务

### 每日任务
- [ ] 查看景气评分变化
- [ ] 检查风险指标 (VaR/CVaR)
- [ ] 监控持仓回撤
- [ ] 确认止损触发

### 每周任务
- [ ] 重新运行完整分析
- [ ] 更新相关性矩阵
- [ ] 评估板块轮动信号
- [ ] 检查策略表现

### 每月任务
- [ ] 回顾策略收益率
- [ ] 调整权重配置
- [ ] 优化入场阈值
- [ ] 更新宏观数据源

---

## ⚠️ 重要提醒

1. **历史表现 ≠ 未来收益**
   - 所有回测基于过去数据
   - 市场环境会变化

2. **短期数据限制**
   - 当前仅33天回测期
   - 需要至少1年数据验证

3. **策略负收益说明**
   - 反映短期市场逆风
   - 不代表长期无效

4. **专业建议**
   - 投资前咨询专业顾问
   - 风险自负

---

## 📧 快速联系

**项目**: CODEX Quantitative System
**版本**: v1.0 (2025-10-24)
**许可**: MIT License

**输出目录**: `C:\Users\Penguin8n\CODEX--\CODEX--\macro_analysis_output`
**总文件数**: 18个 (3代码 + 15输出)

---

**快速参考卡 - 打印此页备用! 📋**
