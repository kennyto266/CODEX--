#!/usr/bin/env python3
"""
密钥管理工具
命令行工具，用于管理加密密钥

使用方法:
    python key_management_tool.py --help
"""

import argparse
import sys
import json
from pathlib import Path
from typing import Optional

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from encryption.manager import EncryptionManager
from encryption.key_manager import KeyManager
from data.storage import DataStorage

def setup_encryption(args):
    """设置加密系统"""
    print("=== 设置加密系统 ===\n")

    # 输入密码
    password = args.password
    if not password:
        import getpass
        password = getpass.getpass("请输入密码: ")

    # 创建加密管理器
    manager = EncryptionManager(
        keys_dir=args.keys_dir,
        encrypted_data_dir=args.data_dir,
        use_password=(args.mode == 'password')
    )

    # 设置
    result = manager.setup_with_password(password)

    print(f"✓ 加密系统设置完成")
    print(f"  算法: {result['algorithm']}")
    print(f"  密钥派生: {result['key_derivation']}")
    print(f"  迭代次数: {result['iterations']}")
    print(f"  主密钥: {'✓' if result['master_key_created'] else '✗'}")
    print(f"  密码密钥: {'✓' if result['password_key_created'] else '✗'}")

def verify_password(args):
    """验证密码"""
    print("=== 验证密码 ===\n")

    manager = EncryptionManager(use_password=True)

    if not manager.password_key_file.exists():
        print("✗ 密码密钥文件不存在，请先运行 setup 命令")
        return 1

    password = args.password
    if not password:
        import getpass
        password = getpass.getpass("请输入密码: ")

    if manager.verify_password(password):
        print("✓ 密码正确")
        return 0
    else:
        print("✗ 密码错误")
        return 1

def generate_key(args):
    """生成新密钥"""
    print("=== 生成密钥 ===\n")

    key_manager = KeyManager(args.keys_dir)

    key_info = key_manager.generate_master_key(
        key_id=args.key_id,
        description=args.description
    )

    print(f"✓ 密钥已生成")
    print(f"  ID: {key_info['id']}")
    print(f"  路径: {key_info['file']}")
    print(f"  创建时间: {key_info['created_at']}")
    print(f"  算法: {key_info['algorithm']}")

def rotate_key(args):
    """轮换密钥"""
    print("=== 轮换密钥 ===\n")

    key_manager = KeyManager(args.keys_dir)

    if not key_manager.get_key(args.key_id):
        print(f"✗ 密钥不存在: {args.key_id}")
        return 1

    if key_manager.rotate_key(args.key_id):
        print(f"✓ 密钥已轮换: {args.key_id}")
        return 0
    else:
        print(f"✗ 密钥轮换失败: {args.key_id}")
        return 1

def list_keys(args):
    """列出密钥"""
    print("=== 密钥列表 ===\n")

    key_manager = KeyManager(args.keys_dir)
    keys = key_manager.list_keys()

    if not keys:
        print("未找到密钥")
        return 0

    for key in keys:
        print(f"ID: {key['id']}")
        print(f"  状态: {key['status']}")
        print(f"  创建: {key['created_at']}")
        print(f"  轮换次数: {key.get('rotation_count', 0)}")
        print()

def get_stats(args):
    """获取统计信息"""
    print("=== 统计信息 ===\n")

    manager = EncryptionManager(use_password=True)

    if not manager.use_password:
        key_manager = KeyManager(args.keys_dir)
        stats = key_manager.get_key_statistics()
    else:
        stats = manager.get_encryption_statistics()

    for key, value in stats.items():
        print(f"{key}: {value}")

def encrypt_file(args):
    """加密文件"""
    print(f"=== 加密文件 ===\n")
    print(f"源文件: {args.input}")
    print(f"输出: {args.output}\n")

    manager = EncryptionManager(use_password=True)

    if not manager.password_key_file.exists():
        print("✗ 加密系统未设置，请先运行 setup 命令")
        return 1

    # 解锁
    password = args.password
    if not password:
        import getpass
        password = getpass.getpass("请输入密码: ")

    if not manager.unlock(password):
        print("✗ 密码错误")
        return 1

    try:
        encrypted_path = manager.encrypt_file(
            file_path=args.input,
            output_path=args.output
        )
        print(f"✓ 文件已加密: {encrypted_path}")
        return 0
    except Exception as e:
        print(f"✗ 加密失败: {e}")
        return 1

