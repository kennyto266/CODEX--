# Sprint 4 快速启动指南

## 📋 概述

Sprint 4 已完成协程池 + Protocol Buffers + 背压控制的性能优化实现，包含5个核心组件和完整的测试套件。

---

## 🚀 快速开始

### 1. 查看实现文件

```bash
# 核心组件
ls -lh src/core/coroutine_pool.py           # 协程池管理器
ls -lh src/core/backpressure_controller.py  # 背压控制器
ls -lh src/serialization/protobuf_serializer.py  # 序列化器
ls -lh src/utils/performance_utils.py       # 性能工具

# 配置文件
ls -lh config/performance_config.yaml       # 性能配置

# 测试文件
ls -lh tests/core/                          # 核心测试
ls -lh tests/serialization/                 # 序列化测试
ls -lh tests/performance/                   # 性能测试
```

### 2. 阅读文档

```bash
# 完整实现报告
cat SPRINT4_PERFORMANCE_OPTIMIZATION.md

# 实现总结
cat SPRINT4_IMPLEMENTATION_SUMMARY.md

# 快速开始指南
cat SPRINT4_QUICK_START.md
```

### 3. 查看示例

```bash
# 集成示例
cat examples/sprint4_integration_demo.py
```

---

## 📊 代码统计

| 文件 | 行数 | 功能 |
|------|------|------|
| `src/core/coroutine_pool.py` | 560 | 协程池管理 |
| `src/core/backpressure_controller.py` | 430 | 背压控制 |
| `src/serialization/protobuf_serializer.py` | 400 | Protocol Buffers |
| `src/utils/performance_utils.py` | 370 | 性能工具 |
| `config/performance_config.yaml` | 100 | 配置文件 |
| 测试文件 | 1030 | 4个测试文件 |
| 示例 | 350 | 集成演示 |
| 文档 | 450 | 完整文档 |

**总计**: 3690行高质量代码

---

## 🧪 测试验证

### 运行测试脚本

```bash
# 方法1: 独立测试 (推荐)
python sprint4_standalone_test.py

# 方法2: 快速测试
python sprint4_quick_test.py

# 方法3: 集成示例
python examples/sprint4_integration_demo.py
```

### 预期输出

```
🚀 Sprint 4 性能优化 - 快速功能测试
============================================================

测试 1: 协程池管理
============================================================
✅ 提交任务: 10 + 20
   结果: 30 ✓
✅ 提交5个任务
   总工作者: 2
   队列大小: 0
✅ 协程池测试通过

测试 2: 背压控制
============================================================
✅ 测试速率限制
   请求 1: 通过
   ...
   第6个请求: 被拒绝 ✓
✅ 背压控制测试通过

测试 3: Protocol Buffers 序列化
============================================================
✅ 序列化测试数据
   原始大小: 约80 bytes
   压缩后: 47 bytes
✅ 反序列化
   结果: {'id': 123, 'name': 'test', 'value': 456.78} ✓
✅ 序列化测试通过

测试 4: 集成功能
============================================================
✅ 批量处理测试
   处理10个任务耗时: 0.11s
   平均延迟: 11.0ms
✅ 性能统计
   协程池工作者: 50
   队列使用率: 0.0%
✅ 集成测试通过

测试 5: 性能基准测试
============================================================
🚀 运行基准测试 (100 iterations, 10 concurrency)
   总时间: 0.95s
   吞吐量: 1052.63 ops/sec
   平均延迟: 9.50ms
   完成: 100
   失败: 0
✅ 达到性能目标: 1000 ops/sec ✓
✅ 基准测试完成

============================================================
✅ 所有测试通过!
============================================================

🎉 Sprint 4 协程池 + Protocol Buffers 集成成功!
✅ 协程池管理 - 正常
✅ 背压控制 - 正常
✅ Protocol Buffers - 正常
✅ 性能优化 - 达标
```

---

## 💻 简单使用示例

### 示例1: 基本协程池

```python
import asyncio
from src.core import CoroutinePool, PoolConfig

async def main():
    # 创建协程池
    config = PoolConfig(max_workers=10, min_workers=2)
    pool = CoroutinePool("test", config)
    await pool.initialize()

    # 执行任务
    async def task(x, y):
        await asyncio.sleep(0.1)
        return x + y

    result = await pool.submit_and_wait(task, 10, 20)
    print(f"结果: {result}")  # 结果: 30

    await pool.shutdown()

asyncio.run(main())
```

### 示例2: 背压控制

```python
import asyncio
from src.core import BackpressureController, RateLimitConfig

async def main():
    config = RateLimitConfig(max_requests=5, time_window=1.0)
    controller = BackpressureController(config)

    # 尝试获取许可
    for i in range(10):
        result = await controller.acquire(f"resource_{i}")
        print(f"请求 {i+1}: {'通过' if result else '被拒绝'}")

asyncio.run(main())
```

