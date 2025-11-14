# 视频教程指南

欢迎使用港股量化交易系统视频教程！本教程将帮助您快速掌握系统使用方法。

## 📚 教程目录

### 1. 基础入门系列 (30-45分钟)

#### 1.1 系统安装与配置 (10分钟)
- **视频**: `01_installation_and_setup.mp4`
- **内容**:
  - 环境准备
  - 依赖安装
  - TA-Lib配置
  - 常见安装问题解决
- **代码示例**: `01_installation_example.py`
- **文档**: 参见 `docs/quickstart.md`

#### 1.2 第一次运行策略 (15分钟)
- **视频**: `02_first_strategy.mp4`
- **内容**:
  - 启动系统
  - 运行基础策略
  - 理解回测结果
  - 查看日志
- **代码示例**: `02_first_strategy_example.py`
- **实践**: 尝试运行您的第一个KDJ策略

#### 1.3 Web仪表板使用 (10分钟)
- **视频**: `03_dashboard_overview.mp4`
- **内容**:
  - 界面介绍
  - 实时监控
  - 策略分析
  - 数据可视化
- **访问地址**: http://localhost:8001

#### 1.4 数据源与API (10分钟)
- **视频**: `04_data_sources.mp4`
- **内容**:
  - 数据获取原理
  - API使用方法
  - 数据格式说明
  - 错误处理

### 2. 策略开发系列 (60-90分钟)

#### 2.1 技术指标详解 (20分钟)
- **视频**: `05_technical_indicators.mp4`
- **内容**:
  - 11种技术指标原理
  - 参数设置技巧
  - 指标组合使用
- **参考文档**: `docs/technical_indicators_guide.md`

#### 2.2 基础策略创建 (20分钟)
- **视频**: `06_creating_basic_strategies.mp4`
- **内容**:
  - 策略结构
  - 信号生成
  - 回测流程
- **代码示例**:
  - `basic_ma_strategy.py`
  - `basic_rsi_strategy.py`
  - `basic_macd_strategy.py`

#### 2.3 高级策略开发 (25分钟)
- **视频**: `07_advanced_strategies.mp4`
- **内容**:
  - KDJ策略深度解析
  - CCI超买超卖策略
  - ADX趋势强度策略
  - 组合指标策略
- **代码示例**:
  - `advanced_kdj_strategy.py`
  - `advanced_adx_strategy.py`
  - `combined_indicator_strategy.py`

#### 2.4 策略参数优化 (15分钟)
- **视频**: `08_parameter_optimization.mp4`
- **内容**:
  - 参数搜索方法
  - 并行优化
  - 过拟合避免
  - 最优参数选择
- **代码示例**: `parameter_optimization_demo.py`

### 3. 数据分析系列 (45-60分钟)

#### 3.1 替代数据分析 (20分钟)
- **视频**: `09_alternative_data.mp4`
- **内容**:
  - 35种替代数据指标
  - HIBOR利率数据
  - 地产市场数据
  - 零售销售数据
  - 访客数据
- **代码示例**: `alternative_data_analysis.py`
- **文档**: `docs/alternative-data-guide.md`

#### 3.2 数据质量验证 (15分钟)
- **视频**: `10_data_quality.mp4`
- **内容**:
  - 数据完整性检查
  - 异常值处理
  - 数据清洗
  - 质量报告
- **代码示例**: `data_quality_validation.py`

#### 3.3 数据可视化 (10分钟)
- **视频**: `11_data_visualization.mp4`
- **内容**:
  - 图表类型选择
  - 交互式图表
  - 仪表板自定义
- **示例**: 查看 `examples/quality_report_example.py`

### 4. 系统管理系列 (30-40分钟)

#### 4.1 多智能体系统 (15分钟)
- **视频**: `12_multi_agent_system.mp4`
- **内容**:
  - 7个AI Agent介绍
  - Agent间通信
  - 任务协调
- **文档**: `docs/architecture/agent_system.md`

