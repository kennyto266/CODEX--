#!/usr/bin/env python3
"""
重复文件清理脚本
删除带数字后缀的重复文件，只保留最新版本
"""

import os
import glob
from collections import defaultdict
import re

def get_base_name(filename):
    """获取文件的基名称（去除数字后缀）"""
    # 匹配 filename.ext, filename_1.ext, filename_1_1.ext 等
    match = re.match(r'^(.+?)((_\d+)*)\.(\w+)$', filename)
    if match:
        base = match.group(1)
        suffix = match.group(2)
        ext = match.group(4)
        return base, suffix, ext
    return None, None, None

def cleanup_duplicate_files():
    """清理重复文件"""
    print("开始清理重复文件...")
    print("=" * 70)
    
    # 统计信息
    total_groups = 0
    total_files = 0
    files_to_delete = []
    
    # 按目录分组
    groups = defaultdict(list)
    
    # 查找所有带数字后缀的文件
    for root, dirs, files in os.walk('.'):
        # 跳过.git和其他系统目录
        dirs[:] = [d for d in dirs if not d.startswith('.git') and d != '__pycache__']
        
        for filename in files:
            if '_' in filename and filename != 'README.md':
                base, suffix, ext = get_base_name(filename)
                if base and suffix is not None:
                    key = f"{root}/{base}.{ext}"
                    groups[key].append(f"{root}/{filename}")
    
    # 处理每个组
    for base_path, files in groups.items():
        if len(files) > 1:
            total_groups += 1
            total_files += len(files)
            
            print(f"\n处理组 {total_groups}:")
            print(f"  基文件: {os.path.basename(base_path)}")
            print(f"  文件数量: {len(files)}")
            
            # 按文件名排序（数字后缀大的在后面）
            files_sorted = sorted(files, key=lambda x: x.split('/')[-1])
            
            # 保留最后一个（最新版本），删除其他的
            files_to_delete.extend(files_sorted[:-1])
            
            print(f"  保留: {os.path.basename(files_sorted[-1])}")
            print(f"  删除: {len(files_sorted) - 1}个文件")
    
    # 执行删除
    print("\n" + "=" * 70)
    print(f"准备删除 {len(files_to_delete)} 个重复文件...")
    print("=" * 70)
    
    deleted_count = 0
    for file_path in files_to_delete:
        try:
            os.remove(file_path)
            deleted_count += 1
            print(f"[DEL] {file_path}")
        except Exception as e:
            print(f"[ERROR] {file_path}: {e}")
    
    print("\n" + "=" * 70)
    print(f"清理完成!")
    print(f"  处理组: {total_groups}")
    print(f"  总文件: {total_files}")
    print(f"  已删除: {deleted_count}")
    print(f"  保留: {total_files - deleted_count}")
    print("=" * 70)
    
    return deleted_count

if __name__ == "__main__":
    cleanup_duplicate_files()
