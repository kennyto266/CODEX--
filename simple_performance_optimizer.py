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
import gc
from datetime import datetime
from typing import Dict, List, Any, Optional
import sqlite3


class SimplePerformanceOptimizer:
    """简单性能优化器"""

    def __init__(self):
        self.metrics = {
            "start_time": datetime.now(),
            "optimizations_applied": [],
            "performance_metrics": {},
            "recommendations": []
        }

    def get_basic_metrics(self) -> Dict[str, Any]:
        """获取基本系统指标"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            return {
                "timestamp": datetime.now().isoformat(),
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "used_gb": round(memory.used / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "percent": memory.percent
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "used_gb": round(disk.used / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "percent": round((disk.used / disk.total) * 100, 2)
                }
            }
        except Exception as e:
            return {"error": str(e)}

    def optimize_memory(self) -> Dict[str, Any]:
        """内存优化"""
        try:
            # 强制垃圾回收
            gc.collect()

            try:
                import psutil
                memory = psutil.virtual_memory()
                return {
                    "success": True,
                    "memory_after": {
                        "percent": memory.percent,
                        "used_gb": round(memory.used / (1024**3), 2),
                        "available_gb": round(memory.available / (1024**3), 2)
                    }
                }
            except:
                return {"success": True, "message": "垃圾回收已完成"}

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
                optimizations.append("已分析数据库")

                # 清理数据库
                conn.execute("VACUUM")
                optimizations.append("已清理数据库")

                # 优化表
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()

                for table in tables:
                    table_name = table[0]
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

        # 内存建议
        if "memory" in metrics:
            mem_percent = metrics["memory"].get("percent", 0)
            if mem_percent > 80:
                recommendations.append({
                    "category": "内存",
                    "issue": "内存使用率过高",
                    "recommendation": "增加内存或优化内存使用",
                    "priority": "高"
                })
            elif mem_percent > 60:
                recommendations.append({
                    "category": "内存",
                    "issue": "内存使用率偏高",
                    "recommendation": "关注内存使用情况",
                    "priority": "中"
                })

        # 磁盘建议
        if "disk" in metrics:
            disk_percent = metrics["disk"].get("percent", 0)
            if disk_percent > 90:
                recommendations.append({
                    "category": "磁盘",
                    "issue": "磁盘空间不足",
                    "recommendation": "清理临时文件或扩展磁盘空间",
                    "priority": "高"
                })
            elif disk_percent > 80:
                recommendations.append({
                    "category": "磁盘",
                    "issue": "磁盘空间使用率较高",
                    "recommendation": "考虑清理不必要的文件",
                    "priority": "中"
                })

        return recommendations

    async def run_optimization(self) -> Dict[str, Any]:
        """运行完整优化"""
        print("=" * 60)
        print("CODEX Performance Optimizer - Starting Optimization")
        print("=" * 60)
        print()

        # 1. 获取系统指标
        print("[1/4] Analyzing system performance...")
        metrics = self.get_basic_metrics()
        self.metrics["performance_metrics"] = metrics

        # 2. 内存优化
        print("[2/4] Optimizing memory...")
        mem_opt = self.optimize_memory()
        if mem_opt["success"]:
            self.metrics["optimizations_applied"].append(mem_opt)
            print("  - Memory optimization completed")

        # 3. 数据库优化
        print("[3/4] Optimizing database...")
        db_opt = self.optimize_database()
        if db_opt["success"]:
            self.metrics["optimizations_applied"].append(db_opt)
            print(f"  - Database optimization completed: {db_opt.get('tables_optimized', 0)} tables")

        # 4. 清理缓存
        print("[4/4] Clearing cache...")
        cache_opt = self.clear_cache()
        if cache_opt["success"]:
            self.metrics["optimizations_applied"].append(cache_opt)
            print(f"  - Cache cleared: {cache_opt.get('files_cleared', 0)} files")

        # 生成建议
        print()
        print("Generating performance recommendations...")
        recommendations = self.generate_recommendations(metrics)
        self.metrics["recommendations"] = recommendations

        # 打印建议
        if recommendations:
            print()
            print("Performance Recommendations:")
            for rec in recommendations:
                print(f"  [{rec['priority']}] {rec['category']}: {rec['recommendation']}")
        else:
            print("  System performance is good, no special recommendations")

        print()
        print("=" * 60)
        print("Optimization Complete!")
        print("=" * 60)

        return self.metrics

    def save_report(self, filepath: str = "performance_report.json"):
        """保存优化报告"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.metrics, f, ensure_ascii=False, indent=2, default=str)
            print(f"Report saved to: {filepath}")
        except Exception as e:
            print(f"Failed to save report: {e}")


def main():
    """主函数"""
    optimizer = SimplePerformanceOptimizer()

    # 运行优化
    asyncio.run(optimizer.run_optimization())

    # 保存报告
    optimizer.save_report("performance_report.json")

    # 打印总结
    print()
    print("Optimization Summary:")
    print(f"  Optimizations applied: {len(optimizer.metrics['optimizations_applied'])}")
    print(f"  Recommendations: {len(optimizer.metrics['recommendations'])}")
    print(f"  Start time: {optimizer.metrics['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
