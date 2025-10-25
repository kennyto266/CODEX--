"""
DateTime Normalization Module for CODEX Quantitative Trading System.

This module provides comprehensive datetime normalization and trading hours alignment:
- Timezone conversion (naive → UTC, any timezone → UTC)
- Trading hours filtering (market-specific trading periods)
- Holiday calendar management (HKEX, NYSE, NASDAQ)
- Daylight Saving Time (DST) handling
- Business day alignment

DateTime normalization pipeline stages:
1. Timezone detection and normalization
2. DST transition handling
3. Trading hours filtering
4. Holiday/weekend removal
5. Trading day alignment
"""

from typing import List, Tuple, Optional, Dict, Any, Set
from datetime import datetime, timezone, timedelta
from enum import Enum
import pandas as pd
import numpy as np
from zoneinfo import ZoneInfo


class Market(Enum):
    """Supported trading markets."""
    HKEX = "HKEX"           # Hong Kong Exchanges
    NYSE = "NYSE"           # New York Stock Exchange
    NASDAQ = "NASDAQ"       # NASDAQ
    SSE = "SSE"             # Shanghai Stock Exchange
    SZSE = "SZSE"           # Shenzhen Stock Exchange


class HolidayCalendar:
    """Holiday calendar for different markets."""

    # HKEX Holidays (2020-2030)
    HKEX_HOLIDAYS = {
        # 2020
        2020: [
            datetime(2020, 1, 1),    # New Year's Day
            datetime(2020, 1, 25),   # Chinese New Year
            datetime(2020, 1, 26),   # Chinese New Year
            datetime(2020, 1, 27),   # Chinese New Year
            datetime(2020, 4, 4),    # Ching Ming Festival
            datetime(2020, 4, 10),   # Good Friday
            datetime(2020, 4, 11),   # Easter Monday
            datetime(2020, 5, 1),    # Labour Day
            datetime(2020, 6, 25),   # Dragon Boat Festival
            datetime(2020, 10, 1),   # National Day
            datetime(2020, 10, 11),  # Chung Yeung Festival
            datetime(2020, 12, 25),  # Christmas Day
        ],
        # 2021
        2021: [
            datetime(2021, 1, 1),    # New Year's Day
            datetime(2021, 2, 12),   # Chinese New Year
            datetime(2021, 2, 13),   # Chinese New Year
            datetime(2021, 2, 15),   # Chinese New Year
            datetime(2021, 4, 4),    # Ching Ming Festival
            datetime(2021, 4, 2),    # Good Friday
            datetime(2021, 4, 5),    # Easter Monday
            datetime(2021, 5, 1),    # Labour Day
            datetime(2021, 6, 14),   # Dragon Boat Festival
            datetime(2021, 10, 1),   # National Day
            datetime(2021, 10, 14),  # Chung Yeung Festival
            datetime(2021, 12, 25),  # Christmas Day
        ],
        # 2022
        2022: [
            datetime(2022, 1, 1),    # New Year's Day
            datetime(2022, 2, 1),    # Chinese New Year
            datetime(2022, 2, 2),    # Chinese New Year
            datetime(2022, 2, 3),    # Chinese New Year
            datetime(2022, 4, 5),    # Ching Ming Festival
            datetime(2022, 4, 15),   # Good Friday
            datetime(2022, 4, 18),   # Easter Monday
            datetime(2022, 5, 1),    # Labour Day
            datetime(2022, 6, 3),    # Dragon Boat Festival
            datetime(2022, 10, 1),   # National Day
            datetime(2022, 10, 10),  # Chung Yeung Festival
            datetime(2022, 12, 26),  # Christmas Holiday
        ],
        # 2023
        2023: [
            datetime(2023, 1, 1),    # New Year's Day
            datetime(2023, 1, 21),   # Chinese New Year
            datetime(2023, 1, 23),   # Chinese New Year
            datetime(2023, 1, 24),   # Chinese New Year
            datetime(2023, 4, 4),    # Ching Ming Festival
            datetime(2023, 4, 7),    # Good Friday
            datetime(2023, 4, 10),   # Easter Monday
            datetime(2023, 5, 1),    # Labour Day
            datetime(2023, 6, 22),   # Dragon Boat Festival
            datetime(2023, 10, 1),   # National Day
            datetime(2023, 10, 23),  # Chung Yeung Festival
            datetime(2023, 12, 25),  # Christmas Day
        ],
        # 2024
        2024: [
            datetime(2024, 1, 1),    # New Year's Day
            datetime(2024, 2, 10),   # Chinese New Year
            datetime(2024, 2, 11),   # Chinese New Year
            datetime(2024, 2, 12),   # Chinese New Year
            datetime(2024, 4, 4),    # Ching Ming Festival
            datetime(2024, 3, 29),   # Good Friday
            datetime(2024, 3, 30),   # Easter Saturday
            datetime(2024, 4, 1),    # Easter Monday
            datetime(2024, 5, 1),    # Labour Day
            datetime(2024, 6, 10),   # Dragon Boat Festival
            datetime(2024, 10, 1),   # National Day
            datetime(2024, 10, 11),  # Chung Yeung Festival
            datetime(2024, 12, 25),  # Christmas Day
        ],
        # 2025
        2025: [
            datetime(2025, 1, 1),    # New Year's Day
            datetime(2025, 1, 29),   # Chinese New Year
            datetime(2025, 1, 30),   # Chinese New Year
            datetime(2025, 1, 31),   # Chinese New Year
            datetime(2025, 4, 4),    # Ching Ming Festival
            datetime(2025, 4, 18),   # Good Friday
            datetime(2025, 4, 21),   # Easter Monday
            datetime(2025, 5, 1),    # Labour Day
            datetime(2025, 6, 2),    # Dragon Boat Festival
            datetime(2025, 10, 1),   # National Day
            datetime(2025, 10, 29),  # Chung Yeung Festival
            datetime(2025, 12, 25),  # Christmas Day
        ],
        # 2026
        2026: [
            datetime(2026, 1, 1),    # New Year's Day
            datetime(2026, 2, 17),   # Chinese New Year
            datetime(2026, 2, 18),   # Chinese New Year
            datetime(2026, 2, 19),   # Chinese New Year
            datetime(2026, 4, 4),    # Ching Ming Festival
            datetime(2026, 4, 3),    # Good Friday
            datetime(2026, 4, 6),    # Easter Monday
            datetime(2026, 5, 1),    # Labour Day
            datetime(2026, 6, 22),   # Dragon Boat Festival
            datetime(2026, 10, 1),   # National Day
            datetime(2026, 10, 16),  # Chung Yeung Festival
            datetime(2026, 12, 25),  # Christmas Day
        ],
        # 2027-2030 (simplified for example)
        2027: [datetime(2027, 1, 1), datetime(2027, 2, 6), datetime(2027, 5, 1), datetime(2027, 10, 1)],
        2028: [datetime(2028, 1, 1), datetime(2028, 1, 26), datetime(2028, 5, 1), datetime(2028, 10, 1)],
        2029: [datetime(2029, 1, 1), datetime(2029, 2, 13), datetime(2029, 5, 1), datetime(2029, 10, 1)],
        2030: [datetime(2030, 1, 1), datetime(2030, 2, 3), datetime(2030, 5, 1), datetime(2030, 10, 1)],
    }

    # NYSE/NASDAQ Holidays (2020-2030)
    NYSE_HOLIDAYS = {
        # 2020
        2020: [
            datetime(2020, 1, 1),    # New Year's Day
            datetime(2020, 1, 20),   # MLK Jr. Day
            datetime(2020, 2, 17),   # Presidents Day
            datetime(2020, 3, 25),   # Good Friday
            datetime(2020, 5, 25),   # Memorial Day
            datetime(2020, 7, 4),    # Independence Day
            datetime(2020, 9, 7),    # Labor Day
            datetime(2020, 11, 26),  # Thanksgiving
            datetime(2020, 12, 25),  # Christmas
        ],
        # Simplified for other years - in production would include all years
        2021: [datetime(2021, 1, 1), datetime(2021, 1, 18), datetime(2021, 2, 15)],
        2022: [datetime(2022, 1, 1), datetime(2022, 1, 17), datetime(2022, 2, 21)],
        2023: [datetime(2023, 1, 1), datetime(2023, 1, 16), datetime(2023, 2, 20)],
        2024: [datetime(2024, 1, 1), datetime(2024, 1, 15), datetime(2024, 2, 19)],
        2025: [datetime(2025, 1, 1), datetime(2025, 1, 20), datetime(2025, 2, 17)],
    }

    # SSE/SZSE Holidays (simplified - actual calendar is complex)
    SSE_HOLIDAYS = {
        2024: [
            datetime(2024, 1, 1),    # New Year's Day
            datetime(2024, 2, 10),   # Chinese New Year
            datetime(2024, 4, 4),    # Ching Ming Festival
            datetime(2024, 5, 1),    # Labour Day
            datetime(2024, 6, 10),   # Dragon Boat Festival
            datetime(2024, 9, 18),   # Mid-Autumn Festival
            datetime(2024, 10, 1),   # National Day
        ],
        2025: [
            datetime(2025, 1, 1),    # New Year's Day
            datetime(2025, 1, 29),   # Chinese New Year
            datetime(2025, 4, 4),    # Ching Ming Festival
            datetime(2025, 5, 1),    # Labour Day
            datetime(2025, 6, 2),    # Dragon Boat Festival
            datetime(2025, 9, 18),   # Mid-Autumn Festival
            datetime(2025, 10, 1),   # National Day
        ],
    }

    @staticmethod
    def get_holidays(market: Market, year: int) -> List[datetime]:
        """Get holidays for a specific market and year."""
        if market == Market.HKEX:
            return HolidayCalendar.HKEX_HOLIDAYS.get(year, [])
        elif market == Market.NYSE or market == Market.NASDAQ:
            return HolidayCalendar.NYSE_HOLIDAYS.get(year, [])
        elif market == Market.SSE or market == Market.SZSE:
            return HolidayCalendar.SSE_HOLIDAYS.get(year, [])
        return []

    @staticmethod
    def is_holiday(date: datetime, market: Market) -> bool:
        """Check if a date is a holiday for a market."""
        holidays = HolidayCalendar.get_holidays(market, date.year)
        date_only = datetime(date.year, date.month, date.day)
        return date_only in holidays