#### 4.2 风险管理 (15分钟)
- **视频**: `13_risk_management.mp4`
- **内容**:
  - 仓位管理
  - 止损止盈
  - 风险预算
  - 压力测试
- **代码示例**: `risk_management_demo.py`

#### 4.3 性能优化 (10分钟)
- **视频**: `14_performance_optimization.mp4`
- **内容**:
  - 内存管理
  - 并行计算
  - 缓存策略
  - 性能监控

### 5. 实战案例系列 (60-90分钟)

#### 5.1 港股回测案例 (30分钟)
- **视频**: `15_hk_stock_backtest.mp4`
- **股票**: 腾讯控股 (0700.hk)
- **策略**: KDJ + RSI组合
- **时间范围**: 2020-2023
- **代码示例**: `hk_stock_case_study.py`
- **预期结果**:
  - 年化收益率: 8-12%
  - 最大回撤: <15%
  - 夏普比率: >1.0

#### 5.2 投资组合案例 (30分钟)
- **视频**: `16_portfolio_management.mp4`
- **内容**:
  - 多股票配置
  - 权重分配
  - 风险分散
- **股票池**: 0700.hk, 0388.hk, 1398.hk, 0939.hk
- **代码示例**: `portfolio_case_study.py`

#### 5.3 实时交易模拟 (30分钟)
- **视频**: `17_live_trading_simulation.mp4`
- **内容**:
  - 信号生成
  - 模拟交易
  - 实时监控
  - Telegram通知
- **代码示例**: `live_trading_simulation.py`

### 6. 最佳实践系列 (30-40分钟)

#### 6.1 策略开发最佳实践 (15分钟)
- **视频**: `18_best_practices.mp4`
- **内容**:
  - 代码规范
  - 策略测试
  - 文档编写
  - 版本控制

#### 6.2 部署与运维 (15分钟)
- **视频**: `19_deployment_operations.mp4`
- **内容**:
  - 生产环境部署
  - 监控告警
  - 日志管理
  - 备份恢复

#### 6.3 故障排除 (10分钟)
- **视频**: `20_troubleshooting.mp4`
- **内容**:
  - 常见错误
  - 调试技巧
  - 日志分析
  - 性能诊断
- **文档**: `docs/troubleshooting.md`

---

## 🎬 视频观看指南

### 建议观看顺序

**初学者路径 (约3-4小时):**
1. 基础入门系列 (1-4)
2. 策略开发系列 (6-8)
3. 数据分析系列 (9)
4. 实战案例系列 (15)

**进阶用户路径 (约2-3小时):**
1. 技术指标详解 (5)
2. 高级策略开发 (7)
3. 数据分析系列 (9-11)
4. 最佳实践 (18-20)

**开发者路径 (约1-2小时):**
1. 多智能体系统 (12)
2. 性能优化 (14)
3. 部署运维 (19)

---

## 📂 代码示例文件

所有视频配套代码位于 `examples/tutorials/` 目录:

```
examples/tutorials/
├── basic/
│   ├── 01_installation_example.py
│   ├── 02_first_strategy_example.py
│   ├── 03_dashboard_example.py
│   └── 04_data_api_example.py
├── strategies/
│   ├── 05_technical_indicators_demo.py
│   ├── 06_basic_ma_strategy.py
│   ├── 06_basic_rsi_strategy.py
│   ├── 06_basic_macd_strategy.py
│   ├── 07_advanced_kdj_strategy.py
│   ├── 07_advanced_adx_strategy.py
│   ├── 07_combined_indicator_strategy.py
│   └── 08_parameter_optimization_demo.py
├── data/
│   ├── 09_alternative_data_analysis.py
│   ├── 10_data_quality_validation.py
│   └── 11_data_visualization.py
├── system/
│   ├── 12_multi_agent_demo.py
│   ├── 13_risk_management_demo.py
│   └── 14_performance_demo.py
└── cases/
    ├── 15_hk_stock_case_study.py
    ├── 16_portfolio_case_study.py
    └── 17_live_trading_simulation.py
```

