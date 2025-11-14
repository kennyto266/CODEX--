# Rust-NonPrice Phase 7 - TODO 列表

## 紧急任务 (1-2 天)

### 1. 修复编译错误 🔥
**优先级**: 最高
**预计时间**: 2-3 小时

- [ ] 搜索并修复所有重复的 derive 宏
  ```bash
  grep -A1 "#\[derive" src/core/data.rs | grep "#\[derive"
  ```

- [ ] 为需要的结构体添加 Default derive
  - [ ] BacktestResult
  - [ ] BacktestConfig
  - [ ] TradingSignal
  - [ ] OHLCV
  - [ ] 其他需要的类型

- [ ] 修复所有类型引用错误
  - [ ] 验证模块路径
  - [ ] 确认类型导入

- [ ] 提供最小实现 (stubs)
  - [ ] 为未实现的函数提供基本实现
  - [ ] 返回空集合或默认结果

- [ ] 验证编译
  ```bash
  cargo build --lib
  ```

### 2. 完成 CLI 工具实现 ⚡
**优先级**: 高
**预计时间**: 1-2 小时

- [ ] 实现 `validate` 子命令
  - [ ] 加载 CSV/Parquet 文件
  - [ ] 验证数据
  - [ ] 生成 JSON 报告

- [ ] 实现 `indicators` 子命令
  - [ ] 加载数据
  - [ ] 计算指标
  - [ ] 保存结果

- [ ] 实现其他子命令
  - [ ] `signals` - 生成交易信号
  - [ ] `optimize` - 优化参数
  - [ ] `backtest` - 运行回测
  - [ ] `report` - 生成报告

- [ ] 添加错误处理
  - [ ] 用户友好的错误消息
  - [ ] 适当的退出码

- [ ] 测试所有子命令
  ```bash
  cargo run --bin np-indicator -- --help
  ```

---

## 重要任务 (3-5 天)

### 3. Python 绑定实现 🐍
**优先级**: 高
**预计时间**: 3-4 小时

- [ ] 修复 Rust 编译错误 (Python 绑定依赖这些)
- [ ] 完善 PyO3 绑定
  - [ ] 添加缺失的方法
  - [ ] 实现类型转换 (Polars ↔ NumPy)
  - [ ] 错误处理

- [ ] 构建 Python wheel
  ```bash
  cd python
  maturin build --release
  pip install target/wheels/*.whl
  ```

- [ ] 测试 Python 绑定
  ```bash
  python examples/python_demo.py
  ```

- [ ] 创建更多 Python 示例
  - [ ] 简单指标计算
  - [ ] 完整回测流程
  - [ ] 参数优化示例

### 4. 测试套件 📋
**优先级**: 中
**预计时间**: 2-3 小时

- [ ] 创建集成测试
  - [ ] `tests/integration/test_cli_tool.rs`
  - [ ] `tests/integration/test_python_bindings.rs`

- [ ] 创建单元测试
  - [ ] 每个模块的核心功能
  - [ ] 错误处理
  - [ ] 边界条件

- [ ] 创建性能测试
  - [ ] 大数据集处理
  - [ ] 并行计算性能
  - [ ] 内存使用

- [ ] 运行所有测试
  ```bash
  cargo test
  ```

---

## 增强任务 (1 周)

### 5. 文档完善 📚
**优先级**: 中
**预计时间**: 2-3 小时

- [ ] API 文档
  ```bash
  cargo doc --no-deps --open
  ```
  - [ ] 为所有公共函数添加文档
  - [ ] 添加使用示例
  - [ ] 链接相关类型

- [ ] 用户指南
  - [ ] 安装说明
  - [ ] 快速开始
  - [ ] 完整示例
  - [ ] 故障排除

- [ ] Python 文档
  - [ ] 完善 `python/README.md`
  - [ ] 添加 API 参考
  - [ ] 添加更多示例

### 6. 代码质量 ✨
**优先级**: 中
**预计时间**: 1-2 小时

- [ ] Clippy 检查
  ```bash
  cargo clippy --all-targets --all-features -- -D warnings
  ```
  - [ ] 修复所有警告
  - [ ] 遵循最佳实践

- [ ] 格式化代码
  ```bash
  cargo fmt
  ```

- [ ] 添加更多文档注释
  - [ ] 模块级别说明
  - [ ] 复杂函数的详细说明
  - [ ] 示例代码

### 7. 性能优化 🚀
**优先级**: 低
**预计时间**: 2-3 小时

- [ ] 运行基准测试
  ```bash
  cargo bench
  ```

- [ ] 优化热点代码
  - [ ] 指标计算
  - [ ] 数据加载
  - [ ] 信号生成

- [ ] 并行优化
  - [ ] 验证 Rayon 并行效果
  - [ ] 优化并行粒度

---

## 新功能任务 (2 周+)

### 8. 新的技术指标 ➕
**优先级**: 低
**预计时间**: 4-6 小时

- [ ] KDJ 指标
- [ ] CCI (Commodity Channel Index)
- [ ] ADX (Average Directional Index)
- [ ] ATR (Average True Range)
- [ ] OBV (On-Balance Volume)
- [ ] Ichimoku Cloud
- [ ] Parabolic SAR

### 9. 更多数据源 📊
**优先级**: 低
**预计时间**: 3-4 小时

- [ ] JSON 数据加载
- [ ] 数据库连接 (PostgreSQL, SQLite)
- [ ] HTTP API 客户端
- [ ] 实时数据流

### 10. 可视化 📈
**优先级**: 低
**预计时间**: 4-6 小时

- [ ] 图表生成
- [ ] 回测结果可视化
- [ ] 指标趋势图
- [ ] Web 界面

---

## 测试检查清单

### 基本功能
- [ ] 库可以成功编译
- [ ] CLI 工具可以构建
- [ ] 所有子命令可以运行
- [ ] Python 绑定可以导入

### 示例运行
- [ ] `cargo run --example basic_usage`
- [ ] `cargo run --example optimization`
- [ ] `python examples/python_demo.py`

### 文档
- [ ] API 文档可以生成
- [ ] README 完整且准确
- [ ] 示例代码可运行

---

## 资源链接

- [Rust 官方文档](https://doc.rust-lang.org/)
- [PyO3 指南](https://pyo3.rs/)
- [Clap 文档](https://clap.rs/)
- [Polars 文档](https://pola.rs/)
- [Criterion 基准测试](https://bheisler.github.io/criterion.rs/book/)

---

## 备注

1. **优先级排序**: 优先完成编译错误和核心功能
2. **测试驱动**: 在实现功能时同时编写测试
3. **文档更新**: 每次重大变更后更新文档
4. **性能监控**: 定期运行基准测试
5. **代码审查**: 保持代码质量和一致性

---

**最后更新**: 2025-11-10
**状态**: 进行中