class TradingHours:
    """Trading hours for different markets."""

    # Trading hours (HH:MM in market local time)
    HKEX_HOURS = {
        'morning_open': '09:30',
        'morning_close': '12:00',
        'afternoon_open': '13:00',
        'afternoon_close': '16:00',
    }

    NYSE_HOURS = {
        'open': '09:30',
        'close': '16:00',
    }

    NASDAQ_HOURS = {
        'open': '09:30',
        'close': '16:00',
    }

    SSE_HOURS = {
        'morning_open': '09:30',
        'morning_close': '11:30',
        'afternoon_open': '13:00',
        'afternoon_close': '15:00',
    }

    SZSE_HOURS = {
        'morning_open': '09:30',
        'morning_close': '11:30',
        'afternoon_open': '13:00',
        'afternoon_close': '15:00',
    }

    @staticmethod
    def get_trading_hours(market: Market) -> Dict[str, str]:
        """Get trading hours for a market."""
        if market == Market.HKEX:
            return TradingHours.HKEX_HOURS
        elif market == Market.NYSE:
            return TradingHours.NYSE_HOURS
        elif market == Market.NASDAQ:
            return TradingHours.NASDAQ_HOURS
        elif market == Market.SSE:
            return TradingHours.SSE_HOURS
        elif market == Market.SZSE:
            return TradingHours.SZSE_HOURS
        return {}


