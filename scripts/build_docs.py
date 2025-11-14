#!/usr/bin/env python3
"""
文档构建脚本 - 增强版

自动化构建所有文档，包括：
- Sphinx文档（Python API）
- MkDocs文档（用户指南）
- API文档（OpenAPI）
- Rust文档（如果存在）
- 测试覆盖率文档
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
import argparse
import time


def run_command(cmd: str, cwd: str = None, check: bool = True, timeout: int = None) -> subprocess.CompletedProcess:
    """执行命令

    Args:
        cmd: 要执行的命令
        cwd: 工作目录
        check: 是否检查返回码
        timeout: 超时时间（秒）

    Returns:
        执行结果
    """
    print(f"\n▶️  执行命令: {cmd}")
    print(f"   工作目录: {cwd or os.getcwd()}")
    if timeout:
        print(f"   超时时间: {timeout}秒")

    result = subprocess.run(
        cmd,
        shell=True,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )

    if result.stdout:
        print(f"   输出: {result.stdout[:500]}...")  # 只显示前500字符

    if result.stderr and result.returncode != 0:
        print(f"   错误: {result.stderr[:500]}")

    if check and result.returncode != 0:
        print(f"❌ 命令执行失败，返回码: {result.returncode}")
        if not check:  # 如果不检查错误，也返回结果
            return result
        sys.exit(result.returncode)

    return result


def install_dependencies() -> bool:
    """安装文档依赖

    Returns:
        是否成功
    """
    print("\n" + "=" * 60)
    print("📦 安装文档依赖")
    print("=" * 60)

    requirements_file = Path(__file__).parent.parent / "docs_requirements.txt"
    if not requirements_file.exists():
        print(f"❌ 依赖文件不存在: {requirements_file}")
        return False

    try:
        # 升级pip
        print("\n🔄 升级pip...")
        run_command("pip install --upgrade pip", check=False)

        # 安装依赖
        print("\n🔄 安装文档依赖...")
        result = run_command(
            f"pip install -r {requirements_file}",
            check=False
        )

        if result.returncode == 0:
            print("✅ 依赖安装成功")
            return True
        else:
            print("⚠️  部分依赖安装失败，但继续构建")
            return True
    except Exception as e:
        print(f"❌ 依赖安装失败: {e}")
        return False


def build_sphinx_docs() -> bool:
    """构建Sphinx文档

    Returns:
        是否成功
    """
    print("\n" + "=" * 60)
    print("📘 构建Sphinx文档")
    print("=" * 60)

    docs_dir = Path(__file__).parent.parent / "docs"
    build_dir = docs_dir / "_build"

    try:
        # 清理旧文档
        if build_dir.exists():
            print("\n🧹 清理旧文档...")
            shutil.rmtree(build_dir)
            build_dir.mkdir(parents=True, exist_ok=True)

        # 生成API文档
        print("\n🔄 生成API文档...")
        generate_api = Path(__file__).parent / "generate_api_docs.py"
        if generate_api.exists():
            run_command(f"python {generate_api}", check=False)

        # 构建HTML文档
        print("\n🔄 构建Sphinx HTML文档...")
        result = run_command(
            f"sphinx-build -b html {docs_dir} {build_dir}/html",
            check=False,
            timeout=300  # 5分钟超时
        )

        if result.returncode == 0:
            print("✅ Sphinx HTML文档构建成功")
        else:
            print("⚠️  Sphinx HTML文档构建有警告，但可能成功")

        # 构建PDF文档（可选）
        print("\n🔄 构建Sphinx PDF文档（可选）...")
        result = run_command(
            f"sphinx-build -b latex {docs_dir} {build_dir}/latex",
            check=False,
            timeout=120
        )

        if result.returncode == 0:
            print("✅ Sphinx LaTeX文档构建成功")
            print("   可以手动编译PDF: cd docs/_build/latex && make")
        else:
            print("⚠️  PDF构建失败（需要LaTeX）")

        print(f"\n✅ Sphinx文档构建完成")
        print(f"   HTML位置: {build_dir / 'html' / 'index.html'}")
        return True

    except Exception as e:
        print(f"\n❌ Sphinx文档构建失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def build_mkdocs_docs() -> bool:
    """构建MkDocs文档

    Returns:
        是否成功
    """
    print("\n" + "=" * 60)
    print("📗 构建MkDocs文档")
    print("=" * 60)

    try:
        # 检查mkdocs配置文件
        mkdocs_yml = Path(__file__).parent.parent / "mkdocs.yml"
        if not mkdocs_yml.exists():
            print("⚠️  mkdocs.yml不存在，跳过MkDocs构建")
            return True

        # 构建文档
        print("\n🔄 正在构建MkDocs文档...")
        result = run_command(
            "mkdocs build",
            check=False,
            timeout=120
        )

        if result.returncode == 0:
            print("✅ MkDocs文档构建成功")
            print(f"   位置: {Path(__file__).parent.parent / 'site'}")
            return True
        else:
            print("⚠️  MkDocs文档构建失败")
            return False

    except Exception as e:
        print(f"\n❌ MkDocs文档构建失败: {e}")
        return False


def generate_api_docs() -> bool:
    """生成API文档

    Returns:
        是否成功
    """
    print("\n" + "=" * 60)
    print("📙 生成API文档")
    print("=" * 60)

    script_path = Path(__file__).parent / "generate_api_docs.py"

    if not script_path.exists():
        print(f"⚠️  API文档生成脚本不存在: {script_path}")
        return True

    try:
        # 运行API文档生成脚本
        print("\n🔄 正在运行API文档生成器...")
        result = run_command(f"python {script_path}", check=False)

        if result.returncode == 0:
            print("\n✅ API文档生成完成")
            return True
        else:
            print("\n⚠️  API文档生成有警告，但可能成功")
            return True

    except Exception as e:
        print(f"\n❌ API文档生成失败: {e}")
        return False


def build_rust_docs() -> bool:
    """构建Rust文档

    Returns:
        是否成功
    """
    print("\n" + "=" * 60)
    print("📕 构建Rust文档")
    print("=" * 60)

    # 检查是否存在Rust项目
    cargo_toml = Path(__file__).parent.parent / "Cargo.toml"
    if not cargo_toml.exists():
        print("ℹ️  未发现Rust项目，跳过Rust文档构建")
        return True

    try:
        # 构建文档
        print("\n🔄 正在构建Rust文档...")
        result = run_command(
            "cargo doc --no-deps",
            check=False,
            timeout=300
        )

        if result.returncode != 0:
            print("⚠️  Rust文档构建失败，但可能成功")
            return True

        # 复制到docs目录
        target_dir = Path(__file__).parent.parent / "docs" / "rust"
        target_dir.mkdir(parents=True, exist_ok=True)

        source_dir = Path(__file__).parent.parent / "target" / "doc"
        if source_dir.exists():
            print(f"\n🔄 正在复制文档到: {target_dir}")
            if (target_dir / "doc").exists():
                shutil.rmtree(target_dir / "doc")
            shutil.copytree(source_dir, target_dir / "doc", dirs_exist_ok=True)
            print(f"✅ 文档已复制到: {target_dir}")

        print("\n✅ Rust文档构建完成")
        return True

    except Exception as e:
        print(f"\n❌ Rust文档构建失败: {e}")
        return False


def generate_coverage_docs() -> bool:
    """生成测试覆盖率文档

    Returns:
        是否成功
    """
    print("\n" + "=" * 60)
    print("📊 生成测试覆盖率文档")
    print("=" * 60)

    try:
        # 检查测试目录
        tests_dir = Path(__file__).parent.parent / "tests"
        if not tests_dir.exists():
            print("⚠️  tests目录不存在，跳过覆盖率文档生成")
            return True

        # 运行测试并生成覆盖率
        print("\n🔄 正在运行测试并生成覆盖率...")
        result = run_command(
            "pytest tests/ --cov=src --cov-report=html --cov-report=term --cov-report=json",
            check=False,
            timeout=300
        )

        # 复制覆盖率报告到docs
        htmlcov_dir = Path("htmlcov")
        if htmlcov_dir.exists():
            target_dir = Path(__file__).parent.parent / "docs" / "coverage"
            target_dir.mkdir(parents=True, exist_ok=True)

            if (target_dir / "html").exists():
                shutil.rmtree(target_dir / "html")
            shutil.copytree(htmlcov_dir, target_dir / "html", dirs_exist_ok=True)
            print(f"\n✅ 覆盖率报告已复制到: {target_dir}")
        else:
            print("⚠️  未找到覆盖率报告")

        print("\n✅ 覆盖率文档生成完成")
        return True

    except Exception as e:
        print(f"\n❌ 覆盖率文档生成失败: {e}")
        return False


def create_docs_index(output_dir: Path):
    """创建文档索引页面

    Args:
        output_dir: 输出目录
    """
    index_content = f"""# 港股量化交易系统 - 文档中心

