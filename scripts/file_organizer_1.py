#!/usr/bin/env python3
"""
文件整理工具 - 将未跟踪文件分类移动到相应目录
"""
import os
import shutil
import json
from datetime import datetime

def create_log():
    log = {
        'timestamp': datetime.now().isoformat(),
        'moved_files': [],
        'errors': []
    }
    return log

def classify_file(filename):
    """根据文件名分类文件"""
    name_lower = filename.lower()

    # 文档分类
    if 'guide' in name_lower or 'readme' in name_lower:
        return 'docs/guides'
    elif 'summary' in name_lower or 'completion' in name_lower:
        return 'docs/summaries'
    elif 'sprint' in name_lower or 'story' in name_lower:
        return 'docs/sprints'
    elif 'report' in name_lower or 'analysis' in name_lower or 'implementation' in name_lower:
        return 'docs/reports'
    elif 'api' in name_lower or 'api_' in name_lower:
        return 'docs/api'

    # 脚本分类
    elif filename.endswith('.py'):
        if 'test' in name_lower or 'benchmark' in name_lower:
            return 'scripts/tests'
        elif 'optimization' in name_lower or 'optimize' in name_lower or 'hibor' in name_lower:
            return 'scripts/optimization'
        elif 'demo' in name_lower or 'example' in name_lower:
            return 'scripts/demo'
        elif 'fetch' in name_lower or 'collect' in name_lower or 'download' in name_lower or 'crawl' in name_lower:
            return 'scripts/collection'
        else:
            return 'scripts'

    # 配置分类
    elif filename.endswith(('.yaml', '.yml', '.json', '.conf', '.js')):
        if 'workflow' in name_lower or 'ci' in name_lower or 'deploy' in name_lower:
            return 'config/deployment'
        elif 'cache' in name_lower or 'performance' in name_lower:
            return 'config/monitoring'
        else:
            return 'config'

    # 数据分类
    elif filename.endswith(('.json', '.csv', '.parquet', '.db')):
        if 'result' in name_lower or 'backtest' in name_lower or 'optimization' in name_lower:
            return 'data/results'
        elif 'test' in name_lower or 'mock' in name_lower:
            return 'data/test'
        elif 'real' in name_lower or 'gov' in name_lower:
            return 'data/real'
        else:
            return 'data/temp'

    # 其他
    else:
        if 'log' in name_lower or 'tmp' in name_lower or filename.startswith('.'):
            return 'archive'
        return 'archive'

def organize_files(test_mode=True, test_limit=50):
    """整理未跟踪文件（支持测试模式）"""
    log = create_log()

    # 获取未跟踪文件列表
    result = os.popen('git status --porcelain | grep "^??" | awk \'{print $2}\'').read()
    untracked_files = [f.strip().strip('"') for f in result.split('\n') if f.strip()]

    # 测试模式限制文件数量
    if test_mode:
        untracked_files = untracked_files[:test_limit]
        print(f"TEST MODE: Processing first {test_limit} files")
    else:
        print(f"PROCESSING ALL: {len(untracked_files)} files")

    print(f"Found {len(untracked_files)} untracked files to process")
    print("=" * 80)

    for filename in untracked_files:
        if not filename:
            continue

        try:
            # 跳过不存在的文件
            if not os.path.exists(filename):
                log['errors'].append(f"File not found: {filename}")
                continue

            # 分类文件
            target_dir = classify_file(filename)

            # 创建目标目录
            os.makedirs(target_dir, exist_ok=True)

            # 构建目标路径
            target_path = os.path.join(target_dir, os.path.basename(filename))

            # 处理文件名冲突
            counter = 1
            original_target = target_path
            while os.path.exists(target_path):
                name, ext = os.path.splitext(original_target)
                target_path = f"{name}_{counter}{ext}"
                counter += 1

            # 移动文件
            shutil.move(filename, target_path)
            log['moved_files'].append({
                'from': filename,
                'to': target_path,
                'category': target_dir
            })

            print(f"[OK] {filename} -> {target_path}")

        except Exception as e:
            error_msg = f"Error moving {filename}: {str(e)}"
            print(f"[ERROR] {error_msg}")
            log['errors'].append(error_msg)

    # 保存日志
    with open('file_organization_log.json', 'w', encoding='utf-8') as f:
        json.dump(log, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80)
    print(f"Summary:")
    print(f"  Moved: {len(log['moved_files'])} files")
    print(f"  Errors: {len(log['errors'])} errors")
    print(f"  Log saved to: file_organization_log.json")

    return log

if __name__ == "__main__":
    import sys
    test_mode = '--test' in sys.argv or '-t' in sys.argv
    organize_files(test_mode=test_mode, test_limit=50)
