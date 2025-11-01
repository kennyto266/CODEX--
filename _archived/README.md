# 已存档文件 (_archived)

本目录包含 Phase 1 代码清理中备份的文件。这些文件已被移除或替换，但保留在此作为备份。

## 备份内容

### 冗余系统启动脚本 (10 个)
- `complete_project_system.py` - 107KB 的完整系统文件（功能已合并到 src/application.py）
- `secure_complete_system.py` - 安全版本（重复）
- `unified_quant_system.py` - 统一版本（重复）
- `simple_dashboard.py` - 简单仪表板（使用 src/dashboard/）
- `enhanced_interactive_dashboard.py` - 增强版仪表板（重复）
- `test_system_startup.py` - 系统启动测试（已移至 tests/）
- `system_status_report.py` - 临时脚本
- `run_complete_macro_analysis.py` - 临时脚本
- `demo_real_data_backtest.py` - 示例代码
- `demo_verification_system.py` - 示例代码

### 过时的数据处理脚本 (5 个)
- `find_hkex_data.py` - 过时的 HKEX 探索脚本
- `find_hkex_selectors.py` - 过时的选择器脚本
- `parse_hkex_data.py` - 过时的解析脚本
- `generate_visualization_data.py` - 过时的可视化脚本
- `data_handler.py` - 过时的数据处理脚本

### 过时的 Telegram 脚本 (可选)
- `start_telegram_bot.py` - 使用 src/telegram_bot/ 替代
- `deploy_telegram_bot.py` - 使用 src/telegram_bot/ 替代

## 恢复说明

如果需要恢复某个文件：

```bash
# 恢复单个文件
cp _archived/complete_project_system.py .

# 或通过 git 恢复
git checkout HEAD -- complete_project_system.py
```

## Phase 1 清理信息

- **完成日期**: 2025-10-25
- **目的**: 清理根目录混乱，整理代码结构
- **目标**:
  - 根目录从 110 个 .py 文件减少到 <50 个
  - 总 .py 文件数从 445 减少到 <380 个
  - 消除 30% 的代码重复

## 相关文档

- 提案: openspec/changes/phase1-code-cleanup/proposal.md
- 设计: openspec/changes/phase1-code-cleanup/design.md
- 任务: openspec/changes/phase1-code-cleanup/tasks.md
