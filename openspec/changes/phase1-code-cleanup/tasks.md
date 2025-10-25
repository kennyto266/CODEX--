# Phase 1 实施任务清单 (45 个任务)

## 总览

Phase 1 包含 45 个具体任务，分为 7 个主要组：

| 组 | 任务数 | 优先级 | 时间 |
|------|---------|--------|------|
| 1.1 准备工作 | 3 | CRITICAL | 1h |
| 1.2 删除冗余文件 | 10 | CRITICAL | 1h |
| 1.3 移动测试文件 | 15 | HIGH | 3h |
| 1.4 移动策略文件 | 6 | HIGH | 1h |
| 1.5 整理数据文件 | 5 | HIGH | 2h |
| 1.6 整理 Telegram | 2 | MEDIUM | 1h |
| 1.7 验证和文档 | 4 | CRITICAL | 3h |

**总计**: 45 任务，18-26 小时

---

## 组 1.1: 准备工作 (3 个任务)

### Task 1.1.1: 创建备份目录
- [ ] 创建 `_archived/` 目录: `mkdir _archived`
- [ ] 验证目录创建成功: `ls -la _archived/`
- [ ] 创建 `_archived/README.md` 说明备份内容

**验收标准**: `_archived/` 目录存在且可写入

### Task 1.1.2: 创建 git 分支
- [ ] 在 main 分支上: `git status`（确保干净）
- [ ] 创建特性分支: `git checkout -b feature/phase1-code-cleanup`
- [ ] 验证分支: `git branch`

**验收标准**: 当前分支为 `feature/phase1-code-cleanup`

### Task 1.1.3: 创建备份脚本
- [ ] 创建 `backup.sh` 脚本，备份待删除的 10 个文件
- [ ] 脚本内容:
```bash
#!/bin/bash
cp complete_project_system.py _archived/
cp secure_complete_system.py _archived/
# ... (所有 10 个文件)
```
- [ ] 使脚本可执行: `chmod +x backup.sh`
- [ ] 测试运行: `bash backup.sh`

**验收标准**: 10 个文件成功备份到 `_archived/`

---

## 组 1.2: 删除冗余文件 (10 个任务)

### Task 1.2.1: 备份并删除 complete_project_system.py
- [ ] 验证文件存在: `ls -lh complete_project_system.py`（107K）
- [ ] 备份: `cp complete_project_system.py _archived/`
- [ ] 验证备份: `ls -lh _archived/complete_project_system.py`
- [ ] 删除: `rm complete_project_system.py`
- [ ] 验证删除: `ls complete_project_system.py` (应报错)
- [ ] 检查是否被导入: `grep -r "from complete_project_system" src/` (应为空)

**验收标准**: 文件备份并删除，无其他地方导入

### Task 1.2.2: 删除 secure_complete_system.py
- [ ] 备份、删除、验证（同 1.2.1）
- [ ] 确认 `src/application.py` 包含安全功能

**验收标准**: 文件已删除，功能保留

### Task 1.2.3-1.2.10: 删除其他 8 个冗余文件
重复相同流程删除:
- [ ] unified_quant_system.py
- [ ] simple_dashboard.py
- [ ] enhanced_interactive_dashboard.py
- [ ] test_system_startup.py
- [ ] system_status_report.py
- [ ] run_complete_macro_analysis.py
- [ ] demo_real_data_backtest.py
- [ ] demo_verification_system.py

**验收标准**: 所有 10 个文件备份到 `_archived/` 并从根目录删除

---

## 组 1.3: 移动测试文件 (15 个任务)

### Task 1.3.1: 确保 tests/ 目录结构
- [ ] 验证 `tests/` 目录存在
- [ ] 创建 `tests/__init__.py`（如果不存在）
- [ ] 创建 `tests/conftest.py`（如果不存在）
- [ ] 列出 `tests/` 内容: `ls -la tests/`

**验收标准**: `tests/` 目录结构完整

### Task 1.3.2: 列出所有测试文件
- [ ] 列出根目录的所有测试文件:
```bash
ls test_*.py > /tmp/tests_to_move.txt
cat /tmp/tests_to_move.txt
```
- [ ] 计数应该在 40+ 个
- [ ] 验证没有 test_*.py 在 src/ 目录中

**验收标准**: 清单包含所有需要移动的测试文件

### Task 1.3.3-1.3.14: 移动各个测试文件 (12 个任务)
对每个测试文件执行:
```bash
mv test_FILE_NAME.py tests/
grep -r "from test_FILE_NAME" src/ || echo "✓ No imports"
```

