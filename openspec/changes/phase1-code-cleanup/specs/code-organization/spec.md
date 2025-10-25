# 代码组织规范

## 目的
建立清晰的代码项目结构，消除根目录混乱和文件散乱问题，实现可维护的代码库组织。

## ADDED Requirements

### Requirement: 整理根目录文件结构
The system SHALL reduce root directory Python files from 110 to less than 50, preserving necessary configuration and entry point files, and organizing other files logically into appropriate directories.

#### Scenario: 清理冗余的系统启动脚本
- **WHEN** 项目中有 10 个不同版本的系统启动脚本
- **THEN** 保留唯一的 `src/application.py` 作为系统入口
- **AND** 备份其他版本到 `_archived/` 目录
- **AND** 删除根目录的 10 个冗余脚本
- **AND** 验证应用仍能正常启动

#### Scenario: 开发者查找入口点
- **WHEN** 新开发者想要启动系统
- **THEN** 在根目录或 src/ 中轻易找到主入口点
- **AND** README.md 清晰说明启动方式
- **AND** 只有一个标准启动脚本，避免混淆

### Requirement: 集中测试文件
The system SHALL consolidate over 40 test files scattered in the root directory into the `tests/` directory, complying with Python project standards.

#### Scenario: 自动发现和运行测试
- **WHEN** 开发者运行 `pytest tests/` 时
- **THEN** pytest 自动发现所有测试文件
- **AND** 所有 test_*.py 文件在 tests/ 目录
- **AND** 测试可以正常运行（导入正确）
- **AND** IDE（PyCharm、VSCode）能自动识别测试

#### Scenario: 维护测试套件
- **WHEN** 需要添加新测试
- **THEN** 放在 tests/ 目录中
- **AND** 遵循 test_*.py 命名规范
- **AND** 易于找到相关的现有测试

### Requirement: 组织策略文件
The system SHALL consolidate all strategy files from the root directory into the `src/strategies/` directory, forming a unified strategy management system.

#### Scenario: 管理多个策略实现
- **WHEN** 项目中有 6 个不同的策略
- **THEN** 所有策略在 `src/strategies/` 目录
- **AND** 可以通过统一接口加载和管理
- **AND** 新策略开发者知道放在哪个目录

#### Scenario: 导入和使用策略
- **WHEN** 回测引擎需要加载策略
- **THEN** 通过 `from src.strategies import WarrantAnalysis`
- **AND** 无需关心策略文件的具体位置
- **AND** 策略加载统一和可维护

### Requirement: 组织 CLI 工具和脚本
The system SHALL centralize command-line tools and one-off scripts from the root directory into the `scripts/` directory.

#### Scenario: 使用命令行工具
- **WHEN** 需要运行 `analyze_stock_cli.py`
- **THEN** 在 `scripts/` 目录中找到
- **AND** 运行方式为 `python scripts/analyze_stock_cli.py`
- **AND** 与核心系统分离

#### Scenario: 清理根目录
- **WHEN** 梳理根目录文件
- **THEN** 所有过时的一次性脚本备份到 `_archived/`
- **AND** 仍在使用的工具移到 `scripts/`
- **AND** 避免根目录充满各种脚本

### Requirement: 统一 Telegram 机器人实现
The system SHALL unify multiple Telegram-related files into the `src/telegram_bot/` directory.

#### Scenario: 启动 Telegram 机器人
- **WHEN** 需要启动 Telegram 机器人
- **THEN** 通过 `src/application.py --telegram` 或类似方式
- **AND** Telegram 代码在 `src/telegram_bot/` 目录
- **AND** 根目录不包含 `start_telegram_bot.py` 等文件

#### Scenario: 维护 Telegram 功能
- **WHEN** 需要修改 Telegram 功能
- **THEN** 所有相关文件在一个目录
- **AND** 易于找到和修改
- **AND** 支持未来的 Telegram 增强功能

### Requirement: 验证文件移动安全性
The system SHALL verify functionality is not compromised after each file movement, ensuring the safety of the code reorganization process.

#### Scenario: 删除冗余文件后验证
- **WHEN** 删除 10 个冗余的系统启动脚本
- **THEN** 检查没有其他代码导入这些脚本
- **AND** 应用仍能正常启动
- **AND** 所有单元测试通过

#### Scenario: 移动文件后检查导入
- **WHEN** 将 40+ 个测试文件移到 tests/
- **THEN** 更新所有导入路径
- **AND** 验证没有坏的导入
- **AND** pytest 能发现所有测试

#### Scenario: 验证系统完整性
- **WHEN** Phase 1 清理完成
- **THEN** 运行完整的测试套件
- **AND** 所有测试通过
- **AND** 基本功能验证（应用启动、API 调用等）

## 依赖关系
- 无外部依赖
- 后续 Phase 2 依赖本变更的清晰结构

## 交叉参考
- 相关：design.md 中的架构决策
- 相关：tasks.md 中的具体实现步骤
