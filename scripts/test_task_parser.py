#!/usr/bin/env python3
"""
簡單的任務解析測試腳本
"""

import re

def test_parse_tasks(file_path):
    """測試解析任務"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        lines = content.split('\n')

        # 統計任務
        task_lines = [line for line in lines if line.strip().startswith('- [ ]')]
        task_count = len(task_lines)

        # 優先級統計
        priority_counts = {'P0': 0, 'P1': 0, 'P2': 0}
        for line in task_lines:
            for p in priority_counts.keys():
                if f'[{p}]' in line:
                    priority_counts[p] += 1

        # 工時統計
        hours = []
        for line in task_lines:
            match = re.search(r'\((\d+)\s*小時\)', line)
            if match:
                hours.append(int(match.group(1)))

        # 顯示結果
        print(f"\n{'='*60}")
        print(f"[TEST] 任務解析測試")
        print(f"{'='*60}\n")

        print(f"文件: {file_path}")
        print(f"總行數: {len(lines)}")
        print(f"任務數量: {task_count}\n")

        print("優先級分布:")
        for priority, count in priority_counts.items():
            percentage = (count / task_count * 100) if task_count > 0 else 0
            print(f"  {priority}: {count} 個 ({percentage:.1f}%)")

        if hours:
            print(f"\n工時統計:")
            print(f"  最小: {min(hours)} 小時")
            print(f"  最大: {max(hours)} 小時")
            print(f"  平均: {sum(hours) / len(hours):.1f} 小時")
            print(f"  總計: {sum(hours)} 小時")

        print(f"\n{'='*60}")
        print(f"[SUCCESS] 測試完成")
        print(f"{'='*60}\n")

        # 顯示前5個任務作為示例
        print("前5個任務示例:")
        for i, line in enumerate(task_lines[:5], 1):
            line = re.sub(r'^- \[ \]\s*', '', line)
            line = re.sub(r'\s*\[[P012]\]\s*', '', line)
            time_match = re.search(r'\((\d+)\s*小時\)', line)
            time_str = time_match.group(0) if time_match else ''
            line = re.sub(r'\(\d+\s*小時\)', '', line).strip()
            print(f"  {i}. {line} {time_str}")

        return True

    except Exception as e:
        print(f"\n[ERROR] 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    file_path = "openspec/changes/optimize-project-plan/tasks.md"
    success = test_parse_tasks(file_path)
    exit(0 if success else 1)
