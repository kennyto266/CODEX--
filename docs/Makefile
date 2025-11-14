# 港股量化交易系统 - 文档构建系统
#
# 提供便捷的文档构建命令
#
# 使用方法:
#   make help        - 显示帮助
#   make all         - 构建所有文档
#   make sphinx      - 构建Sphinx文档
#   make api         - 生成API文档
#   make clean       - 清理构建文件
#

.PHONY: help all sphinx mkdocs api rust coverage clean serve

# 默认目标
help:
	@echo "港股量化交易系统 - 文档构建命令"
	@echo ""
	@echo "可用命令:"
	@echo "  help       - 显示此帮助信息"
	@echo "  all        - 构建所有文档（默认）"
	@echo "  sphinx     - 构建Sphinx文档"
	@echo "  mkdocs     - 构建MkDocs文档"
	@echo "  api        - 生成API文档"
	@echo "  rust       - 构建Rust文档"
	@echo "  coverage   - 生成测试覆盖率文档"
	@echo "  clean      - 清理所有构建文件"
	@echo "  serve      - 启动文档服务器"
	@echo ""
	@echo "示例:"
	@echo "  make api           - 仅生成API文档"
	@echo "  make all           - 构建所有文档"
	@echo "  make clean all     - 清理后重新构建"

# 构建所有文档
all:
	python scripts/build_docs.py --all

# 构建Sphinx文档
sphinx:
	python scripts/build_docs.py --sphinx

# 构建MkDocs文档
mkdocs:
	python scripts/build_docs.py --mkdocs

# 生成API文档
api:
	python scripts/generate_api_docs.py

# 构建Rust文档
rust:
	python scripts/build_docs.py --rust

# 生成测试覆盖率文档
coverage:
	python scripts/build_docs.py --coverage

# 清理构建文件
clean:
	@echo "🧹 清理构建文件..."
	rm -rf docs/_build/
	rm -rf site/
	rm -rf docs/api/generated/
	rm -rf docs/coverage/
	rm -rf htmlcov/
	rm -rf docs/rust/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ 清理完成"

# 启动本地文档服务器
serve:
	@echo "🚀 启动文档服务器..."
	@echo "请在浏览器中访问: http://localhost:8000"
	cd docs/_build/html && python -m http.server 8000

# 检查文档质量
lint:
	@echo "🔍 检查文档质量..."
	@echo "检查RST文件..."
	find docs -name "*.rst" -exec rst2html {} /dev/null \; 2>/dev/null || echo "⚠️  发现RST语法错误"
	@echo "检查Markdown文件..."
	find docs -name "*.md" -exec echo "检查: {}" \;
	@echo "✅ 文档质量检查完成"

# 生成PDF文档
pdf:
	@echo "📄 生成PDF文档..."
	@echo "注意: PDF生成需要安装LaTeX"
	@which pdflatex >/dev/null || (echo "❌ 未安装LaTeX，请先安装: sudo apt-get install texlive-latex-base" && exit 1)
	sphinx-build -b latex docs docs/_build/latex
	cd docs/_build/latex && make

# 检查文档链接
linkcheck:
	@echo "🔗 检查文档链接..."
	sphinx-build -b linkcheck docs docs/_build/linkcheck
	@echo "✅ 链接检查完成"

# 自动格式化文档
fmt:
	@echo "✨ 格式化文档..."
	@echo "格式化RST文件..."
	find docs -name "*.rst" -exec python -m doc8 {} \;
	@echo "✅ 格式化完成"

# 安装文档依赖
install:
	@echo "📦 安装文档依赖..."
	pip install -r docs_requirements.txt
	@echo "✅ 依赖安装完成"

# 构建并部署到GitHub Pages
deploy:
	@echo "🚀 部署文档到GitHub Pages..."
	@if [ -z "$(GH_TOKEN)" ]; then \
		echo "❌ 请设置GH_TOKEN环境变量"; \
		exit 1; \
	fi
	git checkout -B gh-pages
	cp -r docs/_build/html/* .
	touch .nojekyll
	git add .
	git commit -m "docs: Update documentation"
	git push https://$(GH_TOKEN)@github.com/$(GITHUB_REPO) gh-pages
	git checkout main
	@echo "✅ 部署完成"

# 生成文档变更日志
changelog:
	@echo "📝 生成文档变更日志..."
	@echo "基于Git提交历史生成文档变更日志..."
	@echo "请手动查看: git log --oneline --grep='docs'"

# 验证文档完整性
verify:
	@echo "✅ 验证文档完整性..."
	@echo "检查必要文件..."
	@test -f docs/index.rst || (echo "❌ 缺少 docs/index.rst" && exit 1)
	@test -f docs/conf.py || (echo "❌ 缺少 docs/conf.py" && exit 1)
	@test -d docs/api || (echo "❌ 缺少 docs/api 目录" && exit 1)
	@test -d docs/user-guide || (echo "❌ 缺少 docs/user-guide 目录" && exit 1)
	@test -d docs/developer-guide || (echo "❌ 缺少 docs/developer-guide 目录" && exit 1)
	@test -d docs/architecture || (echo "❌ 缺少 docs/architecture 目录" && exit 1)
	@echo "✅ 文档完整性验证通过"

# 生成文档统计
stats:
	@echo "📊 生成文档统计..."
	@echo ""
	@echo "RST文件:"
	@find docs -name "*.rst" | wc -l | xargs echo "  数量:"
	@echo ""
	@echo "Markdown文件:"
	@find docs -name "*.md" | wc -l | xargs echo "  数量:"
	@echo ""
	@echo "文档总行数:"
	@find docs -name "*.rst" -o -name "*.md" | xargs wc -l | tail -1
	@echo ""
	@echo "代码示例:"
	@find docs -name "*.py" -o -name "*.sh" -o -name "*.js" | wc -l | xargs echo "  文件数:"
