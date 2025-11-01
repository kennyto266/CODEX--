# CODEX Trading System - Development Makefile
# 使用 make help 查看所有可用命令

.PHONY: help install install-dev clean format lint test test-cov type-check security docs build serve

# 默认目标
.DEFAULT_GOAL := help

# 颜色定义
CYAN := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
NC := \033[0m # No Color

# 项目配置
PYTHON := python3
PIP := pip3
PROJECT_NAME := codex-trading-system
SRC_DIR := src
TEST_DIR := tests
DOCS_DIR := docs

help: ## 显示帮助信息
	@echo "$(CYAN)CODEX Trading System - Development Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""

install: ## 安装生产依赖
	@echo "$(CYAN)安装生产依赖...$(NC)"
	$(PIP) install -r requirements.txt

install-dev: ## 安装开发依赖
	@echo "$(CYAN)安装开发依赖...$(NC)"
	$(PIP) install -r requirements-dev.txt
	$(PIP) install -e .

setup-precommit: ## 设置pre-commit hooks
	@echo "$(CYAN)设置pre-commit hooks...$(NC)"
	pre-commit install
	pre-commit install --hook-type commit-msg

clean: ## 清理临时文件和缓存
	@echo "$(CYAN)清理临时文件...$(NC)"
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .tox/
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true

# 代码格式化
format: ## 运行所有代码格式化工具
	@echo "$(CYAN)运行代码格式化...$(NC)"
	@echo "  $(YELLOW)→ Black 格式化$(NC)"
	black $(SRC_DIR) $(TEST_DIR) --line-length=100
	@echo "  $(YELLOW)→ isort 排序导入$(NC)"
	isort $(SRC_DIR) $(TEST_DIR) --profile=black --line-length=100
	@echo "  $(YELLOW)→ autoflake 清理未使用导入$(NC)"
	autoflake --in-place --recursive --remove-all-unused-imports $(SRC_DIR) $(TEST_DIR)

format-check: ## 检查代码格式（不修改）
	@echo "$(CYAN)检查代码格式...$(NC)"
	black --check $(SRC_DIR) $(TEST_DIR) --line-length=100
	isort --check-only $(SRC_DIR) $(TEST_DIR) --profile=black --line-length=100
	autoflake --check --recursive --remove-all-unused-imports $(SRC_DIR) $(TEST_DIR)

# 代码质量检查
lint: ## 运行所有代码质量检查工具
	@echo "$(CYAN)运行代码质量检查...$(NC)"
	@echo "  $(YELLOW)→ Flake8 检查$(NC)"
	flake8 $(SRC_DIR) $(TEST_DIR) --max-line-length=100
	@echo "  $(YELLOW)→ Pydocstyle 检查$(NC)"
	pydocstyle $(SRC_DIR) --convention=google
	@echo "  $(YELLOW)→ Bandit 安全检查$(NC)"
	bandit -r $(SRC_DIR) -f json -o bandit-report.json || true

type-check: ## 运行类型检查
	@echo "$(CYAN)运行类型检查...$(NC)"
	mypy $(SRC_DIR) --ignore-missing-imports --strict-optional

security: ## 运行安全检查
	@echo "$(CYAN)运行安全检查...$(NC)"
	bandit -r $(SRC_DIR) -f json -o bandit-report.json
	safety check
	@echo "$(GREEN)✓ 安全检查完成$(NC)"

quality: format-check lint type-check security ## 运行完整代码质量检查（不修改文件）

# 测试
test: ## 运行所有测试
	@echo "$(CYAN)运行测试...$(NC)"
	pytest $(TEST_DIR) -v

test-cov: ## 运行测试并生成覆盖率报告
	@echo "$(CYAN)运行测试并生成覆盖率报告...$(NC)"
	pytest $(TEST_DIR) -v --cov=$(SRC_DIR) --cov-report=term-missing --cov-report=html --cov-report=xml

test-unit: ## 仅运行单元测试
	@echo "$(CYAN)运行单元测试...$(NC)"
	pytest $(TEST_DIR) -v -m "not integration"

test-integration: ## 运行集成测试
	@echo "$(CYAN)运行集成测试...$(NC)"
	pytest $(TEST_DIR) -v -m "integration"

test-api: ## 运行API测试
	@echo "$(CYAN)运行API测试...$(NC)"
	pytest $(TEST_DIR) -v -m "api"

test-fast: ## 运行快速测试（跳过慢速测试）
	@echo "$(CYAN)运行快速测试...$(NC)"
	pytest $(TEST_DIR) -v -m "not slow"

# 文档
docs: ## 生成文档
	@echo "$(CYAN)生成文档...$(NC)"
	cd $(DOCS_DIR) && make html

docs-serve: docs ## 生成并启动文档服务器
	@echo "$(CYAN)启动文档服务器...$(NC)"
	cd $(DOCS_DIR)/_build/html && $(PYTHON) -m http.server 8000

docs-clean: ## 清理文档
	@echo "$(CYAN)清理文档...$(NC)"
	cd $(DOCS_DIR) && make clean

# 构建和打包
build: clean ## 构建包
	@echo "$(CYAN)构建包...$(NC)"
	$(PYTHON) -m build

build-check: build ## 构建并检查包
	@echo "$(CYAN)检查包...$(NC)"
	twine check dist/*

# 开发服务器
serve: ## 启动开发服务器
	@echo "$(CYAN)启动开发服务器...$(NC)"
	$(PYTHON) complete_project_system.py --port 8001 --host 0.0.0.0

serve-dev: ## 启动开发服务器（调试模式）
	@echo "$(CYAN)启动开发服务器（调试模式）...$(NC)"
	uvicorn complete_project_system:app --reload --port 8001 --host 0.0.0.0

# 预提交检查
precommit: format lint type-check test-cov ## 运行完整预提交检查
	@echo "$(GREEN)✓ 预提交检查完成$(NC)"

# 清理虚拟环境
clean-venv: ## 清理虚拟环境
	@echo "$(CYAN)清理虚拟环境...$(NC)"
	rm -rf .venv/
	rm -rf venv/
	@echo "$(GREEN)✓ 虚拟环境已清理$(NC)"

# 开发环境设置
dev-setup: install-dev setup-precommit ## 完整开发环境设置
	@echo "$(GREEN)✓ 开发环境设置完成$(NC)"
	@echo ""
	@echo "$(CYAN)下一步操作:$(NC)"
	@echo "  1. 运行 $(YELLOW)make test$(NC) 验证测试"
	@echo "  2. 运行 $(YELLOW)make quality$(NC) 检查代码质量"
	@echo "  3. 运行 $(YELLOW)make serve$(NC) 启动开发服务器"

# 数据库操作
db-migrate: ## 运行数据库迁移
	@echo "$(CYAN)运行数据库迁移...$(NC)"
	alembic upgrade head

db-migrate-create: ## 创建数据库迁移（需要指定消息）
	@echo "$(CYAN)创建数据库迁移...$(NC)"
	@echo "使用方法: make db-migrate-create MSG='迁移描述'"

db-reset: ## 重置数据库（警告：这会删除所有数据）
	@echo "$(RED)警告：这会删除所有数据！$(NC)"
	@echo "输入 'YES' 确认重置："
	@read -r CONFIRM && [ "$$CONFIRM" = "YES" ] || (echo "取消操作" && exit 1)
	@echo "$(CYAN)重置数据库...$(NC)"
	alembic downgrade base
	alembic upgrade head

# 日志相关
logs-clean: ## 清理日志文件
	@echo "$(CYAN)清理日志文件...$(NC)"
	rm -rf logs/*.log*
	rm -rf logs/archive/*
	@echo "$(GREEN)✓ 日志文件已清理$(NC)"

logs-view: ## 查看最新日志
	@echo "$(CYAN)查看最新日志...$(NC)"
	tail -f logs/app.log

# Docker 相关
docker-build: ## 构建Docker镜像
	@echo "$(CYAN)构建Docker镜像...$(NC)"
	docker build -t $(PROJECT_NAME) .

docker-run: ## 运行Docker容器
	@echo "$(CYAN)运行Docker容器...$(NC)"
	docker run -p 8001:8001 $(PROJECT_NAME)

docker-clean: ## 清理Docker资源
	@echo "$(CYAN)清理Docker资源...$(NC)"
	docker system prune -f

# CI/CD 相关
ci-setup: ## 设置CI/CD环境
	@echo "$(CYAN)设置CI/CD环境...$(NC)"
	@echo "检查GitHub Actions配置..."
	@echo "确保.github/workflows/ci.yml存在"
	@echo "确保所有质量检查通过"

# 性能分析
profile: ## 运行性能分析
	@echo "$(CYAN)运行性能分析...$(NC)"
	$(PYTHON) -m cProfile -o profile.stats -m pytest $(TEST_DIR) -v
	@echo "性能报告生成: profile.stats"
	@echo "查看报告: $(YELLOW)python -m pstats profile.stats$(NC)"

# 内存分析
memcheck: ## 运行内存检查
	@echo "$(CYAN)运行内存检查...$(NC)"
	$(PYTHON) -m pytest $(TEST_DIR) -v --memray

# 依赖检查
deps-check: ## 检查依赖安全性
	@echo "$(CYAN)检查依赖安全性...$(NC)"
	safety check
	@echo "检查过时的依赖..."
	$(PIP) list --outdated

deps-update: ## 更新依赖（谨慎使用）
	@echo "$(CYAN)更新依赖...$(NC)"
	@echo "请手动更新requirements*.txt文件并测试"

# 完整检查（CI用）
ci-full: clean format lint type-check security test-cov build ## 运行完整CI检查
	@echo "$(GREEN)✓ 完整CI检查通过$(NC)"

# 快速开发循环
dev-cycle: format lint test-fast ## 快速开发循环
	@echo "$(GREEN)✓ 快速开发循环完成$(NC)"
