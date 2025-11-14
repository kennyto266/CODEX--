import os
from collections import defaultdict

with open('untracked_files.txt', 'r', encoding='utf-8') as f:
    files = [line.strip().strip('"') for line in f if line.strip()]

categories = {
    'Documentation': [],
    'Configuration': [],
    'Data': [],
    'Logs/Results': [],
    'Python Scripts': [],
    'Workflows': [],
    'Tests': [],
    'Deployment': [],
    'Temp/Cache': [],
    'Other': []
}

for file in files:
    ext = os.path.splitext(file)[1].lower()
    basename = os.path.basename(file)

    if file.startswith('.github/') or 'GUIDE' in file or 'README' in file or 'SUMMARY' in file or 'REPORT' in file or file.endswith('.md'):
        categories['Documentation'].append(file)
    elif file.startswith('config/') or ext in ['.yaml', '.yml', '.json', '.js', '.conf'] or 'config' in file:
        categories['Configuration'].append(file)
    elif ext in ['.json', '.csv', '.parquet', '.h5', '.db', '.sqlite'] and not 'test' in file.lower():
        categories['Data'].append(file)
    elif 'result' in file.lower() or 'log' in file.lower() or 'optimization' in file.lower() or 'backtest' in file.lower():
        categories['Logs/Results'].append(file)
    elif ext == '.py' or 'optimization' in file or 'test' in file or 'complete_' in file or 'run_' in file or 'fetch_' in file or 'demo_' in file:
        categories['Python Scripts'].append(file)
    elif file.startswith('.github/workflows/') or 'workflow' in file:
        categories['Workflows'].append(file)
    elif 'test' in file.lower() or ext in ['.yaml', '.yml', '.json'] and 'test' in file.lower():
        categories['Tests'].append(file)
    elif 'docker' in file.lower() or 'deploy' in file.lower() or 'helm' in file.lower() or 'k8s' in file.lower():
        categories['Deployment'].append(file)
    elif 'cache' in file.lower() or 'temp' in file.lower() or 'auto_' in file or basename.startswith('.'):
        categories['Temp/Cache'].append(file)
    else:
        categories['Other'].append(file)

print("=" * 80)
print("未跟踪文件分类分析报告")
print("=" * 80)
print(f"总计: {len(files)} 个未跟踪文件")
print()

for category, files_list in categories.items():
    print(f"\n{'=' * 80}")
    print(f"{category} ({len(files_list)} 文件)")
    print(f"{'=' * 80}")
    for f in sorted(files_list)[:15]:
        print(f"  {f}")
    if len(files_list) > 15:
        print(f"  ... 还有 {len(files_list) - 15} 个文件")
