"""
性能分析和优化建议 - QA审查
"""

import time
import psutil
try:
    import memory_profiler
    HAS_MEMORY_PROFILER = True
except ImportError:
    HAS_MEMORY_PROFILER = False
    print("Warning: memory_profiler not installed, using simplified version")
from functools import wraps
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Callable
import logging

# 配置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class PerformanceProfiler:
    """性能分析器"""
    
    def __init__(self):
        self.metrics = {}
        self.start_time = time.time()
    
    def profile_function(self, func: Callable) -> Callable:
        """函数性能装饰器"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            result = func(*args, **kwargs)
            
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            execution_time = end_time - start_time
            memory_used = end_memory - start_memory
            
            # 记录性能指标
            func_name = func.__name__
            if func_name not in self.metrics:
                self.metrics[func_name] = {
                    'calls': 0,
                    'total_time': 0,
                    'total_memory': 0,
                    'max_time': 0,
                    'max_memory': 0
                }
            
            self.metrics[func_name]['calls'] += 1
            self.metrics[func_name]['total_time'] += execution_time
            self.metrics[func_name]['total_memory'] += memory_used
            self.metrics[func_name]['max_time'] = max(
                self.metrics[func_name]['max_time'], execution_time
            )
            self.metrics[func_name]['max_memory'] = max(
                self.metrics[func_name]['max_memory'], memory_used
            )
            
            logging.info(f"{func_name}: {execution_time:.3f}s, {memory_used:.1f}MB")
            return result
        
        return wrapper
    
    def get_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        summary = {}
        for func_name, metrics in self.metrics.items():
            avg_time = metrics['total_time'] / metrics['calls']
            avg_memory = metrics['total_memory'] / metrics['calls']
            
            summary[func_name] = {
                'calls': metrics['calls'],
                'avg_time': avg_time,
                'max_time': metrics['max_time'],
                'avg_memory': avg_memory,
                'max_memory': metrics['max_memory']
            }
        
        return summary

# 性能优化建议
class PerformanceOptimizer:
    """性能优化器"""
    
    @staticmethod
    def optimize_dataframe_operations(df: pd.DataFrame) -> pd.DataFrame:
        """优化DataFrame操作"""
        # 1. 使用更高效的数据类型
        for col in df.select_dtypes(include=['object']).columns:
            if df[col].dtype == 'object':
                try:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                except:
                    pass
        
        # 2. 使用category类型减少内存
        for col in df.select_dtypes(include=['object']).columns:
            if df[col].nunique() / len(df) < 0.5:  # 如果唯一值比例小于50%
                df[col] = df[col].astype('category')
        
        return df
    
    @staticmethod
    def vectorized_technical_indicators(df: pd.DataFrame) -> Dict[str, float]:
        """向量化技术指标计算"""
        close = df['close']
        high = df['high']
        low = df['low']
        
        indicators = {}
        
        # 使用numpy进行向量化计算
        if len(close) >= 20:
            # SMA - 向量化计算
            sma_20 = np.convolve(close, np.ones(20)/20, mode='valid')
            indicators['sma_20'] = float(sma_20[-1])
        
        if len(close) >= 50:
            sma_50 = np.convolve(close, np.ones(50)/50, mode='valid')
            indicators['sma_50'] = float(sma_50[-1])
        
        # RSI - 向量化计算
        if len(close) >= 14:
            delta = np.diff(close)
            gain = np.where(delta > 0, delta, 0)
            loss = np.where(delta < 0, -delta, 0)
            
            # 使用滑动窗口
            gain_ma = np.convolve(gain, np.ones(14)/14, mode='valid')
            loss_ma = np.convolve(loss, np.ones(14)/14, mode='valid')
            
            rs = gain_ma / (loss_ma + 1e-10)  # 避免除零
            rsi = 100 - (100 / (1 + rs))
            indicators['rsi'] = float(rsi[-1])
        
        return indicators
    
    @staticmethod
    def optimize_memory_usage(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """优化内存使用"""
        # 1. 只保留必要的数据
        required_keys = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        optimized_data = []
        
        for item in data:
            optimized_item = {k: v for k, v in item.items() if k in required_keys}
            optimized_data.append(optimized_item)
        
        return optimized_data

# 性能测试
def performance_test():
    """性能测试函数"""
    profiler = PerformanceProfiler()
    
    # 模拟数据
    data = []
    for i in range(1000):
        data.append({
            'timestamp': f'2023-01-{i%30+1:02d}',
            'open': 100 + np.random.randn(),
            'high': 105 + np.random.randn(),
            'low': 95 + np.random.randn(),
            'close': 100 + np.random.randn(),
            'volume': 1000000 + np.random.randint(-100000, 100000)
        })
    
    @profiler.profile_function
    def test_original_method(data):
        """原始方法测试"""
        df = pd.DataFrame(data)
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df = df.dropna()
        
        # 计算SMA
        close = df['close']
        if len(close) >= 20:
            sma_20 = close.rolling(window=20).mean().iloc[-1]
        if len(close) >= 50:
            sma_50 = close.rolling(window=50).mean().iloc[-1]
        
        return {'sma_20': sma_20, 'sma_50': sma_50}
    
    @profiler.profile_function
    def test_optimized_method(data):
        """优化方法测试"""
        df = pd.DataFrame(data)
        df = PerformanceOptimizer.optimize_dataframe_operations(df)
        df = df.dropna()
        
        # 使用向量化计算
        indicators = PerformanceOptimizer.vectorized_technical_indicators(df)
        return indicators
    
    # 运行测试
    print("Running performance tests...")
    
    # 测试原始方法
    for _ in range(10):
        test_original_method(data)
    
    # 测试优化方法
    for _ in range(10):
        test_optimized_method(data)
    
    # 输出结果
    summary = profiler.get_summary()
    print("\nPerformance Test Results:")
    print("-" * 50)

    for func_name, metrics in summary.items():
        print(f"{func_name}:")
        print(f"  Calls: {metrics['calls']}")
        print(f"  Avg Time: {metrics['avg_time']:.4f}s")
        print(f"  Max Time: {metrics['max_time']:.4f}s")
        print(f"  Avg Memory: {metrics['avg_memory']:.2f}MB")
        print(f"  Max Memory: {metrics['max_memory']:.2f}MB")
        print()

# Performance Optimization Recommendations
PERFORMANCE_RECOMMENDATIONS = {
    "High Priority": [
        "Use connection pooling to reduce HTTP connection overhead",
        "Implement data preloading and caching strategies",
        "Use vectorized computation instead of loops",
        "Optimize DataFrame data types to reduce memory usage"
    ],
    "Medium Priority": [
        "Implement async processing to improve concurrent performance",
        "Use database instead of file storage",
        "Implement pagination for large data loading",
        "Add performance monitoring and alerting"
    ],
    "Low Priority": [
        "Use CDN to accelerate static resources",
        "Implement data compression for transmission",
        "Optimize frontend rendering performance",
        "Add cache preheating mechanism"
    ]
}

if __name__ == "__main__":
    try:
        print("Starting Performance Analysis...")
        print("System Information:")
        print(f"  CPU Cores: {psutil.cpu_count()}")
        print(f"  Available Memory: {psutil.virtual_memory().available / 1024 / 1024 / 1024:.1f} GB")
        print()

        performance_test()

        print("\nPerformance Optimization Recommendations:")
        print("=" * 50)
        for priority, recommendations in PERFORMANCE_RECOMMENDATIONS.items():
            print(f"\n{priority}:")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")

        print("\nAnalysis Complete!")

    except Exception as e:
        print(f"Error occurred during performance analysis: {e}")
        print("Please check if required modules are installed correctly")
        import traceback
        traceback.print_exc()
