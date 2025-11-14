#!/usr/bin/env python3
"""
Performance Benchmark Script
Establish baseline performance metrics before optimization
"""

import time
import psutil
import os
import sys

def get_system_metrics():
    """Get current system metrics"""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    
    return {
        'cpu_percent': cpu_percent,
        'memory_total_gb': memory.total / (1024**3),
        'memory_available_gb': memory.available / (1024**3),
        'memory_percent': memory.percent
    }

def count_python_files():
    """Count Python files in project"""
    count = 0
    total_size = 0
    
    for root, dirs, files in os.walk('.'):
        # Skip .git and other system directories
        dirs[:] = [d for d in dirs if not d.startswith('.git') and d != '__pycache__']
        
        for file in files:
            if file.endswith('.py'):
                count += 1
                try:
                    total_size += os.path.getsize(os.path.join(root, file))
                except:
                    pass
    
    return {
        'count': count,
        'total_size_mb': total_size / (1024**2)
    }

def find_large_files():
    """Find files larger than 100KB"""
    large_files = []
    
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if not d.startswith('.git') and d != '__pycache__']
        
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                try:
                    size = os.path.getsize(path)
                    if size > 100 * 1024:  # 100KB
                        large_files.append((path, size))
                except:
                    pass
    
    large_files.sort(key=lambda x: x[1], reverse=True)
    return large_files

def find_inefficient_loops():
    """Find files with inefficient loop patterns"""
    inefficient_patterns = [
        'for i in range(len(',
        'time.sleep(',
        'import pandas'
    ]
    
    results = {}
    
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if not d.startswith('.git') and d != '__pycache__']
        
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                    for pattern in inefficient_patterns:
                        if pattern in content:
                            if pattern not in results:
                                results[pattern] = []
                            results[pattern].append(path)
                except:
                    pass
    
    return results

def main():
    print("=" * 70)
    print("PERFORMANCE BASELINE MEASUREMENT")
    print("=" * 70)
    
    # System metrics
    print("\n[1] System Metrics")
    print("-" * 70)
    metrics = get_system_metrics()
    print(f"CPU Usage: {metrics['cpu_percent']:.1f}%")
    print(f"Memory Total: {metrics['memory_total_gb']:.2f} GB")
    print(f"Memory Available: {metrics['memory_available_gb']:.2f} GB")
    print(f"Memory Usage: {metrics['memory_percent']:.1f}%")
    
    # Python files
    print("\n[2] Python Files")
    print("-" * 70)
    file_info = count_python_files()
    print(f"Total Python files: {file_info['count']}")
    print(f"Total size: {file_info['total_size_mb']:.2f} MB")
    print(f"Average size: {file_info['total_size_mb'] / file_info['count']:.2f} KB/file")
    
    # Large files
    print("\n[3] Large Python Files (>100KB)")
    print("-" * 70)
    large_files = find_large_files()
    print(f"Found {len(large_files)} large files")
    for path, size in large_files[:10]:
        print(f"  {size/1024:.1f}KB - {path}")
    
    # Inefficient patterns
    print("\n[4] Inefficient Loop Patterns")
    print("-" * 70)
    inefficient = find_inefficient_loops()
    for pattern, files in inefficient.items():
        print(f"{pattern}: {len(files)} files")
        for f in files[:3]:
            print(f"  - {f}")
        if len(files) > 3:
            print(f"  ... and {len(files) - 3} more")
    
    print("\n" + "=" * 70)
    print("BASELINE MEASUREMENT COMPLETE")
    print("=" * 70)
    
    # Save baseline
    baseline = {
        'timestamp': time.time(),
        'system': metrics,
        'files': file_info,
        'large_files': [(p, s) for p, s in large_files],
        'inefficient': {k: len(v) for k, v in inefficient.items()}
    }
    
    import json
    with open('performance_baseline.json', 'w') as f:
        json.dump(baseline, f, indent=2)
    
    print("Baseline saved to: performance_baseline.json")

if __name__ == "__main__":
    main()
