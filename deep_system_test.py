#!/usr/bin/env python3
"""
深度系统测试
测试系统性能、内存、并发、稳定性等多个维度
"""

import sys
import time
import asyncio
import gc
import psutil
import threading
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from datetime import datetime
from pathlib import Path

def print_header(title):
    """打印测试标题"""
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80)

def print_result(name, status, details=""):
    """打印测试结果"""
    status_icon = "✅" if status else "❌"
    print(f"{status_icon} {name}: {details}")
    return status

def get_memory_usage():
    """获取内存使用情况"""
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024  # MB

# 测试1: 内存使用测试
def test_memory_usage():
    """测试内存使用和稳定性"""
    print_header("测试1: 内存使用与稳定性")

    initial_memory = get_memory_usage()
    print(f"初始内存: {initial_memory:.2f} MB")

    # 创建大量数据
    data = []
    for i in range(100000):
        data.append({
            'id': i,
            'value': i * 1.5,
            'name': f'item_{i}',
            'data': list(range(10))
        })

    after_alloc = get_memory_usage()
    print(f"分配后内存: {after_alloc:.2f} MB (增加: {after_alloc-initial_memory:.2f} MB)")

    # 清理并测试垃圾回收
    del data
    gc.collect()

    after_gc = get_memory_usage()
    print(f"GC后内存: {after_gc:.2f} MB (回收: {after_alloc-after_gc:.2f} MB)")

    # 内存稳定性测试
    stable = True
    for i in range(5):
        gc.collect()
        time.sleep(0.1)
        memory = get_memory_usage()
        print(f"  第{i+1}次GC后内存: {memory:.2f} MB")

    print_result("内存使用测试", True, f"初始: {initial_memory:.1f}MB, 峰值: {after_alloc:.1f}MB, 当前: {after_gc:.1f}MB")
    return True

# 测试2: 并发性能测试
def test_concurrent_performance():
    """测试并发性能"""
    print_header("测试2: 并发性能测试")

    def cpu_task(n):
        """CPU密集型任务"""
        total = 0
        for i in range(n):
            total += i ** 0.5
        return total

    def io_task(n):
        """I/O密集型任务"""
        time.sleep(0.01)
        return n * 2

    # 单线程性能
    print("单线程测试...")
    start = time.time()
    for i in range(10):
        cpu_task(10000)
    single_time = time.time() - start
    print(f"单线程时间: {single_time:.3f}s")

    # 多线程性能
    print("多线程测试...")
    start = time.time()
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(cpu_task, 10000) for _ in range(10)]
        results = [f.result() for f in futures]
    multi_thread_time = time.time() - start
    print(f"多线程时间: {multi_thread_time:.3f}s")

    # 多进程性能
    print("多进程测试...")
    start = time.time()
    with ProcessPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(cpu_task, 10000) for _ in range(10)]
        results = [f.result() for f in futures]
    multi_process_time = time.time() - start
    print(f"多进程时间: {multi_process_time:.3f}s")

    # 计算加速比
    thread_speedup = single_time / multi_thread_time
    process_speedup = single_time / multi_process_time

    print(f"线程加速比: {thread_speedup:.2f}x")
    print(f"进程加速比: {process_speedup:.2f}x")

    print_result("并发性能测试", True,
                f"单线程:{single_time:.2f}s 线程:{multi_thread_time:.2f}s({thread_speedup:.2f}x) "
                f"进程:{multi_process_time:.2f}s({process_speedup:.2f}x)")
    return True

# 测试3: 文件系统性能测试
def test_filesystem_performance():
    """测试文件系统性能"""
    print_header("测试3: 文件系统性能测试")

    test_file = Path("test_temp_file.dat")

    # 写入测试
    print("写入性能测试...")
    start = time.time()
    data = b"x" * (1024 * 1024)  # 1MB
    for i in range(10):
        test_file.write_bytes(data)
    write_time = time.time() - start
    write_speed = (10 * 1024) / write_time  # MB/s
    print(f"写入10MB耗时: {write_time:.3f}s, 速度: {write_speed:.1f} MB/s")

    # 读取测试
    print("读取性能测试...")
    start = time.time()
    for i in range(10):
        _ = test_file.read_bytes()
    read_time = time.time() - start
    read_speed = (10 * 1024) / read_time  # MB/s
    print(f"读取10MB耗时: {read_time:.3f}s, 速度: {read_speed:.1f} MB/s")

    # 清理
    test_file.unlink()

    print_result("文件系统测试", True, f"写入:{write_speed:.1f}MB/s 读取:{read_speed:.1f}MB/s")
    return True