示例需要移动的文件（共 40+ 个，这里列出 12 个关键的）:
- [ ] test_core_functions.py
- [ ] test_api_endpoints.py
- [ ] test_data_processing.py
- [ ] test_validators.py
- [ ] test_database.py
- [ ] test_cleaners.py
- [ ] test_datetime_normalizer.py
- [ ] test_backtest_simple.py
- [ ] test_hkex_collector.py
- [ ] test_real_scraper.py
- [ ] test_scraper_integration.py
- [ ] test_scraper_simple.py

**验收标准**: 每个文件成功移动，无导入错误

### Task 1.3.15: 验证测试运行
- [ ] 运行 pytest 发现测试: `pytest tests/ --collect-only | wc -l`
- [ ] 应该找到 40+ 个测试
- [ ] 运行测试: `pytest tests/ -v`
- [ ] 所有测试应通过

**验收标准**: `pytest tests/ -v` 所有通过，至少 40 个测试

---

## 组 1.4: 移动策略文件 (6 个任务)

### Task 1.4.1: 创建 src/strategies/ 目录
- [ ] 创建目录: `mkdir -p src/strategies`
- [ ] 创建 `src/strategies/__init__.py`
- [ ] 验证结构: `ls -la src/strategies/`

**验收标准**: 目录结构完整

### Task 1.4.2-1.4.7: 移动 6 个策略文件
- [ ] Task 1.4.2: `mv warrant_analysis_simple.py src/strategies/`
- [ ] Task 1.4.3: `mv warrant_contrarian_analysis.py src/strategies/`
- [ ] Task 1.4.4: `mv warrant_sentiment_analysis.py src/strategies/`
- [ ] Task 1.4.5: `mv warrant_timing_impact_analysis.py src/strategies/`
- [ ] Task 1.4.6: `mv hibor_6m_prediction_strategy.py src/strategies/`
- [ ] Task 1.4.7: `mv hibor_threshold_optimization.py src/strategies/`

每个文件移动后:
- [ ] 验证移动成功
- [ ] 检查导入: `grep -r "from warrant_analysis_simple" src/`

**验收标准**: 所有策略文件在 `src/strategies/`，无导入错误

---

## 组 1.5: 整理数据处理文件 (5 个任务)

### Task 1.5.1: 备份过时的探索脚本
- [ ] 备份以下文件到 `_archived/`:
  - [ ] find_hkex_data.py
  - [ ] find_hkex_selectors.py
  - [ ] parse_hkex_data.py
  - [ ] generate_visualization_data.py
  - [ ] data_handler.py
- [ ] 命令: `for f in find_hkex_data.py find_hkex_selectors.py ...; do cp "$f" _archived/; done`
- [ ] 验证: `ls -lh _archived/ | grep hkex`

**验收标准**: 5 个文件备份到 `_archived/`

### Task 1.5.2: 删除过时脚本
- [ ] 删除上述 5 个文件: `rm find_hkex_data.py find_hkex_selectors.py ...`
- [ ] 验证删除: `ls find_hkex_data.py` (应报错)

**验收标准**: 文件已删除

### Task 1.5.3: 创建 scripts/ 目录
- [ ] 创建: `mkdir -p scripts`
- [ ] 创建: `scripts/__init__.py`（可选）

**验收标准**: `scripts/` 目录存在

### Task 1.5.4: 移动 CLI 工具
- [ ] 移动 `analyze_stock_cli.py` 到 `scripts/`
- [ ] 移动 `batch_stock_analysis.py` 到 `scripts/`
- [ ] 验证导入（如有）: `grep -r "analyze_stock_cli" src/`

**验收标准**: CLI 工具在 `scripts/` 目录

### Task 1.5.5: 检查数据处理一致性
- [ ] 验证 `src/data_pipeline/` 包含核心数据处理
- [ ] 验证 `src/data_adapters/` 包含适配器
- [ ] 检查没有重复功能: `grep -r "def fetch_data" src/` | wc -l

**验收标准**: 数据处理功能一致，无重复

---

## 组 1.6: 整理 Telegram (2 个任务)

### Task 1.6.1: 验证 Telegram 实现位置
- [ ] 检查 `src/telegram_bot/` 目录: `ls -la src/telegram_bot/`
- [ ] 如果不存在，创建: `mkdir -p src/telegram_bot`
- [ ] 验证有 `__init__.py`、`bot.py`、`handlers.py` 等

**验收标准**: `src/telegram_bot/` 目录结构完整

### Task 1.6.2: 删除根目录 Telegram 脚本
- [ ] 备份到 `_archived/`:
  - [ ] start_telegram_bot.py
  - [ ] deploy_telegram_bot.py
  - [ ] test_bot_connection.py（如果有）
- [ ] 删除根目录的这些文件
- [ ] 更新启动方式在 `src/application.py` 中

