#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置迁移脚本 - 从 .env 迁移到 YAML 分层配置
将现有的环境变量配置迁移到新的分层架构配置系统

使用方式:
    python scripts/migrate_config.py --source .env --target config/environments/development.yaml
    python scripts/migrate_config.py --source .env --target config/environments/production.yaml --env production
"""

import os
import sys
import argparse
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import shutil

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class ConfigMigrator:
    """配置迁移器 - 将 .env 格式迁移到 YAML"""

    def __init__(self, source_env: str, target_yaml: str):
        self.source_env = source_env
        self.target_yaml = target_yaml
        self.env_vars: Dict[str, str] = {}
        self.migrated_config: Dict[str, Any] = {}
        self.backup_created = False

    def load_env_file(self) -> Dict[str, str]:
        """加载 .env 文件"""
        env_vars = {}

        if not os.path.exists(self.source_env):
            raise FileNotFoundError(f"源文件不存在: {self.source_env}")

        with open(self.source_env, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                # 跳过空行和注释
                if not line or line.startswith('#'):
                    continue

                # 解析 KEY=VALUE 格式
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"\'')  # 移除引号

                    env_vars[key] = value
                else:
                    print(f"⚠️  警告: 第 {line_num} 行格式不正确: {line}")

        return env_vars

    def map_env_to_yaml(self) -> Dict[str, Any]:
        """将环境变量映射到YAML配置结构"""
        config = {}

        # === 应用配置 ===
        config['application'] = {
            'name': 'CODEX Trading System',
            'version': '7.0.0',
            'debug': self._parse_bool(self.env_vars.get('DEBUG', 'false')),
            'environment': self._determine_environment()
        }

        # === API 配置 ===
        api_config = {
            'host': self.env_vars.get('API_HOST', self.env_vars.get('DASHBOARD_HOST', 'localhost')),
            'port': int(self.env_vars.get('API_PORT', self.env_vars.get('DASHBOARD_PORT', 8001))),
            'workers': 4,
            'reload': self.env_vars.get('ENVIRONMENT', 'development') == 'development'
        }

        # 添加数据库相关配置
        if 'DATABASE_URL' in self.env_vars:
            config['database'] = {
                'url': self.env_vars['DATABASE_URL'],
                'pool_size': 10,
                'max_overflow': 20,
                'pool_timeout': 30,
                'echo': api_config['debug']
            }

        # === 数据源配置 ===
        data_sources = {}
        if 'STOCK_API_BASE_URL' in self.env_vars or 'STOCK_API_URL' in self.env_vars:
            data_sources['hkex'] = {
                'endpoint': self.env_vars.get('STOCK_API_BASE_URL', 'http://18.180.162.113:9191'),
                'timeout': int(self.env_vars.get('STOCK_API_TIMEOUT', 30)),
                'retry_attempts': 3
            }

        if 'yfinance' in str(self.env_vars).lower():
            data_sources['yahoo_finance'] = {
                'timeout': 30,
                'rate_limit': 2000
            }

        if data_sources:
            config['data_sources'] = data_sources

        # === 交易配置 ===
        trading_config = {
            'enabled': self._parse_bool(self.env_vars.get('TRADING_ENABLED', 'false')),
            'initial_capital': float(self.env_vars.get('INITIAL_CAPITAL', 1000000.0)),
            'max_position_size': float(self.env_vars.get('MAX_POSITION_SIZE', 100000.0)),
            'risk_limit': float(self.env_vars.get('RISK_LIMIT', 0.02))
        }
        config['trading'] = trading_config

        # === 日志配置 ===
        log_level = self.env_vars.get('LOG_LEVEL', 'INFO').upper()
        config['logging'] = {
            'level': log_level,
            'format': 'json',
            'handlers': [
                {
                    'type': 'console',
                    'level': 'INFO'
                },
                {
                    'type': 'file',
                    'level': 'DEBUG',
                    'path': 'logs/codex.log',
                    'max_size': '100MB',
                    'backup_count': 5
                }
            ]
        }

        # === 缓存配置 ===
        config['caching'] = {
            'l1_size': int(self.env_vars.get('CACHE_L1_SIZE', 1000)),
            'l2_ttl': int(self.env_vars.get('CACHE_L2_TTL', 300)),
            'l3_ttl': int(self.env_vars.get('CACHE_L3_TTL', 3600))
        }

        # === 监控配置 ===
        config['monitoring'] = {
            'enabled': self._parse_bool(self.env_vars.get('MONITORING_ENABLED', 'true')),
            'metrics_port': int(self.env_vars.get('METRICS_PORT', 9090)),
            'health_check_interval': 30
        }

        # === Telegram 配置 ===
        if 'TELEGRAM_BOT_TOKEN' in self.env_vars:
            config['telegram'] = {
                'bot_token': self.env_vars['TELEGRAM_BOT_TOKEN'],
                'allowed_user_ids': [
                    int(uid) for uid in
                    self.env_vars.get('TG_ALLOWED_USER_IDS', '0').split(',')
                    if uid.strip().isdigit()
                ],
                'enabled': bool(self.env_vars['TELEGRAM_BOT_TOKEN'].strip())
            }

        # === AI API 配置 ===
        if 'AI_API_KEY' in self.env_vars:
            config['ai'] = {
                'api_key': self.env_vars['AI_API_KEY'],
                'base_url': self.env_vars.get('AI_API_BASE_URL', 'https://api.openai.com/v1'),
                'model': self.env_vars.get('AI_MODEL', 'gpt-3.5-turbo'),
                'max_tokens': int(self.env_vars.get('AI_MAX_TOKENS', 1000)),
                'enabled': bool(self.env_vars['AI_API_KEY'].strip())
            }

        # === 体育数据配置 ===
        if 'SPORTS_API_KEY' in self.env_vars:
            config['sports'] = {
                'api_key': self.env_vars['SPORTS_API_KEY'],
                'enabled': self._parse_bool(self.env_vars.get('SPORTS_ENABLED', 'true'))
            }

        # === 天气 API 配置 ===
        if 'WEATHER_API_KEY' in self.env_vars or 'OPENWEATHER_API_KEY' in self.env_vars:
            config['weather'] = {
                'hk_api_key': self.env_vars.get('WEATHER_API_KEY', ''),
                'openweather_api_key': self.env_vars.get('OPENWEATHER_API_KEY', ''),
                'enabled': bool(self.env_vars.get('WEATHER_API_KEY') or self.env_vars.get('OPENWEATHER_API_KEY'))
            }

        # === 安全配置 ===
        config['security'] = {
            'secret_key': self.env_vars.get('SECRET_KEY', 'your-secret-key'),
            'jwt_secret_key': self.env_vars.get('JWT_SECRET_KEY', 'your-jwt-secret-key'),
            'cors_origins': ['*'],  # 可以从环境变量解析
            'jwt_expiration_hours': 24
        }

        # === 替代数据配置 ===
        config['alternative_data'] = {
            'enabled': self._parse_bool(self.env_vars.get('ALT_DATA_ENABLED', 'true')),
            'update_frequency': self.env_vars.get('ALT_DATA_UPDATE_FREQUENCY', 'daily'),
            'data_sources': [
                'hibor',
                'property',
                'retail',
                'gdp',
                'visitor_arrivals'
            ]
        }

        # === 爬虫配置 ===
        config['crawlers'] = {
            'enabled': True,
            'rate_limit': 2,  # 每秒请求数
            'timeout': 30,
            'retry_attempts': 3,
            'user_agent': 'CODEX-Trading-System/7.0.0'
        }

        return config

    def _parse_bool(self, value: str) -> bool:
        """解析布尔值"""
        return value.lower() in ('true', '1', 'yes', 'on')

    def _determine_environment(self) -> str:
        """确定运行环境"""
        return self.env_vars.get('ENVIRONMENT', 'development')

    def create_backup(self) -> str:
        """创建备份文件"""
        if os.path.exists(self.target_yaml):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = f"{self.target_yaml}.backup.{timestamp}"

            shutil.copy2(self.target_yaml, backup_path)
            self.backup_created = True

            print(f"✅ 已创建备份文件: {backup_path}")
            return backup_path

        return ""

    def merge_with_existing(self, new_config: Dict[str, Any]) -> Dict[str, Any]:
        """与现有配置合并"""
        if not os.path.exists(self.target_yaml):
            return new_config

        with open(self.target_yaml, 'r', encoding='utf-8') as f:
            existing_config = yaml.safe_load(f)

        # 深度合并配置
        merged = self._deep_merge(existing_config, new_config)

        print("✅ 已与现有配置合并")
        return merged

    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """深度合并两个字典"""
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def save_yaml_config(self, config: Dict[str, Any]) -> None:
        """保存YAML配置文件"""
        # 确保目标目录存在
        os.makedirs(os.path.dirname(self.target_yaml), exist_ok=True)

        # 生成带注释的YAML
        yaml_content = self._generate_yaml_with_comments(config)

        with open(self.target_yaml, 'w', encoding='utf-8') as f:
            f.write(yaml_content)

        print(f"✅ 配置已保存到: {self.target_yaml}")

    def _generate_yaml_with_comments(self, config: Dict[str, Any]) -> str:
        """生成带注释的YAML内容"""
        lines = []

        # 文件头部注释
        lines.append("# " + "="*60)
        lines.append(f"# CODEX Trading System - 环境配置文件")
        lines.append(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"# 迁移自: .env 文件")
        lines.append("# " + "="*60)
        lines.append("")

        # 各部分的注释和配置
        self._add_yaml_section(lines, config, "")
        return "\n".join(lines)

    def _add_yaml_section(self, lines: list, config: Dict[str, Any], indent: str):
        """递归添加YAML配置节"""
        for key, value in config.items():
            section_comments = self._get_section_comment(key)
            if section_comments:
                lines.append(f"{indent}# {section_comments}")

            if isinstance(value, dict):
                lines.append(f"{indent}{key}:")
                self._add_yaml_section(lines, value, indent + "  ")
            elif isinstance(value, list):
                lines.append(f"{indent}{key}:")
                for item in value:
                    lines.append(f"{indent}  - {item}")
            else:
                # 处理特殊类型
                if isinstance(value, bool):
                    value_str = str(value).lower()
                elif value is None:
                    value_str = "null"
                else:
                    value_str = str(value)

                lines.append(f"{indent}{key}: {value_str}")

            lines.append("")

    def _get_section_comment(self, key: str) -> str:
        """获取配置节的注释"""
        comments = {
            'application': '应用程序基础配置',
            'api': 'API服务器配置',
            'database': '数据库连接配置',
            'redis': 'Redis缓存配置',
            'data_sources': '数据源配置',
            'trading': '交易系统配置',
            'logging': '日志系统配置',
            'caching': '多级缓存配置',
            'monitoring': '系统监控配置',
            'telegram': 'Telegram机器人配置',
            'ai': 'AI API配置',
            'sports': '体育数据API配置',
            'weather': '天气数据API配置',
            'security': '安全配置',
            'alternative_data': '替代数据配置',
            'crawlers': '网络爬虫配置'
        }
        return comments.get(key, '')

    def generate_migration_report(self, backup_path: str) -> None:
        """生成迁移报告"""
        print("\n" + "="*60)
        print("📋 配置迁移报告")
        print("="*60)

        print(f"\n📂 源文件: {self.source_env}")
        print(f"📂 目标文件: {self.target_yaml}")

        if backup_path:
            print(f"💾 备份文件: {backup_path}")

        print(f"\n🔢 环境变量数量: {len(self.env_vars)}")

        # 按类别统计
        categories = {
            'API': ['API_HOST', 'API_PORT', 'DASHBOARD_HOST', 'DASHBOARD_PORT'],
            '数据源': ['STOCK_API_BASE_URL', 'STOCK_API_URL', 'STOCK_API_TIMEOUT'],
            'Telegram': ['TELEGRAM_BOT_TOKEN', 'TG_ALLOWED_USER_IDS'],
            'AI': ['AI_API_KEY', 'AI_API_BASE_URL', 'AI_MODEL', 'AI_MAX_TOKENS'],
            '安全': ['SECRET_KEY', 'JWT_SECRET_KEY'],
            '数据库': ['DATABASE_URL'],
            '体育': ['SPORTS_API_KEY', 'SPORTS_ENABLED'],
            '天气': ['WEATHER_API_KEY', 'OPENWEATHER_API_KEY'],
            '交易': ['TRADING_ENABLED', 'INITIAL_CAPITAL', 'MAX_POSITION_SIZE', 'RISK_LIMIT'],
            '监控': ['MONITORING_ENABLED', 'METRICS_PORT'],
            '替代数据': ['ALT_DATA_ENABLED', 'ALT_DATA_UPDATE_FREQUENCY'],
            '日志': ['LOG_LEVEL'],
            'Cursor': ['CURSOR_API_KEY']
        }

        print("\n📊 配置分类统计:")
        for category, keys in categories.items():
            count = sum(1 for key in keys if key in self.env_vars)
            if count > 0:
                print(f"  • {category}: {count} 项")

        print(f"\n✅ 迁移完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 使用说明
        print("\n" + "="*60)
        print("📖 使用说明")
        print("="*60)
        print("1. 新的YAML配置文件已生成")
        print("2. 旧版.env文件仍可继续使用（向后兼容）")
        print("3. 建议逐步迁移到新配置系统:")
        print("   - 更新应用程序代码使用新配置")
        print("   - 测试无误后可删除旧版.env文件")
        print("4. 配置优先级：环境变量 > 特定环境YAML > 基础YAML")
        print("5. 使用帮助: python scripts/migrate_config.py --help")

    def run_migration(self) -> bool:
        """运行迁移流程"""
        try:
            print("🚀 开始配置迁移...")

            # 1. 加载.env文件
            print(f"\n📖 加载源文件: {self.source_env}")
            self.env_vars = self.load_env_file()
            print(f"✅ 成功加载 {len(self.env_vars)} 个环境变量")

            # 2. 创建备份
            if os.path.exists(self.target_yaml):
                print(f"\n💾 创建备份文件...")
                self.create_backup()

            # 3. 映射到YAML配置
            print(f"\n🔄 映射配置到YAML格式...")
            new_config = self.map_env_to_yaml()
            self.migrated_config = new_config
            print(f"✅ 生成 {len(new_config)} 个配置节")

            # 4. 合并现有配置
            print(f"\n🔀 合并现有配置...")
            final_config = self.merge_with_existing(new_config)

            # 5. 保存配置
            print(f"\n💾 保存YAML配置...")
            self.save_yaml_config(final_config)

            # 6. 生成报告
            backup_path = f"{self.target_yaml}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}" if self.backup_created else ""
            self.generate_migration_report(backup_path)

            return True

        except Exception as e:
            print(f"\n❌ 迁移失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='配置迁移工具 - 从.env迁移到YAML',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python scripts/migrate_config.py --source .env --target config/environments/development.yaml
  python scripts/migrate_config.py --source .env --target config/environments/production.yaml --env production
  python scripts/migrate_config.py --source .env --target config/environments/development.yaml --dry-run
        """
    )

    parser.add_argument(
        '--source',
        default='.env',
        help='源.env文件路径 (默认: .env)'
    )

    parser.add_argument(
        '--target',
        required=True,
        help='目标YAML文件路径'
    )

    parser.add_argument(
        '--env',
        default='development',
        choices=['development', 'production', 'testing'],
        help='目标环境 (默认: development)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='仅预览迁移结果，不实际执行'
    )

    args = parser.parse_args()

    # 检查源文件
    if not os.path.exists(args.source):
        print(f"❌ 错误: 源文件不存在: {args.source}")
        sys.exit(1)

    # 如果是dry-run，创建临时目标路径
    target_path = args.target
    if args.dry_run:
        target_path = f"{args.target}.preview"
        print("🔍 预览模式 - 将生成临时文件用于预览")

    # 执行迁移
    migrator = ConfigMigrator(args.source, target_path)

    if args.dry_run:
        # 干运行模式
        print("🔍 干运行模式 - 仅预览配置映射")
        try:
            env_vars = migrator.load_env_file()
            print(f"\n📋 源配置包含 {len(env_vars)} 个变量:")
            for key, value in sorted(env_vars.items()):
                # 隐藏敏感信息
                if any(sensitive in key.upper() for sensitive in ['KEY', 'TOKEN', 'SECRET', 'PASSWORD']):
                    print(f"  • {key}: {'*' * 8}")
                else:
                    print(f"  • {key}: {value}")

            mapped_config = migrator.map_env_to_yaml()
            print(f"\n📋 将映射到 {len(mapped_config)} 个YAML配置节:")
            for section in sorted(mapped_config.keys()):
                print(f"  • {section}")

            print("\n✅ 干运行完成 - 配置映射正常")
            return

        except Exception as e:
            print(f"❌ 干运行失败: {str(e)}")
            sys.exit(1)

    # 实际迁移
    success = migrator.run_migration()

    if success:
        print("\n🎉 迁移成功完成！")
        sys.exit(0)
    else:
        print("\n💥 迁移失败！")
        sys.exit(1)

if __name__ == '__main__':
    main()