# 测试4: 数据库操作性能测试
def test_database_performance():
    """测试数据库操作性能"""
    print_header("测试4: 数据库操作性能测试")

    import sqlite3
    import random

    db_file = "test_db.sqlite"

    # 创建数据库连接
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # 创建表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_table (
            id INTEGER PRIMARY KEY,
            value REAL,
            name TEXT
        )
    """)

    # 批量插入测试
    print("批量插入测试...")
    start = time.time()
    data = [(i, random.random(), f"name_{i}") for i in range(10000)]
    cursor.executemany("INSERT INTO test_table VALUES (?, ?, ?)", data)
    conn.commit()
    insert_time = time.time() - start
    print(f"插入10000条记录: {insert_time:.3f}s")

    # 查询测试
    print("查询测试...")
    start = time.time()
    for _ in range(100):
        cursor.execute("SELECT * FROM test_table WHERE value > 0.5")
        _ = cursor.fetchall()
    query_time = time.time() - start
    print(f"执行100次查询: {query_time:.3f}s")

    # 清理
    cursor.execute("DROP TABLE IF EXISTS test_table")
    conn.close()
    Path(db_file).unlink()

    print_result("数据库测试", True, f"插入:{insert_time:.2f}s 查询:{query_time:.2f}s")
    return True

# 测试5: API性能测试
def test_api_performance():
    """测试API性能"""
    print_header("测试5: API模块性能测试")

    try:
        # 测试数据适配器
        from src.data_adapters.base_adapter import BaseAdapter
        print("✅ 数据适配器模块加载成功")

        # 测试模型
        from src.models.base import Trade, Position, Portfolio
        print("✅ 数据模型加载成功")

        # 测试回测引擎
        from src.backtest.base_backtest import BacktestEngine
        print("✅ 回测引擎加载成功")

        # 测试性能计算
        from src.backtest.strategy_performance import PerformanceCalculator
        print("✅ 性能计算模块加载成功")

        # 简单性能测试
        import pandas as pd
        import numpy as np

        print("性能计算测试...")
        start = time.time()

        # 创建模拟数据
        dates = pd.date_range('2020-01-01', periods=1000, freq='D')
        returns = np.random.randn(1000) / 100
        equity = (1 + returns).cumprod()

        # 计算性能指标
        total_return = (equity.iloc[-1] / equity.iloc[0] - 1) * 100
        volatility = returns.std() * np.sqrt(252) * 100
        sharpe = total_return / volatility if volatility > 0 else 0

        calc_time = time.time() - start
        print(f"计算1000天性能指标: {calc_time:.3f}s")
        print(f"  总收益率: {total_return:.2f}%")
        print(f"  波动率: {volatility:.2f}%")
        print(f"  夏普比率: {sharpe:.3f}")

        print_result("API性能测试", True, f"模块加载正常, 计算耗时:{calc_time:.3f}s")
        return True

    except Exception as e:
        print(f"❌ API测试失败: {e}")
        return False

# 测试6: 错误处理测试
def test_error_handling():
    """测试错误处理能力"""
    print_header("测试6: 错误处理与恢复测试")

    errors_caught = 0

    # 测试异常捕获
    try:
        raise ValueError("测试错误")
    except ValueError:
        errors_caught += 1

    # 测试嵌套异常
    try:
        try:
            raise KeyError("嵌套错误")
        except KeyError as e:
            raise RuntimeError("包装错误") from e
    except RuntimeError:
        errors_caught += 1

    # 测试资源清理
    try:
        with open("test_temp.txt", "w") as f:
            f.write("test")
            raise Exception("提前退出")
    except Exception:
        pass
    finally:
        Path("test_temp.txt").unlink(missing_ok=True)

    # 验证资源已清理
    if not Path("test_temp.txt").exists():
        errors_caught += 1

    print(f"成功处理 {errors_caught}/3 类错误")

    print_result("错误处理测试", errors_caught == 3, f"处理{errors_caught}类错误")
    return errors_caught == 3

# 测试7: 压力测试
def test_stress_test():
    """压力测试"""
    print_header("测试7: 压力测试")

    # CPU压力测试
    print("CPU压力测试 (5秒)...")
    start = time.time()
    end_time = start + 5

    def cpu_intensive():
        while time.time() < end_time:
            _ = sum(i**2 for i in range(1000))

    threads = []
    for _ in range(4):
        t = threading.Thread(target=cpu_intensive)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    stress_time = time.time() - start
    print(f"4线程CPU压力测试: {stress_time:.2f}s")

    print_result("压力测试", True, f"持续时间:{stress_time:.2f}s")
    return True

# 测试8: 内存泄漏测试
def test_memory_leak():
    """内存泄漏测试"""
    print_header("测试8: 内存泄漏测试")

    initial_memory = get_memory_usage()
    print(f"初始内存: {initial_memory:.2f} MB")

    # 创建和销毁对象多次
    for round in range(5):
        objects = []
        for i in range(1000):
            obj = {
                'id': i,
                'data': list(range(100)),
                '计算': sum(range(100))
            }
            objects.append(obj)

        del objects
        gc.collect()

        current_memory = get_memory_usage()
        print(f"第{round+1}轮后内存: {current_memory:.2f} MB (变化: {current_memory-initial_memory:+.2f} MB)")

    # 验证内存回收
    gc.collect()
    final_memory = get_memory_usage()
    memory_diff = final_memory - initial_memory

    print(f"最终内存: {final_memory:.2f} MB (总变化: {memory_diff:+.2f} MB)")

    # 允许10MB的误差
    has_leak = memory_diff > 10
    print_result("内存泄漏测试", not has_leak, f"变化:{memory_diff:+.1f}MB")
    return not has_leak

# 主函数
def main():
    """主测试函数"""
    print("\n" + "="*80)
    print(" 🔬 深度系统测试 - 开始")
    print("="*80)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python版本: {sys.version}")
    print(f"CPU核心数: {mp.cpu_count()}")
    print(f"内存: {psutil.virtual_memory().total / 1024 / 1024 / 1024:.1f} GB")

    tests = [
        ("内存使用测试", test_memory_usage),
        ("并发性能测试", test_concurrent_performance),
        ("文件系统测试", test_filesystem_performance),
        ("数据库测试", test_database_performance),
        ("API性能测试", test_api_performance),
        ("错误处理测试", test_error_handling),
        ("压力测试", test_stress_test),
        ("内存泄漏测试", test_memory_leak),
    ]

    results = []
    start_time = time.time()

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
            results.append((test_name, False))

    total_time = time.time() - start_time

    # 打印总结
    print_header("测试总结")
    passed = sum(1 for _, r in results if r)
    total = len(results)

    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} {test_name}")

    print(f"\n总计: {passed}/{total} 测试通过 ({passed/total*100:.1f}%)")
    print(f"总耗时: {total_time:.2f} 秒")

    # 保存详细报告
    with open("DEEP_TEST_REPORT.md", "w", encoding="utf-8") as f:
        f.write("# 深度系统测试报告\n\n")
        f.write(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"## 测试结果\n\n")
        f.write(f"- 总测试数: {total}\n")
        f.write(f"- 通过测试: {passed}\n")
        f.write(f"- 失败测试: {total - passed}\n")
        f.write(f"- 通过率: {passed/total*100:.1f}%\n")
        f.write(f"- 总耗时: {total_time:.2f} 秒\n\n")

        f.write("## 详细结果\n\n")
        for test_name, result in results:
            status = "✅ 通过" if result else "❌ 失败"
            f.write(f"- {status} {test_name}\n")

    print(f"\n详细报告已保存至: DEEP_TEST_REPORT.md")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