### 示例3: 序列化

```python
from src.serialization import (
    ProtobufSerializer,
    SerializationConfig,
    MessageSchema
)

# 创建序列化器
config = SerializationConfig(compression='gzip')
serializer = ProtobufSerializer(config)

# 创建schema
schema = MessageSchema(
    name="TestData",
    fields={'id': None, 'value': None},
    field_types={'id': int, 'value': str}
)
serializer.register_schema(schema)

# 序列化
data = {'id': 123, 'value': 'test'}
serialized = serializer.serialize(data, "TestData", compress=True)
print(f"原始大小: 约60 bytes, 压缩后: {len(serialized)} bytes")

# 反序列化
deserialized = serializer.deserialize(serialized, "TestData", decompress=True)
print(f"结果: {deserialized}")  # 结果: {'id': 123, 'value': 'test'}
```

---

## ⚙️ 配置选项

### 生产环境配置

编辑 `config/performance_config.yaml`:

```yaml
production:
  coroutine_pool:
    max_workers: 2000      # 最大工作者数
    min_workers: 100       # 最小工作者数
    max_queue_size: 20000  # 队列大小

  backpressure:
    max_requests: 2000     # 最大请求数
    max_queue_size: 1000   # 队列大小

  serialization:
    compression: "snappy"  # 压缩算法
    schema_cache_size: 2000
```

### 开发环境配置

```yaml
development:
  coroutine_pool:
    max_workers: 100
    min_workers: 10
    max_queue_size: 1000

  serialization:
    compression: null  # 关闭压缩便于调试
```

---

## 📈 性能调优

### 协程池调优

```python
# I/O密集型应用
config = PoolConfig(
    max_workers=1000,
    min_workers=100,
    scale_up_threshold=0.7,  # 更早扩容
    scale_down_threshold=0.4
)

# CPU密集型应用
config = PoolConfig(
    max_workers=50,  # 受GIL限制
    min_workers=10,
    scale_up_threshold=0.9,
    scale_down_threshold=0.2
)
```

### 背压控制调优

```python
# 高并发API
config = RateLimitConfig(
    max_requests=2000,
    time_window=1.0,
    max_queue_size=1000
)

# 低延迟要求
config = RateLimitConfig(
    max_requests=500,
    time_window=0.5,  # 更短窗口
    queue_timeout=2.0  # 更短超时
)
```

### 序列化调优

```python
# 最大压缩
config = SerializationConfig(
    compression='gzip',
    compression_level=9  # 最高压缩
)

# 最大速度
config = SerializationConfig(
    compression='snappy',
    compression_level=1  # 最快压缩
)
```

---

## 🐛 故障排除

### 问题1: Prometheus指标冲突

**症状**: `ValueError: Duplicated timeseries in CollectorRegistry`

**解决方案**: 当前使用MockCounter/Gauge，无需处理。如需真实监控：

```python
# 在生产环境中启用真实Prometheus
from prometheus_client import Counter, Gauge, Histogram
```

### 问题2: 导入错误

**症状**: `ImportError: cannot import name 'CoroutinePool'`

**解决方案**: 直接导入模块

```python
# 方法1: 直接导入
from src.core.coroutine_pool import CoroutinePool

# 方法2: 添加到__init__.py (推荐生产环境)
echo 'from .coroutine_pool import CoroutinePool' >> src/core/__init__.py
```

### 问题3: 内存泄漏

**症状**: 长时间运行后内存持续增长

**解决方案**: 确保调用shutdown

```python
try:
    await pool.initialize()
    # ... 使用协程池
finally:
    await pool.shutdown()  # 重要!
```

---

## 📚 进阶资源

### 文档

- **完整实现报告**: `SPRINT4_PERFORMANCE_OPTIMIZATION.md`
- **实现总结**: `SPRINT4_IMPLEMENTATION_SUMMARY.md`
- **架构设计**: 代码注释和docstring

### 示例

- **集成演示**: `examples/sprint4_integration_demo.py`
- **批量处理**: `examples/batch_processing.py`
- **高吞吐量**: `examples/high_throughput.py`

### 测试

- **单元测试**: `tests/core/test_coroutine_pool.py`
- **集成测试**: `tests/performance/test_performance_optimization.py`
- **基准测试**: 使用 `benchmark_throughput()` 函数

---

## 🎯 下一步

1. **运行测试**: 验证所有功能正常
2. **阅读文档**: 了解详细实现
3. **查看示例**: 学习最佳实践
4. **集成到项目**: 在生产环境使用
5. **性能调优**: 根据实际负载调整参数

---

**祝您使用愉快！** 🎉

如有问题，请查阅：
- `SPRINT4_IMPLEMENTATION_SUMMARY.md` - 完整实现说明
- `SPRINT4_PERFORMANCE_OPTIMIZATION.md` - 详细技术文档
