"""
Backtest Result Service - Phase 4.7

Manages backtest results storage, retrieval, and comparison analysis.
Provides API layer for dashboard integration.

Features:
    - Store backtest results with metadata
    - Query and retrieve results by ID
    - Compare results (with alt data vs without)
    - Generate signal visualization data
    - Support parameter adjustment and re-backtesting
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field, asdict
import json
import sqlite3
from pathlib import Path

import pandas as pd
import numpy as np


class BacktestStatus(str, Enum):
    """Backtest execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SignalSource(str, Enum):
    """Signal source classification"""
    PRICE_ONLY = "price_only"
    ALT_DATA_ONLY = "alt_data_only"
    COMBINED = "combined"


@dataclass
class BacktestResultMetadata:
    """Metadata for backtest result"""
    result_id: str
    symbol: str
    strategy_name: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    use_alt_data: bool
    alt_data_indicators: List[str] = field(default_factory=list)
    status: BacktestStatus = BacktestStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


@dataclass
class BacktestResultData:
    """Complete backtest result data"""
    metadata: BacktestResultMetadata

    # Performance metrics
    total_return: float = 0.0
    annualized_return: float = 0.0
    volatility: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    max_drawdown: float = 0.0

    # Trade statistics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0

    # Alt data specific metrics (if applicable)
    price_only_sharpe: Optional[float] = None
    alt_data_contribution_pct: Optional[float] = None
    signal_source_breakdown: Dict[SignalSource, int] = field(default_factory=dict)

    # Trade details
    trades: List[Dict[str, Any]] = field(default_factory=list)
    daily_values: List[Tuple[datetime, float]] = field(default_factory=list)
    daily_returns: List[float] = field(default_factory=list)