**验收标准**: 根目录没有 telegram 相关 .py 文件

---

## 组 1.7: 验证和文档 (4 个任务)

### Task 1.7.1: 综合验证
- [ ] 文件清点:
```bash
echo "根目录文件数:"
ls *.py 2>/dev/null | wc -l  # 应该 <50

echo "总 Python 文件数:"
find . -name "*.py" | grep -v ".git" | grep -v "__pycache__" | wc -l  # 应该 <380
```
- [ ] 验证应用启动: `python src/application.py` (或实际命令)
- [ ] 验证数据层: `python -c "from src.data_pipeline import *"`
- [ ] 验证回测: `python -c "from src.backtest import *"`

**验收标准**: 所有检查通过，文件数量达到目标

### Task 1.7.2: 运行完整测试套件
- [ ] 清空 pytest 缓存: `pytest --cache-clear`
- [ ] 运行所有测试: `pytest tests/ -v --tb=short`
- [ ] 统计通过数: `pytest tests/ -v 2>&1 | grep "passed"`
- [ ] 应该所有通过，覆盖率 ≥80%（如果 coverage 配置了）

**验收标准**: `pytest tests/ -v` 所有通过

### Task 1.7.3: 检查导入完整性
- [ ] 查找可能的坏导入:
```bash
grep -r "from complete_project_system" src/ || echo "✓"
grep -r "from simple_dashboard" src/ || echo "✓"
grep -r "from test_" src/ || echo "✓"
```
- [ ] 所有应返回空（或 ✓）

**验收标准**: 没有导入删除的文件

### Task 1.7.4: 更新文档和提交
- [ ] 更新 `README.md`:
  - [ ] 启动命令改为 `python src/application.py`
  - [ ] 添加项目结构说明
  - [ ] 添加文件组织说明
- [ ] 更新 `CLAUDE.md` 中的文件参考
- [ ] 创建 git 提交:
```bash
git add -A
git commit -m "Phase 1: Clean up root directory and organize code structure

- Removed 10 redundant system startup scripts (saved 107K)
- Moved 40+ test files to tests/ directory
- Moved 6 strategy files to src/strategies/
- Moved CLI tools to scripts/
- Organized Telegram implementation to src/telegram_bot/
- Backed up legacy files to _archived/

Result:
- Root directory: 110 → <50 Python files
- Total files: 445 → <380 Python files
- No functionality lost, all tests passing"
```
- [ ] 验证提交: `git log -1`

**验收标准**: git 提交成功，包含清晰的变更说明

---

## 验收检查清单

Phase 1 完成检查:

### 结构指标
- [ ] 根目录 Python 文件数 <50 (当前目标)
- [ ] 所有 test_*.py 在 tests/
- [ ] 所有策略在 src/strategies/
- [ ] 所有 CLI 工具在 scripts/
- [ ] Telegram 实现在 src/telegram_bot/
- [ ] _archived/ 目录包含 10+ 个备份文件

### 功能验证
- [ ] `python src/application.py` 正常启动
- [ ] `pytest tests/ -v` 所有通过
- [ ] `python -c "from src.strategies import *"` 成功
- [ ] `python -c "from src.data_adapters import *"` 成功
- [ ] 无导入错误

### 代码质量
- [ ] 没有语法错误
- [ ] 没有坏导入
- [ ] git 历史清晰
- [ ] 所有更改都有适当的提交信息

### 文档更新
- [ ] README.md 已更新
- [ ] CLAUDE.md 已更新
- [ ] 项目结构文档已更新

---

## 完成后 (Post-Phase 1)

✅ 一旦所有 45 个任务完成:

1. **提交 PR**:
```bash
git push origin feature/phase1-code-cleanup
```

2. **请求代码审查**:
   - 审查者检查文件移动的完整性
   - 验证测试全部通过
   - 批准合并

3. **合并到 main**:
```bash
git checkout main
git pull
git merge feature/phase1-code-cleanup
```

4. **准备 Phase 2**:
   - 开始整合 HKEX 实现
   - 计划 Agent 合并

---

## 预期时间线

| 日期 | 任务 | 时间 | 完成指标 |
|------|------|------|----------|
| **Day 1** | 1.1 + 1.2 | 2h | 10 个文件删除 |
| **Day 1** | 1.3 (前 6 个) | 2h | 测试开始移动 |
| **Day 2** | 1.3 (后 9 个) | 2h | 所有测试移动 |
| **Day 2** | 1.4 + 1.5 | 2h | 策略和数据整理 |
| **Day 3** | 1.6 | 1h | Telegram 整理 |
| **Day 3** | 1.7 | 3h | 验证、测试、文档 |

**总计**: 3 天，约 12 小时（可以分散到 2 周）