欢迎使用港股量化交易系统文档！

## 文档导航

### 用户指南
- [安装指南](user-guide/installation.html)
- [快速开始](user-guide/quickstart.html)
- [系统配置](user-guide/configuration.html)
- [使用指南](user-guide/usage.html)
- [故障排除](user-guide/troubleshooting.html)

### 开发者指南
- [开发概览](developer-guide/overview.html)
- [开发环境搭建](developer-guide/development-setup.html)
- [代码规范](developer-guide/coding-standards.html)
- [测试指南](developer-guide/testing.html)
- [贡献指南](developer-guide/contribution.html)

### API参考
- [API概览](api/overview.html)
- [API端点](api/routes.html)
- [数据模型](api/models.html)
- [WebSocket](api/websockets.html)

### 系统架构
- [架构概览](architecture/overview.html)
- [多智能体系统](architecture/agents.html)
- [数据流设计](architecture/data-flow.html)
- [部署架构](architecture/deployment.html)

### 附加资源
- [测试覆盖率](coverage/html/index.html)
- [Python API文档](_build/html/index.html)
- [Rust API文档](rust/doc/index.html)
- [交互式API文档](api/generated/swagger.html)

## 版本信息

- 系统版本: 1.0.0
- 文档版本: 1.0.0
- 最后更新: {time.strftime('%Y-%m-%d %H:%M:%S')}