class BacktestResultService:
    """Service for managing backtest results"""

    def __init__(self, data_dir: str = "data/backtest_results"):
        """Initialize result service"""
        self.logger = logging.getLogger("hk_quant_system.result_service")
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # In-memory cache
        self.results_cache: Dict[str, BacktestResultData] = {}

        # Initialize SQLite database for metadata
        self.db_path = self.data_dir / "backtest_results.db"
        self._initialize_database()

    def _initialize_database(self) -> None:
        """Initialize SQLite database for backtest metadata"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS backtest_results (
                    result_id TEXT PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    strategy_name TEXT NOT NULL,
                    start_date TIMESTAMP NOT NULL,
                    end_date TIMESTAMP NOT NULL,
                    initial_capital REAL NOT NULL,
                    use_alt_data INTEGER NOT NULL,
                    alt_data_indicators TEXT,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    completed_at TIMESTAMP,
                    error_message TEXT,
                    result_file TEXT NOT NULL
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_symbol ON backtest_results(symbol)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_strategy ON backtest_results(strategy_name)
            """)

            conn.commit()
            conn.close()

            self.logger.info("Database initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise

    async def save_result(self, result: BacktestResultData) -> str:
        """Save backtest result and return result ID"""
        try:
            result_id = result.metadata.result_id

            # Save to JSON file
            result_file = self.data_dir / f"{result_id}.json"
            result_data = {
                "metadata": asdict(result.metadata),
                "metrics": {
                    "total_return": result.total_return,
                    "annualized_return": result.annualized_return,
                    "volatility": result.volatility,
                    "sharpe_ratio": result.sharpe_ratio,
                    "sortino_ratio": result.sortino_ratio,
                    "max_drawdown": result.max_drawdown,
                    "total_trades": result.total_trades,
                    "winning_trades": result.winning_trades,
                    "losing_trades": result.losing_trades,
                    "win_rate": result.win_rate,
                    "avg_win": result.avg_win,
                    "avg_loss": result.avg_loss,
                    "profit_factor": result.profit_factor,
                    "price_only_sharpe": result.price_only_sharpe,
                    "alt_data_contribution_pct": result.alt_data_contribution_pct,
                },
                "trades": result.trades,
                "daily_values": [(str(d), v) for d, v in result.daily_values],
                "daily_returns": result.daily_returns,
            }

            # Convert datetime objects to strings for JSON serialization
            result_data["metadata"]["created_at"] = result.metadata.created_at.isoformat()
            result_data["metadata"]["start_date"] = result.metadata.start_date.isoformat()
            result_data["metadata"]["end_date"] = result.metadata.end_date.isoformat()
            if result.metadata.completed_at:
                result_data["metadata"]["completed_at"] = result.metadata.completed_at.isoformat()

            with open(result_file, 'w') as f:
                json.dump(result_data, f, indent=2)

            # Save metadata to database
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO backtest_results
                (result_id, symbol, strategy_name, start_date, end_date,
                 initial_capital, use_alt_data, alt_data_indicators, status,
                 created_at, completed_at, error_message, result_file)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result_id,
                result.metadata.symbol,
                result.metadata.strategy_name,
                result.metadata.start_date.isoformat(),
                result.metadata.end_date.isoformat(),
                result.metadata.initial_capital,
                1 if result.metadata.use_alt_data else 0,
                json.dumps(result.metadata.alt_data_indicators),
                result.metadata.status.value,
                result.metadata.created_at.isoformat(),
                result.metadata.completed_at.isoformat() if result.metadata.completed_at else None,
                result.metadata.error_message,
                str(result_file)
            ))

            conn.commit()
            conn.close()

            # Cache result
            self.results_cache[result_id] = result

            self.logger.info(f"Saved backtest result: {result_id}")
            return result_id

        except Exception as e:
            self.logger.error(f"Failed to save backtest result: {e}")
            raise

    async def get_result(self, result_id: str) -> Optional[BacktestResultData]:
        """Retrieve backtest result by ID"""
        try:
            # Check cache first
            if result_id in self.results_cache:
                return self.results_cache[result_id]

            # Load from file
            result_file = self.data_dir / f"{result_id}.json"
            if not result_file.exists():
                self.logger.warning(f"Result file not found: {result_id}")
                return None

            with open(result_file, 'r') as f:
                data = json.load(f)

            # Reconstruct result object
            metadata_dict = data["metadata"]
            metadata = BacktestResultMetadata(
                result_id=metadata_dict["result_id"],
                symbol=metadata_dict["symbol"],
                strategy_name=metadata_dict["strategy_name"],
                start_date=datetime.fromisoformat(metadata_dict["start_date"]),
                end_date=datetime.fromisoformat(metadata_dict["end_date"]),
                initial_capital=metadata_dict["initial_capital"],
                use_alt_data=metadata_dict["use_alt_data"],
                alt_data_indicators=metadata_dict.get("alt_data_indicators", []),
                status=BacktestStatus(metadata_dict["status"]),
                created_at=datetime.fromisoformat(metadata_dict["created_at"]),
                completed_at=datetime.fromisoformat(metadata_dict["completed_at"]) if metadata_dict.get("completed_at") else None,
                error_message=metadata_dict.get("error_message"),
            )

            result = BacktestResultData(metadata=metadata)

            # Load metrics
            for key, value in data["metrics"].items():
                if hasattr(result, key):
                    setattr(result, key, value)

            # Load trades and values
            result.trades = data.get("trades", [])
            result.daily_values = [(datetime.fromisoformat(d), v) for d, v in data.get("daily_values", [])]
            result.daily_returns = data.get("daily_returns", [])

            # Cache result
            self.results_cache[result_id] = result

            return result

        except Exception as e:
            self.logger.error(f"Failed to retrieve result {result_id}: {e}")
            return None

    async def list_results(
        self,
        symbol: Optional[str] = None,
        strategy_name: Optional[str] = None,
        use_alt_data: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[BacktestResultMetadata]:
        """List backtest results with optional filtering"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            query = "SELECT * FROM backtest_results WHERE 1=1"
            params = []

            if symbol:
                query += " AND symbol = ?"
                params.append(symbol)

            if strategy_name:
                query += " AND strategy_name = ?"
                params.append(strategy_name)

            if use_alt_data is not None:
                query += " AND use_alt_data = ?"
                params.append(1 if use_alt_data else 0)

            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            results = []
            for row in rows:
                metadata = BacktestResultMetadata(
                    result_id=row["result_id"],
                    symbol=row["symbol"],
                    strategy_name=row["strategy_name"],
                    start_date=datetime.fromisoformat(row["start_date"]),
                    end_date=datetime.fromisoformat(row["end_date"]),
                    initial_capital=row["initial_capital"],
                    use_alt_data=bool(row["use_alt_data"]),
                    alt_data_indicators=json.loads(row["alt_data_indicators"]) if row["alt_data_indicators"] else [],
                    status=BacktestStatus(row["status"]),
                    created_at=datetime.fromisoformat(row["created_at"]),
                    completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
                    error_message=row["error_message"],
                )
                results.append(metadata)

            return results

        except Exception as e:
            self.logger.error(f"Failed to list results: {e}")
            return []

    async def compare_results(
        self,
        result_id_with_alt: str,
        result_id_without_alt: str
    ) -> Dict[str, Any]:
        """Compare two backtest results (with and without alt data)"""
        try:
            result_with = await self.get_result(result_id_with_alt)
            result_without = await self.get_result(result_id_without_alt)

            if not result_with or not result_without:
                raise ValueError("One or both results not found")

            comparison = {
                "result_with_alt_data": {
                    "id": result_id_with_alt,
                    "sharpe_ratio": result_with.sharpe_ratio,
                    "total_return": result_with.total_return,
                    "max_drawdown": result_with.max_drawdown,
                    "win_rate": result_with.win_rate,
                    "total_trades": result_with.total_trades,
                },
                "result_without_alt_data": {
                    "id": result_id_without_alt,
                    "sharpe_ratio": result_without.sharpe_ratio,
                    "total_return": result_without.total_return,
                    "max_drawdown": result_without.max_drawdown,
                    "win_rate": result_without.win_rate,
                    "total_trades": result_without.total_trades,
                },
                "improvement": {
                    "sharpe_ratio_improvement_pct": (
                        (result_with.sharpe_ratio - result_without.sharpe_ratio) /
                        abs(result_without.sharpe_ratio) * 100
                        if result_without.sharpe_ratio != 0 else 0
                    ),
                    "return_improvement_pct": (
                        (result_with.total_return - result_without.total_return) /
                        abs(result_without.total_return) * 100
                        if result_without.total_return != 0 else 0
                    ),
                    "drawdown_improvement_pct": (
                        (abs(result_with.max_drawdown) - abs(result_without.max_drawdown)) /
                        abs(result_without.max_drawdown) * 100
                        if result_without.max_drawdown != 0 else 0
                    ),
                },
            }

            return comparison

        except Exception as e:
            self.logger.error(f"Failed to compare results: {e}")
            raise

    async def get_signal_visualization_data(self, result_id: str) -> Dict[str, Any]:
        """Get signal visualization data for dashboard"""
        try:
            result = await self.get_result(result_id)
            if not result:
                raise ValueError(f"Result {result_id} not found")

            # Generate signal timeline
            signal_timeline = []
            for trade in result.trades:
                signal_timeline.append({
                    "timestamp": trade.get("timestamp"),
                    "symbol": trade.get("symbol"),
                    "signal_type": trade.get("side"),  # buy/sell
                    "source": trade.get("signal_source", "unknown"),
                    "price": trade.get("price"),
                    "quantity": trade.get("quantity"),
                    "pnl": trade.get("pnl"),
                })

            # Calculate signal statistics
            signal_stats = {
                "total_signals": len(result.trades),
                "buy_signals": len([t for t in result.trades if t.get("side") == "buy"]),
                "sell_signals": len([t for t in result.trades if t.get("side") == "sell"]),
                "winning_signals": len([t for t in result.trades if t.get("pnl", 0) > 0]),
                "losing_signals": len([t for t in result.trades if t.get("pnl", 0) < 0]),
            }

            return {
                "signal_timeline": signal_timeline,
                "signal_statistics": signal_stats,
                "source_breakdown": result.signal_source_breakdown,
            }

        except Exception as e:
            self.logger.error(f"Failed to get signal visualization data: {e}")
            raise


# Global service instance
_result_service: Optional[BacktestResultService] = None


def get_result_service() -> BacktestResultService:
    """Get or create global result service instance"""
    global _result_service
    if _result_service is None:
        _result_service = BacktestResultService()
    return _result_service
