#!/usr/bin/env python3
"""
Duplicate File Cleanup Script
Remove duplicate files with numeric suffixes, keep only the latest version
"""

import os
import glob
from collections import defaultdict
import re

def get_base_name(filename):
    """Get base name of file (without numeric suffix)"""
    match = re.match(r'^(.+?)((_\d+)*)\.(\w+)$', filename)
    if match:
        base = match.group(1)
        suffix = match.group(2)
        ext = match.group(4)
        return base, suffix, ext
    return None, None, None

def cleanup_duplicate_files():
    """Clean up duplicate files"""
    print("Starting duplicate file cleanup...")
    print("=" * 70)
    
    # Statistics
    total_groups = 0
    total_files = 0
    files_to_delete = []
    
    # Group by directory
    groups = defaultdict(list)
    
    # Find all files with numeric suffixes
    for root, dirs, files in os.walk('.'):
        # Skip .git and other system directories
        dirs[:] = [d for d in dirs if not d.startswith('.git') and d != '__pycache__']
        
        for filename in files:
            if '_' in filename and filename != 'README.md':
                base, suffix, ext = get_base_name(filename)
                if base and suffix is not None:
                    key = f"{root}/{base}.{ext}"
                    groups[key].append(f"{root}/{filename}")
    
    # Process each group
    for base_path, files in groups.items():
        if len(files) > 1:
            total_groups += 1
            total_files += len(files)
            
            print(f"\nProcessing group {total_groups}:")
            print(f"  Base: {os.path.basename(base_path)}")
            print(f"  Count: {len(files)}")
            
            # Sort by filename (higher numeric suffix last)
            files_sorted = sorted(files, key=lambda x: x.split('/')[-1])
            
            # Keep last (latest), delete others
            files_to_delete.extend(files_sorted[:-1])
            
            print(f"  Keep: {os.path.basename(files_sorted[-1])}")
            print(f"  Delete: {len(files_sorted) - 1} files")
    
    # Execute deletion
    print("\n" + "=" * 70)
    print(f"Ready to delete {len(files_to_delete)} duplicate files...")
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
    print(f"Cleanup completed!")
    print(f"  Groups: {total_groups}")
    print(f"  Total: {total_files}")
    print(f"  Deleted: {deleted_count}")
    print(f"  Kept: {total_files - deleted_count}")
    print("=" * 70)
    
    return deleted_count

if __name__ == "__main__":
    cleanup_duplicate_files()