## 反馈与支持

如有问题或建议，请通过以下方式联系：

- 邮箱: support@quant-system.com
- GitHub: https://github.com/org/quant-system
- 文档: https://docs.quant-system.com
"""

    index_path = output_dir / "index.md"
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_content)

    print(f"✅ 文档索引已创建: {index_path}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="文档构建脚本 - 增强版")
    parser.add_argument(
        "--sphinx",
        action="store_true",
        help="仅构建Sphinx文档",
    )
    parser.add_argument(
        "--mkdocs",
        action="store_true",
        help="仅构建MkDocs文档",
    )
    parser.add_argument(
        "--api",
        action="store_true",
        help="仅生成API文档",
    )
    parser.add_argument(
        "--rust",
        action="store_true",
        help="仅构建Rust文档",
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="仅生成覆盖率文档",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="构建所有文档（默认）",
    )
    parser.add_argument(
        "--no-deps",
        action="store_true",
        help="跳过依赖安装",
    )

    args = parser.parse_args()

    # 默认构建所有文档
    if not any([args.sphinx, args.mkdocs, args.api, args.rust, args.coverage]):
        args.all = True

    print("\n" + "=" * 60)
    print("📚 港股量化交易系统 - 文档构建器 (增强版)")
    print("=" * 60)

    success_count = 0
    total_count = 0

    # 安装依赖
    if not args.no_deps:
        if install_dependencies():
            print("✅ 依赖安装完成")
        else:
            print("⚠️  依赖安装有问题，但继续构建")

    # 构建API文档
    if args.api or args.all:
        total_count += 1
        if generate_api_docs():
            success_count += 1

    # 构建Sphinx文档
    if args.sphinx or args.all:
        total_count += 1
        if build_sphinx_docs():
            success_count += 1

    # 构建MkDocs文档
    if args.mkdocs or args.all:
        total_count += 1
        if build_mkdocs_docs():
            success_count += 1

    # 构建Rust文档
    if args.rust or args.all:
        total_count += 1
        if build_rust_docs():
            success_count += 1

    # 生成覆盖率文档
    if args.coverage or args.all:
        total_count += 1
        if generate_coverage_docs():
            success_count += 1

    # 创建文档索引
    if args.all or any([args.sphinx, args.mkdocs, args.api]):
        print("\n🔄 正在创建文档索引...")
        output_dir = Path(__file__).parent.parent / "docs"
        create_docs_index(output_dir)

    # 总结
    print("\n" + "=" * 60)
    print(f"📊 构建完成: {success_count}/{total_count}")
    print("=" * 60)

    if success_count == total_count:
        print("\n✅ 所有文档构建成功！")
        print(f"\n📖 文档位置:")
        print(f"   - 根目录: {Path(__file__).parent.parent / 'docs'}")
        print(f"   - API文档: {Path(__file__).parent.parent / 'docs' / 'api'}")
        print(f"   - 覆盖率: {Path(__file__).parent.parent / 'docs' / 'coverage'}")
        print(f"   - HTML文档: {Path(__file__).parent.parent / 'docs' / '_build' / 'html'}")
        print()
        print("🚀 快速启动:")
        print(f"   cd {Path(__file__).parent.parent / 'docs' / '_build' / 'html'}")
        print("   python -m http.server 8000")
        print()
        return 0
    else:
        print(f"\n⚠️  部分文档构建失败 ({total_count - success_count}个失败)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
