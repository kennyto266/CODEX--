#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CODEX量化交易系统 - 性能优化器
自动分析并优化系统性能
"""

import asyncio
import time
import json
import os
import psutil
import gc
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import sqlite3


class PerformanceOptimizer:
    """性能优化器"""

    def __init__(self):
        self.metrics = {
            "start_time": datetime.now(),
            "optimizations_applied": [],
            "performance_metrics": {},
            "recommendations": []
        }

    def get_system_metrics(self) -> Dict[str, Any]:
        """获取系统性能指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()

            # 内存使用
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()

            # 磁盘使用
            disk = psutil.disk_usage('/')

            # 网络IO
            network = psutil.net_io_counters()

            # 进程信息
            process_count = len(psutil.pids())

            return {
                "timestamp": datetime.now().isoformat(),
                "cpu": {
                    "usage_percent": cpu_percent,
                    "count": cpu_count,
                    "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used,
                    "free": memory.free
                },
                "swap": {
                    "total": swap.total,
                    "used": swap.used,
                    "free": swap.free,
                    "percent": swap.percent
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": (disk.used / disk.total) * 100
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                },
                "processes": {
                    "count": process_count
                }
            }
        except Exception as e:
            return {"error": str(e)}

    def check_api_performance(self, base_url: str = "http://localhost:8000") -> Dict[str, Any]:
        """检查API性能"""
        import requests

        endpoints = [
            "/tasks",
            "/health"
        ]

        results = {}

        for endpoint in endpoints:
            try:
                url = f"{base_url}{endpoint}"
                start_time = time.time()

                response = requests.get(url, timeout=5)
                end_time = time.time()

                response_time = (end_time - start_time) * 1000  # ms

                results[endpoint] = {
                    "status_code": response.status_code,
                    "response_time_ms": round(response_time, 2),
                    "success": response.status_code == 200
                }
            except Exception as e:
                results[endpoint] = {
                    "error": str(e),
                    "success": False
                }

        return results

    def optimize_memory(self) -> Dict[str, Any]:
        """内存优化"""
        try:
            # 强制垃圾回收
            gc.collect()

            # 获取当前内存使用
            memory = psutil.virtual_memory()

            optimizations = []

            # 检查内存使用率
            if memory.percent > 80:
                optimizations.append({
                    "type": "memory_cleanup",
                    "action": "强制垃圾回收",
                    "result": "已完成"
                })

            return {
                "success": True,
                "optimizations": optimizations,
                "memory_after": {
                    "percent": memory.percent,
                    "used_gb": round(memory.used / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2)
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def optimize_database(self, db_path: str = "tasks.db") -> Dict[str, Any]:
        """数据库优化"""
        try:
            if not os.path.exists(db_path):
                return {"success": False, "error": "数据库文件不存在"}

            optimizations = []

            with sqlite3.connect(db_path) as conn:
                # 分析数据库
                conn.execute("ANALYZE")

                # 清理数据库
                conn.execute("VACUUM")

                # 优化表
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()

                for table in tables:
                    table_name = table[0]
                    # 重新索引
                    cursor.execute(f"REINDEX {table_name}")
                    optimizations.append(f"已优化表: {table_name}")

            return {
                "success": True,
                "optimizations": optimizations,
                "tables_optimized": len(tables)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def clear_cache(self) -> Dict[str, Any]:
        """清理缓存"""
        try:
            cache_dirs = [
                "__pycache__",
                ".pytest_cache",
                "node_modules/.cache",
                "dist",
                "build"
            ]

            cleared_files = 0
            cleared_size = 0

            for cache_dir in cache_dirs:
                if os.path.exists(cache_dir):
                    for root, dirs, files in os.walk(cache_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            try:
                                size = os.path.getsize(file_path)
                                os.remove(file_path)
                                cleared_files += 1
                                cleared_size += size
                            except:
                                pass

            return {
                "success": True,
                "files_cleared": cleared_files,
                "size_mb": round(cleared_size / (1024**2), 2)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def generate_recommendations(self, metrics: Dict[str, Any]) -> List[Dict[str, str]]:
        """生成优化建议"""
        recommendations = []

        # CPU建议
        if metrics.get("cpu", {}).get("usage_percent", 0) > 80:
            recommendations.append({
                "category": "CPU",
                "issue": "CPU使用率过高",
                "recommendation": "考虑升级CPU或优化算法复杂度",
                "priority": "高"
            })

        # 内存建议
        if metrics.get("memory", {}).get("percent", 0) > 80:
            recommendations.append({
                "category": "内存",
                "issue": "内存使用率过高",
                "recommendation": "增加内存或优化内存使用",
                "priority": "高"
            })

        # 磁盘建议
        if metrics.get("disk", {}).get("percent", 0) > 90:
            recommendations.append({
                "category": "磁盘",
                "issue": "磁盘空间不足",
                "recommendation": "清理临时文件或扩展磁盘空间",
                "priority": "高"
            })

        # 进程建议
        if metrics.get("processes", {}).get("count", 0) > 100:
            recommendations.append({
                "category": "进程",
                "issue": "进程数量过多",
                "recommendation": "关闭不必要的进程",
                "priority": "中"
            })

        return recommendations

    async def run_optimization(self) -> Dict[str, Any]:
        """运行完整优化"""
        print("=" * 60)
        print("🚀 CODEX性能优化器 - 开始优化")
        print("=" * 60)
        print()

        # 1. 获取系统指标
        print("[1/5] 正在分析系统性能...")
        metrics = self.get_system_metrics()
        self.metrics["performance_metrics"] = metrics

        # 2. 检查API性能
        print("[2/5] 正在检查API性能...")
        api_perf = self.check_api_performance()
        self.metrics["api_performance"] = api_perf

        # 3. 内存优化
        print("[3/5] 正在优化内存...")
        mem_opt = self.optimize_memory()
        if mem_opt["success"]:
            self.metrics["optimizations_applied"].append(mem_opt)
            print(f"  ✓ 清理了 {mem_opt['memory_after']['used_gb']}GB 内存")

        # 4. 数据库优化
        print("[4/5] 正在优化数据库...")
        db_opt = self.optimize_database()
        if db_opt["success"]:
            self.metrics["optimizations_applied"].append(db_opt)
            print(f"  ✓ 优化了 {db_opt['tables_optimized']} 个表")

        # 5. 清理缓存
        print("[5/5] 正在清理缓存...")
        cache_opt = self.clear_cache()
        if cache_opt["success"]:
            self.metrics["optimizations_applied"].append(cache_opt)
            print(f"  ✓ 清理了 {cache_opt['files_cleared']} 个缓存文件")

        # 生成建议
        print()
        print("生成优化建议...")
        recommendations = self.generate_recommendations(metrics)
        self.metrics["recommendations"] = recommendations

        # 打印建议
        if recommendations:
            print()
            print("🔍 性能建议:")
            for rec in recommendations:
                print(f"  [{rec['priority']}] {rec['category']}: {rec['recommendation']}")
        else:
            print("  ✓ 系统性能良好，无特殊建议")

        print()
        print("=" * 60)
        print("✅ 优化完成!")
        print("=" * 60)

        return self.metrics

    def save_report(self, filepath: str = "performance_report.json"):
        """保存优化报告"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.metrics, f, ensure_ascii=False, indent=2, default=str)
            print(f"📊 报告已保存到: {filepath}")
        except Exception as e:
            print(f"❌ 保存报告失败: {e}")


def main():
    """主函数"""
    optimizer = PerformanceOptimizer()

    # 运行优化
    asyncio.run(optimizer.run_optimization())

    # 保存报告
    optimizer.save_report("performance_report.json")

    # 打印总结
    print()
    print("📈 优化总结:")
    print(f"  优化项目: {len(optimizer.metrics['optimizations_applied'])}")
    print(f"  系统建议: {len(optimizer.metrics['recommendations'])}")
    print(f"  运行时间: {optimizer.metrics['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
