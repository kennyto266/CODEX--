"""
Market Data Domain Services
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class Quote:
    """Market quote data"""
    symbol: str
    price: float
    bid: Optional[float] = None
    ask: Optional[float] = None
    volume: Optional[int] = None
    timestamp: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "price": self.price,
            "bid": self.bid,
            "ask": self.ask,
            "volume": self.volume,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }


@dataclass
class HistoricalPrice:
    """Historical price data"""
    symbol: str
    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "date": self.date.isoformat(),
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume
        }


class MarketDataService:
    """Domain service for market data operations"""

    def __init__(self, data_adapter=None):
        """Initialize with a data adapter (implementation-specific)"""
        self._data_adapter = data_adapter
        self._price_cache: Dict[str, Quote] = {}
        self._cache_timestamp: Dict[str, datetime] = {}

    async def get_quote(self, symbol: str) -> Quote:
        """Get real-time quote for a symbol"""
        # Check cache first (cache for 5 seconds)
        now = datetime.now()
        if symbol in self._price_cache:
            cache_time = self._cache_timestamp.get(symbol)
            if cache_time and now - cache_time < timedelta(seconds=5):
                return self._price_cache[symbol]

        # In real implementation, fetch from data adapter
        # For now, return mock data
        quote = Quote(
            symbol=symbol,
            price=350.0 + hash(symbol) % 100,  # Mock price
            bid=349.5,
            ask=350.5,
            volume=1000000,
            timestamp=now
        )

        # Update cache
        self._price_cache[symbol] = quote
        self._cache_timestamp[symbol] = now

        return quote

    async def get_quotes(self, symbols: List[str]) -> List[Quote]:
        """Get real-time quotes for multiple symbols"""
        tasks = [self.get_quote(symbol) for symbol in symbols]
        return await asyncio.gather(*tasks)

    async def get_historical_prices(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[HistoricalPrice]:
        """Get historical price data"""
        # In real implementation, fetch from data adapter
        # For now, generate mock data
        prices = []
        current_date = start_date

        while current_date <= end_date:
            # Skip weekends (simplified)
            if current_date.weekday() < 5:
                base_price = 350.0 + hash(symbol) % 100
                price = HistoricalPrice(
                    symbol=symbol,
                    date=current_date,
                    open=base_price,
                    high=base_price * 1.02,
                    low=base_price * 0.98,
                    close=base_price * (0.99 + hash(str(current_date)) % 200 / 10000),
                    volume=1000000
                )
                prices.append(price)

            current_date += timedelta(days=1)

        return prices

    async def get_market_summary(self, symbols: List[str]) -> Dict[str, Any]:
        """Get market summary for multiple symbols"""
        quotes = await self.get_quotes(symbols)

        total_volume = sum(q.volume or 0 for q in quotes)
        avg_price = sum(q.price for q in quotes) / len(quotes) if quotes else 0

        # Calculate price changes (simplified - in real implementation, compare with previous close)
        price_changes = []
        for quote in quotes:
            # Mock price change calculation
            change = (hash(quote.symbol) % 200 - 100) / 100  # -1% to +1%
            price_changes.append(change)

        avg_change = sum(price_changes) / len(price_changes) if price_changes else 0

        return {
            "timestamp": datetime.now().isoformat(),
            "symbol_count": len(symbols),
            "total_volume": total_volume,
            "average_price": avg_price,
            "average_change_percent": avg_change * 100,
            "quotes": [q.to_dict() for q in quotes]
        }

    async def calculate_returns(self, symbol: str, days: int = 30) -> List[float]:
        """Calculate daily returns for a symbol"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        historical_prices = await self.get_historical_prices(symbol, start_date, end_date)

        # Sort by date
        historical_prices.sort(key=lambda p: p.date)

        # Calculate returns
        returns = []
        for i in range(1, len(historical_prices)):
            prev_close = historical_prices[i-1].close
            curr_close = historical_prices[i].close
            daily_return = (curr_close - prev_close) / prev_close
            returns.append(daily_return)

        return returns

    async def get_price_volatility(self, symbol: str, days: int = 30) -> float:
        """Calculate price volatility"""
        returns = await self.calculate_returns(symbol, days)

        if len(returns) < 2:
            return 0.0

        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)
        volatility = math.sqrt(variance) * math.sqrt(252)  # Annualized

        return volatility

    async def get_market_cap(self, symbol: str, shares_outstanding: float) -> float:
        """Calculate market capitalization"""
        quote = await self.get_quote(symbol)
        market_cap = quote.price * shares_outstanding
        return market_cap


import asyncio
import math