def decrypt_file(args):
    """解密文件"""
    print(f"=== 解密文件 ===\n")
    print(f"源文件: {args.input}")
    print(f"输出: {args.output}\n")

    manager = EncryptionManager(use_password=True)

    if not manager.password_key_file.exists():
        print("✗ 加密系统未设置，请先运行 setup 命令")
        return 1

    # 解锁
    password = args.password
    if not password:
        import getpass
        password = getpass.getpass("请输入密码: ")

    if not manager.unlock(password):
        print("✗ 密码错误")
        return 1

    try:
        decrypted_path = manager.decrypt_file(
            encrypted_file_path=args.input,
            output_path=args.output
        )
        print(f"✓ 文件已解密: {decrypted_path}")
        return 0
    except Exception as e:
        print(f"✗ 解密失败: {e}")
        return 1

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="密钥管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 设置加密系统
  %(prog)s setup --password mypassword

  # 验证密码
  %(prog)s verify --password mypassword

  # 生成密钥
  %(prog)s gen-key --key-id master --description "主密钥"

  # 轮换密钥
  %(prog)s rotate-key --key-id master

  # 列出密钥
  %(prog)s list-keys

  # 加密文件
  %(prog)s encrypt --input data.txt --output data.enc

  # 解密文件
  %(prog)s decrypt --input data.enc --output data.txt
        """
    )

    # 全局参数
    parser.add_argument('--keys-dir', default='keys',
                       help='密钥存储目录 (默认: keys)')
    parser.add_argument('--data-dir', default='encrypted_data',
                       help='加密数据目录 (默认: encrypted_data)')

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # setup 命令
    setup_parser = subparsers.add_parser('setup', help='设置加密系统')
    setup_parser.add_argument('--password', help='密码')
    setup_parser.add_argument('--mode', choices=['password', 'key'],
                             default='password', help='加密模式')

    # verify 命令
    verify_parser = subparsers.add_parser('verify', help='验证密码')
    verify_parser.add_argument('--password', help='密码')

    # gen-key 命令
    genkey_parser = subparsers.add_parser('gen-key', help='生成新密钥')
    genkey_parser.add_argument('--key-id', required=True, help='密钥ID')
    genkey_parser.add_argument('--description', default='', help='密钥描述')

    # rotate-key 命令
    rotate_parser = subparsers.add_parser('rotate-key', help='轮换密钥')
    rotate_parser.add_argument('--key-id', required=True, help='密钥ID')

    # list-keys 命令
    subparsers.add_parser('list-keys', help='列出密钥')

    # stats 命令
    subparsers.add_parser('stats', help='显示统计信息')

    # encrypt 命令
    encrypt_parser = subparsers.add_parser('encrypt', help='加密文件')
    encrypt_parser.add_argument('--input', required=True, help='输入文件')
    encrypt_parser.add_argument('--output', help='输出文件')
    encrypt_parser.add_argument('--password', help='密码')

    # decrypt 命令
    decrypt_parser = subparsers.add_parser('decrypt', help='解密文件')
    decrypt_parser.add_argument('--input', required=True, help='输入文件')
    decrypt_parser.add_argument('--output', help='输出文件')
    decrypt_parser.add_argument('--password', help='密码')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # 执行命令
    commands = {
        'setup': setup_encryption,
        'verify': verify_password,
        'gen-key': generate_key,
        'rotate-key': rotate_key,
        'list-keys': list_keys,
        'stats': get_stats,
        'encrypt': encrypt_file,
        'decrypt': decrypt_file
    }

    try:
        return commands[args.command](args)
    except KeyboardInterrupt:
        print("\n操作已取消")
        return 1
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
