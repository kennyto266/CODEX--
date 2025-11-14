#!/usr/bin/env python3
"""
港股量化交易系统 - 真实数据采集模块启动脚本
基于OpenSpec规范设计

功能：
- 一键启动完整真实数据系统
- 支持开发和生产环境
- 自动检查依赖和环境
- 提供友好的交互界面

使用方法：
  python start_real_data_system.py --dev     # 开发模式
  python start_real_data_system.py --prod    # 生产模式
  python start_real_data_system.py --test    # 运行测试
"""

import argparse
import asyncio
import os
import sys
import time
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_dependencies():
    """检查系统依赖"""
    logger.info("检查系统依赖...")

    required_packages = [
        'fastapi',
        'uvicorn',
        'pandas',
        'numpy',
        'asyncpg',
        'redis',
        'aiohttp',
        'apscheduler'
    ]

    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            logger.info(f"✓ {package}")
        except ImportError:
            missing_packages.append(package)
            logger.error(f"✗ {package} (未安装)")

    if missing_packages:
        logger.error(f"\n缺少以下依赖包: {', '.join(missing_packages)}")
        logger.error("请运行: pip install -r requirements.txt")
        return False

    logger.info("✓ 所有依赖已满足")
    return True


def check_environment():
    """检查环境变量"""
    logger.info("检查环境变量...")

    env_file = project_root / ".env"
    if not env_file.exists():
        logger.warning("未找到 .env 文件")
        logger.info("请复制 .env.example 为 .env 并配置API密钥")
        return False

    # 检查关键环境变量
    required_vars = [
        'HKMA_API_KEY',
        'RVD_API_KEY',
        'TOURISM_API_KEY'
    ]

    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value and value != f"your_{var.lower()}_here":
            logger.info(f"✓ {var}")
        else:
            missing_vars.append(var)
            logger.error(f"✗ {var} (未配置或使用默认值)")

    if missing_vars:
        logger.warning(f"\n请配置以下环境变量: {', '.join(missing_vars)}")
        logger.info("编辑 .env 文件并填入真实的API密钥")

    return len(missing_vars) == 0


def check_databases():
    """检查数据库连接"""
    logger.info("检查数据库连接...")

    # 检查PostgreSQL
    postgres_host = os.getenv('POSTGRES_HOST', 'localhost')
    postgres_port = os.getenv('POSTGRES_PORT', '5432')

    logger.info(f"PostgreSQL: {postgres_host}:{postgres_port}")

    # 检查Redis
    redis_host = os.getenv('REDIS_HOST', 'localhost')
    redis_port = os.getenv('REDIS_PORT', '6379')

    logger.info(f"Redis: {redis_host}:{redis_port}")

    # 注意：这里只是显示配置，实际连接检查在应用启动时进行
    return True


async def start_development_mode():
    """启动开发模式"""
    logger.info("🚀 启动开发模式...")

    try:
        from src.systems.complete_real_data_system import main
        await main()
    except KeyboardInterrupt:
        logger.info("\n✓ 开发模式已停止")
    except Exception as e:
        logger.error(f"✗ 开发模式启动失败: {e}")
        sys.exit(1)


async def start_production_mode():
    """启动生产模式"""
    logger.info("🚀 启动生产模式...")

    try:
        import uvicorn
        from src.api.real_data_api import app

        # 生产模式配置
        config = uvicorn.Config(
            app,
            host="0.0.0.0",
            port=8001,
            workers=4,
            loop="asyncio",
            http="httptools",
            log_level="info",
            access_log=True
        )
        server = uvicorn.Server(config)

        logger.info("✓ 生产服务器启动中...")
        logger.info("✓ 访问地址: http://localhost:8001")
        logger.info("✓ API文档: http://localhost:8001/docs")

        await server.serve()

    except KeyboardInterrupt:
        logger.info("\n✓ 生产模式已停止")
    except Exception as e:
        logger.error(f"✗ 生产模式启动失败: {e}")
        sys.exit(1)


async def run_tests():
    """运行测试"""
    logger.info("🧪 运行测试...")

    try:
        import pytest

        # 测试配置
        test_args = [
            "tests/",
            "-v",
            "--tb=short",
            "--disable-warnings",
            f"--cov=src",
            f"--cov-report=term-missing",
            f"--cov-report=html:htmlcov"
        ]

        # 运行测试
        exit_code = pytest.main(test_args)

        if exit_code == 0:
            logger.info("✓ 所有测试通过")
        else:
            logger.error("✗ 测试失败")
            sys.exit(1)

    except ImportError:
        logger.error("未安装pytest，请运行: pip install pytest pytest-cov")
        sys.exit(1)
    except Exception as e:
        logger.error(f"✗ 测试运行失败: {e}")
        sys.exit(1)


def show_system_info():
    """显示系统信息"""
    print("\n" + "="*60)
    print("  港股量化交易系统 - 真实数据采集模块")
    print("="*60)
    print(f"  版本: v2.0.0")
    print(f"  基于: OpenSpec 规范文档")
    print(f"  项目路径: {project_root}")
    print(f"  Python版本: {sys.version}")
    print("="*60)
    print()


