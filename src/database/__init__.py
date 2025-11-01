"""
Database layer package.

Provides data persistence and retrieval interfaces:
- IDataRepository: Abstract repository interface
- MemoryRepository: In-memory storage
- SQLiteRepository: SQLite-based storage

Usage:
    from src.database import MemoryRepository, SQLiteRepository

    # Use memory repository (development)
    repo = MemoryRepository()

    # Use SQLite repository (production)
    repo = SQLiteRepository("data/quant_data.db")

    # Save data
    repo.save("0700.hk", df, data_type="stock")

    # Load data
    loaded_df = repo.load("0700.hk", start_date, end_date)
"""

from .repository import (
    IDataRepository,
    MemoryRepository,
    SQLiteRepository,
)

__all__ = [
    'IDataRepository',
    'MemoryRepository',
    'SQLiteRepository',
]
