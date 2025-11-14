"""
工作区数据库初始化
创建SQLite数据库和表结构
"""

import sqlite3
import os
from typing import List


class WorkspaceDatabase:
    """工作区数据库管理器"""

    def __init__(self, db_path: str = "workspace_data/workspace.db"):
        self.db_path = db_path
        self._ensure_data_dir()

    def _ensure_data_dir(self):
        """确保数据目录存在"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def create_tables(self):
        """创建所有表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 用户工作区表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workspaces (
                user_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                theme TEXT DEFAULT 'dark',
                language TEXT DEFAULT 'zh-TW',
                timezone TEXT DEFAULT 'Asia/Hong_Kong',
                strategy_type TEXT DEFAULT 'technical',
                risk_tolerance TEXT DEFAULT 'medium',
                investment_style TEXT DEFAULT 'growth',
                preferred_timeframe TEXT DEFAULT '1D',
                technical_indicators TEXT,  -- JSON array
                color_scheme TEXT DEFAULT 'blue',
                default_symbols TEXT,  -- JSON array
                refresh_interval INTEGER DEFAULT 60,
                notifications_enabled BOOLEAN DEFAULT 1,
                auto_save BOOLEAN DEFAULT 1,
                dashboard_layout TEXT,  -- JSON
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')

        # 投资组合表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolios (
                portfolio_id TEXT PRIMARY KEY,  -- user_id_portfolio_name
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                cash REAL DEFAULT 0.0,
                total_value REAL DEFAULT 0.0,
                total_pnl REAL DEFAULT 0.0,
                total_pnl_pct REAL DEFAULT 0.0,
                day_change REAL DEFAULT 0.0,
                day_change_pct REAL DEFAULT 0.0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES workspaces(user_id)
            )
        ''')

        # 持仓表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS positions (
                position_id TEXT PRIMARY KEY,  -- portfolio_id_symbol
                portfolio_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                quantity REAL NOT NULL,
                avg_cost REAL NOT NULL,
                current_price REAL DEFAULT 0.0,
                market_value REAL DEFAULT 0.0,
                unrealized_pnl REAL DEFAULT 0.0,
                unrealized_pnl_pct REAL DEFAULT 0.0,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (portfolio_id) REFERENCES portfolios(portfolio_id),
                UNIQUE(portfolio_id, symbol)
            )
        ''')

        # 交易记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                trade_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                portfolio_name TEXT NOT NULL,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL CHECK (side IN ('buy', 'sell')),
                quantity REAL NOT NULL,
                price REAL NOT NULL,
                value REAL NOT NULL,
                fees REAL DEFAULT 0.0,
                pnl REAL DEFAULT 0.0,
                timestamp TEXT NOT NULL,
                notes TEXT,
                strategy TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES workspaces(user_id)
            )
        ''')

        # 交易笔记表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trade_notes (
                note_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                trade_id TEXT,
                symbol TEXT NOT NULL,
                note_type TEXT NOT NULL CHECK (note_type IN ('entry', 'exit', 'review', 'reflection')),
                content TEXT NOT NULL,
                strategy TEXT,
                emotion TEXT,
                tags TEXT,  -- JSON array
                timestamp TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES workspaces(user_id)
            )
        ''')

        # 市场观察表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_observations (
                obs_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                market TEXT NOT NULL,
                mood TEXT NOT NULL CHECK (mood IN ('bullish', 'bearish', 'neutral')),
                observations TEXT NOT NULL,
                key_events TEXT,  -- JSON array
                tags TEXT,  -- JSON array
                symbol_specific TEXT,
                timestamp TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES workspaces(user_id)
            )
        ''')

        # 策略反思表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS strategy_reflections (
                reflection_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                strategy_name TEXT NOT NULL,
                period_start TEXT NOT NULL,
                period_end TEXT NOT NULL,
                performance REAL NOT NULL,
                what_worked TEXT,  -- JSON array
                what_didnt_work TEXT,  -- JSON array
                improvements TEXT,  -- JSON array
                overall_rating INTEGER CHECK (overall_rating BETWEEN 1 AND 10),
                timestamp TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES workspaces(user_id)
            )
        ''')

        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_portfolios_user_id ON portfolios(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_positions_portfolio_id ON positions(portfolio_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_user_id ON trades(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_notes_user_id ON trade_notes(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_obs_user_id ON market_observations(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_reflections_user_id ON strategy_reflections(user_id)')

        conn.commit()
        conn.close()
        print("✅ 数据库表创建成功!")

    def insert_sample_data(self):
        """插入示例数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = "2024-11-09T10:00:00"

        # 插入工作区示例
        cursor.execute('''
            INSERT OR REPLACE INTO workspaces (
                user_id, name, theme, language, strategy_type, risk_tolerance,
                investment_style, technical_indicators, default_symbols,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            "user_001", "我的投资工作区", "dark", "zh-TW", "technical", "medium",
            "growth", '["sma", "rsi", "macd"]', '["0700.HK", "0388.HK", "1398.HK"]',
            now, now
        ))

        # 插入投资组合示例
        cursor.execute('''
            INSERT OR REPLACE INTO portfolios (
                portfolio_id, user_id, name, cash, total_value,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            "user_001_核心组合", "user_001", "核心组合", 50000.0, 150000.0,
            now, now
        ))

        # 插入持仓示例
        cursor.execute('''
            INSERT OR REPLACE INTO positions (
                position_id, portfolio_id, symbol, quantity, avg_cost,
                current_price, market_value, unrealized_pnl, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            "user_001_核心组合_0700.HK", "user_001_核心组合", "0700.HK",
            1000, 380.50, 385.60, 385600.0, 5100.0, now
        ))

        cursor.execute('''
            INSERT OR REPLACE INTO positions (
                position_id, portfolio_id, symbol, quantity, avg_cost,
                current_price, market_value, unrealized_pnl, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            "user_001_核心组合_0388.HK", "user_001_核心组合", "0388.HK",
            500, 280.30, 285.40, 142700.0, 2550.0, now
        ))

        conn.commit()
        conn.close()
        print("✅ 示例数据插入成功!")

    def drop_all_tables(self):
        """删除所有表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        tables = [
            'positions', 'portfolios', 'trades', 'trade_notes',
            'market_observations', 'strategy_reflections', 'workspaces'
        ]

        for table in tables:
            cursor.execute(f'DROP TABLE IF EXISTS {table}')

        conn.commit()
        conn.close()
        print("✅ 所有表已删除!")

    def backup_database(self, backup_path: str):
        """备份数据库"""
        import shutil
        if os.path.exists(self.db_path):
            shutil.copy2(self.db_path, backup_path)
            print(f"✅ 数据库已备份到: {backup_path}")
        else:
            print("❌ 数据库文件不存在!")

    def restore_database(self, backup_path: str):
        """恢复数据库"""
        import shutil
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, self.db_path)
            print(f"✅ 数据库已从 {backup_path} 恢复")
        else:
            print("❌ 备份文件不存在!")

    def get_table_info(self) -> List[dict]:
        """获取表信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()

        table_info = []
        for (table_name,) in tables:
            cursor.execute(f'PRAGMA table_info({table_name})')
            columns = cursor.fetchall()
            table_info.append({
                'table': table_name,
                'columns': [{'name': col[1], 'type': col[2], 'nullable': not col[3]}
                           for col in columns]
            })

        conn.close()
        return table_info


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='工作区数据库管理')
    parser.add_argument('--create', action='store_true', help='创建数据库表')
    parser.add_argument('--sample', action='store_true', help='插入示例数据')
    parser.add_argument('--init', action='store_true', help='创建表并插入示例数据')
    parser.add_argument('--drop', action='store_true', help='删除所有表')
    parser.add_argument('--info', action='store_true', help='显示表信息')
    parser.add_argument('--db-path', default='workspace_data/workspace.db', help='数据库路径')

    args = parser.parse_args()

    db = WorkspaceDatabase(args.db_path)

    if args.create:
        db.create_tables()

    if args.sample:
        db.insert_sample_data()

    if args.init:
        db.create_tables()
        db.insert_sample_data()

    if args.drop:
        response = input("确定要删除所有表吗? (y/N): ")
        if response.lower() == 'y':
            db.drop_all_tables()

    if args.info:
        info = db.get_table_info()
        print("\n数据库表信息:")
        for table in info:
            print(f"\n表: {table['table']}")
            for col in table['columns']:
                nullable = "NULL" if col['nullable'] else "NOT NULL"
                print(f"  - {col['name']}: {col['type']} {nullable}")


if __name__ == "__main__":
    main()