def show_menu():
    """显示交互菜单"""
    print("\n请选择操作模式:")
    print("  1. 开发模式 (--dev)")
    print("  2. 生产模式 (--prod)")
    print("  3. 运行测试 (--test)")
    print("  4. 检查系统 (--check)")
    print("  5. 查看状态 (--status)")
    print("  6. 退出 (q)")

    while True:
        choice = input("\n请输入选择 (1-6, q): ").strip().lower()

        if choice in ['1', 'dev']:
            return 'dev'
        elif choice in ['2', 'prod']:
            return 'prod'
        elif choice in ['3', 'test']:
            return 'test'
        elif choice in ['4', 'check']:
            return 'check'
        elif choice in ['5', 'status']:
            return 'status'
        elif choice in ['q', 'quit', 'exit']:
            return 'quit'
        else:
            print("无效选择，请重新输入")


async def check_system():
    """检查系统状态"""
    print("\n🔍 系统检查报告")
    print("-" * 40)

    # 检查依赖
    deps_ok = check_dependencies()

    # 检查环境
    env_ok = check_environment()

    # 检查数据库
    db_ok = check_databases()

    # 总结
    print("\n" + "="*40)
    if deps_ok and env_ok and db_ok:
        print("✓ 系统检查通过，可以启动服务")
        return True
    else:
        print("✗ 系统检查未通过，请解决上述问题")
        return False


async def show_status():
    """显示系统状态"""
    print("\n📊 系统状态")
    print("-" * 40)

    try:
        # 检查主服务
        import requests

        response = requests.get(
            'http://localhost:8001/api/v1/real_data/health',
            timeout=5
        )

        if response.status_code == 200:
            health_data = response.json()
            print("✓ 主服务: 运行中")

            # 显示存储状态
            storage = health_data.get('storage', {})
            if storage.get('storage_system'):
                print("✓ 存储系统: 正常")
            else:
                print("✗ 存储系统: 异常")

            # 显示适配器状态
            adapters = health_data.get('adapters', [])
            for adapter in adapters:
                status = "✓" if adapter.get('status') == 'healthy' else "✗"
                print(f"{status} {adapter.get('source_name', 'Unknown')}: {adapter.get('status', 'unknown')}")
        else:
            print("✗ 主服务: 未响应")

    except requests.exceptions.RequestException:
        print("✗ 主服务: 连接失败")
        print("  请确保服务已启动: python start_real_data_system.py --dev")


def print_usage_examples():
    """打印使用示例"""
    print("\n📖 使用示例:")
    print("-" * 40)

    print("\n1. 启动开发模式:")
    print("   python start_real_data_system.py --dev")

    print("\n2. 启动生产模式:")
    print("   python start_real_data_system.py --prod")

    print("\n3. 运行测试:")
    print("   python start_real_data_system.py --test")

    print("\n4. 检查系统:")
    print("   python start_real_data_system.py --check")

    print("\n5. 交互模式:")
    print("   python start_real_data_system.py")

    print("\n📚 API使用示例:")
    print("-" * 40)

    print("\n# 获取HIBOR数据")
    print("curl 'http://localhost:8001/api/v1/real_data/hibor?period=1m&start_date=2024-10-01&end_date=2024-11-04'")

    print("\n# 获取物业数据")
    print("curl 'http://localhost:8001/api/v1/real_data/property?district=中區&start_date=2024-10-01'")

    print("\n# 获取旅客数据")
    print("curl 'http://localhost:8001/api/v1/real_data/tourism?month=11&year=2024'")


async def main():
    """主函数"""
    show_system_info()

    # 解析命令行参数
    parser = argparse.ArgumentParser(description="港股量化交易系统启动脚本")
    parser.add_argument('--dev', action='store_true', help='启动开发模式')
    parser.add_argument('--prod', action='store_true', help='启动生产模式')
    parser.add_argument('--test', action='store_true', help='运行测试')
    parser.add_argument('--check', action='store_true', help='检查系统')
    parser.add_argument('--status', action='store_true', help='查看状态')
    parser.add_argument('--examples', action='store_true', help='显示使用示例')

    args = parser.parse_args()

    # 如果没有参数，进入交互模式
    if not any([args.dev, args.prod, args.test, args.check, args.status, args.examples]):
        print_usage_examples()
        mode = show_menu()

        if mode == 'quit':
            return
        elif mode == 'dev':
            args.dev = True
        elif mode == 'prod':
            args.prod = True
        elif mode == 'test':
            args.test = True
        elif mode == 'check':
            args.check = True
        elif mode == 'status':
            args.status = True

    # 执行相应操作
    if args.examples:
        print_usage_examples()

    elif args.check:
        await check_system()

    elif args.status:
        await show_status()

    elif args.test:
        await run_tests()

    elif args.dev:
        deps_ok = await check_system()
        if deps_ok:
            await start_development_mode()

    elif args.prod:
        deps_ok = await check_system()
        if deps_ok:
            await start_production_mode()

    else:
        print_usage_examples()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 再见!")
        sys.exit(0)
    except Exception as e:
        logger.error(f"系统启动失败: {e}")
        sys.exit(1)