---

## 🎯 学习目标

### 观看视频后，您将能够:

**基础技能:**
- [ ] 独立安装和配置系统
- [ ] 运行基本回测策略
- [ ] 理解回测结果
- [ ] 使用Web仪表板

**策略开发:**
- [ ] 创建自定义策略
- [ ] 优化策略参数
- [ ] 避免过拟合
- [ ] 评估策略性能

**数据分析:**
- [ ] 获取和处理数据
- [ ] 验证数据质量
- [ ] 进行数据分析
- [ ] 可视化结果

**系统管理:**
- [ ] 理解系统架构
- [ ] 配置风险管理
- [ ] 优化性能
- [ ] 部署生产环境

---

## 📖 配套文档

观看视频时，建议同时参考以下文档:

| 视频 | 配套文档 | 章节 |
|------|----------|------|
| 1-4  | `docs/quickstart.md` | 全部 |
| 5    | `docs/technical_indicators_guide.md` | 指标详解 |
| 6-8  | `docs/user_guide.md` | 策略开发 |
| 9-11 | `docs/alternative-data-guide.md` | 数据分析 |
| 12   | `docs/architecture/agent_system.md` | 架构设计 |
| 13   | `docs/risk_management.md` | 风险管理 |
| 18-20| `docs/troubleshooting.md` | 故障排除 |

---

## 🛠 实践环境

### 推荐的实践配置

**最低配置:**
- CPU: 4核心
- 内存: 8GB
- 存储: 5GB
- 网络: 10Mbps

**推荐配置:**
- CPU: 8核心 (Intel i7/AMD Ryzen 7)
- 内存: 16GB
- 存储: 20GB (SSD)
- 网络: 50Mbps

### 测试数据

教程中使用的测试数据:
- **股票**: 0700.hk (腾讯控股)
- **时间范围**: 2020-01-01 至 2023-12-31
- **数据频率**: 日线
- **初始资金**: 100,000港币

---

## 💡 学习技巧

### 高效观看建议

1. **边看边练**: 打开代码文件，同步实践
2. **记录笔记**: 记录关键概念和命令
3. **重复观看**: 复杂部分可多次观看
4. **实践为主**: 观看后立即动手实践
5. **讨论交流**: 加入社区讨论

### 常见问题预防

1. **提前准备**: 视频前完成环境安装
2. **版本一致**: 使用教程指定的Python版本
3. **网络稳定**: 确保网络连接稳定
4. **充足时间**: 每个实战案例预留30分钟

---

## 📞 获取帮助

### 观看视频时遇到问题:

1. **技术问题**:
   - 查看 `docs/troubleshooting.md`
   - 检查系统日志: `tail -f quant_system.log`
   - 提交GitHub Issue

2. **理解困难**:
   - 重复观看相关视频
   - 查看配套文档
   - 参与社区讨论

3. **代码问题**:
   - 对比示例代码
   - 检查Python环境
   - 验证依赖安装

---

## 🎓 完成认证

完成所有视频学习后，您将获得:

✅ **系统使用认证**
- 掌握基本操作
- 理解系统架构
- 能够独立使用

✅ **策略开发认证**
- 创建自定义策略
- 优化策略参数
- 避免常见错误

✅ **数据分析认证**
- 处理多源数据
- 验证数据质量
- 提取有效信息

---

## 📈 后续学习

完成基础教程后，建议继续学习:

1. **机器学习策略**
   - 神经网络预测
   - 强化学习
   - 深度学习应用

2. **高频交易**
   - 分钟级数据
   - 实时信号
   - 低延迟系统

3. **另类数据**
   - 新闻情绪分析
   - 卫星图像数据
   - 社交媒体数据

---

**祝您学习愉快！** 🎉

如有任何问题或建议，欢迎通过以下方式联系:
- **GitHub**: 提交Issue
- **社区**: 参与讨论
- **邮件**: 发送建议