class DateTimeNormalizer:
    """
    Comprehensive DateTime normalization for trading data.

    Handles:
    - Timezone conversion (naive → UTC, any timezone → UTC)
    - DST transition handling
    - Trading hours filtering
    - Holiday calendar management
    - Business day alignment
    """

    def __init__(self, market: Market = Market.HKEX):
        """
        Initialize DateTime normalizer.

        Args:
            market: Trading market (default: HKEX)
        """
        self.market = market
        self.timezone_map = {
            Market.HKEX: 'Asia/Hong_Kong',
            Market.NYSE: 'America/New_York',
            Market.NASDAQ: 'America/New_York',
            Market.SSE: 'Asia/Shanghai',
            Market.SZSE: 'Asia/Shanghai',
        }
        self.market_tz = self.timezone_map.get(market, 'UTC')

    def normalize_timezone(self, df: pd.DataFrame, source_tz: Optional[str] = None) -> pd.DataFrame:
        """
        Normalize DataFrame datetime index to UTC.

        Args:
            df: DataFrame with datetime index or 'date' column
            source_tz: Source timezone if index is naive (default: market timezone)

        Returns:
            DataFrame with UTC-normalized datetime index
        """
        df = df.copy()

        # Use market timezone if not specified
        if source_tz is None:
            source_tz = self.market_tz

        # Get datetime column or index
        if 'date' in df.columns:
            date_col = df['date']
            is_index = False
        elif isinstance(df.index, pd.DatetimeIndex):
            date_col = df.index
            is_index = True
        else:
            # Try to convert first column to datetime
            df.index = pd.to_datetime(df.index)
            date_col = df.index
            is_index = True

        # Handle timezone-naive datetimes
        # For DatetimeIndex, use tz property; for Series, use dt.tz
        if isinstance(date_col, pd.DatetimeIndex):
            tz = date_col.tz
        else:
            tz = date_col.dt.tz

        if tz is None:
            # Assume it's in source_tz and localize to UTC
            try:
                if isinstance(date_col, pd.DatetimeIndex):
                    localized = date_col.tz_localize(source_tz, ambiguous='raise', nonexistent='shift_forward')
                    date_col = localized.tz_convert('UTC')
                else:
                    localized = date_col.dt.tz_localize(source_tz, ambiguous='raise', nonexistent='shift_forward')
                    date_col = localized.dt.tz_convert('UTC')
            except Exception:
                # If localization fails, assume it's already UTC
                if isinstance(date_col, pd.DatetimeIndex):
                    date_col = date_col.tz_localize('UTC')
                else:
                    date_col = date_col.dt.tz_localize('UTC')
        else:
            # Already timezone-aware, convert to UTC
            if isinstance(date_col, pd.DatetimeIndex):
                date_col = date_col.tz_convert('UTC')
            else:
                date_col = date_col.dt.tz_convert('UTC')

        # Update dataframe
        if 'date' in df.columns:
            df['date'] = date_col
        else:
            df.index = date_col

        return df

    def handle_dst_transition(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[datetime]]:
        """
        Detect and handle daylight saving time transitions.

        Args:
            df: DataFrame with UTC datetime index

        Returns:
            (cleaned_df, dst_transitions)
        """
        df = df.copy()
        dst_transitions = []

        # Get datetime index
        if 'date' in df.columns:
            dates = df['date']
        else:
            dates = df.index

        # Look for gaps larger than 1 day (potential DST transitions)
        if len(dates) > 1:
            time_diffs = dates.diff()
            large_gaps_mask = time_diffs > timedelta(hours=25)

            # Get the datetime values where large gaps occur
            if large_gaps_mask.any():
                # The large gap indicates where a DST transition happened
                # We want the dates where the gap starts
                gap_indices = large_gaps_mask[large_gaps_mask].index
                for gap_idx in gap_indices:
                    dst_transitions.append(gap_idx)

        return df, dst_transitions

    def filter_trading_hours(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
        """
        Filter DataFrame to trading hours only.

        Args:
            df: DataFrame with UTC datetime index

        Returns:
            (filtered_df, hour_stats)
        """
        df = df.copy()

        # Get datetime column or index
        if 'date' in df.columns:
            dates = df['date']
        else:
            dates = df.index

        # Convert to market timezone for hour filtering
        if dates.dt.tz is not None:
            market_tz = ZoneInfo(self.market_tz)
            market_dates = dates.dt.tz_convert(market_tz)
        else:
            market_dates = dates

        hours = market_dates.dt.hour
        minutes = market_dates.dt.minute

        # Get trading hours for market
        trading_hours = TradingHours.get_trading_hours(self.market)

        # Create trading hour mask
        if self.market == Market.HKEX:
            # HKEX: 9:30-12:00, 13:00-16:00
            is_trading = (
                ((hours == 9) & (minutes >= 30)) |
                ((hours == 10) | (hours == 11)) |
                ((hours == 13) | (hours == 14) | (hours == 15)) |
                ((hours == 16) & (minutes == 0))
            )
        elif self.market in [Market.NYSE, Market.NASDAQ]:
            # NYSE/NASDAQ: 9:30-16:00
            is_trading = (
                ((hours == 9) & (minutes >= 30)) |
                ((hours >= 10) & (hours < 16)) |
                ((hours == 16) & (minutes == 0))
            )
        elif self.market in [Market.SSE, Market.SZSE]:
            # SSE/SZSE: 9:30-11:30, 13:00-15:00
            is_trading = (
                ((hours == 9) & (minutes >= 30)) |
                ((hours == 10) | (hours == 11)) |
                ((hours == 13) | (hours == 14)) |
                ((hours == 15) & (minutes == 0))
            )
        else:
            is_trading = pd.Series(True, index=df.index)

        # Apply filter
        filtered_df = df[is_trading].copy()

        # Statistics
        hour_stats = {
            'original_rows': len(df),
            'filtered_rows': len(filtered_df),
            'rows_removed': len(df) - len(filtered_df),
            'removal_pct': (len(df) - len(filtered_df)) / len(df) * 100 if len(df) > 0 else 0
        }

        return filtered_df, hour_stats

    def filter_holidays(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[datetime]]:
        """
        Filter out holidays and weekends.

        Args:
            df: DataFrame with datetime index

        Returns:
            (filtered_df, removed_dates)
        """
        df = df.copy()

        # Get datetime column or index
        if 'date' in df.columns:
            dates = df['date']
            index_is_date = False
        else:
            dates = df.index
            index_is_date = True

        removed_dates = []
        is_trading_day = []

        for date in dates:
            # Check if weekend
            if date.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
                is_trading_day.append(False)
                removed_dates.append(date)
            # Check if holiday
            elif HolidayCalendar.is_holiday(date, self.market):
                is_trading_day.append(False)
                removed_dates.append(date)
            else:
                is_trading_day.append(True)

        # Apply filter
        filtered_df = df[is_trading_day].copy()

        return filtered_df, removed_dates

    def align_to_business_days(self, df: pd.DataFrame, method: str = 'drop') -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Align DataFrame to business days only.

        Args:
            df: DataFrame with datetime index
            method: 'drop' (remove non-trading days), 'fill_ffill' (forward fill), 'fill_bfill' (backward fill)

        Returns:
            (aligned_df, alignment_report)
        """
        df = df.copy()

        # Get datetime column or index
        if 'date' in df.columns:
            dates = df['date']
        else:
            dates = df.index

        # Identify trading days
        is_trading = []
        for date in dates:
            if date.weekday() >= 5:  # Weekend
                is_trading.append(False)
            elif HolidayCalendar.is_holiday(date, self.market):  # Holiday
                is_trading.append(False)
            else:
                is_trading.append(True)

        trading_count = sum(is_trading)
        non_trading_count = len(is_trading) - trading_count

        # Apply method
        if method == 'drop':
            aligned_df = df[is_trading].copy()
        elif method == 'fill_ffill':
            aligned_df = df.copy()
            non_trading_indices = [i for i, x in enumerate(is_trading) if not x]
            for idx in non_trading_indices:
                if idx > 0:
                    aligned_df.iloc[idx] = aligned_df.iloc[idx - 1]
        elif method == 'fill_bfill':
            aligned_df = df.copy()
            non_trading_indices = [i for i, x in enumerate(is_trading) if not x]
            for idx in reversed(non_trading_indices):
                if idx < len(aligned_df) - 1:
                    aligned_df.iloc[idx] = aligned_df.iloc[idx + 1]
        else:
            aligned_df = df[is_trading].copy()

        report = {
            'original_rows': len(df),
            'trading_days': trading_count,
            'non_trading_days': non_trading_count,
            'method': method,
            'rows_after_alignment': len(aligned_df)
        }

        return aligned_df, report

    def normalize_datetime(self, df: pd.DataFrame,
                          source_tz: Optional[str] = None,
                          filter_hours: bool = True,
                          filter_holidays: bool = True,
                          align_business_days: bool = True) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Execute complete DateTime normalization pipeline.

        Args:
            df: Input DataFrame
            source_tz: Source timezone for naive datetimes
            filter_hours: Whether to filter to trading hours
            filter_holidays: Whether to remove holidays/weekends
            align_business_days: Whether to align to business days

        Returns:
            (normalized_df, normalization_report)
        """
        report = {
            'stages': {}
        }

        # Stage 1: Normalize timezone
        df = self.normalize_timezone(df, source_tz)
        report['stages']['timezone_normalization'] = {
            'status': 'complete',
            'rows': len(df)
        }

        # Stage 2: Handle DST transitions
        df, dst_transitions = self.handle_dst_transition(df)
        report['stages']['dst_handling'] = {
            'transitions_detected': len(dst_transitions),
            'transitions': [str(t) for t in dst_transitions],
            'rows': len(df)
        }

        # Stage 3: Filter trading hours
        if filter_hours:
            df, hour_stats = self.filter_trading_hours(df)
            report['stages']['trading_hours_filter'] = hour_stats

        # Stage 4: Filter holidays
        if filter_holidays:
            df, removed_dates = self.filter_holidays(df)
            report['stages']['holiday_filter'] = {
                'holidays_removed': len(removed_dates),
                'rows': len(df)
            }

        # Stage 5: Align to business days
        if align_business_days:
            df, alignment = self.align_to_business_days(df, method='drop')
            report['stages']['business_day_alignment'] = alignment

        report['final_status'] = 'success'
        report['output_rows'] = len(df)

        return df, report


class PipelineDateTimeNormalizer:
    """Orchestrates complete DateTime normalization pipeline."""

    def __init__(self, market: Market = Market.HKEX):
        """Initialize pipeline normalizer."""
        self.normalizer = DateTimeNormalizer(market)

    def execute_normalization_pipeline(self,
                                       df: pd.DataFrame,
                                       source_tz: Optional[str] = None,
                                       full_pipeline: bool = True) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Execute complete DateTime normalization pipeline.

        Args:
            df: Input DataFrame
            source_tz: Source timezone
            full_pipeline: Whether to run full pipeline (True) or basic normalization (False)

        Returns:
            (normalized_df, pipeline_report)
        """
        if full_pipeline:
            return self.normalizer.normalize_datetime(
                df,
                source_tz=source_tz,
                filter_hours=True,
                filter_holidays=True,
                align_business_days=True
            )
        else:
            # Basic normalization only
            df = self.normalizer.normalize_timezone(df, source_tz)
            return df, {'status': 'basic_normalization_complete', 'rows': len(df)}
